<div align="center">

# Agentic Executor

### The execution layer for AI agents that need real hands

[![Version](https://img.shields.io/badge/version-1.0.2-blue.svg?style=flat-square)](https://github.com/Logeion/agentic-executor)
[![Python](https://img.shields.io/badge/python-3.10+-yellow.svg?style=flat-square)]()
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg?style=flat-square)]()
[![No deps](https://img.shields.io/badge/dependencies-zero-brightgreen.svg?style=flat-square)]()

</div>

---

AI agents are powerful thinkers but poor actors. They call one tool, wait for a result, call another tool, wait again. Every step is a round-trip.

**Agentic Executor** gives the agent a Python interpreter and a set of high-performance commands. Instead of ten tool calls, it writes one script. Loops, conditionals, error handling — all in a single thought.

```python
# One thought. Ten files. Zero round-trips.
python -m agentic_executor.cli --thought-stdin <<'EOF'
files = execute('search', {'pattern': '*.py'})
for f in files['data']['files']:
    result = execute('read', {'path': f, 'lines': 5})
    if result['success']:
        print(f"=== {f} ===")
        print('\n'.join(result['data']['lines']))
EOF
```

---

## Install

```bash
pip install agentic-executor
```

No dependencies. Works immediately with Python's built-in `ast` for Python files.  
For full multi-language support (20+ languages via tree-sitter):

```bash
pip install "agentic-executor[languages]"
```

---

## Activate the /exec skill

After installing, deploy the `/exec` skill to your AI agent of choice:

```bash
exec-install                       # Claude Code  (default)
exec-install --agent cursor        # Cursor
exec-install --agent windsurf      # Windsurf
exec-install --agent kiro          # Kiro
exec-install --agent codex         # Codex
exec-install --agent copilot       # GitHub Copilot
exec-install --agent opencode      # OpenCode
exec-install --agent aider         # Aider
exec-install --agent claw          # OpenClaw
exec-install --agent hermes        # Hermes
exec-install --agent trae          # Trae
exec-install --agent droid         # Factory Droid
exec-install --agent all           # All at once
```

Check status at any time:

```bash
exec-install --list
```

---

## How it works

Everything goes through one function: `execute(command, args)`.

The agent writes Python code that calls `execute()`. That code runs locally, with full Python logic — loops, conditions, error handling, chaining results between steps.

```python
# Standard return format — every command
{
    "success": bool,
    "data":    Any,       # command result
    "error":   str|None   # message if failed
}
```

Always check `result['success']` before reading `result['data']`.

---

## Commands

### Filesystem

```python
execute('read',    {'path': 'file.txt'})                                   # first 200 lines (default)
execute('read',    {'path': 'file.txt', 'full': True})                    # full file, no limit
execute('read',    {'path': 'file.txt', 'lines': 20})                     # first N lines
execute('read',    {'path': 'file.txt', 'start': 10, 'end': 30})          # range
execute('write',   {'path': 'out.txt', 'content': 'hello'})
execute('write',   {'path': 'log.txt', 'content': 'x\n', 'mode': 'a'})  # append
execute('replace', {'path': 'f.py', 'line': 42, 'new': '    # fixed'})   # line mode
execute('replace', {'path': 'f.py', 'old': 'foo()', 'new': 'bar()'})     # text mode
execute('copy',    {'src': 'a.txt', 'dst': 'b.txt'})
execute('move',    {'src': 'old.txt', 'dst': 'new.txt'})
execute('delete',  {'path': 'file.txt'})
execute('mkdir',   {'path': 'new/dir'})
execute('ls',      {'path': '.'})
```

### Search

```python
execute('search', {'pattern': '*.py', 'path': '.', 'recursive': True})
# → {"files": ["src/main.py", ...]}

execute('grep', {'pattern': 'TODO:', 'file_pattern': '*.py', 'path': '.'})
# → {"matches": [{"file": str, "line": int, "text": str}, ...]}

execute('info', {'path': 'file.txt'})
# → {"exists": bool, "type": "file"|"dir", "size": int, "modified": float}
```

### Codebase intelligence

```python
# Scan — supports Python, JS, TS, Go, Rust, Java, C, C++, Ruby, C#, Kotlin, Scala, PHP, Swift, Lua...
execute('scan_codebase', {'path': '.'})
# Writes cache to .agentic_executor/metadata.json

execute('get_metadata', {'type': 'summary'})
# → total files, functions, classes, imports

execute('get_metadata', {'type': 'structure'})
# → per-file: functions (name, line), classes, imports

execute('get_metadata', {'type': 'imports'})
# → import graph: who imports whom (bidirectional)

execute('get_metadata', {'type': 'all', 'filter': {'file': 'src/main.py'}})
# → single-file detail
```

### Process

```python
execute('run', {'cmd': 'pytest tests/', 'timeout': 60})
# → {"stdout": str, "stderr": str, "returncode": int}
```

---

## Usage patterns

### Batch operations

```python
python -m agentic_executor.cli --thought-stdin <<'EOF'
files = execute('search', {'pattern': 'test_*.py'})

for f in files['data']['files']:
    result = execute('read', {'path': f, 'lines': 3})
    if result['success']:
        print(f"--- {f} ---")
        for line in result['data']['lines']:
            print(line)
EOF
```

### Metadata-driven analysis

```python
python -m agentic_executor.cli --thought-stdin <<'EOF'
execute('scan_codebase', {'path': '.'})
meta = execute('get_metadata', {'type': 'structure'})

# Find the most complex files
by_size = sorted(
    ((path, len(data['functions'])) for path, data in meta['data']['files'].items()),
    key=lambda x: x[1], reverse=True
)
for path, count in by_size[:5]:
    print(f"{count:3}  functions  {path}")
EOF
```

### Conditional logic + cache

```python
python -m agentic_executor.cli --thought-stdin <<'EOF'
info = execute('info', {'path': '.agentic_executor/metadata.json'})

if not info['data']['exists']:
    execute('scan_codebase', {'path': '.'})

meta = execute('get_metadata', {'type': 'summary'})
s = meta['data']['summary']
print(f"Files: {s['total_files']}  Functions: {s['total_functions']}  Classes: {s['total_classes']}")
EOF
```

### Orchestrate external tools

```python
python -m agentic_executor.cli --thought-stdin <<'EOF'
# Run any CLI tool and process its output with Python
result = execute('run', {'cmd': 'git log --oneline -10'})
if result['success']:
    commits = result['data']['stdout'].strip().split('\n')
    print(f"Last {len(commits)} commits:")
    for c in commits:
        print(f"  {c}")
EOF
```

### Error handling

```python
result = execute('read', {'path': 'file.txt'})

if result['success']:
    print(result['data']['content'])
else:
    print(f"Error: {result['error']}")
    # fallback logic
```

---

## Multi-language support

Without tree-sitter (default): Python files via `ast`, other languages via regex patterns.  
With `pip install "agentic-executor[languages]"`: accurate parsing for 20+ languages.

| Language | Extension | Parser |
|----------|-----------|--------|
| Python | `.py` | tree-sitter / ast |
| JavaScript | `.js .jsx .mjs` | tree-sitter / regex |
| TypeScript | `.ts .tsx` | tree-sitter / regex |
| Go | `.go` | tree-sitter / regex |
| Rust | `.rs` | tree-sitter / regex |
| Java | `.java` | tree-sitter / regex |
| C / C++ | `.c .h .cpp .hpp` | tree-sitter / regex |
| Ruby | `.rb` | tree-sitter / regex |
| C# | `.cs` | tree-sitter / regex |
| Kotlin | `.kt` | tree-sitter / regex |
| Scala | `.scala` | tree-sitter / regex |
| PHP | `.php` | tree-sitter / regex |
| Swift | `.swift` | tree-sitter / regex |
| Lua | `.lua` | tree-sitter / regex |
| Elixir, Bash, R, Dart | ... | regex |

To install tree-sitter parsers separately:

```bash
exec-install --languages        # 9 essential languages
exec-install --full             # all 16
```

---

## CLI reference

```bash
# Execute a thought inline
python -m agentic_executor.cli --thought "result = execute('ls', {'path': '.'}); print(result['data'])"

# Execute from stdin (recommended for multi-line code)
python -m agentic_executor.cli --thought-stdin <<'EOF'
# your Python code
EOF

# JSON output (for subprocess use)
python -m agentic_executor.cli --thought "..." --json-output

# Show available commands
python -m agentic_executor.cli --help-commands
```

Use `--thought-stdin` with heredoc for any script longer than one line or containing quotes. It avoids all shell escaping issues.

---

## Tips

**Raw strings for file content with escape sequences:**

```python
# Wrong — double escaping needed
content = 'def f():\n    print("hello")'

# Right — raw string, no escaping
content = r'''
def f():
    print("hello")
'''
execute('write', {'path': 'f.py', 'content': content})
```

**Reading large files:**

`read` always returns `result['data']['content']` (str) — even when the file
is truncated. Check `truncated` and use `next_start` to continue:

```python
result = execute('read', {'path': 'big.py'})    # up to 200 lines, always 'content'
data = result['data']

if data.get('truncated'):
    # fetch the rest — next_start points to the first unread line
    rest = execute('read', {'path': 'big.py',
                            'start': data['next_start'],
                            'end':   data['total_lines']})
    full = data['content'] + '\n'.join(rest['data']['lines'])

# Or skip the loop entirely:
result = execute('read', {'path': 'big.py', 'full': True})
```

**Scan before querying metadata:**

```python
execute('scan_codebase', {'path': '.'})   # always first
meta = execute('get_metadata', {'type': 'summary'})
```

**Cache location:** `.agentic_executor/metadata.json` — add to `.gitignore`.

---

## Project structure

```
agentic_executor/
├── __init__.py          public API
├── cli.py               --thought / --thought-stdin interface
├── install.py           exec-install command
├── skills/
│   └── exec/
│       └── skill.md     /exec skill for Claude Code and others
└── code_parts/
    ├── executor.py      core execute() function
    └── commands.py      14 commands + multi-language scanner

pyproject.toml           pip packaging
```

---

## When to use it

Use Agentic Executor when the task needs **more than two steps or a loop**.  
For single reads or writes, use your agent's native tools directly — they're simpler.

---

<div align="center">

*Part of the [Logeion](https://github.com/5005-69) projects*

</div>
