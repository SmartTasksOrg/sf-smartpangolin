"""
gitignore.py — a dependency-free .gitignore matcher.

SmartPangolin honours the project's own ignore rules as an *auditable* exclusion
source (rule ``OPS-GITIGNORE``): anything git already ignores is, by default, not
worth shipping to a third party either. It is deliberately conservative — when a
pattern is ambiguous it errs toward *excluding* (fail-closed), and every ignore
can still be forced back in via ``.pangolin.json`` ``allow`` (which is recorded
as an override).

Supported syntax (a robust subset of gitignore(5)):
  - blank lines and ``#`` comments
  - ``!`` negation (last matching rule wins)
  - trailing ``/``  -> directory-only match
  - leading ``/``   -> anchored to the .gitignore's directory
  - ``**``          -> spans directories
  - ``*`` / ``?``   -> within a single path segment
  - nested .gitignore files, each scoped to their own subtree
"""
from __future__ import annotations
import os
import re
from pathlib import Path

__all__ = ["GitignoreSpec", "build_spec"]


def _translate(pattern: str) -> str:
    """Translate one gitignore glob body into a regex fragment (no anchors)."""
    i, n, out = 0, len(pattern), []
    while i < n:
        c = pattern[i]
        if c == "*":
            if pattern[i:i + 2] == "**":
                # ** possibly followed by /
                if pattern[i:i + 3] == "**/":
                    out.append("(?:.*/)?")
                    i += 3
                    continue
                out.append(".*")
                i += 2
                continue
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        elif c == "/":
            out.append("/")
        else:
            out.append(re.escape(c))
        i += 1
    return "".join(out)


class _Rule:
    __slots__ = ("regex", "negate", "dir_only", "base")

    def __init__(self, line: str, base: str):
        self.negate = False
        self.dir_only = False
        self.base = base  # posix rel dir of the owning .gitignore ("" == root)

        body = line
        if body.startswith("!"):
            self.negate = True
            body = body[1:]
        if body.startswith("\\#") or body.startswith("\\!"):
            body = body[1:]
        if body.endswith("/"):
            self.dir_only = True
            body = body[:-1]

        anchored = body.startswith("/") or ("/" in body.rstrip("/"))
        body = body.lstrip("/")
        frag = _translate(body)

        prefix = ""
        if base:
            prefix = re.escape(base + "/")
        if anchored:
            self.regex = re.compile("^" + prefix + frag + "(?:/.*)?$")
        else:
            # match at any depth beneath base
            self.regex = re.compile("^" + prefix + "(?:.*/)?" + frag + "(?:/.*)?$")

    def match(self, rel: str) -> bool:
        return self.regex.match(rel) is not None


class GitignoreSpec:
    """Ordered set of rules. Last matching rule decides; negation un-ignores."""

    def __init__(self, rules):
        self.rules = rules

    def __bool__(self):
        return bool(self.rules)

    def ignored(self, rel: str, is_dir: bool = False) -> bool:
        rel = rel.replace(os.sep, "/").lstrip("./")
        decision = False
        for r in self.rules:
            if r.dir_only and not is_dir:
                continue
            if r.match(rel):
                decision = not r.negate
        return decision


def _read_lines(path: Path):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    out = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        out.append(line)
    return out


def build_spec(root: Path, extra_files=None) -> GitignoreSpec:
    """Collect the root .gitignore plus any nested ones into one ordered spec.

    Deeper .gitignore files come later so their rules can override the root's,
    matching git's precedence. ``extra_files`` may name additional ignore files
    to honour (e.g. ``.dockerignore``); each is scoped to its own directory.
    """
    root = Path(root)
    names = [".gitignore"] + list(extra_files or [])
    found = []  # (depth, base_rel, path)
    for dirpath, dirnames, filenames in os.walk(root):
        # don't descend into VCS metadata while gathering ignore files
        dirnames[:] = [d for d in dirnames if d not in (".git", ".hg", ".svn")]
        base = Path(dirpath).relative_to(root).as_posix()
        base = "" if base == "." else base
        for nm in names:
            if nm in filenames:
                found.append((base.count("/") + (1 if base else 0),
                              base, Path(dirpath) / nm))
    found.sort(key=lambda t: (t[0], t[1]))
    rules = []
    for _depth, base, path in found:
        for line in _read_lines(path):
            rules.append(_Rule(line, base))
    return GitignoreSpec(rules)
