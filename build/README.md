# Build all packages from source

    ./build-all.sh        # macOS / Linux
    .\build-all.ps1       # Windows

Syncs the policy spec, then builds PyPI (wheel+sdist), the Node/Go/Java/PHP
ports, and runs the cross-language conformance gate. Nothing here uploads —
publishing lives in the **private** parent folder (`../private/publish`).
