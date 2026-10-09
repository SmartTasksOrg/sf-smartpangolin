#!/usr/bin/env python3
"""Export the Python engine's ruleset to spec/policy.json and sync every port.

The policy is the contract. Run this whenever a rule changes so the Node, Go,
and Java ports stay byte-for-byte aligned with the reference engine:

    python3 tools/export_policy.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sf_smartpangolin import engine as E  # noqa: E402
from sf_smartpangolin import pii as _P  # noqa: E402


def _pii_rules():
    return [{'id': r, 'regex': rx.pattern, 'token': tok} for (r, rx, tok) in _P.PII_RULES]


def build_spec():
    return {
        "policy_version": E.POLICY_VERSION,
        "path_rules":     [{"id": r, "globs": g, "desc": d} for (r, g, d) in E.PATH_RULES],
        "dir_rules":      [{"id": r, "names": sorted(s), "desc": d} for (r, s, d) in E.PATH_DIR_RULES],
        "content_rules":  [{"id": r, "regex": rx, "desc": d} for (r, rx, d) in E.CONTENT_RULES],
        "local_rules":    [{"id": r, "regex": rx, "desc": d} for (r, rx, d) in E.LOCAL_RULES],
        "path_allowlist": list(E.PATH_ALLOWLIST),
        "source_extensions": sorted(E.SOURCE_EXTENSIONS),
        "source_extensionless": sorted(E.SOURCE_EXTENSIONLESS),
        "pii_rules": _pii_rules(),
        "pii_author_regex": _P.AUTHOR_RE.pattern,
    }


def gen_java(spec):
    def s(x):
        return '"' + x.replace("\\", "\\\\").replace('"', '\\"') + '"'
    out = ["// GENERATED from spec/policy.json by tools/export_policy.py — do not edit.",
           "public final class Policy {",
           f"  public static final String VERSION = {s(spec['policy_version'])};"]
    pr = [f"    new PathRule({s(r['id'])}, new String[]{{" +
          ",".join(s(g) for g in r["globs"]) + "})" for r in spec["path_rules"]]
    out.append("  public static final PathRule[] PATH = {\n" + ",\n".join(pr) + "\n  };")
    names = sorted({n for d in spec["dir_rules"] for n in d["names"]})
    out.append("  public static final String[] DIRS = {" + ",".join(s(n) for n in names) + "};")
    for field, arr in (("CONTENT", spec["content_rules"]), ("LOCAL", spec["local_rules"])):
        body = ",\n".join(f"    new Rule({s(r['id'])}, {s(r['regex'])})" for r in arr)
        out.append(f"  public static final Rule[] {field} = {{\n{body}\n  }};")
    pii = ",\n".join(f"    new Rule({s(r['id'])}, {s(r['regex'])})" for r in spec["pii_rules"])
    out.append("  public static final Rule[] PII = {\n" + pii + "\n  };")
    out.append("  public static final String AUTHOR = " + s(spec["pii_author_regex"]) + ";")
    out.append("  public static final String[] ALLOW = {" +
               ",".join(s(a) for a in spec["path_allowlist"]) + "};")
    out.append("  public static final class PathRule { public final String id; public final String[] globs;"
               " public PathRule(String i,String[] g){id=i;globs=g;} }")
    out.append("  public static final class Rule { public final String id; public final String regex;"
               " public Rule(String i,String r){id=i;regex=r;} }")
    out.append("}")
    return "\n".join(out) + "\n"


def main():
    spec = build_spec()
    blob = json.dumps(spec, indent=2)
    (ROOT / "spec").mkdir(exist_ok=True)
    (ROOT / "spec" / "policy.json").write_text(blob + "\n")
    (ROOT / "ports" / "node" / "lib" / "policy.json").write_text(blob + "\n")
    (ROOT / "ports" / "go" / "policy.json").write_text(blob + "\n")
    (ROOT / "ports" / "php" / "policy.json").write_text(blob + "\n")
    (ROOT / "ports" / "java" / "src" / "Policy.java").write_text(gen_java(spec))
    print(f"policy {spec['policy_version']}: "
          f"{len(spec['path_rules'])} path, {len(spec['dir_rules'])} dir, "
          f"{len(spec['content_rules'])} content, {len(spec['local_rules'])} local")
    print("synced: spec/policy.json, ports/node, ports/go, ports/java, ports/php")


if __name__ == "__main__":
    main()
