#!/usr/bin/env python3
"""
smartpangolin.engine — deterministic, secret-scrubbing share packager (core).

This module is the deterministic core of SmartPangolin.

It takes a project tree (or the flat path list stage 1 emits), applies a
*mechanistic, versioned, deterministic* exclusion ruleset, and emits a zip that
is safe to hand to a cloud endpoint, together with the evidence needed to prove
what went in and what did not.

Design commitments
------------------
1. SECRETS ARE ALWAYS EXCLUDED, in both share modes. A credential is a
   credential. What ``--share`` switches is *local infrastructure disclosure*,
   not secrets.
2. FAIL CLOSED. Unreadable, undecodable, oversized or unknown-binary files are
   excluded rather than shipped unexamined.
3. NO SILENT REDACTION. A file is included whole or excluded whole. Rewriting
   file contents to "clean" them is not done: it is error prone and it makes the
   shipped artifact differ from the tree you tested.
4. DETERMINISTIC, at two levels:
   - ``content_sha256`` : hash over the sorted (path, filehash) list. Depends
     ONLY on what was packaged. Two runs over an unchanged tree always agree.
   - ``zip_sha256``     : hash of the artifact itself. Byte-identical across runs
     only if the embedded generation timestamp is pinned; set ``SOURCE_DATE_EPOCH``
     (or pass ``source_date_epoch``) to do that.
5. AUDITABLE. Every exclusion is recorded with its rule ID. Rule *values* are
   never recorded — only the rule that fired, the offset, and a length.

Stdlib only. Python 3.8+.
"""
from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import stat
import subprocess
import time
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ._version import __version__ as VERSION

POLICY_VERSION = "2026-08-02.1"

# Fixed DOS timestamp for every zip entry. Without this, mtimes leak into the
# archive and two runs over an identical tree produce different bytes.
FIXED_ZIP_DATE = (1980, 1, 1, 0, 0, 0)

MAX_SCAN_BYTES = 8 * 1024 * 1024        # files larger than this are not scanned
CONFIG_FILE = "patches_config.json"      # shared with stage 1 (folder_structure)
PANGOLIN_CONFIG = ".pangolin.json"   # SmartPangolin per-repo override standard


def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "replace").decode("ascii"))


# =============================================================================
# Rule engine
# =============================================================================
# Four families, each rule with a stable ID that appears verbatim in
# EXCLUSIONS.json so an operator can grep for it and tune the policy.
#
#   SEC-PATH-*   filename / glob / directory match       -> always excludes
#   SEC-CONT-*   anchored content regex for a credential  -> always excludes
#   LOC-*        local infrastructure disclosure          -> excludes in PUBLIC only
#   OPS-*        operational (unreadable, oversized, binary)

# --- SEC-PATH: files whose *existence* implies credentials -------------------
PATH_RULES = [
    ("SEC-PATH-ENV",        [".env", ".env.*", "*.env"],                        "dotenv file (credential store)"),
    ("SEC-PATH-PEM",        ["*.pem", "*.key", "*.p8", "*.pkcs8", "*.pkcs12"],  "private key material"),
    ("SEC-PATH-PFX",        ["*.pfx", "*.p12", "*.jks", "*.keystore", "*.bks"], "certificate/key store"),
    ("SEC-PATH-SSH",        ["id_rsa", "id_dsa", "id_ecdsa", "id_ed25519",
                             "*.ppk", "authorized_keys", "known_hosts"],        "SSH key material"),
    ("SEC-PATH-NETRC",      [".netrc", "_netrc", ".git-credentials",
                             ".pypirc", ".npmrc", ".dockercfg"],                "credential helper file"),
    ("SEC-PATH-CLOUD",      ["credentials", "credentials.json", "client_secret*.json",
                             "service-account*.json", "gcloud-*.json",
                             "*serviceaccount*.json", "azureauth.json"],        "cloud service-account credential"),
    ("SEC-PATH-KUBE",       ["kubeconfig", "*.kubeconfig", "admin.conf"],       "kubeconfig (cluster credential)"),
    ("SEC-PATH-VAULT",      ["*.kdbx", "*.kdb", "*.opvault", "*.agilekeychain",
                             ".vault-token", "*.gpg", "secring.*"],             "password vault / keyring"),
    ("SEC-PATH-TFSTATE",    ["*.tfstate", "*.tfstate.backup", "*.tfvars"],      "terraform state/vars (contains resolved secrets)"),
    ("SEC-PATH-HISTORY",    [".bash_history", ".zsh_history", ".psql_history",
                             ".mysql_history", ".python_history",
                             "ConsoleHost_history.txt"],                        "shell history (frequently contains pasted tokens)"),
    ("SEC-PATH-DBDUMP",     ["*.sql", "*.dump", "*.sqlite", "*.sqlite3", "*.db"],
     "database dump/file (unvetted payload)"),
]

# Directories that are never packaged, regardless of mode.
PATH_DIR_RULES = [
    ("SEC-DIR-SECRET",  {".secret", ".secrets"},
     "enforced secret directory (SmartPangolin standard) — never shipped in any mode"),
    ("SEC-DIR-SSH",     {".ssh", ".gnupg", ".aws", ".azure", ".kube", ".docker"},
     "credential directory"),
    ("SEC-DIR-VCS",     {".git", ".svn", ".hg"},
     "VCS metadata (packed refs and remotes may embed tokens)"),
    ("OPS-DIR-BUILD",   {"__pycache__", "node_modules", ".venv", "venv", "ft-venv",
                         "env", ".tox", ".mypy_cache", ".pytest_cache", ".next",
                         "dist", "build", "site-packages", ".terraform"},
     "build/vendor directory"),
]

# Explicit allowlist: these win over SEC-PATH so template files still ship.
PATH_ALLOWLIST = [".env.example", ".env.sample", ".env.template", "env.example"]


# --- SEC-CONT: anchored credential formats -----------------------------------
# Every pattern is anchored on a vendor-specific prefix and a fixed body length.
# That is what makes them deterministic and low-noise: they match the token
# *format*, not "something that looks secret".
CONTENT_RULES = [
    ("SEC-CONT-HF",        r"\bhf_[A-Za-z0-9]{34}\b",                                    "HuggingFace access token"),
    ("SEC-CONT-AWSKEY",    r"\b(?:AKIA|ASIA|ABIA|ACCA)[0-9A-Z]{16}\b",                   "AWS access key ID"),
    ("SEC-CONT-AWSSEC",    r"(?i)aws_secret_access_key\s*[=:]\s*[\"']?[A-Za-z0-9/+=]{40}", "AWS secret access key"),
    ("SEC-CONT-GHPAT",     r"\bgh[pousr]_[A-Za-z0-9]{36}\b",                             "GitHub personal access token"),
    ("SEC-CONT-GHFINE",    r"\bgithub_pat_[A-Za-z0-9_]{60,}\b",                          "GitHub fine-grained PAT"),
    ("SEC-CONT-GITLAB",    r"\bglpat-[A-Za-z0-9_\-]{20}\b",                              "GitLab personal access token"),
    # Anthropic first: its prefix is a subset of the OpenAI pattern, so the more
    # specific rule must be evaluated earlier or the attribution is wrong.
    ("SEC-CONT-ANTHROPIC", r"\bsk-ant-[A-Za-z0-9_\-]{24,}\b",                            "Anthropic API key"),
    ("SEC-CONT-OPENAI",    r"\bsk-(?!ant-)(?:proj-)?[A-Za-z0-9_\-]{32,}\b",              "OpenAI API key"),
    ("SEC-CONT-SLACK",     r"\bxox[baprse]-[A-Za-z0-9\-]{10,}\b",                        "Slack token"),
    ("SEC-CONT-GOOGLE",    r"\bAIza[0-9A-Za-z_\-]{35}\b",                                "Google API key"),
    ("SEC-CONT-STRIPE",    r"\b[rs]k_(?:live|test)_[A-Za-z0-9]{24,}\b",                  "Stripe secret key"),
    ("SEC-CONT-NPM",       r"\bnpm_[A-Za-z0-9]{36}\b",                                   "npm access token"),
    ("SEC-CONT-PYPI",      r"\bpypi-AgEIcHlwaS5vcmc[A-Za-z0-9_\-]{50,}\b",               "PyPI upload token"),
    ("SEC-CONT-TELEGRAM",  r"\b\d{8,10}:AA[A-Za-z0-9_\-]{33}\b",                         "Telegram bot token"),
    ("SEC-CONT-SENDGRID",  r"\bSG\.[A-Za-z0-9_\-]{22}\.[A-Za-z0-9_\-]{43}\b",            "SendGrid API key"),
    ("SEC-CONT-PEM",       r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----", "inline PEM private key"),
    ("SEC-CONT-PUTTY",     r"PuTTY-User-Key-File-\d",                                    "inline PuTTY private key"),
    ("SEC-CONT-JWT",       r"\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b", "JWT (may be a live bearer token)"),
    ("SEC-CONT-DOCKERAUTH", r"\"auths\"\s*:\s*\{",                                       "docker registry auth block"),
    ("SEC-CONT-CONNSTR",   r"(?i)\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp|mssql)://[^\s:@/\"']+:[^\s:@/\"']+@", "connection string with inline password"),
    # Deliberately broader. Fires on assignment of a non-trivial literal to a
    # secret-named key. Produces occasional false positives; those are visible
    # in EXCLUSIONS.json and allowlistable. Fail-closed is the correct default.
    ("SEC-CONT-ASSIGN",
     r"(?i)\b(?:api[_\-]?key|secret[_\-]?key|access[_\-]?token|auth[_\-]?token|"
     r"client[_\-]?secret|private[_\-]?key|passwd|password|bearer[_\-]?token)\b"
     r"\s*[:=]\s*[\"'][^\"'\n]{8,}[\"']",
     "secret-named variable assigned a literal value"),
]

# --- LOC: local infrastructure. Excluded in PUBLIC, retained in PRIVATE. ------
# Note 127.0.0.1 and localhost are intentionally absent: they disclose nothing
# about your network, and excluding them would drop nearly every server script.
LOCAL_RULES = [
    ("LOC-RFC1918",  r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
                     r"|192\.168\.\d{1,3}\.\d{1,3}"
                     r"|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b",   "private (RFC1918) IP address"),
    ("LOC-CGNAT",    r"\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b", "CGNAT/tailnet IP address"),
    ("LOC-IPV6ULA",  r"\bfd[0-9a-f]{2}:(?:[0-9a-f]{0,4}:){1,6}[0-9a-f]{0,4}\b", "IPv6 unique-local address"),
    ("LOC-UNC",      r"\\\\[A-Za-z0-9][A-Za-z0-9._\-]{1,62}\\",             "UNC network share path"),
    ("LOC-WINUSER",  r"[A-Za-z]:\\Users\\[^\\\s\"'<>|]+",                   "Windows user profile path"),
    ("LOC-NIXUSER",  r"/(?:home|Users)/(?!runner\b|user\b|ubuntu\b)[A-Za-z0-9._\-]+/", "POSIX home directory with username"),
    ("LOC-INTHOST",  r"\b[a-z0-9][a-z0-9\-]{0,62}\.(?:local|lan|internal|intranet|corp|home|arpa)\b", "internal hostname"),
    ("LOC-MAC",      r"\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b",           "MAC address"),
    ("LOC-SSHCFG",   r"(?m)^\s*HostName\s+\S+",                             "SSH client host configuration"),
]

# Mirrors stage-2 DEFAULT_SOURCE_EXTENSIONS (used by --source-only).
SOURCE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".html", ".htm", ".css", ".scss", ".sass",
    ".java", ".c", ".cpp", ".h", ".hpp",
    ".go", ".rs", ".rb", ".php", ".tf", ".mod",
    ".sh", ".bash", ".zsh",
    ".json", ".yaml", ".yml", ".toml", ".ini",
    ".md", ".txt", ".rst",
    ".sql", ".xml", ".xsl", ".xslt",
    ".conf", ".config", ".gitignore",
}
SOURCE_EXTENSIONLESS = {"dockerfile", "docker-compose.yml", "makefile", "cmakelists.txt"}

# Language fence map so merged output is identical in form to stage 2.
LANG_MAP = {
    "py": "python", "js": "javascript", "jsx": "jsx", "ts": "typescript", "tsx": "tsx",
    "html": "html", "css": "css", "java": "java", "c": "c", "cpp": "cpp", "go": "go",
    "rs": "rust", "rb": "ruby", "php": "php", "sh": "bash", "bash": "bash",
    "json": "json", "yaml": "yaml", "yml": "yaml", "toml": "toml", "md": "markdown",
    "sql": "sql", "xml": "xml",
}

BINARY_SAFE_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
}


def compile_rules(user_path_rules=None):
    """Compile content/local regexes once. ``user_path_rules`` are extra
    SEC-PATH-USER globs contributed by ``.pangolin.json``; they are matched
    by :func:`match_path_rules` (glob based) so nothing to compile here."""
    return {
        "content": [(rid, re.compile(pat), desc) for rid, pat, desc in CONTENT_RULES],
        "content_relaxed": [(rid, re.compile(pat.replace(r"\b", "")), desc)
                            for rid, pat, desc in CONTENT_RULES],
        "local":   [(rid, re.compile(pat), desc) for rid, pat, desc in LOCAL_RULES],
        "user_path": list(user_path_rules or []),
    }


def policy_fingerprint(user=None):
    """Stable hash of the ruleset. Changes if any rule *or user override*
    changes -> visible in every manifest and ledger entry."""
    blob = json.dumps(
        {
            "version": POLICY_VERSION,
            "path": PATH_RULES,
            "dirs": [[r, sorted(s), d] for r, s, d in PATH_DIR_RULES],
            "allow": PATH_ALLOWLIST,
            "content": CONTENT_RULES,
            "local": LOCAL_RULES,
            "user": user or {},
        },
        sort_keys=True,
    ).encode()
    return hashlib.sha256(blob).hexdigest()


# =============================================================================
# .pangolin.json — per-repo override standard
# =============================================================================

def load_pangolin_config(root: Path):
    """Read the optional ``.pangolin.json`` override file at the repo root.

    Recognised keys (all optional):
      share_mode      : "public" | "private"     default share mode
      source_only     : bool
      max_chars       : int
      allow           : [relpath, ...]           force-include despite a rule
      deny_globs      : [glob, ...]              extra SEC-PATH-USER exclusions
      exclude_folders : [name, ...]
      exclude_paths   : [relpath, ...]

    Returns (config_dict, user_policy_dict). ``user_policy_dict`` is what folds
    into the policy fingerprint so every override is auditable.
    """
    cfg_path = root / PANGOLIN_CONFIG
    if not cfg_path.is_file():
        return {}, {}
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        safe_print(f"WARNING: could not parse {PANGOLIN_CONFIG}: {e}; ignoring it")
        return {}, {}
    user_policy = {
        "deny_globs": sorted(cfg.get("deny_globs", [])),
        "allow": sorted(cfg.get("allow", [])),
        "exclude_folders": sorted(x.lower() for x in cfg.get("exclude_folders", [])),
        "exclude_paths": sorted(cfg.get("exclude_paths", [])),
    }
    return cfg, user_policy


def user_path_rules_from_config(user_policy):
    """Turn deny_globs into a SEC-PATH-USER rule tuple list."""
    globs = user_policy.get("deny_globs") if user_policy else None
    if not globs:
        return []
    return [("SEC-PATH-USER", [g.lower() for g in globs],
             "excluded by .pangolin.json deny_globs")]


# =============================================================================
# Classification helpers
# =============================================================================

def is_backup_name(name: str) -> bool:
    b = os.path.basename(name)
    return (".bak" in b.lower() or b.endswith("~") or b.startswith("~$"))


def is_source_name(name: str) -> bool:
    low = name.lower()
    ext = os.path.splitext(low)[1]
    if not ext:
        return low in SOURCE_EXTENSIONLESS
    return ext in SOURCE_EXTENSIONS


def match_path_rules(name: str, user_path_rules=None):
    low = name.lower()
    if low in PATH_ALLOWLIST:
        return None
    for rid, globs, desc in (user_path_rules or []):
        for g in globs:
            if fnmatch.fnmatch(low, g):
                return (rid, desc, g)
    for rid, globs, desc in PATH_RULES:
        for g in globs:
            if fnmatch.fnmatch(low, g):
                return (rid, desc, g)
    if is_backup_name(name):
        return ("OPS-BACKUP", "backup/temp file (may hold rotated-out credentials)",
                "backup name pattern")
    return None


def match_dir_rules(dirname: str):
    low = dirname.lower()
    for rid, names, desc in PATH_DIR_RULES:
        if low in names:
            return (rid, desc)
    if low.startswith("venv_") or low.endswith("_venv") or low.endswith("-venv"):
        return ("OPS-DIR-BUILD", "virtualenv directory (wildcard match)")
    return None


_INVISIBLE = {c: None for c in (0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF, 0x00AD)}


def _strip_invisible(t):
    """Remove zero-width / invisible characters used to break token matches."""
    return t.translate(_INVISIBLE)


def _read_head_tail(path, n=1_048_576):
    """First n and last n bytes of a large file (secrets often sit at the edges)."""
    try:
        with path.open("rb") as fh:
            head = fh.read(n)
            try:
                fh.seek(-n, 2); tail = fh.read()
            except OSError:
                tail = b""
        return head + b"\n" + tail
    except OSError:
        return b""


def _scan_text(text, rules, share_mode, secrets_only=False, relaxed=False):
    hits = []
    content = rules.get("content_relaxed", rules["content"]) if relaxed else rules["content"]
    for order, (rid, rx, desc) in enumerate(content):
        m = rx.search(text)
        if m:
            hits.append({"rule": rid, "desc": desc, "offset": m.start(),
                         "match_len": m.end() - m.start(), "family": "secret", "order": order})
    if share_mode == "public" and not secrets_only:
        base = len(rules["content"])
        for order, (rid, rx, desc) in enumerate(rules["local"]):
            m = rx.search(text)
            if m:
                hits.append({"rule": rid, "desc": desc, "offset": m.start(),
                             "match_len": m.end() - m.start(), "family": "local", "order": base + order})
    return hits


def _binary_secret_scan(raw, rules):
    """Best-effort ASCII secret scan of a binary/oversize file (secrets only)."""
    return _scan_text(_strip_invisible(raw.decode("latin-1", "ignore")), rules, "public", secrets_only=True, relaxed=True)


def scan_content(path: Path, rules, share_mode: str, size: int):
    """Return (list_of_hits, ops_reason_or_None). Hits carry rule id + offset only."""
    ext = path.suffix.lower()

    if size > MAX_SCAN_BYTES:
        if ext in BINARY_SAFE_EXTS:
            hits = _binary_secret_scan(_read_head_tail(path), rules)
            return (hits, None) if hits else ([], None)
        return [], ("OPS-OVERSIZE", f"file exceeds {MAX_SCAN_BYTES // (1024*1024)} MB scan limit")

    try:
        raw = path.read_bytes()
    except (OSError, PermissionError) as e:
        return [], ("OPS-UNREADABLE", f"cannot read file ({e.__class__.__name__})")

    if b"\x00" in raw[:8192]:
        if ext in BINARY_SAFE_EXTS:
            hits = _binary_secret_scan(raw, rules)
            return (hits, None) if hits else ([], None)
        return [], ("OPS-BINARY", "binary content cannot be verified; excluded fail-closed")

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("latin-1")
        except Exception:
            return [], ("OPS-UNDECODABLE", "content not decodable as text")

    text = _strip_invisible(text)
    hits = _scan_text(text, rules, share_mode)
    return hits, None


def build_merged_shards(included, max_chars: int, prefix: str):
    """Merge included files into character-bounded shards.

    CRITICAL ORDERING: this runs on the *classified* include list, never on the
    raw candidate list. Stage 2 merged before any secret check, so a .env ended
    up inlined verbatim in source_code_part1.txt — merging here instead means a
    dropped file is absent from the shards too, rather than taking the whole
    shard down with it.
    """
    ordered = sorted(included, key=lambda i: (i["size"], i["path"]))
    shards, cur, cur_len = [], [], 0

    for item in ordered:
        ext = os.path.splitext(item["path"])[1].lstrip(".").lower()
        lang = LANG_MAP.get(ext, "")
        try:
            body = item["abs"].read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        numbered = "\n".join(f"{str(n + 1).rjust(4)} | {line.rstrip()}"
                              for n, line in enumerate(body.splitlines()))
        block = f"### {item['path']}\n```{lang}\n{numbered}\n```\n\n"

        if cur and cur_len + len(block) > max_chars:
            shards.append("".join(cur))
            cur, cur_len = [], 0
        cur.append(block)
        cur_len += len(block)

    if cur:
        shards.append("".join(cur))

    width = max(2, len(str(len(shards))))
    return [(f"_MERGED/{prefix}source_code_part{n + 1:0{width}d}.txt", text)
            for n, text in enumerate(shards)]


def git_tracked(root: Path):
    """git ls-files, for provenance: what the repo tracks vs what we shipped."""
    if not (root / ".git").is_dir():
        return None
    try:
        r = subprocess.run(["git", "ls-files"], cwd=str(root), capture_output=True,
                           text=True, check=True, encoding="utf-8", timeout=60)
        return sorted(line.strip() for line in r.stdout.splitlines() if line.strip())
    except (subprocess.SubprocessError, OSError):
        return None


def sha256_file(path: Path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(chunk), b""):
            h.update(blk)
    return h.hexdigest()


# =============================================================================
# Collection
# =============================================================================

def clean_staged_shards(out_dir: Path, prefix: str = "", debug: bool = False):
    """Remove shard .txt files from a previous run so a run at a smaller
    --max-chars can't leave orphaned high-numbered parts behind."""
    if not out_dir.is_dir():
        return 0
    n = 0
    for f in sorted(out_dir.glob(f"{prefix}source_code_part*.txt")):
        try:
            f.unlink()
            n += 1
            if debug:
                safe_print(f"  [clean] {f.name}")
        except OSError as e:
            safe_print(f"  [clean] FAILED {f.name}: {e}")
    return n


def load_shared_config(config_file: str = CONFIG_FILE):
    """Honour the same patches_config.json stage 1 reads."""
    extra_dirs, extra_exts, extra_names = set(), set(), set()
    if os.path.exists(config_file):
        try:
            cfg = json.loads(Path(config_file).read_text(encoding="utf-8"))
            extra_dirs.update(x.lower() for x in cfg.get("exclude_dirs", []))
            extra_exts.update(x.lower() for x in cfg.get("exclude_exts", []))
            extra_names.update(x.lower() for x in cfg.get("exclude_filenames", []))
        except (json.JSONDecodeError, OSError):
            safe_print(f"WARNING: could not parse {config_file}; using built-in policy only")
    return extra_dirs, extra_exts, extra_names


def collect_candidates(root: Path, archive_dir: Path, *, focus=None, files=None,
                       path_output="file_folder_path.txt", rebuild_tree=False,
                       source_only=False, exclude_paths=None, exclude_folders=None,
                       exclude_ext=None, extra_dirs=None, extra_exts=None,
                       extra_names=None, gitignore_spec=None, gitignore_sink=None):
    """Prefer the path list from stage 1; else walk the filesystem.

    The archive directory is always excluded from its own scan.
    """
    extra_dirs = extra_dirs or set()
    extra_exts = extra_exts or set()
    extra_names = extra_names or set()

    scan_root = (root / focus if focus else root).resolve()
    archive_res = archive_dir.resolve()

    def in_archive(p: Path):
        try:
            p.relative_to(archive_res)
            return True
        except ValueError:
            return False

    ex_paths = [(root / p).resolve() for p in (exclude_paths or [])]

    def under_excluded(p: Path):
        for ep in ex_paths:
            try:
                p.relative_to(ep)
                return True
            except ValueError:
                continue
        return False

    root_res = root.resolve()
    def gi_ignored(p: Path, is_dir: bool):
        if not gitignore_spec:
            return False
        try:
            rel = p.resolve().relative_to(root_res).as_posix()
        except ValueError:
            return False
        if gitignore_spec.ignored(rel, is_dir):
            if gitignore_sink is not None:
                gitignore_sink.append(rel + ('/' if is_dir else ''))
            return True
        return False

    def keep(p: Path):
        if in_archive(p) or under_excluded(p):
            return False
        if gi_ignored(p, p.is_dir()):
            return False
        if source_only and not is_source_name(p.name):
            return False
        return True

    if files:
        return sorted({(root / f).resolve() for f in files
                       if keep((root / f).resolve())}), "explicit files"

    plist = Path(path_output)
    if plist.exists() and not rebuild_tree:
        out = []
        for line in plist.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.endswith("/") or line == "./":
                continue
            p = Path(line)
            if not p.is_absolute():
                p = root / p
            rp = p.resolve()
            if p.is_file() and keep(rp):
                out.append(rp)
        if out:
            mode = " +source-only" if source_only else ""
            return sorted(set(out)), f"path list ({plist}){mode}"

    out = []
    skip_dirs = set(extra_dirs)
    user_dirs = {d.lower() for d in (exclude_folders or [])}

    for cur, dirnames, filenames in os.walk(scan_root, topdown=True):
        if in_archive(Path(cur).resolve()):
            dirnames[:] = []
            continue
        keep_dirs = []
        for d in dirnames:
            dl = d.lower()
            full = (Path(cur) / d).resolve()
            if match_dir_rules(d) or dl in skip_dirs or dl in user_dirs:
                continue
            if in_archive(full) or under_excluded(full):
                continue
            if gi_ignored(full, True):
                continue
            keep_dirs.append(d)
        dirnames[:] = sorted(keep_dirs)
        for f in filenames:
            fl = f.lower()
            if fl in extra_names:
                continue
            ext = os.path.splitext(fl)[1]
            if ext and (ext in extra_exts or ext in {e.lower() for e in (exclude_ext or [])}):
                continue
            if source_only and not is_source_name(f):
                continue
            if gi_ignored(Path(cur) / f, False):
                continue
            out.append((Path(cur) / f).resolve())
    mode = " +source-only" if source_only else ""
    return sorted(set(out)), f"filesystem walk ({scan_root}){mode}"


def classify(candidates, root: Path, rules, share_mode: str, debug: bool = False):
    included, excluded = [], []
    user_path_rules = rules.get("user_path")
    for p in candidates:
        try:
            rel = p.relative_to(root).as_posix()
        except ValueError:
            rel = p.name

        pr = match_path_rules(p.name, user_path_rules)
        if pr:
            rid, desc, glob = pr
            excluded.append({"path": rel, "rule": rid, "desc": desc,
                             "detail": f"matched glob '{glob}'", "family": "secret"})
            continue

        try:
            size = p.stat().st_size
        except OSError as e:
            hint = ""
            if len(str(p)) > 255:
                hint = f"; path is {len(str(p))} chars — likely Windows MAX_PATH"
            excluded.append({"path": rel, "rule": "OPS-STAT",
                             "desc": "cannot stat file",
                             "detail": f"{e.__class__.__name__}: "
                                       f"{getattr(e, 'strerror', None) or e}{hint}",
                             "family": "ops",
                             "abs_path_len": len(str(p))})
            continue

        hits, ops = scan_content(p, rules, share_mode, size)
        if ops:
            excluded.append({"path": rel, "rule": ops[0], "desc": ops[1],
                             "detail": f"{size} bytes", "family": "ops"})
            continue
        if hits:
            top = min(hits, key=lambda h: (h["offset"], h["order"]))
            excluded.append({"path": rel, "rule": top["rule"], "desc": top["desc"],
                             "detail": f"first match at byte {top['offset']}, "
                                       f"length {top['match_len']}",
                             "family": top["family"],
                             "all_rules": sorted({h["rule"] for h in hits})})
            if debug:
                safe_print(f"  [drop] {rel}  <- {top['rule']}")
            continue

        included.append({"path": rel, "abs": p, "size": size})

    included.sort(key=lambda d: d["path"])
    excluded.sort(key=lambda d: d["path"])
    return included, excluded


# =============================================================================
# Zip writing
# =============================================================================

def _tally(excluded):
    out = {}
    for e in excluded:
        out[e["rule"]] = out.get(e["rule"], 0) + 1
    return dict(sorted(out.items()))


def write_zip(zip_path: Path, included, excluded, meta, dry_run: bool,
              merge: bool = True, include_raw: bool = True,
              max_chars: int = 3500000, prefix: str = "",
              git_list=None, stage_dir: Path = None, keep_txt: bool = False,
              debug: bool = False):
    manifest_files = []
    for item in included:
        item["sha256"] = sha256_file(item["abs"])
        manifest_files.append({"path": item["path"], "size": item["size"],
                               "sha256": item["sha256"]})

    ch = hashlib.sha256()
    for f in manifest_files:
        ch.update(f["path"].encode("utf-8"))
        ch.update(b"\x00")
        ch.update(f["sha256"].encode("ascii"))
        ch.update(b"\n")
    content_sha256 = ch.hexdigest()
    meta["content_sha256"] = content_sha256

    manifest = {
        "schema": "smartpangolin.share_manifest/v1",
        "legacy_schema": "smarttasks.share_manifest/v1",
        "generated_utc": meta["generated_utc"],
        "share_mode": meta["share_mode"],
        "policy_version": POLICY_VERSION,
        "policy_sha256": meta["policy_sha256"],
        "content_sha256": content_sha256,
        "tool_version": VERSION,
        "source_root": meta["source_root"],
        "focus": meta["focus"],
        "selection": meta["selection"],
        "overrides": meta.get("overrides", []),
        "file_count": len(manifest_files),
        "total_bytes": sum(f["size"] for f in manifest_files),
        "excluded_count": len(excluded),
        "files": manifest_files,
    }
    exclusions = {
        "schema": "smartpangolin.share_exclusions/v1",
        "generated_utc": meta["generated_utc"],
        "share_mode": meta["share_mode"],
        "policy_sha256": meta["policy_sha256"],
        "note": "Rule IDs and offsets only. Matched values are never recorded.",
        "count": len(excluded),
        "by_rule": _tally(excluded),
        "entries": excluded,
    }
    policy = {
        "schema": "smartpangolin.share_policy/v1",
        "policy_version": POLICY_VERSION,
        "policy_sha256": meta["policy_sha256"],
        "share_mode": meta["share_mode"],
        "semantics": {
            "secret_rules": "always enforced, both modes",
            "local_rules": "enforced in public mode only; retained in private mode",
            "ops_rules": "fail-closed: unreadable/oversize/binary content is excluded",
            "redaction": "none - files are included whole or excluded whole",
        },
        "path_rules": [{"id": r, "globs": g, "desc": d} for r, g, d in PATH_RULES],
        "dir_rules": [{"id": r, "names": sorted(s), "desc": d} for r, s, d in PATH_DIR_RULES],
        "path_allowlist": PATH_ALLOWLIST,
        "content_rules": [{"id": r, "desc": d} for r, _, d in CONTENT_RULES],
        "local_rules": [{"id": r, "desc": d} for r, _, d in LOCAL_RULES],
        "user_overrides": meta.get("user_policy", {}),
    }
    merged = build_merged_shards(included, max_chars, prefix) if merge else []
    manifest["merged"] = {
        "enabled": merge,
        "shard_count": len(merged),
        "max_chars": max_chars if merge else None,
        "raw_files_included": include_raw,
        "shards": [{"path": n, "chars": len(t),
                    "sha256": hashlib.sha256(t.encode("utf-8")).hexdigest()}
                   for n, t in merged],
        "note": "Shards are built from the included set only; excluded files "
                "never appear in merged output.",
    }
    if git_list is not None:
        shipped = {f["path"] for f in manifest_files}
        manifest["git"] = {
            "tracked_count": len(git_list),
            "tracked_not_shipped": sorted(set(git_list) - shipped),
            "shipped_not_tracked": sorted(shipped - set(git_list)),
        }

    sha_lines = "".join(f"{f['sha256']}  {f['path']}\n" for f in manifest_files)
    sha_lines += "".join(
        f"{hashlib.sha256(t.encode('utf-8')).hexdigest()}  {n}\n" for n, t in merged)
    report = render_report(manifest, exclusions, meta)

    if dry_run:
        return manifest, exclusions, report, None

    zip_path.parent.mkdir(parents=True, exist_ok=True)

    def _add(zf, name, payload):
        zi = zipfile.ZipInfo(name, date_time=FIXED_ZIP_DATE)
        zi.compress_type = zipfile.ZIP_DEFLATED
        zi.external_attr = (stat.S_IFREG | 0o644) << 16
        zf.writestr(zi, payload)

    staged = []
    if merged and stage_dir is not None:
        stage_dir.mkdir(parents=True, exist_ok=True)
        for name, text in merged:
            f = stage_dir / os.path.basename(name)
            f.write_text(text, encoding="utf-8")
            staged.append((f, name))
            if debug:
                safe_print(f"  [stage] {f}  ({len(text):,} chars)")

    try:
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED,
                             compresslevel=6) as zf:
            if include_raw:
                for item in included:
                    _add(zf, item["path"], item["abs"].read_bytes())
            if staged:
                for f, name in staged:
                    _add(zf, name, f.read_text(encoding="utf-8"))
            else:
                for name, text in merged:
                    _add(zf, name, text)
            if git_list is not None:
                _add(zf, "_SHARE/GIT_TRACKED.txt", "\n".join(git_list) + "\n")
            for name, payload in (
                ("_SHARE/MANIFEST.json", json.dumps(manifest, indent=2)),
                ("_SHARE/EXCLUSIONS.json", json.dumps(exclusions, indent=2)),
                ("_SHARE/POLICY.json", json.dumps(policy, indent=2)),
                ("_SHARE/SHA256SUMS", sha_lines),
                ("_SHARE/SHARE_REPORT.md", report),
            ):
                _add(zf, name, payload)
    finally:
        if staged and not keep_txt:
            for f, _ in staged:
                try:
                    f.unlink()
                    if debug:
                        safe_print(f"  [clean] {f.name}")
                except OSError as e:
                    safe_print(f"  [clean] FAILED {f.name}: {e}")

    return manifest, exclusions, report, sha256_file(zip_path)


def render_report(manifest, exclusions, meta):
    lines = [
        f"# SmartPangolin share report — {meta['share_mode'].upper()}",
        "",
        f"- Generated: {meta['generated_utc']}",
        f"- Source root: `{meta['source_root']}`",
        f"- Focus: `{meta['focus'] or '(none)'}`",
        f"- Selection: {meta['selection']}",
        f"- Policy: {POLICY_VERSION} (`{meta['policy_sha256'][:16]}…`)",
        f"- Content SHA256: `{meta['content_sha256']}`",
        f"- Tool: smartpangolin {VERSION}",
        "",
        f"**Included: {manifest['file_count']} files, "
        f"{manifest['total_bytes'] / 1024:.1f} KiB**  ",
        f"**Excluded: {exclusions['count']} files**",
        (f"**Merged: {manifest['merged']['shard_count']} shard(s) @ "
         f"{manifest['merged']['max_chars']:,} chars**"
         if manifest["merged"]["enabled"] else "**Merged: disabled**"),
        "",
        "## Exclusions by rule",
        "",
        "| Rule | Count | Meaning |",
        "|---|---:|---|",
    ]
    desc = {r: d for r, _, d in CONTENT_RULES}
    desc.update({r: d for r, _, d in LOCAL_RULES})
    desc.update({r: d for r, _, d in PATH_RULES})
    desc.update({r: d for r, _, d in PATH_DIR_RULES})
    desc.update({
        "OPS-BACKUP": "backup/temp file",
        "OPS-BINARY": "binary content, excluded fail-closed",
        "OPS-OVERSIZE": "exceeds scan size limit",
        "OPS-UNREADABLE": "unreadable",
        "OPS-UNDECODABLE": "undecodable",
        "OPS-STAT": "cannot stat",
        "SEC-PATH-USER": "excluded by .pangolin.json deny_globs",
    })
    for rule, count in exclusions["by_rule"].items():
        lines.append(f"| `{rule}` | {count} | {desc.get(rule, '')} |")
    if not exclusions["by_rule"]:
        lines.append("| — | 0 | nothing excluded |")

    lines += ["", "## Excluded files", ""]
    for e in exclusions["entries"]:
        lines.append(f"- `{e['path']}` — **{e['rule']}** ({e['desc']}); {e['detail']}")
    if not exclusions["entries"]:
        lines.append("_none_")

    lines += [
        "", "## Verification", "",
        "```bash",
        "unzip -p <zip> _SHARE/SHA256SUMS > /tmp/sums",
        "unzip -d /tmp/share <zip> && cd /tmp/share && sha256sum -c /tmp/sums",
        "```",
        "",
        "Re-running SmartPangolin over an unchanged tree reproduces the zip byte for "
        "byte when `SOURCE_DATE_EPOCH` is pinned; compare the `.sha256` sidecar "
        "to confirm.",
    ]
    return "\n".join(lines) + "\n"


# =============================================================================
# History + retention
# =============================================================================

def append_history(archive_dir: Path, record: dict):
    archive_dir.mkdir(parents=True, exist_ok=True)
    with open(archive_dir / "share_history.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def purge_archive(archive_dir: Path, retention_days: int, retention_mb: int,
                  keep: Path = None, dry_run: bool = False, debug: bool = False):
    """Delete oldest zips until BOTH the age and the total-size caps are met."""
    if not archive_dir.is_dir():
        return {"deleted": [], "freed_bytes": 0, "remaining_bytes": 0, "remaining_count": 0}

    keep_res = keep.resolve() if keep else None
    zips = []
    for p in sorted(archive_dir.glob("*.zip")):
        if keep_res and p.resolve() == keep_res:
            continue
        try:
            zips.append((p, p.stat().st_mtime, p.stat().st_size))
        except OSError:
            continue
    zips.sort(key=lambda t: t[1])           # oldest first, deterministic

    deleted, freed = [], 0
    cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).timestamp()

    def sidecars(z: Path):
        return [q for q in (z.with_suffix(z.suffix + ".sha256"),
                            z.with_suffix(".report.md")) if q.exists()]

    def drop(z, mtime, size, reason):
        nonlocal freed
        extra = sidecars(z)
        if not dry_run:
            try:
                z.unlink()
                for q in extra:
                    q.unlink()
            except OSError as e:
                safe_print(f"  [purge] FAILED {z.name}: {e}")
                return False
        freed += size
        deleted.append({
            "file": z.name, "bytes": size, "reason": reason,
            "mtime_utc": datetime.fromtimestamp(mtime, timezone.utc).isoformat(),
            "sidecars": [q.name for q in extra],
        })
        safe_print(f"  [purge]{' (dry-run)' if dry_run else ''} {z.name} "
                   f"({size / 1024**2:.1f} MB) — {reason}")
        return True

    survivors = []
    for z, mtime, size in zips:
        if retention_days > 0 and mtime < cutoff:
            age = int((time.time() - mtime) / 86400)
            if drop(z, mtime, size, f"older than {retention_days}d (age {age}d)"):
                continue
        survivors.append((z, mtime, size))

    cap = retention_mb * 1024 * 1024
    total = sum(s for _, _, s in survivors)
    if keep_res and keep_res.exists():
        total += keep_res.stat().st_size
    idx = 0
    while retention_mb > 0 and total > cap and idx < len(survivors):
        z, mtime, size = survivors[idx]
        if drop(z, mtime, size, f"archive over {retention_mb} MB cap"):
            total -= size
        idx += 1

    remaining = [t for t in survivors[idx:]]
    rem_bytes = sum(s for _, _, s in remaining)
    if keep_res and keep_res.exists():
        rem_bytes += keep_res.stat().st_size
    return {"deleted": deleted, "freed_bytes": freed,
            "remaining_bytes": rem_bytes,
            "remaining_count": len(remaining) + (1 if keep_res else 0)}


# =============================================================================
# Verify
# =============================================================================

def verify_zip(zip_path: Path):
    if not zip_path.exists():
        safe_print(f"ERROR: {zip_path} not found")
        return 1
    safe_print(f"\n=== VERIFY {zip_path.name} ===")
    safe_print(f"  zip sha256 : {sha256_file(zip_path)}")
    side = zip_path.with_suffix(zip_path.suffix + ".sha256")
    if side.exists():
        recorded = side.read_text(encoding="utf-8").split()[0]
        ok = recorded == sha256_file(zip_path)
        safe_print(f"  sidecar    : {'MATCH' if ok else 'MISMATCH'} ({recorded[:16]}…)")
        if not ok:
            return 2

    bad = 0
    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
        for req in ("_SHARE/MANIFEST.json", "_SHARE/SHA256SUMS",
                    "_SHARE/EXCLUSIONS.json", "_SHARE/POLICY.json"):
            if req not in names:
                safe_print(f"  MISSING    : {req}")
                bad += 1
        if bad:
            return 2
        man = json.loads(zf.read("_SHARE/MANIFEST.json"))
        safe_print(f"  mode       : {man['share_mode']}")
        safe_print(f"  policy     : {man['policy_version']} ({man['policy_sha256'][:16]}…)")
        safe_print(f"  files      : {man['file_count']}   excluded: {man['excluded_count']}")
        ch = hashlib.sha256()
        for f in man["files"]:
            ch.update(f["path"].encode("utf-8")); ch.update(b"\x00")
            ch.update(f["sha256"].encode("ascii")); ch.update(b"\n")
        recorded = man.get("content_sha256")
        if recorded:
            ok = ch.hexdigest() == recorded
            safe_print(f"  content    : {'MATCH' if ok else 'MISMATCH'} ({recorded[:16]}…)")
            if not ok:
                bad += 1
        raw_included = man.get("merged", {}).get("raw_files_included", True)
        if raw_included:
            for entry in man["files"]:
                if entry["path"] not in names:
                    safe_print(f"  MISSING    : {entry['path']}")
                    bad += 1
                    continue
                got = hashlib.sha256(zf.read(entry["path"])).hexdigest()
                if got != entry["sha256"]:
                    safe_print(f"  CORRUPT    : {entry['path']}")
                    bad += 1
        else:
            safe_print(f"  raw files  : omitted (--merged-only); "
                       f"{len(man['files'])} listed in manifest, content is in the shards")
        shards = man.get("merged", {}).get("shards", [])
        if shards:
            safe_print(f"  merged     : {len(shards)} shard(s)")
        for sh in shards:
            if sh["path"] not in names:
                safe_print(f"  MISSING    : {sh['path']}")
                bad += 1
                continue
            got = hashlib.sha256(zf.read(sh["path"])).hexdigest()
            if got != sh["sha256"]:
                safe_print(f"  CORRUPT    : {sh['path']}")
                bad += 1

        accounted = ({sh["path"] for sh in shards}
                     | {n for n in names if n.startswith("_SHARE/")})
        if raw_included:
            accounted |= {e["path"] for e in man["files"]}
        extra = names - accounted
        for n in sorted(extra):
            safe_print(f"  UNLISTED   : {n}  <- present in zip but not in MANIFEST")
            bad += 1
    safe_print(f"  result     : {'OK' if bad == 0 else str(bad) + ' PROBLEM(S)'}\n")
    return 0 if bad == 0 else 2
