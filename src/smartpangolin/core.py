"""SmartPangolin core — deterministic secret scanner (paths + content)."""
import base64, binascii, hashlib, os, re
from .models import Finding, ScanResult

PATH_RULES = [
    ("SEC-PATH-ENV", re.compile(r"(^|/)\.env$")),
    ("SEC-PATH-KEY", re.compile(r"(id_rsa|\.pem|\.key)$")),
    ("SEC-PATH-TFSTATE", re.compile(r"\.tfstate$")),
]
# high-signal secret shapes, matched against plaintext AND decoded content
_SECRETS = [
    ("SEC-CONT-AWS", re.compile(r"AKIA[0-9A-Z]{12,}")),
    ("SEC-CONT-OPENAI", re.compile(r"sk-[A-Za-z0-9]{16,}")),
    ("SEC-CONT-PRIVKEY", re.compile(r"BEGIN (OPENSSH|RSA) PRIVATE KEY")),
    ("LOC-HOST", re.compile(r"[a-z0-9-]+\.corp\.internal")),
]
CONTENT_RULES = _SECRETS  # back-compat alias

# base64 / hex blobs long enough to hide a credential
_B64 = re.compile(r"[A-Za-z0-9+/]{16,}={0,2}")
_HEX = re.compile(r"(?:0x)?[0-9A-Fa-f]{32,}")


def _decoded_variants(text: str):
    """Yield decoded strings for base64/hex blobs — so a secret that was encoded
    to slip past a naive scanner is still caught. High precision: we only act on
    a decode if the RESULT matches a known secret shape (checked by the caller)."""
    seen = 0
    for m in _B64.finditer(text):
        tok = m.group(0)
        if seen > 200:
            break
        seen += 1
        try:
            pad = "=" * (-len(tok) % 4)
            dec = base64.b64decode(tok + pad, validate=False).decode("utf-8", "ignore")
            if dec.strip():
                yield dec
        except (binascii.Error, ValueError):
            continue
    for m in _HEX.finditer(text):
        tok = m.group(0)[2:] if m.group(0).startswith("0x") else m.group(0)
        if len(tok) % 2:
            continue
        try:
            dec = bytes.fromhex(tok).decode("utf-8", "ignore")
            if dec.strip():
                yield dec
        except ValueError:
            continue


def scan(root: str) -> ScanResult:
    findings = []
    for dp, _, files in os.walk(root):
        for f in files:
            rel = os.path.relpath(os.path.join(dp, f), root)
            for rid, rx in PATH_RULES:
                if rx.search(rel.replace(os.sep, "/")):
                    findings.append(Finding(rid, "high", rel, "dangerous filename"))
            try:
                text = open(os.path.join(dp, f), "r", errors="ignore").read()
            except Exception:
                continue
            # 1) plaintext secrets
            for rid, rx in _SECRETS:
                if rx.search(text):
                    findings.append(Finding(rid, "high", rel, "secret in content"))
            # 2) encoded secrets (base64/hex) — only flags if the DECODED content
            #    is itself a known secret, so precision stays high (no FPs on
            #    ordinary encoded data).
            for dec in _decoded_variants(text):
                for rid, rx in _SECRETS:
                    if rx.search(dec):
                        findings.append(Finding("SEC-CONT-ENCODED", "high", rel,
                                                f"encoded {rid} secret"))
                        break
    # de-dup identical (rule, path) findings
    uniq, seen = [], set()
    for fnd in findings:
        k = (fnd.rule, fnd.path)
        if k not in seen:
            seen.add(k)
            uniq.append(fnd)
    findings = uniq
    verdict = "BLOCKED" if findings else "CLEAN"
    # deterministic, real SHA-256 over the matched rule ids (stable across runs)
    key = ",".join(sorted(f.rule for f in findings))
    policy_hash = "sha256:" + hashlib.sha256(key.encode()).hexdigest()[:12]
    return ScanResult(findings, verdict, policy_hash)
