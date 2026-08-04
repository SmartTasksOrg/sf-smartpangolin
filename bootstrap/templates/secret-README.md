# .secret/  — the standardized safe zone

Everything under `.secret/` is **never shared** (SmartPangolin rule `SEC-DIR-SECRET`)
and is git-ignored. Put anything sensitive here so it's caught by default:

    .secret/local/   local-only env files, dev keys, tokens
    .secret/ci/      CI/CD secrets, deploy keys
    .secret/data/    private fixtures, dumps

This mirrors the SmartPangolin architecture: a single, predictable location the
scanner, your editor patterns, and your teammates all recognize.
