"""
smartpangolin.cli — command-line interface.

Subcommands:
  pack     seal a project tree into a share zip (default)
  verify   verify an existing share zip against its manifest
  triage   read _SHARE/EXCLUSIONS.json out of a zip
  tree     run stage 1 (folder structure) only
  purge    run retention cleanup on an archive directory
  policy   print the active policy (JSON) or its fingerprint
  init     scaffold .secret/ and .pangolin.json in a repo

`smartpangolin` with no subcommand behaves like `smartpangolin pack`.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import engine
from ._version import __version__
from .api import pack, resolve_layout
from .bootstrap import maybe_reexec_in_venv
from .folder_structure import build_tree
from .triage import triage as run_triage

PACK_SUBCOMMANDS = {"pack", "verify", "triage", "tree", "purge", "policy", "init"}


def _add_shared(p):
    p.add_argument("--root", default=os.getcwd(), help="Root folder of the project")
    p.add_argument("--focus", help="Focus on a specific subfolder relative to --root")
    p.add_argument("--files", nargs="*", help="Specific files to include")
    p.add_argument("--tree-output", default="file_folder_tree.txt")
    p.add_argument("--path-output", default="file_folder_path.txt")
    p.add_argument("--rebuild-tree", action="store_true",
                   help="Re-run stage 1 (folder structure) before packaging")
    p.add_argument("--exclude-ext", nargs="*", help="Extra extensions to exclude")
    p.add_argument("--exclude-folders", nargs="*", help="Extra folder names to exclude")
    p.add_argument("--exclude-paths", nargs="*", help="Specific folder paths to exclude")
    p.add_argument("--output-folder", default="extracted_source",
                   help="Staging folder for merged shards. Relative paths resolve "
                        "against the PARENT of --root (default: <root>/../extracted_source)")
    p.add_argument("--source-only", action="store_true",
                   help="Restrict selection to recognised source extensions")
    p.add_argument("--max-chars", type=int, default=3500000,
                   help="Character ceiling per merged shard (default: %(default)s)")
    p.add_argument("--prefix", default="", help="Prefix for generated output filenames")
    p.add_argument("--config-file", default=engine.CONFIG_FILE,
                   help="Shared patches_config.json (default: %(default)s)")
    p.add_argument("--venv", default="auto",
                   help="'auto' (default), 'none', or a path to a venv to re-exec under")
    p.add_argument("--debug", action="store_true", help="Verbose output")


def _add_pack(p):
    _add_shared(p)
    g = p.add_argument_group("share policy")
    g.add_argument("--share", choices=["public", "private"], default=None,
                   help="public: secrets AND local infra excluded. private: secrets "
                        "excluded, local infra retained. (default: public, or "
                        ".pangolin.json share_mode)")
    g.add_argument("--archive-dir", default="share_archive",
                   help="Zips + ledger. Relative paths resolve inside --output-folder.")
    g.add_argument("--keep-txt", action="store_true",
                   help="Keep staged source_code_part*.txt after zipping")
    g.add_argument("--zip-name", help="Override the generated zip filename")
    g.add_argument("--allow", nargs="*", default=[],
                   help="Relative paths to force-include despite a rule match "
                        "(recorded in manifest + ledger)")
    g.add_argument("--dry-run", action="store_true", help="Classify and report; write nothing")
    g.add_argument("--no-gitignore", action="store_true",
                   help="Do NOT honour the project .gitignore (default: honour it)")
    g.add_argument("--pii", action="store_true",
                   help="Higher scan level: also flag PII in text (emails, phones, SSNs, cards). Author tags are kept.")
    g.add_argument("--merge", dest="merge", action="store_true", default=True,
                   help="Build merged source_code_part*.txt shards (default: on)")
    g.add_argument("--no-merge", dest="merge", action="store_false",
                   help="Skip merged shards; ship raw files only")
    g.add_argument("--merged-only", action="store_true",
                   help="Ship only the merged shards, omitting the raw file tree")
    g.add_argument("--no-git-list", action="store_true",
                   help="Skip the git ls-files provenance listing")
    g.add_argument("--name-template", default="{prefix}{stamp}_share_{mode}",
                   help="Zip name template. Placeholders: {prefix} {stamp} {mode} {focus}")
    g.add_argument("--source-date-epoch", type=int,
                   help="Pin the embedded timestamp (unix seconds) for a byte-reproducible zip")
    r = p.add_argument_group("retention")
    r.add_argument("--retention-days", type=int, default=30,
                   help="Delete archived zips older than N days (0 disables; default 30)")
    r.add_argument("--retention-mb", type=int, default=1024,
                   help="Cap total archive size in MB, oldest deleted first (0 disables; default 1024)")
    r.add_argument("--no-purge", action="store_true", help="Build the zip but skip retention")


def build_parser():
    p = argparse.ArgumentParser(
        prog="pango",
        description="SmartPangolin — deterministic, fail-closed, auditable share packager.",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version",
                   version=f"smartpangolin {__version__} (policy {engine.POLICY_VERSION})")
    sub = p.add_subparsers(dest="command")

    _add_pack(sub.add_parser("pack", help="Seal a project tree into a share zip"))

    v = sub.add_parser("verify", help="Verify a share zip against its manifest")
    v.add_argument("zip", help="Path to the share zip")

    t = sub.add_parser("triage", help="Read exclusion records out of a zip")
    t.add_argument("zip", help="Path to the share zip")
    t.add_argument("prefix", nargs="?", default="", help="Rule-ID prefix filter, e.g. SEC-")
    t.add_argument("--full", action="store_true", help="No 40-line truncation")
    t.add_argument("--ext", action="store_true", help="Extension histogram per rule")
    t.add_argument("--git", action="store_true", help="Tracked-but-not-shipped view")

    tr = sub.add_parser("tree", help="Run stage 1 (folder structure) only")
    tr.add_argument("--root", default=os.getcwd())
    tr.add_argument("--focus")
    tr.add_argument("--tree-output", default="file_folder_tree.txt")
    tr.add_argument("--path-output", default="file_folder_path.txt")
    tr.add_argument("--config-file", default=engine.CONFIG_FILE)
    tr.add_argument("--debug", action="store_true")

    pg = sub.add_parser("purge", help="Run retention cleanup on an archive dir")
    pg.add_argument("--root", default=os.getcwd())
    pg.add_argument("--output-folder", default="extracted_source")
    pg.add_argument("--archive-dir", default="share_archive")
    pg.add_argument("--retention-days", type=int, default=30)
    pg.add_argument("--retention-mb", type=int, default=1024)
    pg.add_argument("--dry-run", action="store_true")
    pg.add_argument("--debug", action="store_true")

    po = sub.add_parser("policy", help="Print the active policy or its fingerprint")
    po.add_argument("--root", default=os.getcwd(),
                    help="Root to read .pangolin.json overrides from")
    po.add_argument("--fingerprint", action="store_true",
                    help="Print only the policy sha256")

    ini = sub.add_parser("init", help="Scaffold .secret/ and .pangolin.json")
    ini.add_argument("--root", default=os.getcwd())
    ini.add_argument("--force", action="store_true", help="Overwrite existing files")

    return p


def _cmd_pack(args):
    root = Path(args.root).resolve()
    maybe_reexec_in_venv(root, args.venv, args.debug)
    result = pack(
        root, share=args.share, focus=args.focus, files=args.files,
        output_folder=args.output_folder, archive_dir=args.archive_dir,
        path_output=args.path_output, rebuild_tree=args.rebuild_tree,
        source_only=args.source_only, exclude_paths=args.exclude_paths,
        exclude_folders=args.exclude_folders, exclude_ext=args.exclude_ext,
        allow=args.allow, merge=args.merge, merged_only=args.merged_only,
        max_chars=args.max_chars, prefix=args.prefix, zip_name=args.zip_name,
        name_template=args.name_template, dry_run=args.dry_run,
        no_git_list=args.no_git_list, keep_txt=args.keep_txt,
        source_date_epoch=args.source_date_epoch, retention_days=args.retention_days,
        retention_mb=args.retention_mb, no_purge=args.no_purge,
        config_file=args.config_file, debug=args.debug,
        respect_gitignore=not getattr(args, 'no_gitignore', False),
        pii=getattr(args, 'pii', False))

    share = result.manifest["share_mode"]
    print(f"\n=== PANGO ({share.upper()}) ===")
    print(f"  root       : {root}")
    print(f"  selection  : {result.manifest['selection']}")
    print(f"  policy     : {engine.POLICY_VERSION} ({result.manifest['policy_sha256'][:16]}…)")
    print(f"  included   : {result.included_count} files "
          f"({result.manifest['total_bytes'] / 1024:.1f} KiB)")
    print(f"  excluded   : {result.excluded_count} files")
    for rule, count in result.exclusions["by_rule"].items():
        print(f"                 {rule:22} {count}")
    m = result.manifest["merged"]
    if m["enabled"]:
        print(f"  merged     : {m['shard_count']} shard(s) @ {m['max_chars']:,} chars"
              f"{' (merged-only)' if not m['raw_files_included'] else ''}")
    if result.manifest.get("git"):
        g = result.manifest["git"]
        print(f"  git        : {g['tracked_count']} tracked, "
              f"{len(g['tracked_not_shipped'])} tracked-but-not-shipped")
    if result.overrides:
        print(f"  OVERRIDES  : {len(result.overrides)} (recorded in manifest + history)")
    if result.dry_run:
        print("\n  [dry-run] nothing written\n")
        return 0
    print(f"  zip        : {result.zip_path}")
    print(f"  zip sha256 : {result.zip_sha256}")
    print(f"  content    : {result.content_sha256}\n")
    return 0


def _cmd_purge(args):
    root = Path(args.root).resolve()
    _out, arch = resolve_layout(root, args.output_folder, args.archive_dir)
    print(f"\n=== PURGE {arch} (>{args.retention_days}d, cap {args.retention_mb} MB) ===")
    res = engine.purge_archive(arch, args.retention_days, args.retention_mb,
                               dry_run=args.dry_run, debug=args.debug)
    print(f"  deleted {len(res['deleted'])} file(s), "
          f"freed {res['freed_bytes'] / 1024**2:.1f} MB; "
          f"{res['remaining_count']} remain ({res['remaining_bytes'] / 1024**2:.1f} MB)\n")
    if not args.dry_run and res["deleted"]:
        engine.append_history(arch, {
            "event": "purge", "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "retention_days": args.retention_days, "retention_mb": args.retention_mb, **res})
    return 0


def _cmd_policy(args):
    root = Path(args.root).resolve()
    _cfg, user_policy = engine.load_pangolin_config(root)
    fp = engine.policy_fingerprint(user_policy)
    if args.fingerprint:
        print(fp)
        return 0
    doc = {
        "schema": "smartpangolin.share_policy/v1",
        "policy_version": engine.POLICY_VERSION,
        "policy_sha256": fp,
        "path_rules": [{"id": r, "globs": g, "desc": d} for r, g, d in engine.PATH_RULES],
        "dir_rules": [{"id": r, "names": sorted(s), "desc": d} for r, s, d in engine.PATH_DIR_RULES],
        "path_allowlist": engine.PATH_ALLOWLIST,
        "content_rules": [{"id": r, "desc": d} for r, _, d in engine.CONTENT_RULES],
        "local_rules": [{"id": r, "desc": d} for r, _, d in engine.LOCAL_RULES],
        "user_overrides": user_policy,
    }
    print(json.dumps(doc, indent=2))
    return 0


_PANGOLIN_TEMPLATE = {
    "share_mode": "public",
    "source_only": False,
    "allow": [],
    "deny_globs": [],
    "exclude_folders": [],
    "exclude_paths": [],
}


def _cmd_init(args):
    root = Path(args.root).resolve()
    secret_dir = root / ".secret"
    cfg = root / engine.PANGOLIN_CONFIG
    gitignore = secret_dir / ".gitignore"

    secret_dir.mkdir(exist_ok=True)
    if not gitignore.exists() or args.force:
        gitignore.write_text("# Everything in .secret/ is git-ignored AND never shipped by SmartPangolin.\n*\n!.gitignore\n", encoding="utf-8")
    if cfg.exists() and not args.force:
        print(f"  {engine.PANGOLIN_CONFIG} already exists (use --force to overwrite)")
    else:
        cfg.write_text(json.dumps(_PANGOLIN_TEMPLATE, indent=2) + "\n", encoding="utf-8")
        print(f"  wrote {cfg}")
    print(f"  ensured {secret_dir}/ (contents never shipped: rule SEC-DIR-SECRET)")
    print("  put real secrets under .secret/; commit .env.example, never .env\n")
    return 0


_TOP_LEVEL = {"-h", "--help", "--version"}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)

    # Convenience: `smartpangolin` or `smartpangolin --root ...` (no subcommand and
    # not a top-level flag) is treated as `smartpangolin pack ...`.
    if not argv:
        argv = ["pack"]
    elif argv[0] not in PACK_SUBCOMMANDS and argv[0] not in _TOP_LEVEL:
        argv = ["pack"] + argv

    parser = build_parser()
    args = parser.parse_args(argv)
    cmd = args.command or "pack"

    if cmd == "pack":
        return _cmd_pack(args)
    if cmd == "verify":
        return engine.verify_zip(Path(args.zip))
    if cmd == "triage":
        return run_triage(args.zip, prefix=args.prefix, full=args.full,
                          ext_mode=args.ext, git_mode=args.git)
    if cmd == "tree":
        n = build_tree(args.root, tree_output=args.tree_output,
                       path_output=args.path_output, focus=args.focus,
                       config_file=args.config_file, debug=args.debug)
        print(f"stage 1: {n} files -> {args.path_output}")
        return 0
    if cmd == "purge":
        return _cmd_purge(args)
    if cmd == "policy":
        return _cmd_policy(args)
    if cmd == "init":
        return _cmd_init(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
