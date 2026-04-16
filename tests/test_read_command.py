"""
Tests for read_file — truncation contract and new features.

Verifies:
- Whole-file reads always return 'content' (str), even when truncated
- Truncated results include truncated, total_lines, next_start, truncation_notice
- 'full: True' bypasses the line limit entirely, no truncation metadata
- next_start allows complete continuation via start/end
- 'lines' and 'start'+'end' params still return 'lines' (list) — backward compat
- Truncation emits a warning to stderr; small files do not
- File-not-found error includes the current working directory
"""

import os
import tempfile

import pytest

from agentic_executor.code_parts.commands import read_file, _READ_DEFAULT_LIMIT


# ── helpers ────────────────────────────────────────────────────────────────

def _tmp_file(content: str) -> str:
    """Write content to a temp file and return its absolute path."""
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    )
    f.write(content)
    f.close()
    return f.name


def _numbered_lines(n: int) -> str:
    """Return a string with n numbered lines, each ending with a newline."""
    return "\n".join(f"line {i}" for i in range(1, n + 1)) + "\n"


# ── 'content' key — always present for whole-file reads ───────────────────

def test_small_file_returns_content_key():
    """Files under the limit must return 'content' (str)."""
    path = _tmp_file(_numbered_lines(10))
    result = read_file({"path": path})
    assert "content" in result
    assert isinstance(result["content"], str)
    assert "lines" not in result


def test_truncated_file_returns_content_key():
    """Files over the limit must STILL return 'content' (str), not 'lines' (list)."""
    path = _tmp_file(_numbered_lines(_READ_DEFAULT_LIMIT + 100))
    result = read_file({"path": path})
    assert "content" in result, (
        "read_file must return 'content' key even when file is truncated — "
        f"got keys: {list(result.keys())}"
    )
    assert isinstance(result["content"], str)
    assert "lines" not in result, (
        "read_file must NOT use the 'lines' key for whole-file reads; "
        "use 'content' consistently regardless of file size."
    )


def test_small_file_no_truncation_flag():
    """Files under the limit must not carry a 'truncated' flag."""
    path = _tmp_file(_numbered_lines(10))
    result = read_file({"path": path})
    assert not result.get("truncated")


# ── truncation metadata ────────────────────────────────────────────────────

def test_truncated_flag_is_true():
    path = _tmp_file(_numbered_lines(_READ_DEFAULT_LIMIT + 50))
    result = read_file({"path": path})
    assert result.get("truncated") is True


def test_truncated_total_lines_is_accurate():
    n = _READ_DEFAULT_LIMIT + 50
    path = _tmp_file(_numbered_lines(n))
    result = read_file({"path": path})
    assert result.get("total_lines") == n


def test_truncated_next_start_is_limit_plus_one():
    path = _tmp_file(_numbered_lines(_READ_DEFAULT_LIMIT + 50))
    result = read_file({"path": path})
    assert result.get("next_start") == _READ_DEFAULT_LIMIT + 1


def test_truncated_content_has_exactly_limit_lines():
    path = _tmp_file(_numbered_lines(_READ_DEFAULT_LIMIT + 50))
    result = read_file({"path": path})
    # content should contain exactly _READ_DEFAULT_LIMIT lines
    line_count = len(result["content"].rstrip("\n").split("\n"))
    assert line_count == _READ_DEFAULT_LIMIT


def test_truncated_has_truncation_notice():
    path = _tmp_file(_numbered_lines(_READ_DEFAULT_LIMIT + 50))
    result = read_file({"path": path})
    assert "truncation_notice" in result
    assert isinstance(result["truncation_notice"], str)
    assert result["truncation_notice"]


# ── full: True — bypass limit ──────────────────────────────────────────────

def test_full_true_returns_all_lines():
    """'full: True' must deliver every line of a large file."""
    n = _READ_DEFAULT_LIMIT + 300
    path = _tmp_file(_numbered_lines(n))
    result = read_file({"path": path, "full": True})
    assert "content" in result
    line_count = len(result["content"].rstrip("\n").split("\n"))
    assert line_count == n


def test_full_true_no_truncated_flag():
    path = _tmp_file(_numbered_lines(_READ_DEFAULT_LIMIT + 300))
    result = read_file({"path": path, "full": True})
    assert not result.get("truncated")


def test_full_true_no_next_start():
    """'full: True' must not include 'next_start' — nothing was cut."""
    path = _tmp_file(_numbered_lines(_READ_DEFAULT_LIMIT + 300))
    result = read_file({"path": path, "full": True})
    assert "next_start" not in result


def test_full_true_no_truncation_notice():
    path = _tmp_file(_numbered_lines(_READ_DEFAULT_LIMIT + 300))
    result = read_file({"path": path, "full": True})
    assert "truncation_notice" not in result


# ── next_start enables complete file reconstruction ────────────────────────

def test_next_start_continuation_yields_full_file():
    """
    First chunk + continuation via start/end must reconstruct the complete file.
    This is the core contract: agents can always get all content via two calls.
    """
    n = _READ_DEFAULT_LIMIT + 80
    path = _tmp_file(_numbered_lines(n))

    first = read_file({"path": path})
    assert first.get("truncated"), "Expected truncation for large file"

    next_start = first["next_start"]
    total = first["total_lines"]

    second = read_file({"path": path, "start": next_start, "end": total})
    assert "lines" in second

    first_lines = first["content"].rstrip("\n").split("\n")
    all_lines = first_lines + second["lines"]
    assert len(all_lines) == n


def test_next_start_first_line_is_correct():
    """The first line of the continuation must immediately follow the truncated content."""
    n = _READ_DEFAULT_LIMIT + 10
    path = _tmp_file(_numbered_lines(n))

    first = read_file({"path": path})
    next_start = first["next_start"]

    second = read_file({"path": path, "start": next_start, "end": next_start})
    expected = f"line {next_start}"
    assert second["lines"][0] == expected


# ── backward compatibility: 'lines' and 'start'/'end' params ──────────────

def test_lines_param_returns_lines_key():
    """'lines=N' must still return 'lines' (list[str]) — no change to existing API."""
    path = _tmp_file(_numbered_lines(50))
    result = read_file({"path": path, "lines": 10})
    assert "lines" in result
    assert isinstance(result["lines"], list)
    assert len(result["lines"]) == 10
    assert "content" not in result


def test_start_end_param_returns_lines_key():
    """'start'/'end' must still return 'lines' (list[str])."""
    path = _tmp_file(_numbered_lines(50))
    result = read_file({"path": path, "start": 5, "end": 15})
    assert "lines" in result
    assert isinstance(result["lines"], list)
    assert len(result["lines"]) == 11  # inclusive range
    assert "content" not in result


# ── stderr warning ─────────────────────────────────────────────────────────

def test_truncation_emits_stderr_warning(capsys):
    """Truncation must print a visible warning to stderr so agents cannot miss it."""
    path = _tmp_file(_numbered_lines(_READ_DEFAULT_LIMIT + 50))
    read_file({"path": path})
    captured = capsys.readouterr()
    assert captured.err, "Expected a truncation warning on stderr — got nothing"
    assert "truncat" in captured.err.lower()


def test_small_file_no_stderr_output(capsys):
    """Small files must not produce any stderr noise."""
    path = _tmp_file(_numbered_lines(10))
    read_file({"path": path})
    captured = capsys.readouterr()
    assert captured.err == ""


def test_full_true_no_stderr_output(capsys):
    """'full: True' reads must not produce a truncation warning."""
    path = _tmp_file(_numbered_lines(_READ_DEFAULT_LIMIT + 300))
    read_file({"path": path, "full": True})
    captured = capsys.readouterr()
    assert captured.err == ""


# ── file-not-found includes CWD ───────────────────────────────────────────

def test_file_not_found_error_includes_cwd():
    """
    File-not-found errors must include the current working directory so agents
    can diagnose path issues without a separate debug round.
    """
    result = read_file({"path": "this_file_does_not_exist_xyz.txt"})
    assert "error" in result
    cwd = os.getcwd()
    assert cwd in result["error"], (
        f"Error should contain CWD '{cwd}' to help debug relative-path issues. "
        f"Got: {result['error']}"
    )


def test_file_not_found_error_includes_path():
    """Error message must also echo back the path that was not found."""
    result = read_file({"path": "missing_abc.txt"})
    assert "missing_abc.txt" in result["error"]
