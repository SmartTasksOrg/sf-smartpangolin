"""Tests for .gitignore honouring (rule OPS-GITIGNORE) and its overrides."""
from smartpangolin.gitignore import _Rule, GitignoreSpec
from smartpangolin import api


def _spec(lines, base=""):
    return GitignoreSpec([_Rule(line, base) for line in lines])


def test_matcher_basics():
    assert _spec(["*.log"]).ignored("a/b.log")
    assert not _spec(["*.log"]).ignored("a/b.txt")
    assert _spec(["/build"]).ignored("build/x.o")
    assert not _spec(["/build"]).ignored("src/build/x.o")
    assert _spec(["build/"]).ignored("build", is_dir=True)
    assert not _spec(["build/"]).ignored("build", is_dir=False)
    assert _spec(["**/tmp"]).ignored("a/b/tmp", is_dir=True)


def test_matcher_negation_last_wins():
    sp = _spec(["*.key", "!keep.key"])
    assert sp.ignored("priv.key")
    assert not sp.ignored("keep.key")


def _tree(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "logs").mkdir()
    (tmp_path / ".gitignore").write_text("*.log\nsecret_notes.txt\n!keep.log\n", encoding="utf-8")
    (tmp_path / "src" / "app.py").write_text("print('hi')\n", encoding="utf-8")
    (tmp_path / "logs" / "run.log").write_text("debug\n", encoding="utf-8")
    (tmp_path / "keep.log").write_text("keep\n", encoding="utf-8")
    (tmp_path / "secret_notes.txt").write_text("internal\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("readme\n", encoding="utf-8")
    return tmp_path


def _paths(res):
    return {f["path"] for f in res.manifest["files"]}


def test_pack_honours_gitignore(tmp_path):
    root = _tree(tmp_path)
    r = api.pack(root, share="public", dry_run=True)
    paths = _paths(r)
    assert "src/app.py" in paths and "README.md" in paths
    assert "keep.log" in paths                      # negation retained
    assert "logs/run.log" not in paths              # *.log
    assert "secret_notes.txt" not in paths
    assert r.exclusions["by_rule"].get("OPS-GITIGNORE", 0) >= 2


def test_no_gitignore_flag(tmp_path):
    root = _tree(tmp_path)
    r = api.pack(root, share="public", dry_run=True, respect_gitignore=False)
    assert "logs/run.log" in _paths(r) and "secret_notes.txt" in _paths(r)


def test_allow_overrides_gitignore(tmp_path):
    root = _tree(tmp_path)
    r = api.pack(root, share="public", dry_run=True, allow=["logs/run.log"])
    assert "logs/run.log" in _paths(r)
    assert any(o["overrode_rule"] == "OPS-GITIGNORE" for o in r.overrides)


def test_gitignore_is_auditable(tmp_path):
    root = _tree(tmp_path)
    on = api.pack(root, dry_run=True).manifest["policy_sha256"]
    off = api.pack(root, dry_run=True, respect_gitignore=False).manifest["policy_sha256"]
    assert on != off
