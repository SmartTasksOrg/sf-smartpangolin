#!/usr/bin/env python3
"""Thin launcher — the server lives in the installed package.
    install SmartPangolin (see the README, "Install"), then run sf-smartpangolin-mcp
This shim lets you run it straight from a checkout too."""
try:
    from sf_smartpangolin.mcp import main
except ModuleNotFoundError:
    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
    from sf_smartpangolin.mcp import main
if __name__ == "__main__":
    main()
