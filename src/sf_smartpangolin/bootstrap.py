"""
sf_smartpangolin.bootstrap — optional venv re-exec.

SmartPangolin is stdlib-only, so a venv is never strictly required. But the
surrounding pipeline (stage 1/2, git) often runs inside one (.venv / venv /
ft-venv), and running the packager under a different interpreter than the
tooling it shells out to causes confusing failures. If a venv is present and we
are not in it, re-exec under it. ``--venv none`` disables; ``--venv <path>``
pins a specific one.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

VENV_CANDIDATES = (".venv", "venv", "ft-venv", "env")
_BOOTSTRAP_FLAG = "PANGO_BOOTSTRAPPED"


def _venv_python(venv_dir: Path):
    for rel in ("bin/python3", "bin/python", "Scripts/python.exe"):
        p = venv_dir / rel
        if p.exists():
            return p
    return None


def maybe_reexec_in_venv(root: Path, explicit: str, debug: bool = False):
    """Re-exec under a venv interpreter unless already inside one."""
    if os.environ.get(_BOOTSTRAP_FLAG) == "1":
        return
    if explicit == "none":
        return

    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    if in_venv and explicit == "auto":
        if debug:
            print(f"[venv] already inside {sys.prefix}")
        return

    if explicit not in ("auto", "none"):
        candidates = [Path(explicit)]
    else:
        candidates = [root / c for c in VENV_CANDIDATES]
        candidates += [Path.cwd() / c for c in VENV_CANDIDATES]

    for cand in candidates:
        if not cand.is_dir():
            continue
        py = _venv_python(cand)
        if not py:
            continue
        if Path(sys.executable).resolve() == py.resolve():
            return
        env = dict(os.environ, **{_BOOTSTRAP_FLAG: "1"})
        print(f"[venv] re-exec under {py}")
        os.execve(str(py), [str(py), "-m", "sf-smartpangolin"] + sys.argv[1:], env)

    if explicit not in ("auto", "none"):
        print(f"[venv] WARNING: no interpreter found in '{explicit}', "
              f"continuing with {sys.executable}")
