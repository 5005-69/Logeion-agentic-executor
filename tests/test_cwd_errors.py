"""
Tests for CWD inclusion in file-not-found errors.

Every command that can fail with a "not found" path must include
the current working directory in the error message so agents can
diagnose relative-path issues without an extra debug round.

Commands covered:
  read_file, copy_file, move_file, delete_file,
  list_directory, replace_in_file, search_files,
  grep_files, scan_codebase, get_metadata
"""

import os

import pytest

from agentic_executor.code_parts.commands import (
    read_file,
    copy_file,
    move_file,
    delete_file,
    list_directory,
    replace_in_file,
    search_files,
    grep_files,
    scan_codebase,
    get_metadata,
)


# ── helper ─────────────────────────────────────────────────────────────────

def _assert_cwd_in_error(result: dict, label: str = ""):
    """Assert the result is an error that contains the current CWD."""
    assert "error" in result, f"{label}: expected an error result, got {result}"
    cwd = os.getcwd()
    assert cwd in result["error"], (
        f"{label}: error must contain CWD '{cwd}' to help debug path issues.\n"
        f"Got: {result['error']}"
    )


# ── read ───────────────────────────────────────────────────────────────────

def test_read_missing_file_includes_cwd():
    result = read_file({"path": "no_such_file_read.txt"})
    _assert_cwd_in_error(result, "read_file")


# ── copy ───────────────────────────────────────────────────────────────────

def test_copy_missing_src_includes_cwd():
    result = copy_file({"src": "no_such_src.txt", "dst": "dst.txt"})
    _assert_cwd_in_error(result, "copy_file")


# ── move ───────────────────────────────────────────────────────────────────

def test_move_missing_src_includes_cwd():
    result = move_file({"src": "no_such_src.txt", "dst": "dst.txt"})
    _assert_cwd_in_error(result, "move_file")


# ── delete ─────────────────────────────────────────────────────────────────

def test_delete_missing_path_includes_cwd():
    result = delete_file({"path": "no_such_file_delete.txt"})
    _assert_cwd_in_error(result, "delete_file")


# ── list_directory ─────────────────────────────────────────────────────────

def test_ls_missing_dir_includes_cwd():
    result = list_directory({"path": "no_such_dir_xyz"})
    _assert_cwd_in_error(result, "list_directory")


# ── replace_in_file ────────────────────────────────────────────────────────

def test_replace_missing_file_includes_cwd():
    result = replace_in_file({"path": "no_such_file_replace.txt", "old": "x", "new": "y"})
    _assert_cwd_in_error(result, "replace_in_file")


# ── search_files ───────────────────────────────────────────────────────────

def test_search_missing_dir_includes_cwd():
    result = search_files({"path": "no_such_dir_search", "pattern": "*.py"})
    _assert_cwd_in_error(result, "search_files")


# ── grep_files ─────────────────────────────────────────────────────────────

def test_grep_missing_dir_includes_cwd():
    result = grep_files({"pattern": "TODO", "path": "no_such_dir_grep"})
    _assert_cwd_in_error(result, "grep_files")


# ── scan_codebase ──────────────────────────────────────────────────────────

def test_scan_missing_dir_includes_cwd():
    result = scan_codebase({"path": "no_such_dir_scan"})
    _assert_cwd_in_error(result, "scan_codebase")


# ── get_metadata ───────────────────────────────────────────────────────────

def test_get_metadata_missing_cache_includes_cwd():
    result = get_metadata({"cache": "no_such_cache_xyz/metadata.json"})
    _assert_cwd_in_error(result, "get_metadata")
