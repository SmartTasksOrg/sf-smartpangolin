"""Opt-in PII scanning: detection, author-tag skip, allow-list, redaction, pack."""
from smartpangolin import pii, api


DOC = ("# Guide\n\nContact support at help@acme.com or call 415-555-0199.\n"
       "My card is 4111 1111 1111 1111 and SSN 123-45-6789.\n")
CODE = ("# @author jane.doe@acme.com\n# Copyright (c) 2026 Jane Doe <jane@acme.com>\n"
        "print('hello')\n")


def test_detects_all_types():
    rules = {h["rule"] for h in pii.scan_pii(DOC)}
    assert rules == {"PII-EMAIL", "PII-PHONE", "PII-CC", "PII-SSN"}


def test_author_context_is_kept():
    assert pii.scan_pii(CODE) == []                       # @author / copyright lines
    assert {h["rule"] for h in pii.scan_pii(CODE, skip_author=False)} == {"PII-EMAIL"}


def test_allow_list():
    got = {h["rule"] for h in pii.scan_pii(DOC, allow=["help@acme.com"])}
    assert "PII-EMAIL" not in got and "PII-SSN" in got


def test_redaction_and_author_preserved():
    out = pii.redact_pii(DOC)
    assert "[EMAIL]" in out and "[PHONE]" in out and "[CARD]" in out and "[SSN]" in out
    assert "help@acme.com" not in out
    assert pii.redact_pii(CODE).splitlines()[0].endswith("jane.doe@acme.com")


def test_pack_pii_is_opt_in(tmp_path):
    (tmp_path / "doc.md").write_text(DOC, encoding="utf-8")
    (tmp_path / "ok.txt").write_text("nothing here\n", encoding="utf-8")
    off = api.pack(tmp_path, dry_run=True)
    assert "doc.md" in {f["path"] for f in off.manifest["files"]}          # ships by default
    on = api.pack(tmp_path, dry_run=True, pii=True)
    assert "doc.md" not in {f["path"] for f in on.manifest["files"]}       # withheld with --pii
    assert any(k.startswith("PII-") for k in on.exclusions["by_rule"])
