# SmartPangolin MCP server

A zero-dependency MCP server (`server.py`) that plugs SmartPangolin into any
MCP-speaking AI coding tool. Tools exposed: `pangolin_scan` (dry-run report) and
`pangolin_pack` (seal a share zip).

```bash
# SmartPangolin is not on PyPI yet: install it from a clone
git clone https://github.com/SmartTasksOrg/smartpangolin
cd smartpangolin
python -m pip install .              # provides the `smartpangolin-mcp` command
```

Register it (same JSON shape works for **Claude Desktop, Cursor, Cline, Windsurf,
Zed, Continue**):

```json
{
  "mcpServers": {
    "pangolin": {
      "command": "smartpangolin-mcp"
    }
  }
}
```

Where the config lives:
- **Claude Desktop** — `claude_desktop_config.json`
- **Cursor** — `.cursor/mcp.json` (project) or Settings → MCP
- **Cline / Roo** — the extension's `cline_mcp_settings.json`
- **Windsurf** — `~/.codeium/windsurf/mcp_config.json`
- **Zed** — `settings.json` → `context_servers`
- **Continue** — `~/.continue/config.json` → `mcpServers`

Then ask the agent: *"scan this repo with pangolin before we share it."*
