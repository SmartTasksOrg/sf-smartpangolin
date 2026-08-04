"""Red-team regressions: secret-smuggling evasions the scanner must catch."""
from smartpangolin import api

KEY = "AKIAIOSFODNN7EXAMPLE"  # matches SEC-CONT-AWSKEY


def _shipped(root):
    r = api.pack(root, share="public", dry_run=True)
    return {f["path"] for f in r.manifest["files"]}


def test_secret_in_binary_safe_asset_is_caught(tmp_path):
    (tmp_path / "logo.png").write_bytes(b"\x89PNG\r\n\x00tEXt " + KEY.encode() + b"\x00")
    (tmp_path / "font.woff").write_bytes(b"wOFF\x00\x00" + KEY.encode())
    assert "logo.png" not in _shipped(tmp_path)
    assert "font.woff" not in _shipped(tmp_path)


def test_true_binary_nonsafe_ext_is_failclosed(tmp_path):
    (tmp_path / "blob.bin").write_bytes(b"\x00\x01" + KEY.encode() + b"\x00")
    assert "blob.bin" not in _shipped(tmp_path)          # OPS-BINARY, excluded


def test_zero_width_split_is_caught(tmp_path):
    (tmp_path / "k.txt").write_text("AKIA\u200bIOSFODNN7EXAMPLE\n")   # ZWSP inside key
    assert "k.txt" not in _shipped(tmp_path)


def test_plain_secret_is_caught(tmp_path):
    (tmp_path / "c.txt").write_text(KEY + "\n")
    assert "c.txt" not in _shipped(tmp_path)
