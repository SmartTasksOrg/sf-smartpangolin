"""Merged text parts: hard size limits, a limit on the number of parts, and --format txt / both."""
import json
import re
import zipfile

import pytest

from sf_smartpangolin import ShardLimitError, pack, verify_zip
from sf_smartpangolin.cli import main as cli_main

HF = "hf_" + "A" * 34               # format-valid, fake


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "proj"
    (root / "src").mkdir(parents=True)
    (root / ".env").write_text(f"HF_TOKEN={HF}\n", encoding="utf-8")
    (root / "src" / "big.py").write_text("".join(f"value_{i} = {i}\n" for i in range(3000)), encoding="utf-8")
    (root / "src" / "small.py").write_text('print("hello")\n', encoding="utf-8")
    (root / "src" / "accents.py").write_text("".join(f"# naïve café {i} — ü\n" for i in range(400)),
                                             encoding="utf-8")
    (root / "README.md").write_text("# proj\n", encoding="utf-8")
    return root


def _parts_from_zip(zip_path):
    with zipfile.ZipFile(zip_path) as zf:
        return {n: zf.read(n).decode("utf-8") for n in sorted(zf.namelist()) if n.startswith("_MERGED/")}


def _lines_by_file(parts):
    """path -> the numbered source lines, in order, collected from every part."""
    out, path = {}, None
    for text in parts:
        for line in text.splitlines():
            m = re.match(r"^### (\S+)( \(lines \d+-\d+ of \d+\))?$", line)
            if m:
                path = m.group(1)
                continue
            m = re.match(r"^\s*(\d+) \| ", line)
            if m and path:
                out.setdefault(path, []).append(int(m.group(1)))
    return out


def test_max_chars_is_never_exceeded_and_nothing_is_lost(project):
    r = pack(project, no_git_list=True, merged_only=True, max_chars=20000)
    parts = _parts_from_zip(r.zip_path)
    assert len(parts) > 3
    assert all(len(t) <= 20000 for t in parts.values())
    lines = _lines_by_file(parts.values())
    assert lines["src/big.py"] == list(range(1, 3001))          # split across parts, every line once, in order
    assert lines["src/accents.py"] == list(range(1, 401))
    assert any("### src/big.py (lines 1-" in t for t in parts.values())
    assert verify_zip(r.zip_path) == 0


def test_every_part_says_which_part_it_is(project):
    r = pack(project, no_git_list=True, merged_only=True, max_chars=20000)
    parts = list(_parts_from_zip(r.zip_path).values())
    for n, text in enumerate(parts, 1):
        assert text.startswith(f"=== part {n} of {len(parts)}: ")


def test_max_bytes_counts_utf8_bytes(project):
    r = pack(project, no_git_list=True, merged_only=True, max_bytes=8000)
    parts = _parts_from_zip(r.zip_path)
    assert all(len(t.encode("utf-8")) <= 8000 for t in parts.values())
    assert _lines_by_file(parts.values())["src/accents.py"] == list(range(1, 401))


def test_max_files_fails_before_writing_and_names_a_limit_that_fits(project):
    arch = project.parent / "extracted_source" / "share_archive"
    with pytest.raises(ShardLimitError) as e:
        pack(project, no_git_list=True, merged_only=True, max_chars=20000, max_files=2)
    assert "Nothing was written" in str(e.value)
    assert not list(arch.glob("*.zip")) if arch.exists() else True
    suggested = int(re.search(r"--max-chars ([\d,]+) fits", str(e.value)).group(1).replace(",", ""))
    r = pack(project, no_git_list=True, merged_only=True, max_chars=suggested, max_files=2)
    parts = _parts_from_zip(r.zip_path)
    assert len(parts) <= 2 and all(len(t) <= suggested for t in parts.values())
    with pytest.raises(ShardLimitError):                       # the suggestion is the smallest that fits
        pack(project, no_git_list=True, merged_only=True, max_chars=suggested - 1, max_files=2, dry_run=True)


def test_a_line_longer_than_a_part_is_refused(project):
    (project / "src" / "long.py").write_text("x = '" + "y" * 5000 + "'\n", encoding="utf-8")
    with pytest.raises(ShardLimitError, match="line 1"):
        pack(project, no_git_list=True, max_chars=2000, dry_run=True)


def test_format_txt_writes_parts_and_checks_but_no_zip(project):
    r = pack(project, no_git_list=True, fmt="txt", max_chars=20000)
    assert r.zip_path is None and r.txt_dir is not None and r.txt_dir.is_dir()
    names = sorted(p.name for p in r.txt_dir.iterdir())
    assert {"SHA256SUMS", "MANIFEST.json", "SHARE_REPORT.md"} <= set(names)
    parts = [p for p in names if p.endswith(".txt")]
    assert len(parts) == r.manifest["merged"]["shard_count"] > 1
    assert not list(r.txt_dir.parent.glob("*.zip"))
    everything = "".join(p.read_text(encoding="utf-8") for p in r.txt_dir.iterdir())
    assert HF not in everything and "### .env\n" not in everything     # the secret is in no part
    assert json.loads((r.txt_dir / "MANIFEST.json").read_text(encoding="utf-8"))["format"] == "txt"
    assert verify_zip(r.txt_dir) == 0


def test_verify_txt_folder_catches_changes(project):
    r = pack(project, no_git_list=True, fmt="txt", max_chars=20000)
    first = sorted(r.txt_dir.glob("*.txt"))[0]
    first.write_text(first.read_text(encoding="utf-8") + "extra\n", encoding="utf-8")
    assert verify_zip(r.txt_dir) == 2
    r2 = pack(project, no_git_list=True, fmt="txt", max_chars=20000, zip_name="second.zip")
    (r2.txt_dir / "source_code_part99.txt").write_text("not ours\n", encoding="utf-8")
    assert verify_zip(r2.txt_dir) == 2


def test_format_both_keeps_zip_and_txt(project):
    r = pack(project, no_git_list=True, fmt="both", max_chars=20000)
    assert r.zip_path is not None and r.zip_path.exists()
    staged = sorted((project.parent / "extracted_source").glob("source_code_part*.txt"))
    assert len(staged) == r.manifest["merged"]["shard_count"]


def test_format_txt_needs_merged_parts(project):
    with pytest.raises(ShardLimitError, match="no-merge"):
        pack(project, no_git_list=True, fmt="txt", merge=False)


def test_pangolin_json_sets_format_and_limits(project):
    (project / ".pangolin.json").write_text(json.dumps({"format": "txt", "max_files": 50, "max_bytes": 30000}),
                                            encoding="utf-8")
    r = pack(project, no_git_list=True)
    assert r.txt_dir is not None
    assert r.manifest["merged"]["max_bytes"] == 30000 and r.manifest["merged"]["max_files"] == 50


def test_cli_txt_and_limit_error(project, capsys):
    assert cli_main(["pack", "--root", str(project), "--format", "txt", "--max-chars", "20000",
                     "--no-git-list", "--venv", "none"]) == 0
    assert "txt folder" in capsys.readouterr().out
    assert cli_main(["pack", "--root", str(project), "--max-chars", "20000", "--max-files", "1",
                     "--zip-name", "x.zip", "--no-git-list", "--venv", "none"]) == 2
    assert "--max-files 1" in capsys.readouterr().err


def test_default_zip_is_unchanged_for_small_projects(tmp_path):
    root = tmp_path / "p"
    root.mkdir()
    (root / "a.py").write_text("a = 1\n", encoding="utf-8")
    r = pack(root, no_git_list=True)
    parts = _parts_from_zip(r.zip_path)
    assert len(parts) == 1
    assert "### a.py\n```python\n   1 | a = 1\n```" in list(parts.values())[0]
    assert "a.py" in {f["path"] for f in r.manifest["files"]}
