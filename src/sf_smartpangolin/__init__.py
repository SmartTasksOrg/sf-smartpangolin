"""
SmartPangolin — deterministic, fail-closed, auditable secret-scrubbing packager.

Prepare a project tree for sharing with a cloud endpoint or a third party, with
proof of exactly what went in and what did not. Secrets are always excluded;
``--share public`` additionally strips local-infrastructure disclosure.

Quick start (Python)::

    from sf_smartpangolin import pack
    result = pack("./my_project", share="public")
    print(result.zip_path, result.content_sha256)

Quick start (CLI)::

    sf-smartpangolin pack --root ./my_project --share public
    sf-smartpangolin verify <zip>
    sf-smartpangolin triage <zip> --git

Part of the SmartTasks / IAIso ecosystem. See docs/ecosystem.md.
"""
from ._version import __version__
from .api import pack, PackResult, resolve_layout
from .engine import (
    POLICY_VERSION,
    policy_fingerprint,
    verify_zip,
    purge_archive,
    PATH_RULES,
    PATH_DIR_RULES,
    CONTENT_RULES,
    LOCAL_RULES,
    PATH_ALLOWLIST,
)
from .triage import triage
from . import core as core, models as models  # Smart* family quick-scan API (re-exported)
from .core import scan as scan

__all__ = [
    "__version__",
    "pack",
    "PackResult",
    "resolve_layout",
    "verify_zip",
    "purge_archive",
    "triage",
    "policy_fingerprint",
    "POLICY_VERSION",
    "PATH_RULES",
    "PATH_DIR_RULES",
    "CONTENT_RULES",
    "LOCAL_RULES",
    "PATH_ALLOWLIST",
]
