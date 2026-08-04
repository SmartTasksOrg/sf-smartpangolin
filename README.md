<!-- mcp-name: io.github.smarttasksorg/smartpangolin -->
<h1 align="center">🦔 SmartPangolin</h1>
<p align="center"><b>Scan before you share.</b> Stop leaking secrets into AI models, agents, and coding tools.</p>

---

## The problem nobody's watching

You paste your repo into an LLM. You let an AI coding agent read your project. You
zip a folder to a contractor. **What did you just leak?** A `.env`, an AWS key, a
GitHub token, an internal hostname — one line is enough.

SmartPangolin is a **fail-closed** guard that scans a tree for secrets in
**filenames and content**, honours your **`.gitignore`**, and refuses to share
until it's clean. Same rules, five languages, and a plug into most AI coding tools.

```bash
pip install smartpangolin
pango pack --dry-run        # what would leak?  (writes nothing)
```

## Play with our mascot 🦔
Open **[`README-playground.html`](README-playground.html)** — pose Pangi, dress it
up, and export your own SVG/PNG icons. Save it if you like it.

---

## Use it anywhere

| You work in… | Do this |
|---|---|
| **Python** | `pip install smartpangolin` then `pango pack --dry-run` |
| **Node / React** | `npx pangolin-check .` (native, zero-dep) |
| **Go** | `go run ./ports/go .` |
| **Java** | `java -jar pangolin-check.jar .` |
| **PHP** | `php ports/php/pangolin-check.php .` |
| **AI coding tools** (Cursor, Claude Desktop, Cline, Windsurf, Zed, Continue) | add the MCP server (`kits/mcp`): `{ "command": "smartpangolin-mcp" }` |
| **LangChain / LlamaIndex / OpenAI tools** | drop-in adapters in `kits/` |
| **CI / pre-commit / Husky** | templates in `kits/ci` and `kits/precommit` |
| **Your editor's search box** | paste our regexes from `integrations/vscode` |

All ports produce the **same rule IDs** on the same tree — proven by
`ports/conformance/run.sh` (every rule, both share modes, 4 languages).

## Standardize your team in one command
```bash
./bootstrap/pangolin-bootstrap.sh      # or .ps1 on Windows
```
Creates the standardized **`.secret/`** safe-zone (git-ignored, never shared), a
starter `.pangolin.json`, and the right `.gitignore` — so every repo in your org
uses the same predictable, scannable layout.

## How it works
- **`SEC-PATH-*`** — dangerous filenames (`.env`, `*.pem`, ssh keys, `*.tfstate`, ...)
- **`SEC-CONT-*`** — ~20 in-content secret patterns (AWS, GitHub, OpenAI, Stripe, JWT, ...)
- **`LOC-*`** — local-infra leaks (private IPs, internal hostnames) — withheld on **public** shares, kept on **private**
- **`OPS-GITIGNORE`** — honours your `.gitignore`
- Every override (`allow` in `.pangolin.json`) is recorded and folded into a policy hash, so shares are auditable.

## What it catches — and what it can't

SmartPangolin is deterministic pattern matching. It reliably catches
**unintentional** leaks — a committed `.env`, a pasted key, a secret in a
filename, a key embedded in an image/font/oversize file, or one split by an
invisible character. That's the common, dangerous case.

It **cannot** reliably trace a secret that has been *deliberately obfuscated* in
text. By design it will not flag a key that is:

- base64/hex-encoded (`QUtJQU...`),
- split by concatenation (`"AKIA" + "IOSF..."`),
- broken by ordinary whitespace or a newline inside the token, or
- padded with word characters (`xxAKIA...xx`).

Catching those needs entropy analysis, decoding passes, or AST inspection —
non-deterministic, false-positive-prone techniques that are outside a
deterministic scanner's contract (an opt-in entropy detector is the planned
mitigation). **Treat SmartPangolin as a strong last line of defence, not a
guarantee against a motivated insider.** Full detail in [`SECURITY.md`](SECURITY.md).

## Build from source
```bash
./build/build-all.sh        # or .\build\build-all.ps1
```

## Team

Built by **SmartTasks Lab**.

- **Roen Branham** — CEO & AI Strategy Architect · [LinkedIn](https://www.linkedin.com/in/roen-branham-167ab29/)
- **Le Thanh** — Chief Architect (Cortex engine) · [LinkedIn](https://www.linkedin.com/in/lee-thanh-76aa8ba0/)

Full bios in [`AUTHORS.md`](AUTHORS.md).

## License
Apache-2.0. Contributions welcome — see `CONTRIBUTING.md`.
