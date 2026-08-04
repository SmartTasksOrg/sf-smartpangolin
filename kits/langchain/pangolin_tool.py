"""
LangChain tool for SmartPangolin.

    from pangolin_tool import make_pangolin_tools
    tools = make_pangolin_tools()          # add to any agent / llm.bind_tools([...])
"""
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from smartpangolin import api


class ScanInput(BaseModel):
    root: str = Field(".", description="Project root to scan")
    mode: str = Field("public", description="'public' withholds local-infra; 'private' keeps it")


def _scan(root: str = ".", mode: str = "public") -> str:
    r = api.pack(root, share=mode, dry_run=True)
    by = r.exclusions["by_rule"]
    blocked = any(k.startswith("SEC-") for k in by)
    head = "BLOCK (secrets present)" if blocked else "OK (no hard secrets)"
    return f"{head}; would_share={r.included_count} would_hold={r.excluded_count}; by_rule={by}"


def make_pangolin_tools():
    return [StructuredTool.from_function(
        func=_scan,
        name="pangolin_scan",
        description=("Dry-run SmartPangolin over a project tree: report secrets in "
                     "filenames and content, .gitignore and local-infra leaks that "
                     "would be withheld before sharing code with an LLM or third "
                     "party. Writes nothing."),
        args_schema=ScanInput,
    )]
