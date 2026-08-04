# CLI reference

`pango <command> [options]`. Bare `smartpangolin` (or `pango --root …`) is an
alias for `pango pack`.

## pack — seal a tree

```
pango pack --root PATH [--share public|private] [options]
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

Retention: `--retention-days N` (default 30) · `--retention-mb N` (default 1024)
· `--no-purge`.

## verify — check a zip against its manifest

```
pango verify ZIP
```

Recomputes `zip_sha256` vs the sidecar, `content_sha256` vs the manifest, every
file/shard hash, and flags anything present in the zip but absent from the
manifest. Exit 0 = OK, 2 = problem(s).

## triage — read the audit records

```
pango triage ZIP [PREFIX] [--full] [--ext] [--git]
```

`PREFIX` filters rule IDs (e.g. `SEC-`). `--ext` shows an extension histogram per
rule. `--git` shows tracked-but-not-shipped files grouped by the rule that
dropped each — **the most useful view**; a wrongly-dropped source file hides
there. `--full` disables the 40-line truncation.

## tree — stage 1 only

```
pango tree --root PATH [--focus SUB] [--path-output FILE]
```

Writes the indented tree and the flat path list the packager consumes.

## purge — retention only

```
pango purge --root PATH [--retention-days N] [--retention-mb N] [--dry-run]
```

## policy — print the active policy

```
pango policy [--root PATH] [--fingerprint]
```

Full ruleset as JSON, or just the `policy_sha256` (includes `.pangolin.json`
overrides read from `--root`).

## init — scaffold the standard

```
pango init --root PATH [--force]
```

Creates `.secret/` (git-ignored, never-shipped) and a starter `.pangolin.json`.
