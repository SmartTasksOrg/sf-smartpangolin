"""End-to-end and unit tests for SmartPangolin."""
import json
import zipfile

import pytest

from smartpangolin import engine, pack, policy_fingerprint, verify_zip
from smartpangolin.triage import triage

HF = "hf_" + "A" * 34               # format-valid, fake
GHP = "ghp_" + "0" * 36


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "proj"
    (root / "src").mkdir(parents=True)
    (root / ".secret").mkdir()
    (root / ".env").write_text(f"HF_TOKEN={HF}\n")
    (root / ".env.example").write_text("HF_TOKEN=your-token-here\n")
    (root / "src" / "server.py").write_text('print("bind 10.1.2.3")\n')
    (root / "src" / "app.py").write_text('print("hello")\n')
    (root / "README.md").write_text("# proj\n")
    (root / ".secret" / "prod.env").write_text(f"GH={GHP}\n")
    return root


def _names(zip_path):
    with zipfile.ZipFile(zip_path) as zf:
        return set(zf.namelist())


def _merged_blob(zip_path):
    with zipfile.ZipFile(zip_path) as zf:
        return "".join(zf.read(n).decode() for n in zf.namelist()
                       if n.startswith("_MERGED/"))


def test_env_with_token_is_excluded(project):
    r = pack(project, share="public", no_git_list=True)
    assert ".env" not in _names(r.zip_path)
    assert "SEC-PATH-ENV" in r.exclusions["by_rule"]
    # the token never appears anywhere in the artifact
    blob = _merged_blob(r.zip_path)
    assert HF not in blob
    assert "### .env\n" not in blob   # exact header, not .env.example


def test_env_example_is_allowlisted(project):
    r = pack(project, share="public", no_git_list=True)
    assert ".env.example" in _names(r.zip_path)


def test_secret_dir_never_ships(project):
    for mode in ("public", "private"):
        r = pack(project, share=mode, no_git_list=True)
        assert not any(n.startswith(".secret/") for n in _names(r.zip_path))


def test_local_ip_excluded_public_retained_private(project):
    pub = pack(project, share="public", no_git_list=True)
    assert "src/server.py" not in _names(pub.zip_path)
    assert "LOC-RFC1918" in pub.exclusions["by_rule"]

    priv = pack(project, share="private", no_git_list=True)
    assert "src/server.py" in _names(priv.zip_path)


def test_content_hash_is_stable(project):
    a = pack(project, share="public", no_git_list=True, zip_name="a.zip", no_purge=True)
    b = pack(project, share="public", no_git_list=True, zip_name="b.zip", no_purge=True)
    assert a.content_sha256 == b.content_sha256


def test_source_date_epoch_is_byte_reproducible(project):
    a = pack(project, share="public", no_git_list=True, zip_name="a.zip",
             no_purge=True, source_date_epoch=1700000000)
    b = pack(project, share="public", no_git_list=True, zip_name="b.zip",
             no_purge=True, source_date_epoch=1700000000)
    assert engine.sha256_file(a.zip_path) == engine.sha256_file(b.zip_path)


def test_verify_passes_on_fresh_zip(project):
    r = pack(project, share="public", no_git_list=True)
    assert verify_zip(r.zip_path) == 0


def test_verify_detects_corruption(project, tmp_path):
    r = pack(project, share="public", no_git_list=True)
    # rewrite one file in the zip to a different content
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(r.zip_path) as zin, zipfile.ZipFile(bad, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "src/app.py":
                data = b'print("tampered")\n'
            zout.writestr(item, data)
    assert verify_zip(bad) == 2


def test_allow_override_is_recorded_and_changes_fingerprint(project):
    base = policy_fingerprint()
    (project / ".pangolin.json").write_text(json.dumps({"deny_globs": ["*.md"]}))
    _cfg, user = engine.load_pangolin_config(project)
    assert policy_fingerprint(user) != base

    r = pack(project, share="public", no_git_list=True)
    assert "SEC-PATH-USER" in r.exclusions["by_rule"]
    assert "README.md" not in _names(r.zip_path)


def test_allow_force_includes_and_records_override(project):
    # scorecard.py trips SEC-CONT-ASSIGN (quoted literal), then we allow it
    (project / "src" / "scorecard.py").write_text('api_key = "not-needed-value"\n')
    dropped = pack(project, share="public", no_git_list=True, zip_name="d.zip", no_purge=True)
    assert "src/scorecard.py" not in _names(dropped.zip_path)

    kept = pack(project, share="public", no_git_list=True, zip_name="k.zip",
                no_purge=True, allow=["src/scorecard.py"])
    assert "src/scorecard.py" in _names(kept.zip_path)
    assert any(o["path"] == "src/scorecard.py" for o in kept.overrides)


def test_merged_only_omits_raw_but_verifies(project):
    r = pack(project, share="public", no_git_list=True, merged_only=True)
    names = _names(r.zip_path)
    assert not any(n == "src/app.py" for n in names)
    assert any(n.startswith("_MERGED/") for n in names)
    assert verify_zip(r.zip_path) == 0


def test_dry_run_writes_nothing(project):
    r = pack(project, share="public", no_git_list=True, dry_run=True)
    assert r.zip_path is None
    assert r.dry_run is True


def test_triage_runs(project, capsys):
    r = pack(project, share="public", no_git_list=True)
    assert triage(r.zip_path, prefix="SEC-") == 0
    out = capsys.readouterr().out
    assert "SEC-PATH-ENV" in out


def test_manifest_never_contains_secret_values(project):
    r = pack(project, share="public", no_git_list=True)
    with zipfile.ZipFile(r.zip_path) as zf:
        excl = zf.read("_SHARE/EXCLUSIONS.json").decode()
    assert HF not in excl
    assert "byte" in excl        # offsets recorded instead of values
