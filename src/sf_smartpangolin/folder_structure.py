"""
sf_smartpangolin.folder_structure — structural pre-pass (importable).

Walks a project tree,
applies a coarse structural exclusion pass (build dirs, backups, binary
extensions), and writes:

  - an indented tree file (human view)
  - a flat path-list file (machine view, consumed by the packager)

This is deliberately *coarse*. It is NOT the secret scanner — that is the
packager's job (:mod:`sf_smartpangolin.engine`). Stage 1 exists so large trees can be
enumerated once and reused, and so the path list can be hand-edited.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

CONFIG_FILE = "patches_config.json"

DEFAULT_EXCLUDED_FOLDERS = {
    "venv", ".venv", "__pycache__", "node_modules", ".git", "ffmpeg",
    "time_mgmt_venv", "model_cache", "search_results", "data", "cache_folder",
    "wheels_builder", "UI-frameworks", "WorkSpace", "rdb_data",
    "rdb_data_meta_kv", "etcd", "member", ".next", "dist", "build", "out",
    "lib", "bin", "include", "share", "test", "tests", ".pytest_cache",
    ".tox", ".mypy_cache", ".coverage", ".idea", ".vscode", ".DS_Store",
    "test_results", ".secret", ".secrets",
}
DEFAULT_EXCLUDED_EXTENSIONS = {
    ".pyc", ".pyo", ".log", ".bkp", ".tmp", ".pt", ".pth",
    ".zip", ".tar", ".gz", ".rar", ".7z", ".data", ".csv", ".xlsx",
    ".xls", ".db", ".sqlite", ".backup", ".egg-info", ".egg",
    ".whl", ".tar.gz", ".tgz", ".zip.001", ".zip.002", ".zip.003",
    ".onnx_data",
}
DEFAULT_EXCLUDED_FILENAMES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
}
ALWAYS_INCLUDE_ROOT_FILENAMES = {
    "dockerfile", "gemfile", "gemfile.lock", "requirements.txt", "setup.py", "pyproject.toml",
    "package.json", "next.config.js", "next.config.cjs", "vue.config.js", "angular.json",
    "svelte.config.js", "vite.config.js", "vite.config.ts", "tailwind.config.js",
    "postcss.config.js", ".dockerignore", "readme.md", "license", "contributing.md",
    "makefile", "procfile", "docker-compose.yml", "docker-compose.yaml", "vagrantfile",
    ".env.example", "favicon.ico", "robots.txt", "sitemap.xml", "manifest.json",
    "vercel.json", "netlify.toml", ".eslintrc.js", ".eslintrc.cjs", "eslint.config.js",
    ".prettierrc", ".prettierrc.json",
}


def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "replace").decode("ascii"))


def load_config(config_file: str = CONFIG_FILE):
    folders = set(DEFAULT_EXCLUDED_FOLDERS)
    exts = set(DEFAULT_EXCLUDED_EXTENSIONS)
    names = set(DEFAULT_EXCLUDED_FILENAMES)
    if os.path.exists(config_file):
        try:
            cfg = json.loads(Path(config_file).read_text(encoding="utf-8"))
            folders.update(cfg.get("exclude_dirs", []))
            exts.update(cfg.get("exclude_exts", []))
            names.update(cfg.get("exclude_filenames", []))
        except json.JSONDecodeError:
            safe_print(f"WARNING: could not parse {config_file}, using defaults.")
    return folders, exts, names


def is_backup_folder(name: str) -> bool:
    low = name.lower()
    return any(ind in low for ind in
              ("-bak", "-backup", ".bak", ".backup", "_bak", "_backup", "~"))


def is_archive_folder(name: str) -> bool:
    return bool(re.search(r"\b(archive|archived|old|deprecated|legacy)\b", name, re.IGNORECASE))


def is_excluded_folder(folder_path: str, excluded_folders) -> bool:
    name = os.path.basename(folder_path).lower()
    if name in excluded_folders:
        return True
    return is_backup_folder(name) or is_archive_folder(name)


def is_excluded_file(filename, current_dir, scan_root, excluded_exts, excluded_names):
    low = filename.lower()
    if os.path.abspath(current_dir) == os.path.abspath(scan_root):
        if low in ALWAYS_INCLUDE_ROOT_FILENAMES:
            return low in excluded_names
    if low in excluded_names:
        return True
    suffixes = [s.lower() for s in Path(low).suffixes]
    if ".bak" in suffixes:
        return True
    _name, ext = os.path.splitext(low)
    if ext and ext in excluded_exts:
        return True
    if low.startswith("~$") or low.endswith("~"):
        return True
    return False


def build_tree(root, tree_output="file_folder_tree.txt",
               path_output="file_folder_path.txt", focus=None,
               config_file: str = CONFIG_FILE, debug: bool = False):
    """Walk ``root`` (optionally a ``focus`` subfolder), writing a tree file and
    a flat path list. Returns the number of files written to the path list."""
    excluded_folders, excluded_exts, excluded_names = load_config(config_file)
    root_abs = os.path.abspath(root)
    scan_root = os.path.abspath(os.path.join(root_abs, focus)) if focus else root_abs
    if focus and not os.path.isdir(scan_root):
        safe_print(f"WARNING: focus '{focus}' not found under {root_abs}; walking root")
        scan_root = root_abs

    written = 0
    with open(tree_output, "w", encoding="utf-8") as tf, \
         open(path_output, "w", encoding="utf-8") as pf:
        disp = os.path.basename(scan_root)
        tf.write(f"{disp}/ (Scan Root)\n")
        pf.write("./\n")
        for cur, dirnames, filenames in os.walk(scan_root, topdown=True):
            dirnames[:] = sorted(
                d for d in dirnames
                if not is_excluded_folder(os.path.join(cur, d), excluded_folders))
            rel = os.path.relpath(cur, scan_root)
            rel_root = os.path.relpath(cur, root_abs)
            indent = rel.count(os.sep) + 1 if rel != "." else 1
            if cur != scan_root:
                tf.write(f"{'    ' * indent}{os.path.basename(cur)}/\n")
                pf.write(f"{rel_root}/\n")
            valid = [f for f in filenames
                     if not is_excluded_file(f, cur, scan_root, excluded_exts, excluded_names)]
            for f in sorted(valid):
                tf.write(f"{'    ' * (indent + 1)}{f}\n")
                pf.write(f"{os.path.join(cur, f)}\n")
                written += 1
    if debug:
        safe_print(f"[tree] {written} files -> {path_output}")
    return written
