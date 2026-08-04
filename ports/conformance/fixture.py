#!/usr/bin/env python3
"""Build a fixture that exercises EVERY rule, for cross-port conformance.

Each content/local rule gets its own isolated file (so exactly one rule fires);
path rules get real filenames; gitignore is exercised with basename, anchored,
directory, negation and ** patterns; plus an allowlist file and clean files.
"""
import os, sys, shutil
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/conf2")

A = "A"
CONTENT = {
 "SEC-CONT-HF":        "tok " + "hf_" + "a"*26 + "ABCDEF12",                 # hf_ + 34
 "SEC-CONT-AWSKEY":    "key AKIAIOSFODNN7EXAMPLE end",                        # AKIA + 16
 "SEC-CONT-AWSSEC":    'aws_secret_access_key="' + A*40 + '"',
 "SEC-CONT-GHPAT":     "ghp_" + A*36,
 "SEC-CONT-GHFINE":    "github_pat_" + A*60,
 "SEC-CONT-GITLAB":    "glpat-" + A*20,
 "SEC-CONT-ANTHROPIC": "sk-ant-" + A*24,
 "SEC-CONT-OPENAI":    "sk-" + A*32,
 "SEC-CONT-SLACK":     "xoxb-1234567890",
 "SEC-CONT-GOOGLE":    "AIza" + A*35,
 "SEC-CONT-STRIPE":    "sk_live_" + A*24,
 "SEC-CONT-NPM":       "npm_" + A*36,
 "SEC-CONT-PYPI":      "pypi-AgEIcHlwaS5vcmc" + A*50,
 "SEC-CONT-TELEGRAM":  "12345678:AA" + A*33,
 "SEC-CONT-SENDGRID":  "SG." + A*22 + "." + A*43,
 "SEC-CONT-PEM":       "-----BEGIN RSA PRIVATE KEY-----",
 "SEC-CONT-PUTTY":     "PuTTY-User-Key-File-2",
 "SEC-CONT-JWT":       "eyJ" + A*10 + ".eyJ" + A*10 + "." + A*10,
 "SEC-CONT-DOCKERAUTH":'{ "auths": { } }',
 "SEC-CONT-CONNSTR":   "postgres://user:pass@dbhost/app",
 "SEC-CONT-ASSIGN":    'password = "supersecret123"',
}
LOCAL = {
 "LOC-RFC1918":  "peer 10.1.2.3 up",
 "LOC-CGNAT":    "peer 100.64.1.2 up",
 "LOC-IPV6ULA":  "addr fd12:3456:0:0:0:0:1 up",
 "LOC-UNC":      "share \\\\fileserver\\public",
 "LOC-WINUSER":  "path C:\\Users\\alice",
 "LOC-NIXUSER":  "path /home/alice/project",
 "LOC-INTHOST":  "host database.internal reachable",
 "LOC-MAC":      "nic 00:1A:2B:3C:4D:5E",
 "LOC-SSHCFG":   "Host bastion\n  HostName jump.example\n",
}
PATHS = {  # filename -> expected rule
 ".env":            "SEC-PATH-ENV",
 "server.pem":      "SEC-PATH-PEM",
 "store.pfx":       "SEC-PATH-PFX",
 "id_rsa":          "SEC-PATH-SSH",
 ".netrc":          "SEC-PATH-NETRC",
 "credentials.json":"SEC-PATH-CLOUD",
 "kubeconfig":      "SEC-PATH-KUBE",
 "vault.kdbx":      "SEC-PATH-VAULT",
 "state.tfstate":   "SEC-PATH-TFSTATE",
 ".bash_history":   "SEC-PATH-HISTORY",
 "backup.sql":      "SEC-PATH-DBDUMP",
}


def w(rel, text):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def main():
    if ROOT.exists():
        shutil.rmtree(ROOT)
    ROOT.mkdir(parents=True)
    for rid, s in CONTENT.items():
        w(f"content/{rid}.txt", s + "\n")
    for rid, s in LOCAL.items():
        w(f"local/{rid}.txt", s + "\n")
    for name in PATHS:
        w(f"paths/{name}", "placeholder\n")
    # allowlist + clean
    w("config/.env.example", "API_KEY=\n")
    w("src/app.py", "print('hello')\n")
    w("README.md", "# clean\n")
    w("net/ok.txt", "user /home/ubuntu/ci runs here\n")  # NIXUSER negative (ubuntu excluded)
    # pruned dirs (rule-based, must be silently skipped)
    w(".ssh/id_rsa", "x\n")
    w(".git/config", "[core]\n")
    w("node_modules/pkg/index.js", "module.exports={}\n")
    # gitignore variety
    w(".gitignore", "*.tmp\n/anchored.txt\nlogs/\n!keep.tmp\n**/deep.md\n")
    w("a.tmp", "junk\n")                 # ignored by *.tmp
    w("keep.tmp", "keep\n")              # negated -> INCLUDE
    w("anchored.txt", "root only\n")     # ignored (anchored)
    w("sub/anchored.txt", "not ignored\n")  # NOT ignored (anchored to root)
    w("logs/app.log", "log\n")           # dir ignored -> logs/ recorded, pruned
    w("deep.md", "d\n")                  # **/deep.md
    w("x/deep.md", "d\n")                # **/deep.md at depth
    # PII samples (only matter under --pii)
    w("pii/doc.txt", "reach me at a.person@example.com or 415-555-0199; ssn 123-45-6789; card 4111 1111 1111 1111\n")
    w("pii/author.txt", "@author maintainer@example.com\n")  # author tag -> kept even under --pii
    print(f"comprehensive fixture at {ROOT}: "
          f"{len(CONTENT)} content, {len(LOCAL)} local, {len(PATHS)} path rules + gitignore/allow/clean")


if __name__ == "__main__":
    main()
