#!/usr/bin/env python3
"""SmartPangolin integration adapter — the single source of truth for every
framework wrapper in this folder. Exposes TOOL_NAME, DESCRIPTION, INPUT_SCHEMA
and run(payload)->dict, plus a CLI:  python adapter.py --root <input>
"""
import argparse
import json
import os
import sys

from sf_smartpangolin.core import scan

TOOL_NAME = "smartpangolin_scan"
DESCRIPTION = "Scan a project tree for secrets in paths and content before sharing it with an LLM or third party."
INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "root": {
                "type": "string",
                "description": "Project root to scan",
                "default": "."
        }
    },
    "required": [],
}


def _read(p):
    with open(p, encoding="utf-8", errors="ignore") as f:
        return f.read()


def run(payload):
    """Run SmartPangolin on a payload dict and return a compact, JSON-safe result."""
    r = scan(payload.get('root', '.'))
    result = {'verdict': r.verdict, 'policy_hash': r.policy_hash,
              'findings': [{'rule': f.rule, 'path': f.path} for f in r.findings]}
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=DESCRIPTION)
    ap.add_argument("--text")
    ap.add_argument("--file")
    ap.add_argument("--root")
    ap.add_argument("--sources")
    args = ap.parse_args(argv)
    payload = {'root': args.root or '.'}
    print(json.dumps(run(payload)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
