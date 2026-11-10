# CLI reference

`sf-smartpangolin <command> [options]`. Bare `sf-smartpangolin` (or `sf-smartpangolin --root …`) is an
alias for `sf-smartpangolin pack`.

## pack — seal a tree

```
sf-smartpangolin pack --root PATH [--share public|private] [options]
```

Selection precedence: `--files` → `file_folder_path.txt` (from stage 1, unless
`--rebuild-tree`) → direct filesystem walk.

Shared/pipeline flags: `--root --focus --files --tree-output --path-output
--rebuild-tree --exclude-ext --exclude-folders --exclude-paths --output-folder
--source-only --max-chars --prefix --config-file --venv --debug`.

Share policy: `--share {public,private}` · `--archive-dir` · `--keep-txt` ·
`--zip-name` · `--allow PATH…` · `--dry-run` · `--merge`/`--no-merge` ·
`--merged-only` · `--no-git-list` · `--name-template` (placeholders
`{prefix} {stamp} {mode} {focus}`) · `--source-date-epoch`.

Output and limits:

| Option | What it does |
|---|---|
| `--format zip` (default) | The sealed share zip, as before. |
| `--format txt` | No zip: the merged parts as plain `.txt` files in a folder under `--archive-dir` (named like the zip would be), with `SHA256SUMS`, `MANIFEST.json` and `SHARE_REPORT.md`. For models that do not take a zip. Raw files are not included; every included file is in the parts. |
| `--format both` | The zip, and the `.txt` parts kept in `--output-folder` (the same as `--keep-txt`). |
| `--max-chars N` | Most characters in one part (default 3,500,000). Never exceeded: a file larger than a part is split at line boundaries, and each piece's header says which lines it holds (`### src/big.py (lines 1-4200 of 9000)`). |
| `--max-bytes N` | Most UTF-8 bytes in one part, for upload limits given in bytes. Can be combined with `--max-chars`. |
| `--max-files N` | Most parts. When the share needs more, nothing is written, and the error names the smallest `--max-chars` (or `--max-bytes`) that fits in N parts. Content is never dropped to meet a limit. |

Every part starts with `=== part X of N: <file name> (sf-smartpangolin) ===`, so a model given the parts
one at a time knows how many there are. A line longer than a whole part is refused, with the limit that
would hold it. The same settings can go in `.pangolin.json` as `format`, `max_chars`, `max_bytes` and
`max_files`.

```
sf-smartpangolin pack --root . --format txt --max-chars 400000 --max-files 10
sf-smartpangolin verify extracted_source/share_archive/20261110T120000Z_share_public
```

Retention: `--retention-days N` (default 30) · `--retention-mb N` (default 1024)
· `--no-purge`.

## verify — check a zip (or a txt folder) against its manifest

```
sf-smartpangolin verify ZIP
sf-smartpangolin verify FOLDER      # a --format txt folder: every part against MANIFEST.json and SHA256SUMS
```

Recomputes `zip_sha256` vs the sidecar, `content_sha256` vs the manifest, every
file/shard hash, and flags anything present in the zip but absent from the
manifest. Exit 0 = OK, 2 = problem(s).

## triage — read the audit records

```
sf-smartpangolin triage ZIP [PREFIX] [--full] [--ext] [--git]
```

`PREFIX` filters rule IDs (e.g. `SEC-`). `--ext` shows an extension histogram per
rule. `--git` shows tracked-but-not-shipped files grouped by the rule that
dropped each — **the most useful view**; a wrongly-dropped source file hides
there. `--full` disables the 40-line truncation.

## tree — stage 1 only

```
sf-smartpangolin tree --root PATH [--focus SUB] [--path-output FILE]
```

Writes the indented tree and the flat path list the packager consumes.

## purge — retention only

```
sf-smartpangolin purge --root PATH [--retention-days N] [--retention-mb N] [--dry-run]
```

## policy — print the active policy

```
sf-smartpangolin policy [--root PATH] [--fingerprint]
```

Full ruleset as JSON, or just the `policy_sha256` (includes `.pangolin.json`
overrides read from `--root`).

## init — scaffold the standard

```
sf-smartpangolin init --root PATH [--force]
```

Creates `.secret/` (git-ignored, never-shipped) and a starter `.pangolin.json`.
