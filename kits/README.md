# SmartPangolin integration kits

Plug SmartPangolin into (almost) any coding tool by hitting the surfaces they all
share. You rarely need a bespoke integration — pick one of these.

## The two universal surfaces

**1. Git / CI** — covers essentially every repo and IDE.
| Tool | Kit |
|------|-----|
| pre-commit | `precommit/` (uses the repo's `.pre-commit-hooks.yaml`) |
| GitHub Actions | `ci/github-actions.yml` (or `adapters/github-action`) |
| GitLab CI | `ci/gitlab-ci.yml` |
| CircleCI | `ci/circleci.yml` |
| Husky / lint-staged (JS) | `ci/husky-lint-staged.md` — uses the native Node port, no Python |

**2. MCP** — the standard most *AI* coding tools speak, so one server = broad reach.
`mcp/server.py` is a zero-dependency MCP server exposing `pangolin_scan` and
`pangolin_pack`. One JSON block registers it in **Claude Desktop, Cursor, Cline,
Windsurf, Zed, and Continue** (see `mcp/README.md`).

## Agent / framework adapters
| Framework | Kit | Verified here |
|-----------|-----|:---:|
| LangChain | `langchain/` (`StructuredTool`) | ✅ langchain-core 1.5.3 |
| LlamaIndex | `llamaindex/` (`FunctionTool`) | ✅ llama-index-core |
| OpenAI / Anthropic / Gemini / Mistral / Bedrock | `function-calling/` (schemas + `dispatch`) | ✅ |
| MCP clients (Cursor, Cline, Windsurf, Zed, Continue, Claude Desktop) | `mcp/` | ✅ stdio JSON-RPC |

## The pattern they all follow
Every kit does the same thing: **scan before you share.** `pangolin_scan` runs a
dry-run and reports what would be withheld (secrets in filenames and content,
`.gitignore`, local-infra), and flags `blocked` when a `SEC-*` finding is present
so an agent or hook can refuse. Nothing is written unless you call `pangolin_pack`.

```python
# the guard, in three lines, anywhere:
from sf_smartpangolin import api
r = api.pack(".", share="public", dry_run=True)
assert not any(k.startswith("SEC-") for k in r.exclusions["by_rule"]), "secrets present"
```

Most kits need SmartPangolin installed from a clone (`python -m pip install .`
in a clone of this repository; it is not on PyPI yet); the Husky/Node path uses the native
`ports/node` scanner and needs no Python at all.
