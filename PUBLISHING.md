# Publishing — one command per registry

Placeholders to set first: the GitHub org (`smarttasks`), the Maven `groupId`
(`cloud.smarttasks`, needs domain/namespace ownership — or switch to
`io.github.<your-org>`), and real `authors`/URLs. Regenerate ports after any rule
change with `python3 tools/export_policy.py`.

## PyPI — `sf-smartpangolin` (Python, reference + MCP server)
    python -m build
    twine upload dist/*            # or the .github/workflows/release.yml Trusted Publisher
Ships the `sf-smartpangolin` CLI and the `sf-smartpangolin-mcp` MCP server. `twine check` passes.

## npm — `pangolin-check` (Node port)
    cd ports/node && npm login && npm publish
Validated with `npm publish --dry-run` (6 files, test/ excluded).

## Packagist — `smarttasks/pangolin-check` (PHP port)
    # composer.json is valid (`composer validate`).
    # Register once at https://packagist.org/packages/submit with the repo URL,
    # then add the GitHub webhook so tags auto-publish.

## Maven Central — `cloud.smarttasks:pangolin-check` (Java port)
    cd ports/java && mvn -Prelease deploy      # needs Central Portal creds + a GPG key
`pom.xml` is well-formed and `mvn validate` passes; `javac`+`jar` produces a
runnable `pangolin-check.jar` (Main-Class: Main).

## MCP registry — `io.github.smarttasks/smartpangolin`
Publish the PyPI package first (the server ships in it), then:
    cd publish
    mcp-publisher login github        # authenticates the io.github.smarttasks namespace
    mcp-publisher publish             # uploads server.json
`publish/server.json` is **valid against the official schema**
(`publish/mcp.server.schema.json`); the `mcp-name` marker in `README.md` matches
the server name (both required by the registry).
