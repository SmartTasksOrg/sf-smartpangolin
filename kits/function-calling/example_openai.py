# Guarded LLM call: scan before you send a repo to a model.
from pangolin_tool import pangolin_scan
res = pangolin_scan(root=".", mode="public")
if res["blocked"]:
    raise SystemExit(f"Refusing to share: secrets present -> {res['by_rule']}")
print("clear to share:", res["would_share"], "files")
