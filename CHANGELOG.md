# Changelog

All notable changes to this project are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.2] — 2026-04-16

### Fixed

**`read` command — consistent return contract**

`read` used to return different keys depending on whether the file was
truncated or not:

- File ≤ 200 lines → `result['data']['content']` (str) ✓
- File > 200 lines → `result['data']['lines']` (list) ✗

Any agent that read `result['data']['content']` on a large file received a
`KeyError` instead of the content. The fix: `read` now always returns
`content` (str) for whole-file reads, truncated or not.

When truncation occurs, three extra fields are included alongside `content`:
- `truncated: True` — signals the file was cut
- `total_lines: int` — full line count of the file
- `next_start: int` — first unread line (1-indexed), ready for a
  `start`/`end` continuation call

A warning is also printed to stderr so truncation cannot be silently missed.

**`read` command — `full: True` parameter**

A new `full: True` parameter bypasses the 200-line limit entirely and
returns the complete file in one call. Equivalent to `limit: 0` but
expresses intent more clearly.

```python
execute('read', {'path': 'large_file.py', 'full': True})
```

**CWD included in all path-not-found errors**

Every command that can fail with a missing path now appends
`(CWD: /current/directory)` to the error string. Affected commands:
`read`, `copy`, `move`, `delete`, `ls`, `replace`, `search`, `grep`,
`scan_codebase`, `get_metadata`.

Agents running from an unexpected working directory previously received a
bare `"File not found: foo.txt"` with no hint of where the tool was
searching. The CWD annotation surfaces the root cause immediately.

**`--thought-stdin` — removed silent line-merging**

The stdin reader contained a post-processing step that silently merged
lines when:
- the current line ended with `:")` or `':`
- the previous line contained `print("`

This corrupted scripts that matched those patterns and broke scripts
containing triple-quoted strings (`r'''...'''`). The fix is a one-liner:
stdin is now forwarded to `execute_thought()` byte-for-byte.

### Tests added

- `tests/test_read_command.py` — 21 tests covering the `read` contract,
  truncation metadata, `full: True`, continuation via `next_start`,
  backward compatibility, and stderr warnings
- `tests/test_cwd_errors.py` — 10 tests verifying CWD inclusion across
  all commands
- `tests/test_stdin_passthrough.py` — 8 end-to-end CLI tests confirming
  stdin reaches `execute_thought()` intact

---

## [1.0.1] — 2026-04-14

### Fixed

- `exec-install` now deploys the `/exec` skill to `~/.claude/commands/exec.md`
  (the correct Claude Code slash-command location) instead of the old path

---

## [1.0.0] — 2026-04-13

### Added

- Initial release
- `execute()` API with 14 commands: `read`, `write`, `replace`, `copy`,
  `move`, `delete`, `mkdir`, `ls`, `search`, `grep`, `info`, `run`,
  `scan_codebase`, `get_metadata`
- Multi-language codebase scanner: 20+ languages via tree-sitter with
  Python `ast` and regex fallbacks
- `--thought` and `--thought-stdin` CLI interface
- `--json-output` mode for subprocess integration
- `/exec` skill for Claude Code, Cursor, Windsurf, Kiro, Codex, Copilot,
  OpenCode, Aider, OpenClaw, Hermes, Trae, Factory Droid
- `exec-install` / `exec-install --agent <name>` deployment command
- Zero hard dependencies — works out of the box
