#!/usr/bin/env bash
# Prove every port matches the Python reference: secrets (public/private) AND --pii.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; REPO="$(cd "$HERE/../.." && pwd)"
FIX=/tmp/pangolin_fixture
python3 "$HERE/fixture.py" "$FIX" >/dev/null

command -v go    >/dev/null && ( cd "$REPO/ports/go"   && GOCACHE=/tmp/gocache GOFLAGS=-mod=mod go build -o pangolin-check . ) || echo "  (go missing)"
command -v javac >/dev/null && ( cd "$REPO/ports/java" && mkdir -p out && javac -d out src/*.java ) || echo "  (javac missing)"

pyref() { PYTHONPATH="$REPO/src" python3 - "$1" "$2" <<'PY'
import json,sys
from pathlib import Path
from sf_smartpangolin import engine as E, gitignore as G, pii as P
root=Path("/tmp/pangolin_fixture"); mode=sys.argv[1]; do_pii=sys.argv[2]=="1"
spec=G.build_spec(root); sink=[]
c,_=E.collect_candidates(root, root/"share_archive", gitignore_spec=spec, gitignore_sink=sink)
inc,exc=E.classify(c, root, E.compile_rules(None), mode)
d={i["path"]:"INCLUDE" for i in inc}; d.update({e["path"]:e["rule"] for e in exc})
for r in dict.fromkeys(sink): d.setdefault(r.rstrip("/"),"OPS-GITIGNORE")
if do_pii:
    for rel,dec in list(d.items()):
        if dec!="INCLUDE": continue
        try: text=(root/rel).read_text(encoding="utf-8")
        except Exception: continue
        h=P.scan_pii(text, skip_author=True)
        if h: d[rel]=h[0]["rule"]
print(json.dumps(d,sort_keys=True))
PY
}
cmp_port() { python3 - "$1" "$2" "$3" <<'PY'
import json,sys
ref=json.load(open(sys.argv[2]))
try: got=json.load(open(sys.argv[3]))
except Exception as e: print(f"  {sys.argv[1]:6} ERROR {e}"); sys.exit(1)
bad=[k for k in sorted(set(ref)|set(got)) if ref.get(k)!=got.get(k)]
if bad:
    print(f"  {sys.argv[1]:6} FAIL ({len(bad)})")
    for k in bad[:10]: print(f"      {k}: py={ref.get(k)} port={got.get(k)}")
    sys.exit(1)
print(f"  {sys.argv[1]:6} OK ({len(ref)} files)")
PY
}
rc=0
run_cfg() { # $1=label $2=mode $3=pii(0/1)
  local mode="$2" pf=""; [ "$3" = "1" ] && pf="--pii"
  echo "== $1 =="
  pyref "$mode" "$3" > /tmp/ref.json
  if command -v node >/dev/null; then node "$REPO/ports/node/bin/cli.js" "$FIX" --mode $mode $pf --json >/tmp/o.json 2>/dev/null||true; cmp_port node /tmp/ref.json /tmp/o.json||rc=1; fi
  [ -x "$REPO/ports/go/pangolin-check" ] && { "$REPO/ports/go/pangolin-check" "$FIX" --mode $mode $pf --json >/tmp/o.json 2>/dev/null||true; cmp_port go /tmp/ref.json /tmp/o.json||rc=1; }
  [ -f "$REPO/ports/java/out/Main.class" ] && { java -cp "$REPO/ports/java/out" Main "$FIX" --mode $mode $pf --json >/tmp/o.json 2>/dev/null||true; cmp_port java /tmp/ref.json /tmp/o.json||rc=1; }
  command -v php >/dev/null && { php "$REPO/ports/php/pangolin-check.php" "$FIX" --mode $mode $pf --json >/tmp/o.json 2>/dev/null||true; cmp_port php /tmp/ref.json /tmp/o.json||rc=1; }
}
run_cfg "mode=public"          public  0
run_cfg "mode=private"         private 0
run_cfg "mode=public + --pii"  public  1
echo; [ $rc = 0 ] && echo "ALL PORTS CONFORMANT (incl. PII)" || echo "CONFORMANCE FAILURES"; exit $rc
