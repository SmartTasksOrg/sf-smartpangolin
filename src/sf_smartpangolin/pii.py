"""
pii.py — opt-in PII scanning for regular text (a higher scan level).

Off by default. Enable with ``sf-smartpangolin pack --pii`` (or ``api.pack(pii=True)``) to
also catch personal data in prose and docs — emails, phone numbers, US SSNs, and
card numbers — on top of the secret rules.

Two exclusions keep legitimate attribution intact:
  - **Author context** (default on): a match on a line that looks like an author
    tag, maintainer line, copyright, or contact is kept. So ``@author jane@x.com``
    and ``Copyright (c) Jane Doe <jane@x.com>`` survive.
  - **Allow-list**: exact strings in ``.pangolin.json`` ``pii_allow`` are always
    kept (e.g. your published author email).

``redact_pii`` returns cleaned text with each finding replaced by a ``[TYPE]``
token, so you can scrub a doc instead of withholding the whole file.
"""
from __future__ import annotations
import re

__all__ = ["PII_RULES", "scan_pii", "redact_pii"]

# id, compiled regex, redaction token
PII_RULES = [
    ("PII-EMAIL", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), "[EMAIL]"),
    ("PII-SSN",   re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN]"),
    ("PII-CC",    re.compile(r"\b\d(?:[ \-]?\d){14,15}\b"), "[CARD]"),
    ("PII-PHONE", re.compile(r"\b(?:\+?\d{1,3}[ .\-]?)?(?:\(\d{3}\)|\d{3})[ .\-]?\d{3}[ .\-]?\d{4}\b"), "[PHONE]"),
]

AUTHOR_RE = re.compile(
    r"(?i)(?:^|[^a-z])(authors?|maintainer|maintained by|copyright|\(c\)|©|@author)")


def _line_starts(text):
    starts, pos = [0], 0
    for line in text.splitlines(keepends=True):
        pos += len(line)
        starts.append(pos)
    return starts


def _line_of(text, off, starts):
    # binary-ish scan is fine for typical docs
    lo = 0
    for i in range(len(starts) - 1):
        if starts[i] <= off < starts[i + 1]:
            lo = i
            break
    return text[starts[lo]:starts[lo + 1] if lo + 1 < len(starts) else len(text)]


def scan_pii(text, allow=None, skip_author=True):
    """Return a list of {rule, match, offset} for PII in `text`.

    Allow-listed exact strings and (optionally) matches on author-context lines
    are omitted.
    """
    allow = set(allow or [])
    starts = _line_starts(text)
    hits = []
    for rule, rx, _tok in PII_RULES:
        for m in rx.finditer(text):
            val = m.group(0)
            if val in allow:
                continue
            if skip_author and AUTHOR_RE.search(_line_of(text, m.start(), starts)):
                continue
            hits.append({"rule": rule, "match": val, "offset": m.start()})
    hits.sort(key=lambda h: h["offset"])
    return hits


def redact_pii(text, allow=None, skip_author=True):
    """Return `text` with each PII finding replaced by its token (author context
    and allow-listed values preserved)."""
    allow = set(allow or [])
    starts = _line_starts(text)

    def repl_factory(tok):
        def _r(m):
            val = m.group(0)
            if val in allow:
                return val
            if skip_author and AUTHOR_RE.search(_line_of(text, m.start(), starts)):
                return val
            return tok
        return _r

    out = text
    # apply on the original offsets rule-by-rule; tokens don't reintroduce matches
    for rule, rx, tok in PII_RULES:
        out = rx.sub(repl_factory(tok), out)
    return out
