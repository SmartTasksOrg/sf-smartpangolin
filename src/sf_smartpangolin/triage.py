"""
sf_smartpangolin.triage — read _SHARE/EXCLUSIONS.json out of a share zip.

Prints paths and rule IDs only. Matched secret values are never stored in the
zip, so they cannot be printed here either.
"""
from __future__ import annotations

import collections
import json
import os
import zipfile
from pathlib import Path

LIMIT = 40


def triage(zip_path, prefix="", full=False, ext_mode=False, git_mode=False):
    """Print exclusion records from a share zip. Returns an exit code."""
    zp = Path(zip_path)
    with zipfile.ZipFile(zp) as zf:
        data = json.loads(zf.read("_SHARE/EXCLUSIONS.json"))
        man = json.loads(zf.read("_SHARE/MANIFEST.json"))

    print(f"{zp.name}")
    print(f"  mode {data['share_mode']}   policy {data['policy_sha256'][:16]}")
    print(f"  included {man['file_count']}   excluded {data['count']}\n")

    if git_mode:
        g = man.get("git")
        if not g:
            print("  no git data (repo not a git checkout, or --no-git-list used)")
            return 0
        tns = g["tracked_not_shipped"]
        print(f"TRACKED BUT NOT SHIPPED  ({len(tns)})")
        print("  files git tracks that did not make the share — review these\n")
        by_rule = {e["path"]: e["rule"] for e in data["entries"]}
        buckets = collections.defaultdict(list)
        for path in tns:
            buckets[by_rule.get(path, "(not scanned — filtered before classification)")].append(path)
        for rule in sorted(buckets):
            print(f"  {rule}  ({len(buckets[rule])})")
            shown = buckets[rule] if full else buckets[rule][:LIMIT]
            for path in shown:
                print(f"      {path}")
            if not full and len(buckets[rule]) > LIMIT:
                print(f"      ... +{len(buckets[rule]) - LIMIT} more")
            print()
        return 0

    groups = collections.defaultdict(list)
    for e in data["entries"]:
        if e["rule"].startswith(prefix):
            groups[e["rule"]].append(e["path"])

    for rule in sorted(groups):
        paths = groups[rule]
        print(f"{rule}  ({len(paths)})")
        if ext_mode:
            hist = collections.Counter(os.path.splitext(p)[1].lower() or "(none)"
                                       for p in paths)
            for ext, n in hist.most_common():
                print(f"    {ext:12} {n}")
        else:
            shown = paths if full else paths[:LIMIT]
            for p in shown:
                print(f"    {p}")
            if not full and len(paths) > LIMIT:
                print(f"    ... +{len(paths) - LIMIT} more  (--full to list all)")
        print()
    return 0
