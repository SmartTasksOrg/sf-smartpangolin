"""
LlamaIndex tool for SmartPangolin.

    from pangolin_tool import pangolin_tool
    agent = FunctionAgent(tools=[pangolin_tool], llm=llm)
"""
from llama_index.core.tools import FunctionTool
from smartpangolin import api


def pangolin_scan(root: str = ".", mode: str = "public") -> str:
    """Dry-run SmartPangolin: report secrets in paths/content, .gitignore and
    local-infra that would be withheld before sharing code. Writes nothing."""
    r = api.pack(root, share=mode, dry_run=True)
    by = r.exclusions["by_rule"]
    blocked = any(k.startswith("SEC-") for k in by)
    head = "BLOCK (secrets present)" if blocked else "OK (no hard secrets)"
    return f"{head}; would_share={r.included_count} would_hold={r.excluded_count}; by_rule={by}"


pangolin_tool = FunctionTool.from_defaults(fn=pangolin_scan, name="pangolin_scan")
