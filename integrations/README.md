# SmartPangolin — integrations

Drop-in ways to run **SmartPangolin** inside the tools and frameworks you already use.
Every wrapper here calls one source of truth, [`adapter.py`](adapter.py), which wires
straight to the Python core (`scan`).

| Target | Path | What it gives you |
|---|---|---|
| Flowise | [`flowise/`](flowise/) | a custom node for the visual builder |
| VS Code | [`vscode/`](vscode/) | a command that runs it on the active file/workspace |

## Quick check
```bash
python integrations/adapter.py --root <repo>
```
Returns a compact JSON result — the same shape every wrapper emits.
