# SmartPangolin — Go

There is no separate Go binary to maintain; the **policy is the contract**. A Go
port is conformant when, given the same tree, it produces the same
`content_sha256` and the same set of `EXCLUSIONS.json` rule IDs.

## Consume a SmartPangolin artifact (works today)

The manifest and exclusions are plain JSON; `SHA256SUMS` is coreutils-compatible.

```go
package main

import (
    "archive/zip"
    "encoding/json"
    "fmt"
)

type Manifest struct {
    ContentSHA256 string `json:"content_sha256"`
    ShareMode     string `json:"share_mode"`
    FileCount     int    `json:"file_count"`
    Files         []struct {
        Path   string `json:"path"`
        SHA256 string `json:"sha256"`
    } `json:"files"`
}

func main() {
    r, _ := zip.OpenReader("share.zip")
    defer r.Close()
    for _, f := range r.File {
        if f.Name == "_SHARE/MANIFEST.json" {
            rc, _ := f.Open()
            var m Manifest
            json.NewDecoder(rc).Decode(&m)
            rc.Close()
            fmt.Printf("%s: %d files, content %s\n", m.ShareMode, m.FileCount, m.ContentSHA256[:16])
        }
    }
}
```

## Port the scanner (roadmap)

1. `sf-smartpangolin policy > policy.json` — the full ruleset, versioned.
2. Compile `content_rules` and `local_rules` with Go's `regexp` (RE2). Note the
   Anthropic-before-OpenAI ordering matters for attribution.
3. Match `path_rules` globs with `path.Match` (lower-cased basename).
4. Implement fail-closed OPS handling (nul byte in first 8 KiB → binary → exclude
   unless in `BINARY_SAFE_EXTS`).
5. Emit `content_sha256` over the sorted `(path, "\x00", filehash, "\n")` stream.

See [../../docs/porting.md](../../docs/porting.md) for the exact hashing recipe.

> **Update:** a real, conformance-tested native port now lives in `ports/go/`.
