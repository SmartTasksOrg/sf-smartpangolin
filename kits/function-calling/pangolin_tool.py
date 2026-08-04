"""
Framework-agnostic function/tool definitions for SmartPangolin.

Drop these into ANY tool-calling loop — OpenAI, Anthropic, Gemini, Mistral,
Bedrock, or your own agent. `TOOLS_OPENAI` / `TOOLS_ANTHROPIC` are the schemas to
advertise; `dispatch(name, args)` runs the call and returns a string result.
"""
import json
from smartpangolin import api

_PARAMS = {
    "type": "object",
    "properties": {
        "root": {"type": "string", "description": "Project root to scan", "default": "."},
        "mode": {"type": "string", "enum": ["public", "private"], "default": "public"},
    },
}

# OpenAI / Gemini / Mistral style (function wrapper)
TOOLS_OPENAI = [{
    "type": "function",
    "function": {
        "name": "pangolin_scan",
        "description": "Dry-run: report secrets in paths/content, .gitignore and "
                       "local-infra that would be withheld before sharing code. Writes nothing.",
        "parameters": _PARAMS,
    },
}]

# Anthropic style (flat, input_schema)
TOOLS_ANTHROPIC = [{
    "name": "pangolin_scan",
    "description": "Dry-run: report what SmartPangolin would withhold before sharing code externally or with an LLM.",
    "input_schema": _PARAMS,
}]


def pangolin_scan(root=".", mode="public"):
    r = api.pack(root, share=mode, dry_run=True)
    return {
        "would_share": r.included_count,
        "would_hold": r.excluded_count,
        "by_rule": r.exclusions["by_rule"],
        "blocked": any(k.startswith("SEC-") for k in r.exclusions["by_rule"]),
    }


def dispatch(name, args):
    """Run a tool call by name; returns a compact string for the model."""
    if name == "pangolin_scan":
        return json.dumps(pangolin_scan(**args))
    raise ValueError(f"unknown tool: {name}")
