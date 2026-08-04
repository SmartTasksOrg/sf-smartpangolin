# pangolin-check (Go)

Native Go port (RE2). The two lookahead rules are shimmed with a base pattern
plus a code-level post-filter, so results match the Python engine exactly.

```bash
go build -o pangolin-check .
./pangolin-check <path> [--mode public|private] [--json] [--no-gitignore]
```

`policy.json` is embedded via `//go:embed`; regenerate with
`python3 tools/export_policy.py`.
