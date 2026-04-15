# 🧠 Agentic Executor - Tool Reference for Claude Code

## Purpose

High-performance execution layer for filesystem operations, codebase analysis, and process management. Optimized for AI agents requiring batch operations, complex workflows, and metadata-driven reasoning.

**Key Innovation:** Python-first interface with intelligent helpers. Write full Python logic with access to optimized `execute()` commands.

---

## When to Use

### ✅ Use Agentic Executor When:
- **Batch operations**: Reading/modifying multiple files in loops
- **Codebase intelligence**: AST-based analysis (functions, classes, imports)
- **Complex workflows**: Multi-step operations with conditionals/loops
- **Pattern-based operations**: Search + process workflows
- **Metadata queries**: "Find all files with >20 functions"

### ❌ Use Native Tools When:
- **Single file read**: Use `Read` tool directly (simpler)
- **Single file write**: Use `Write` tool directly (simpler)
- **Simple edits**: Use `Edit` tool for targeted changes
- **Git operations**: Use `Bash` tool for git commands

**Rule of Thumb:** If operation requires >2 steps or iteration, use Agentic Executor.

---

## Interface: `--thought` Mode

Execute Python code with access to `execute()` function:

```bash
python -m agentic_executor.cli --thought "
result = execute('command_name', {'arg': 'value'})
print(result['data'])
"
```

**Return Format (all commands):**
```python
{
    "success": bool,
    "data": Any,           # Command-specific data
    "error": str | None,   # Error message if failed
    "command": str,        # Echo of command
    "args": dict           # Echo of args
}
```

---

## Command Reference

### Filesystem Operations

**read** - Read file contents
```python
execute('read', {
    'path': 'file.txt',     # Required
    'lines': 10,            # Optional: first N lines
    'start': 5, 'end': 15   # Optional: line range (1-indexed)
})
# Returns: {"content": str} or {"lines": list}
```

**write** - Write/append to file
```python
execute('write', {
    'path': 'file.txt',
    'content': 'text...',
    'mode': 'w'  # 'w' (overwrite) or 'a' (append)
})
# Returns: {"status": "ok", "bytes": int}
# Note: Auto-decodes base64 content!
```

**replace** - Replace text or lines in file (DUAL MODE)
```python
# MODE 1: Line-based editing (NEW - precise line replacement)
execute('replace', {
    'path': 'file.py',
    'line': 42,                      # Line number (1-indexed)
    'new': '    # Updated comment'   # New line content
})
# Returns: {"status": "ok", "replacements": 1}
# Use case: Batch editing (translate comments, fix indentation, etc.)

# MODE 2: Text-based replacement (EXISTING - find/replace)
execute('replace', {
    'path': 'file.py',
    'old': 'def old():\n    pass',
    'new': 'def new():\n    return 42',
    'count': -1  # -1 = all occurrences
})
# Returns: {"status": "ok", "replacements": int}
# Use case: Rename functions, update strings, refactor code
```

**copy** / **move** / **delete** - Standard operations
```python
execute('copy', {'src': 'a.txt', 'dst': 'b.txt'})
execute('move', {'src': 'old.txt', 'dst': 'new.txt'})
execute('delete', {'path': 'file.txt', 'recursive': False})
```

**mkdir** / **ls** - Directory operations
```python
execute('mkdir', {'path': 'new_dir', 'parents': True})
execute('ls', {'path': '.', 'recursive': False})
# ls returns: {"files": [...], "dirs": [...]}
```

### Search Operations

**search** - Find files by pattern
```python
execute('search', {
    'pattern': '*.py',           # Glob pattern
    'path': '.',                 # Search root
    'recursive': True,           # Traverse subdirs
    'exclude_dirs': ['venv', 'node_modules']
})
# Returns: {"files": [list of paths]}
```

**grep** - Search content in files
```python
execute('grep', {
    'pattern': 'TODO:',          # Regex pattern
    'file_pattern': '*.py',      # File filter
    'path': '.',
    'recursive': True,
    'ignore_case': False
})
# Returns: {"matches": [{"file": str, "line": int, "text": str}]}
```

**info** - File/directory metadata
```python
execute('info', {'path': 'file.txt'})
# Returns: {"exists": bool, "size": int, "is_file": bool, "is_dir": bool, "modified": str}
```

### Codebase Intelligence

**scan_codebase** - Build AST-based metadata cache
```python
execute('scan_codebase', {'path': '.'})
# Scans all Python files, extracts:
# - Functions (name, signature, docstring, line number)
# - Classes (class names only - simple list)
# - Imports (module names)
# - Import graph (who imports whom - bidirectional!)
# Cache stored: .agentic_executor/metadata.json
# Returns: {"files_scanned": int, "functions": int, "classes": int}
```

**get_metadata** - Query cached metadata
```python
execute('get_metadata', {
    'type': 'summary',  # 'summary', 'structure', 'imports', 'all'
    'filter': {'file': 'path/to/file.py'}  # Optional: filter by file
})

# All responses include cache metadata:
# {
#   "cached_at": timestamp,
#   "age_minutes": float,
#   "is_stale": bool,  # True if cache >60 minutes old
#   ...  # Plus type-specific data below
# }

# type='summary' returns aggregate stats:
# {
#   "summary": {
#     "total_files": int,
#     "total_lines": int,
#     "total_functions": int,
#     "total_classes": int,
#     "external_imports": [str],     # Third-party dependencies
#     "internal_modules": [str]      # Your project modules
#   }
# }

# type='structure' returns file-level details:
# {
#   "files": {
#     "path/to/file.py": {
#       "size_bytes": int,
#       "lines": int,
#       "functions": [
#         {
#           "name": str,
#           "signature": str,          # Full signature με types
#           "docstring": str,
#           "line": int
#         }
#       ],
#       "classes": [str],              # Class names only (simple list)
#       "imports": [str]               # Module names imported
#     }
#   }
# }

# type='imports' returns import graph (WHO imports WHOM):
# {
#   "imports": {
#     "path/to/file.py": {
#       "imports": [str],              # What THIS file imports
#       "imported_by": [str]           # WHO imports this file (reverse deps!)
#     }
#   }
# }

# type='all' returns everything:
# {
#   "files": {...},      # Full structure
#   "imports": {...},    # Full import graph
#   "summary": {...}     # Aggregate stats
# }

# filter={'file': 'path.py'} returns single-file data:
# {
#   "file_data": {...},     # Structure for this file only
#   "import_data": {...}    # Imports for this file only
# }
```

**Ignore Patterns:** Create `.agentic_executor/.agentic_ignore` (gitignore syntax)
```
venv/
__pycache__/
*.pyc
.git/
node_modules/
```

### Process Execution

**run** - Execute shell commands
```python
execute('run', {
    'cmd': 'pytest tests/',
    'timeout': 30  # Optional: seconds
})
# Returns: {"stdout": str, "stderr": str, "returncode": int}
```

---

## Usage Patterns

### Pattern 1: Batch File Operations
```python
# Find and process multiple files
files = execute('search', {'pattern': 'test_*.py'})

for f in files['data']['files']:
    content = execute('read', {'path': f, 'lines': 10})
    print(f"=== {f} ===")
    print(content['data']['lines'])
```

### Pattern 2: Metadata-Driven Analysis
```python
# Scan codebase
execute('scan_codebase', {'path': '.'})
meta = execute('get_metadata', {'type': 'structure'})

# Find complex files (>20 functions)
complex_files = [
    (path, len(data['functions']))
    for path, data in meta['data']['files'].items()
    if len(data.get('functions', [])) > 20
]

print(f"Complex files: {complex_files}")

# Get dependency info
for path, func_count in complex_files:
    deps = execute('get_metadata', {
        'type': 'imports',
        'filter': {'file': path}
    })
    imported_by = deps['data']['import_data']['imported_by']
    print(f"{path}: {func_count} functions, used by {len(imported_by)} files")
```

### Pattern 3: Search + Process Workflow
```python
# Find TODO comments
todos = execute('grep', {'pattern': 'TODO:', 'file_pattern': '*.py'})

# Group by file
from collections import defaultdict
by_file = defaultdict(list)
for match in todos['data']['matches']:
    by_file[match['file']].append(match['text'])

# Generate report
for file, comments in by_file.items():
    print(f"\n{file}: {len(comments)} TODOs")
    for comment in comments:
        print(f"  - {comment.strip()}")
```

### Pattern 4: Batch Line-Based Editing
```python
# SCENARIO: Translate all comments (English → Greek) in multiple files

# STEP 1: Scan and display all comments
import re

files = [
    'golden_ratio_project/main.py',
    'golden_ratio_project/calculator.py',
    'golden_ratio_project/config.py'
]

print('📋 SCANNING FOR COMMENTS')
all_comments = []

for file_path in files:
    result = execute('read', {'path': file_path})
    if result['success']:
        lines = result['data']['content'].split('\n')
        for line_num, line in enumerate(lines, 1):
            if '#' in line:
                comment = re.search(r'#(.+)', line).group(0).strip()
                print(f'{file_path}:{line_num} - {comment}')
                all_comments.append({
                    'file': file_path,
                    'line': line_num,
                    'text': comment
                })

print(f'Found {len(all_comments)} comments\n')

# STEP 2: Batch translate ALL comments με ONE command
translations = [
    {'file': 'golden_ratio_project/main.py', 'line': 1, 'new': '# Υπολογιστής Χρυσής Τομής'},
    {'file': 'golden_ratio_project/main.py', 'line': 14, 'new': '    # Μέθοδος 1: Αλγεβρική'},
    {'file': 'golden_ratio_project/config.py', 'line': 1, 'new': '# Ρυθμίσεις Χρυσής Τομής'},
    # ... (all translations)
]

success_count = 0
for trans in translations:
    result = execute('replace', {
        'path': trans['file'],
        'line': trans['line'],
        'new': trans['new']
    })
    if result['success']:
        success_count += 1

print(f'✅ Translated {success_count}/{len(translations)} comments!')

# WHY LINE-BASED IS BETTER:
# ✓ Precise targeting (no ambiguous text matching)
# ✓ Preserves indentation automatically
# ✓ Works με duplicate comments
# ✓ Efficient batch operations (9 edits in 3 files!)
```

### Pattern 5: Conditional Logic
```python
# Check cache existence
info = execute('info', {'path': '.agentic_executor/metadata.json'})

if info['data']['exists']:
    meta = execute('get_metadata', {'type': 'summary'})
else:
    execute('scan_codebase', {'path': '.'})
    meta = execute('get_metadata', {'type': 'summary'})

print(f"Total functions: {meta['data']['summary']['total_functions']}")
```

### Pattern 5: Complex Analysis (Advanced)
```bash
# For complex scripts, use --thought-stdin!
python -m agentic_executor.cli --thought-stdin <<'EOF'
# Detect potential circular imports
execute('scan_codebase', {'path': '.'})
meta = execute('get_metadata', {'type': 'imports'})

# Build import graph from metadata
import_graph = {}
for path, data in meta['data']['imports'].items():
    # Only track internal imports (filter out external packages)
    internal_imports = [
        imp for imp in data['imports']
        if any(imp.startswith(mod) for mod in ['agentic_executor', 'benchmark', 'sequential-logeion'])
    ]
    import_graph[path] = internal_imports

# DFS cycle detection
def has_cycle(graph, node, visited, rec_stack):
    visited.add(node)
    rec_stack.add(node)
    for neighbor in graph.get(node, []):
        if neighbor not in visited:
            if has_cycle(graph, neighbor, visited, rec_stack):
                return True
        elif neighbor in rec_stack:
            return True
    rec_stack.remove(node)
    return False

# Find problematic files
problematic = []
visited = set()
for node in import_graph:
    if node not in visited:
        if has_cycle(import_graph, node, visited, set()):
            problematic.append(node)

print(f"Files with potential circular imports: {problematic}")
EOF
```

### Pattern 6: Dependency Analysis (Reverse Dependencies)
```python
# Find who depends on a specific file
execute('scan_codebase', {'path': '.'})

# Get reverse dependencies για core module
target_file = 'agentic_executor/code_parts/executor.py'
deps = execute('get_metadata', {
    'type': 'imports',
    'filter': {'file': target_file}
})

import_data = deps['data']['import_data']
print(f"File: {target_file}")
print(f"Imports: {import_data['imports']}")
print(f"Imported by {len(import_data['imported_by'])} files:")
for file in import_data['imported_by']:
    print(f"  - {file}")

# Find "high-impact" files (many dependents)
all_imports = execute('get_metadata', {'type': 'imports'})
high_impact = [
    (path, len(data['imported_by']))
    for path, data in all_imports['data']['imports'].items()
    if len(data.get('imported_by', [])) > 5
]
high_impact.sort(key=lambda x: x[1], reverse=True)

print("\nHigh-impact files (>5 dependents):")
for path, count in high_impact[:10]:
    print(f"{path}: {count} dependents")
```

---

## Integration Tips

### Calling from Bash Tool

**Simple one-liner (OK for testing):**
```bash
python -m agentic_executor.cli --thought "
result = execute('search', {'pattern': '*.py'})
print(len(result['data']['files']))
"
```

**Production-ready (use stdin):**
```bash
python -m agentic_executor.cli --thought-stdin <<'EOF'
# Multi-line complex workflow
execute('scan_codebase', {'path': '.'})
meta = execute('get_metadata', {'type': 'summary'})
print(f"Functions: {meta['data']['summary']['total_functions']}")
EOF
```

### Error Handling
```python
# All execute() calls return success: bool
result = execute('read', {'path': 'nonexistent.txt'})

if result['success']:
    print(result['data']['content'])
else:
    print(f"Error: {result['error']}")
    # Fallback logic...
```

### Best Practices: Raw Strings for Complex Content

**CRITICAL TIP:** When writing files with Python code containing escape sequences (`\n`, `\t`, etc.), use **raw strings** (`r'''...'''`) to avoid escaping issues!

**❌ WRONG: Regular strings (requires double escaping)**
```python
# Double backslashes needed - error-prone!
content = '''
def main():
    print("\\nHello World")  # \\n becomes \n
    print("\\tIndented")     # \\t becomes \t
'''
execute('write', {'path': 'file.py', 'content': content})
```

**✅ RIGHT: Raw strings (NO escaping needed!)**
```python
# Raw string preserves ALL backslashes - perfect!
content = r'''
def main():
    print("\nHello World")  # \n stays as \n
    print("\tIndented")     # \t stays as \t
'''
execute('write', {'path': 'file.py', 'content': content})
```

**Real-world example:**
```bash
# Create a complete Python project με ONE command!
python -m agentic_executor.cli --thought "
execute('mkdir', {'path': 'my_project'})

# Use r''' for Python code με escape sequences
main_py = r'''
def calculate_phi():
    import math
    phi = (1 + math.sqrt(5)) / 2
    print(f\"Golden Ratio: {phi}\")
    print(\"\nVerification:\")
    print(f\"Φ² = Φ + 1: {phi**2:.10f} ≈ {phi + 1:.10f}\")

if __name__ == \"__main__\":
    calculate_phi()
'''

execute('write', {'path': 'my_project/main.py', 'content': main_py})
print('Project created!')
"
```

**Why this matters:**
- ✅ Works perfectly με `--thought` (no need for `--thought-stdin`!)
- ✅ No double-escaping headaches (`\\n` vs `\n`)
- ✅ Code is readable and maintainable
- ✅ Prevents syntax errors in generated files

**When to use raw strings:**
- Writing Python files with print statements
- Writing shell scripts with escape sequences
- Writing JSON/YAML με special characters
- Any content με backslashes (`\n`, `\t`, `\r`, `\\`, etc.)

### Performance Considerations
- **Metadata cache**: Scanning 1000 files takes ~2-5 seconds
- **Cache reuse**: Subsequent queries are instant (<1ms)
- **Staleness detection**: Cache marked stale after 60 minutes (check `is_stale` flag)
- **Re-scan triggers**: Manually re-scan when codebase changes significantly
- **Storage**: Cache stored in `.agentic_executor/metadata.json` (add to .gitignore)
- **Cache size**: ~100KB per 1000 files scanned

---

## Robust Execution

### Using `--thought-stdin` for Complex Scripts

**CRITICAL:** For production use or complex Python code, use `--thought-stdin` instead of `--thought`.

**Why?**
- **Bash quote parsing**: `--thought "..."` breaks with nested quotes (' or ")
- **Command-line length limits**: 8KB on Windows, 32KB on Linux/Mac
- **Special characters**: Heredoc (`<<'EOF'`) handles all edge cases safely

**Pattern:**
```bash
# ✅ RECOMMENDED: Use stdin for complex code
python -m agentic_executor.cli --thought-stdin <<'EOF'
# Full Python code - NO quote escaping needed!

code = '''
def hello():
    """Docstring with quotes!"""
    return "Hello World!"
'''

result = execute('write', {'path': 'file.py', 'content': code})
print(f"Written: {result['success']}")
EOF
```

**When to use `--thought-stdin`:**
- ✅ Code contains strings with quotes (single or double)
- ✅ Writing large files (>1KB content)
- ✅ Multi-line Python scripts (>10 lines)
- ✅ Any production/automated workflow

**When `--thought` is OK:**
- Simple one-liners without quotes
- Quick testing/debugging
- Non-production use

### Common Pitfalls

**❌ WRONG: Direct quote nesting**
```bash
# Bash parsing error!
python -m agentic_executor.cli --thought "code = '''...'''"
```

**✅ RIGHT: Use stdin**
```bash
python -m agentic_executor.cli --thought-stdin <<'EOF'
code = '''...'''
EOF
```

**❌ WRONG: Assume command succeeded**
```python
# Crashes if file doesn't exist!
content = execute('read', {'path': 'file.txt'})['data']['content']
```

**✅ RIGHT: Always check success**
```python
result = execute('read', {'path': 'file.txt'})
if result['success']:
    content = result['data']['content']
else:
    print(f"Error: {result['error']}")
```

**❌ WRONG: Query metadata without scanning**
```python
# Error: Cache not found!
execute('get_metadata', {'type': 'summary'})
```

**✅ RIGHT: Scan first**
```python
execute('scan_codebase', {'path': '.'})
meta = execute('get_metadata', {'type': 'summary'})
```

---

## Quick Command Lookup

| Need | Command | Example |
|------|---------|---------|
| Read file | `read` | `execute('read', {'path': 'f.txt'})` |
| Write file | `write` | `execute('write', {'path': 'f.txt', 'content': '...'})` |
| Find files | `search` | `execute('search', {'pattern': '*.py'})` |
| Search content | `grep` | `execute('grep', {'pattern': 'TODO:'})` |
| Replace text | `replace` | `execute('replace', {'path': 'f.py', 'old': '...', 'new': '...'})` (text mode) |
| Replace line | `replace` | `execute('replace', {'path': 'f.py', 'line': 42, 'new': '...'})` (line mode) |
| Scan codebase | `scan_codebase` | `execute('scan_codebase', {'path': '.'})` |
| Get metadata | `get_metadata` | `execute('get_metadata', {'type': 'summary'})` |
| Run command | `run` | `execute('run', {'cmd': 'pytest'})` |

---

## Notes

- **Python environment**: Full standard library available (json, re, pathlib, os, etc.)
- **Imports allowed**: json, re, pathlib, os, collections, itertools, statistics
- **Sandboxing**: Commands are safe to execute (no arbitrary code execution)
- **Return consistency**: All commands use `{"success": bool, "data": Any, "error": str|None}` format
- **Cache location**: `.agentic_executor/` directory (automatically created)
- **Ignore patterns**: `.agentic_executor/.agentic_ignore` (gitignore syntax)
- **Production usage**: Always use `--thought-stdin` for robust execution (see "Robust Execution" section)

---

