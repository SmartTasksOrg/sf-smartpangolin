"""
smartpangolin.api — high-level orchestration.

:func:`pack` is the single entry point most callers want: point it at a project
root, get back a sealed zip plus its audit records. It wires together
collection, classification, config overrides, zipping, the history ledger and
retention exactly as the CLI does, but returns a structured result so it can be
driven from Python (CI scripts, other tools, tests) without a subprocess.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from . import engine
from . import gitignore
from ._version import __version__


@dataclass
class PackResult:
    zip_path: Optional[Path]
    zip_sha256: Optional[str]
    content_sha256: str
    manifest: dict
    exclusions: dict
    report: str
    included_count: int
    excluded_count: int
    overrides: List[dict] = field(default_factory=list)
    dry_run: bool = False


def resolve_layout(root: Path, output_folder="extracted_source",
                   archive_dir="share_archive"):
    """Default artifact location is DELIBERATELY OUTSIDE the scanned tree — one
    level above ``root`` — so generated zips are never candidates for the next
    scan, never land in ``git status``, and never get packaged into a later
    share of themselves. Absolute paths override this."""
    out = Path(output_folder)
    if not out.is_absolute():
        out = (root.parent / out).resolve()
    arch = Path(archive_dir)
    if not arch.is_absolute():
        arch = (out / arch).resolve()
    return out, arch


def pack(root, *, share="public", focus=None, files=None,
         output_folder="extracted_source", archive_dir="share_archive",
         path_output="file_folder_path.txt", rebuild_tree=False,
         source_only=False, exclude_paths=None, exclude_folders=None,
         exclude_ext=None, allow=None, merge=True, merged_only=False,
         max_chars=3500000, prefix="", zip_name=None,
         name_template="{prefix}{stamp}_share_{mode}", dry_run=False,
         no_git_list=False, keep_txt=False, source_date_epoch=None,
         respect_gitignore=True, ignore_files=None,
         pii=False, pii_allow=None, pii_skip_author=True,
         retention_days=30, retention_mb=1024, no_purge=False,
         config_file=engine.CONFIG_FILE, debug=False):
    """Seal a project tree into a share zip. Returns a :class:`PackResult`."""
    root = Path(root).resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"--root '{root}' is not a directory")

    out_dir, arch_dir = resolve_layout(root, output_folder, archive_dir)

    # Per-repo overrides. .pangolin.json is auditable: it folds into the
    # policy fingerprint, so a share made with overrides is distinguishable from
    # one made without.
    ss_cfg, user_policy = engine.load_pangolin_config(root)
    if share is None:
        share = ss_cfg.get("share_mode", "public")
    source_only = source_only or bool(ss_cfg.get("source_only", False))
    if ss_cfg.get("max_chars"):
        max_chars = ss_cfg["max_chars"]
    allow = list(allow or []) + list(ss_cfg.get("allow", []))
    exclude_folders = list(exclude_folders or []) + list(ss_cfg.get("exclude_folders", []))
    exclude_paths = list(exclude_paths or []) + list(ss_cfg.get("exclude_paths", []))

    respect_gitignore = ss_cfg.get('respect_gitignore', respect_gitignore)
    ignore_files = list(ignore_files or []) + list(ss_cfg.get('ignore_files', []))
    pii = pii or bool(ss_cfg.get('pii', False))
    pii_allow = list(pii_allow or []) + list(ss_cfg.get('pii_allow', []))
    pii_skip_author = ss_cfg.get('pii_skip_author', pii_skip_author)
    user_policy['respect_gitignore'] = respect_gitignore
    user_policy['pii'] = pii
    if pii and pii_allow:
        user_policy['pii_allow'] = sorted(pii_allow)
    if ignore_files:
        user_policy['ignore_files'] = sorted(ignore_files)
    user_path_rules = engine.user_path_rules_from_config(user_policy)
    rules = engine.compile_rules(user_path_rules)
    fingerprint = engine.policy_fingerprint(user_policy)

    extra_dirs, extra_exts, extra_names = engine.load_shared_config(config_file)

    gi_spec = gitignore.build_spec(root, extra_files=ignore_files) if respect_gitignore else None
    gi_sink = []
    candidates, selection = engine.collect_candidates(
        root, arch_dir, focus=focus, files=files, path_output=path_output,
        rebuild_tree=rebuild_tree, source_only=source_only,
        exclude_paths=exclude_paths, exclude_folders=exclude_folders,
        exclude_ext=exclude_ext, extra_dirs=extra_dirs, extra_exts=extra_exts,
        extra_names=extra_names, gitignore_spec=gi_spec, gitignore_sink=gi_sink)

    included, excluded = engine.classify(candidates, root, rules, share, debug)

    if gi_spec and gi_sink:
        seen = {e['path'] for e in excluded} | {i['path'] for i in included}
        for rel in dict.fromkeys(gi_sink):
            base = rel.rstrip('/')
            if base in seen:
                continue
            excluded.append({'path': base, 'rule': 'OPS-GITIGNORE',
                             'desc': 'ignored by project .gitignore',
                             'detail': 'matched .gitignore', 'family': 'ops'})
            seen.add(base)

    overrides = []
    if allow:
        allow_set = set(allow)
        still = []
        for e in excluded:
            if e["path"] in allow_set:
                p = root / e["path"]
                if p.is_file():
                    included.append({"path": e["path"], "abs": p,
                                     "size": p.stat().st_size, "override": e["rule"]})
                    overrides.append({"path": e["path"], "overrode_rule": e["rule"]})
                    continue
            still.append(e)
        excluded = still
        included.sort(key=lambda d: d["path"])

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if zip_name:
        name = zip_name
    else:
        name = name_template.format(
            prefix=prefix, stamp=stamp, mode=share,
            focus=(focus or "").replace(os.sep, "_").strip("_")) + ".zip"
    zip_path = arch_dir / name

    sde = source_date_epoch or os.environ.get("SOURCE_DATE_EPOCH")
    gen_utc = (datetime.fromtimestamp(int(sde), timezone.utc).isoformat()
               if sde else datetime.now(timezone.utc).isoformat())

    meta = {
        "generated_utc": gen_utc, "share_mode": share,
        "policy_sha256": fingerprint, "source_root": str(root),
        "focus": focus, "selection": selection, "overrides": overrides,
        "user_policy": user_policy,
    }

    if not dry_run:
        engine.clean_staged_shards(out_dir, prefix, debug)

    git_list = None if no_git_list else engine.git_tracked(root)

    if pii:
        from . import pii as _pii
        kept = []
        for i in included:
            fp = root / i['path']
            try:
                text = fp.read_text(encoding='utf-8')
            except (OSError, UnicodeDecodeError):
                kept.append(i)
                continue
            hits = _pii.scan_pii(text, allow=pii_allow, skip_author=pii_skip_author)
            if hits:
                excluded.append({'path': i['path'], 'rule': hits[0]['rule'],
                                 'desc': 'personal data in text',
                                 'detail': f"{len(hits)} PII match(es)", 'family': 'pii'})
            else:
                kept.append(i)
        included = kept

    manifest, exclusions, report, zip_hash = engine.write_zip(
        zip_path, included, excluded, meta, dry_run,
        merge=merge, include_raw=not merged_only, max_chars=max_chars,
        prefix=prefix, git_list=git_list, stage_dir=out_dir,
        keep_txt=keep_txt, debug=debug)

    result = PackResult(
        zip_path=None if dry_run else zip_path, zip_sha256=zip_hash,
        content_sha256=manifest["content_sha256"], manifest=manifest,
        exclusions=exclusions, report=report, included_count=manifest["file_count"],
        excluded_count=exclusions["count"], overrides=overrides, dry_run=dry_run)

    if dry_run:
        return result

    zip_path.with_suffix(zip_path.suffix + ".sha256").write_text(
        f"{zip_hash}  {zip_path.name}\n", encoding="utf-8")
    zip_path.with_suffix(".report.md").write_text(report, encoding="utf-8")

    engine.append_history(arch_dir, {
        "event": "share", "timestamp_utc": meta["generated_utc"],
        "zip": zip_path.name, "zip_sha256": zip_hash,
        "content_sha256": manifest["content_sha256"],
        "zip_bytes": zip_path.stat().st_size, "share_mode": share,
        "policy_version": engine.POLICY_VERSION, "policy_sha256": fingerprint,
        "tool_version": __version__, "source_root": str(root), "focus": focus,
        "selection": selection, "included_count": manifest["file_count"],
        "included_bytes": manifest["total_bytes"], "excluded_count": exclusions["count"],
        "excluded_by_rule": exclusions["by_rule"],
        "merged_shards": manifest["merged"]["shard_count"],
        "merged_max_chars": manifest["merged"]["max_chars"],
        "raw_files_included": manifest["merged"]["raw_files_included"],
        "excluded_paths": [e["path"] for e in excluded], "overrides": overrides,
    })

    if not no_purge:
        res = engine.purge_archive(arch_dir, retention_days, retention_mb,
                                   keep=zip_path, dry_run=False, debug=debug)
        if res["deleted"]:
            engine.append_history(arch_dir, {
                "event": "purge",
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "retention_days": retention_days, "retention_mb": retention_mb, **res})

    return result
