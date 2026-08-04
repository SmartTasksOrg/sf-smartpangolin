#!/usr/bin/env python3
"""
SmartPangolin MCP server — zero dependencies.

Speaks the Model Context Protocol over stdio (newline-delimited JSON-RPC 2.0),
so it plugs into any MCP client: Claude Desktop, Cursor, Cline, Windsurf, Zed,
Continue, and others. It exposes two tools an AI coding agent can call *before*
sharing code:

  pangolin_scan  — dry-run: report what would be excluded (secrets in paths and
                   content, .gitignore, local-infra), nothing written.
  pangolin_pack  — seal a share zip (only when you actually want the artifact).

Requires `smartpangolin` importable (pip install smartpangolin), or run with
PYTHONPATH pointed at the repo's src/.

Register (Claude Desktop / Cursor / Cline / Windsurf / Zed / Continue):
  { "mcpServers": { "pangolin": { "command": "python3",
      "args": ["/abs/path/to/kits/mcp/server.py"] } } }
"""
import json
import sys
import traceback

PROTOCOL = "2024-11-05"
SERVER = {"name": "smartpangolin", "version": "1.2.1"}

try:
    from smartpangolin import api
except Exception:  # pragma: no cover - surfaced to the client at call time
    api = None

TOOLS = [
    {
        "name": "pangolin_scan",
        "description": ("Dry-run SmartPangolin over a project tree and report what "
                        "would be withheld before sharing code with an LLM or third "
                        "party: secrets in filenames and content, .gitignore, and "
                        "local-infrastructure leaks. Writes nothing."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "root": {"type": "string", "description": "Path to the project root", "default": "."},
                "mode": {"type": "string", "enum": ["public", "private"], "default": "public",
                         "description": "public withholds local-infra (IPs, hostnames); private keeps it"},
            },
        },
    },
    {
        "name": "pangolin_pack",
        "description": ("Seal a project tree into a share-safe zip (excludes secrets, "
                        "honours .gitignore) and return the path plus content/zip "
                        "hashes. Use only when you want the artifact, not just a check."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "root": {"type": "string", "default": "."},
                "mode": {"type": "string", "enum": ["public", "private"], "default": "public"},
            },
        },
    },
]


def _need_api():
    if api is None:
        raise RuntimeError("smartpangolin is not importable. `pip install smartpangolin` "
                           "or set PYTHONPATH to the repo's src/.")


def tool_scan(args):
    _need_api()
    r = api.pack(args.get("root", "."), share=args.get("mode", "public"), dry_run=True)
    by_rule = r.exclusions["by_rule"]
    secret_hits = {k: v for k, v in by_rule.items() if k.startswith("SEC-")}
    lines = [
        f"SmartPangolin scan (mode={args.get('mode', 'public')})",
        f"  would share : {r.included_count} file(s)",
        f"  would hold  : {r.excluded_count} file(s)",
    ]
    if by_rule:
        lines.append("  by rule:")
        for k, v in by_rule.items():
            lines.append(f"    {k:18} {v}")
    verdict = "BLOCK — secrets present" if secret_hits else "clear of hard secrets"
    lines.append(f"  verdict: {verdict}")
    return "\n".join(lines), bool(secret_hits)


def tool_pack(args):
    _need_api()
    r = api.pack(args.get("root", "."), share=args.get("mode", "public"), dry_run=False)
    txt = (f"Sealed {r.included_count} file(s) -> {r.zip_path}\n"
           f"  content_sha256: {r.content_sha256}\n"
           f"  zip_sha256    : {r.zip_sha256}\n"
           f"  withheld      : {r.excluded_count}")
    return txt, False


HANDLERS = {"pangolin_scan": tool_scan, "pangolin_pack": tool_pack}


def send(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def result(id_, payload):
    send({"jsonrpc": "2.0", "id": id_, "result": payload})


def error(id_, code, message):
    send({"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}})


def handle(msg):
    method = msg.get("method")
    id_ = msg.get("id")
    if method == "initialize":
        result(id_, {"protocolVersion": PROTOCOL,
                     "capabilities": {"tools": {}},
                     "serverInfo": SERVER})
    elif method in ("notifications/initialized", "initialized"):
        pass  # notification, no reply
    elif method == "ping":
        result(id_, {})
    elif method == "tools/list":
        result(id_, {"tools": TOOLS})
    elif method == "tools/call":
        params = msg.get("params", {})
        name = params.get("name")
        args = params.get("arguments", {}) or {}
        fn = HANDLERS.get(name)
        if not fn:
            error(id_, -32601, f"unknown tool: {name}")
            return
        try:
            text, is_error = fn(args)
            result(id_, {"content": [{"type": "text", "text": text}], "isError": is_error})
        except Exception as e:  # report as a tool error, not a transport crash
            result(id_, {"content": [{"type": "text", "text": f"error: {e}"}], "isError": True})
    elif id_ is not None:
        error(id_, -32601, f"method not found: {method}")


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        try:
            handle(msg)
        except Exception:
            sys.stderr.write(traceback.format_exc())


if __name__ == "__main__":
    main()
