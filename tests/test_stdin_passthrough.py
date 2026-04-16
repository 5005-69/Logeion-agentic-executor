"""
Tests for --thought-stdin passthrough — stdin must reach execute() unchanged.

The old code had a 'fix_lines' post-processing step that silently merged
lines based on specific endings (':")' or "':") when the previous line
contained 'print("'. This could corrupt legitimate Python scripts.

These tests run the real CLI via subprocess with --thought-stdin so the
full stdin→execute() pipeline is exercised end-to-end.
"""

import subprocess
import sys
import textwrap

import pytest


# ── helper ─────────────────────────────────────────────────────────────────

def _run_stdin(code: str) -> subprocess.CompletedProcess:
    """Run agentic_executor CLI with code fed via stdin (--thought-stdin)."""
    return subprocess.run(
        [sys.executable, "-m", "agentic_executor.cli", "--thought-stdin"],
        input=textwrap.dedent(code),
        capture_output=True,
        text=True,
    )


# ── lines ending in :") or ': must not be merged ──────────────────────────

def test_line_ending_colon_paren_not_merged():
    """
    A line ending with :") must reach execute() unchanged.
    The old fix_lines would merge it with a preceding print("...") line.
    """
    result = _run_stdin("""\
        a = 'hello:")'
        print(a)
    """)
    assert 'hello:")' in result.stdout


def test_print_followed_by_colon_line_not_merged():
    """
    The exact pattern the old fix_lines targeted:
    a print("...") line followed by a line ending in :").
    Both lines must execute as written — no merging, no corruption.
    """
    result = _run_stdin("""\
        print("label:")
        x = 'value:")'
        print(x)
    """)
    assert "label:" in result.stdout
    assert 'value:")' in result.stdout


def test_line_ending_quote_colon_not_merged():
    """A line ending with ': must reach execute() unchanged."""
    result = _run_stdin("""\
        b = "key':"
        print(b)
    """)
    assert "key':" in result.stdout


# ── triple-quoted strings pass through intact ──────────────────────────────

def test_double_triple_quotes_unchanged():
    """Triple double-quoted strings must not be touched."""
    result = _run_stdin("""\
        x = \"\"\"hello
        world\"\"\"
        print(len(x.strip()))
    """)
    assert result.returncode == 0, result.stderr


def test_single_triple_quotes_passthrough():
    """
    Triple single-quoted strings must not cause a syntax error.
    This was the scenario mentioned in feedback.md where agents were
    forced to abandon --thought-stdin entirely.
    """
    result = _run_stdin("""\
        x = '''line one
        line two'''
        print(x.count('\\n'))
    """)
    assert result.returncode == 0, f"Unexpected error:\\n{result.stderr}"
    assert "1" in result.stdout


# ── comment and blank lines preserved ─────────────────────────────────────

def test_comment_lines_preserved():
    result = _run_stdin("""\
        # this is a comment
        print("ok")
    """)
    assert "ok" in result.stdout


def test_blank_lines_preserved():
    """Blank lines between statements must not be dropped."""
    result = _run_stdin("""\
        x = 1


        print(x)
    """)
    assert "1" in result.stdout


# ── execute() calls with dict args are unaffected ─────────────────────────

def test_execute_read_with_real_file():
    """
    A realistic agent script using execute('read', ...) must work correctly
    end-to-end through --thought-stdin.
    """
    result = _run_stdin("""\
        import tempfile, os
        f = tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False, encoding='utf-8'
        )
        f.write('hello world')
        f.close()
        r = execute('read', {'path': f.name})
        print(r['success'])
        print(r['data']['content'].strip())
        os.unlink(f.name)
    """)
    assert result.returncode == 0, result.stderr
    assert "True" in result.stdout
    assert "hello world" in result.stdout
