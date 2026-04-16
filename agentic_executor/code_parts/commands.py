#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
AGENTIC EXECUTOR - COMMAND IMPLEMENTATIONS
═══════════════════════════════════════════════════════════════════════

All executable commands for the agentic system.

Each command:
- Takes args dict as input
- Returns data dict as output
- Handles errors gracefully (returns error dict)

VERSION: v0.1.0 (Initial Implementation)
"""

import os
import sys
import shutil
import subprocess
import json
import time
import base64
import re
from pathlib import Path
from typing import Dict, Any, Optional, List


# ═══════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════

def _is_base64(s: str) -> bool:
    """
    Auto-detect if string is base64-encoded.

    Heuristics:
    1. Only contains base64 chars: A-Z, a-z, 0-9, +, /, =
    2. Length is multiple of 4
    3. Can be decoded successfully
    4. Decoded result is valid UTF-8
    """
    if not isinstance(s, str) or not s:
        return False

    # Remove whitespace
    s = s.strip()

    # Check base64 character set
    if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', s):
        return False

    # Must be multiple of 4
    if len(s) % 4 != 0:
        return False

    # Try decode
    try:
        decoded = base64.b64decode(s)
        # Check if valid UTF-8
        decoded.decode('utf-8')
        return True
    except:
        return False


# ═══════════════════════════════════════════════════════════════════════
# FILESYSTEM COMMANDS
# ═══════════════════════════════════════════════════════════════════════

_READ_DEFAULT_LIMIT = 200


def read_file(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Read file contents.

    Args:
        path:  File path
        lines: Optional — number of lines to read from start
        start: Optional — start line (1-indexed)
        end:   Optional — end line (1-indexed)
        limit: Max lines when reading whole file (default 200). Use 0 for no limit.
        full:  If True, read entire file ignoring limit (equivalent to limit=0).

    Returns:
        Whole-file read (no lines/start/end):
            {"content": str}                         — file fits within limit
            {"content": str, "truncated": True,      — file exceeds limit
             "truncation_notice": str,
             "total_lines": int, "next_start": int}

        Range read (lines or start/end):
            {"lines": list[str]}
    """
    path = args.get("path")
    lines = args.get("lines")
    start = args.get("start")
    end = args.get("end")
    limit = args.get("limit", _READ_DEFAULT_LIMIT)
    full = args.get("full", False)

    # 'full: True' disables truncation (same as limit=0)
    if full:
        limit = 0

    if not path:
        return {"error": "Missing 'path' argument"}

    if not os.path.exists(path):
        return {"error": f"File not found: {path} (CWD: {os.getcwd()})"}

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            if lines is not None:
                # Read first N lines
                result_lines = []
                for i in range(lines):
                    line = f.readline()
                    if not line:
                        break
                    result_lines.append(line.rstrip("\n"))
                return {"lines": result_lines}

            elif start is not None and end is not None:
                # Read line range
                all_lines = f.readlines()
                result_lines = [
                    line.rstrip("\n")
                    for line in all_lines[start-1:end]
                ]
                return {"lines": result_lines}

            else:
                # Read entire file — apply limit
                all_lines = f.readlines()
                total = len(all_lines)

                if limit and total > limit:
                    next_start = limit + 1
                    notice = (
                        f"[TRUNCATED at {limit}/{total} lines — "
                        f"{total - limit} more lines not shown. "
                        f"Continue: execute('read', {{'path': '{path}', 'start': {next_start}, 'end': {total}}}) "
                        f"or read all at once: execute('read', {{'path': '{path}', 'full': True}})]"
                    )
                    print(
                        f"\nWARNING: '{path}' truncated at {limit}/{total} lines "
                        f"(next_start={next_start}). "
                        f"Use full=True or start/end to read more.\n",
                        file=sys.stderr,
                    )
                    return {
                        "content": "".join(all_lines[:limit]),
                        "truncated": True,
                        "truncation_notice": notice,
                        "total_lines": total,
                        "next_start": next_start,
                    }

                return {"content": "".join(all_lines)}

    except Exception as e:
        return {"error": str(e)}


def write_file(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Write content to file.

    Args:
        path: File path
        content: Content to write (plain text OR base64-encoded - auto-detected!)
        mode: "w" (overwrite) or "a" (append), default "w"

    Returns:
        {"status": "ok", "bytes": int, "decoded_from_base64": bool}

    Note:
        If content looks like base64, it will be automatically decoded!
        This eliminates quote/escape issues when writing code.
    """
    path = args.get("path")
    content = args.get("content", "")
    mode = args.get("mode", "w")

    if not path:
        return {"error": "Missing 'path' argument"}

    try:
        # 🔍 AUTO-DETECT: Is content base64-encoded?
        decoded_from_base64 = False
        if _is_base64(content):
            # Decode automatically!
            content = base64.b64decode(content.strip()).decode('utf-8')
            decoded_from_base64 = True

        # Write file
        with open(path, mode, encoding="utf-8") as f:
            f.write(content)

        return {
            "status": "ok",
            "bytes": len(content),
            "decoded_from_base64": decoded_from_base64
        }

    except Exception as e:
        return {"error": str(e)}


def copy_file(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Copy file or directory.

    Args:
        src: Source path
        dst: Destination path

    Returns:
        {"status": "ok"}
    """
    src = args.get("src")
    dst = args.get("dst")

    if not src or not dst:
        return {"error": "Missing 'src' or 'dst' argument"}

    if not os.path.exists(src):
        return {"error": f"Source not found: {src} (CWD: {os.getcwd()})"}

    try:
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        return {"status": "ok"}

    except Exception as e:
        return {"error": str(e)}


def move_file(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Move/rename file or directory.

    Args:
        src: Source path
        dst: Destination path

    Returns:
        {"status": "ok"}
    """
    src = args.get("src")
    dst = args.get("dst")

    if not src or not dst:
        return {"error": "Missing 'src' or 'dst' argument"}

    if not os.path.exists(src):
        return {"error": f"Source not found: {src} (CWD: {os.getcwd()})"}

    try:
        shutil.move(src, dst)
        return {"status": "ok"}

    except Exception as e:
        return {"error": str(e)}


def delete_file(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Delete file or directory.

    Args:
        path: Path to delete
        recursive: If True, delete directories recursively (default False)

    Returns:
        {"status": "ok"}
    """
    path = args.get("path")
    recursive = args.get("recursive", False)

    if not path:
        return {"error": "Missing 'path' argument"}

    if not os.path.exists(path):
        return {"error": f"Path not found: {path} (CWD: {os.getcwd()})"}

    try:
        if os.path.isdir(path):
            if recursive:
                shutil.rmtree(path)
            else:
                os.rmdir(path)
        else:
            os.remove(path)
        return {"status": "ok"}

    except Exception as e:
        return {"error": str(e)}


def make_directory(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create directory.

    Args:
        path: Directory path
        parents: Create parent directories if needed (default True)

    Returns:
        {"status": "ok"}
    """
    path = args.get("path")
    parents = args.get("parents", True)

    if not path:
        return {"error": "Missing 'path' argument"}

    try:
        if parents:
            os.makedirs(path, exist_ok=True)
        else:
            os.mkdir(path)
        return {"status": "ok"}

    except Exception as e:
        return {"error": str(e)}


def list_directory(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    List directory contents.

    Args:
        path: Directory path (default ".")
        pattern: Optional glob pattern (e.g., "*.py")

    Returns:
        {"files": list, "dirs": list}
    """
    path = args.get("path", ".")
    pattern = args.get("pattern")

    if not os.path.exists(path):
        return {"error": f"Directory not found: {path} (CWD: {os.getcwd()})"}

    try:
        if pattern:
            from glob import glob
            all_items = glob(os.path.join(path, pattern))
            files = [f for f in all_items if os.path.isfile(f)]
            dirs = [d for d in all_items if os.path.isdir(d)]
        else:
            all_items = os.listdir(path)
            files = [f for f in all_items if os.path.isfile(os.path.join(path, f))]
            dirs = [d for d in all_items if os.path.isdir(os.path.join(path, d))]

        return {"files": sorted(files), "dirs": sorted(dirs)}

    except Exception as e:
        return {"error": str(e)}


def replace_in_file(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Replace text in file (DUAL MODE: line-based OR text-based).

    MODE 1 - Line-based editing (NEW):
        Args:
            path: File path
            line: Line number to replace (1-indexed)
            new: New line content

        Example:
            execute('replace', {'path': 'file.py', 'line': 4, 'new': '    # Greek comment'})

    MODE 2 - Text-based replacement (EXISTING):
        Args:
            path: File path
            old: Text to find
            new: Replacement text
            count: Max replacements (default -1 = all)

        Example:
            execute('replace', {'path': 'file.py', 'old': '# English', 'new': '# Greek', 'count': 1})

    Returns:
        {"status": "ok", "replacements": int}
    """
    path = args.get("path")
    line_num = args.get("line")
    old = args.get("old")
    new = args.get("new")
    count = args.get("count", -1)

    if not path or new is None:
        return {"error": "Missing required arguments: 'path' and 'new'"}

    if not os.path.exists(path):
        return {"error": f"File not found: {path} (CWD: {os.getcwd()})"}

    try:
        # MODE 1: Line-based editing
        if line_num is not None:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            # Convert to 0-indexed
            idx = line_num - 1

            if idx < 0 or idx >= len(lines):
                return {"error": f"Line {line_num} out of range (file has {len(lines)} lines)"}

            # Replace the line (preserve existing newline if present)
            old_line = lines[idx]
            has_newline = old_line.endswith('\n')

            if has_newline and not new.endswith('\n'):
                lines[idx] = new + '\n'
            elif not has_newline and new.endswith('\n'):
                lines[idx] = new.rstrip('\n')
            else:
                lines[idx] = new

            with open(path, "w", encoding="utf-8") as f:
                f.writelines(lines)

            return {"status": "ok", "replacements": 1}

        # MODE 2: Text-based replacement (EXISTING functionality)
        elif old is not None:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            replacements = content.count(old)
            content = content.replace(old, new, count)

            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            return {"status": "ok", "replacements": replacements}

        else:
            return {"error": "Must provide either 'line' (for line-based edit) or 'old' (for text-based replace)"}

    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# PROCESS EXECUTION COMMANDS
# ═══════════════════════════════════════════════════════════════════════

def run_command(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run shell command.

    Args:
        cmd: Command to execute
        cwd: Working directory (optional)
        timeout: Timeout in seconds (default 60)
        capture_output: Capture stdout/stderr (default True)

    Returns:
        {"stdout": str, "stderr": str, "returncode": int}
    """
    cmd = args.get("cmd")
    cwd = args.get("cwd")
    timeout = args.get("timeout", 60)
    capture_output = args.get("capture_output", True)

    if not cmd:
        return {"error": "Missing 'cmd' argument"}

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            timeout=timeout,
            capture_output=capture_output,
            text=True
        )

        return {
            "stdout": result.stdout if capture_output else "",
            "stderr": result.stderr if capture_output else "",
            "returncode": result.returncode
        }

    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {timeout}s"}

    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# UTILITY COMMANDS
# ═══════════════════════════════════════════════════════════════════════

def search_files(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search for files by name pattern.

    Args:
        path: Root directory (default ".")
        pattern: Filename pattern (e.g., "*.py")
        recursive: Search recursively (default True)

    Returns:
        {"files": list}
    """
    path = args.get("path", ".")
    pattern = args.get("pattern", "*")
    recursive = args.get("recursive", True)

    if not os.path.exists(path):
        return {"error": f"Directory not found: {path} (CWD: {os.getcwd()})"}

    try:
        from glob import glob
        if recursive:
            search_pattern = os.path.join(path, "**", pattern)
            files = glob(search_pattern, recursive=True)
        else:
            search_pattern = os.path.join(path, pattern)
            files = glob(search_pattern)

        # Filter only files (not directories)
        files = [f for f in files if os.path.isfile(f)]

        return {"files": sorted(files)}

    except Exception as e:
        return {"error": str(e)}


def get_file_info(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get file/directory metadata.

    Args:
        path: File or directory path

    Returns:
        {
            "exists": bool,
            "type": "file" | "dir" | "other",
            "size": int,
            "modified": float,
            "created": float
        }
    """
    path = args.get("path")

    if not path:
        return {"error": "Missing 'path' argument"}

    try:
        if not os.path.exists(path):
            return {"exists": False}

        stat = os.stat(path)

        file_type = "other"
        if os.path.isfile(path):
            file_type = "file"
        elif os.path.isdir(path):
            file_type = "dir"

        return {
            "exists": True,
            "type": file_type,
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "created": stat.st_ctime
        }

    except Exception as e:
        return {"error": str(e)}


def grep_files(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search for text pattern in files.

    Args:
        pattern: Text pattern to search
        path: Directory to search (default ".")
        file_pattern: File pattern (e.g., "*.py")
        recursive: Search recursively (default True)
        max_results: Max results to return (default 100)

    Returns:
        {
            "matches": [
                {"file": str, "line": int, "text": str},
                ...
            ]
        }
    """
    pattern = args.get("pattern")
    path = args.get("path", ".")
    file_pattern = args.get("file_pattern", "*")
    recursive = args.get("recursive", True)
    max_results = args.get("max_results", 100)

    if not pattern:
        return {"error": "Missing 'pattern' argument"}

    if not os.path.exists(path):
        return {"error": f"Directory not found: {path} (CWD: {os.getcwd()})"}

    try:
        import re
        from glob import glob

        # Find files
        if recursive:
            search_pattern = os.path.join(path, "**", file_pattern)
            files = glob(search_pattern, recursive=True)
        else:
            search_pattern = os.path.join(path, file_pattern)
            files = glob(search_pattern)

        files = [f for f in files if os.path.isfile(f)]

        # Search in files
        matches = []
        regex = re.compile(pattern)

        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        if regex.search(line):
                            matches.append({
                                "file": file_path,
                                "line": line_num,
                                "text": line.rstrip("\n")
                            })

                            if len(matches) >= max_results:
                                break
            except:
                continue  # Skip files that can't be read

            if len(matches) >= max_results:
                break

        return {"matches": matches}

    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# MULTI-LANGUAGE CODE ANALYSIS (tree-sitter + fallbacks)
# ═══════════════════════════════════════════════════════════════════════

# Map file extensions → language name (None = skip, no extraction)
_EXT_TO_LANG: Dict[str, Optional[str]] = {
    '.py': 'python',
    '.js': 'javascript', '.jsx': 'javascript', '.mjs': 'javascript',
    '.ts': 'typescript', '.tsx': 'typescript',
    '.go': 'go',
    '.rs': 'rust',
    '.java': 'java',
    '.c': 'c', '.h': 'c',
    '.cpp': 'cpp', '.cc': 'cpp', '.cxx': 'cpp', '.hpp': 'cpp',
    '.rb': 'ruby',
    '.cs': 'csharp',
    '.kt': 'kotlin', '.kts': 'kotlin',
    '.scala': 'scala',
    '.php': 'php',
    '.swift': 'swift',
    '.lua': 'lua',
    '.r': 'r',
    '.dart': 'dart',
    '.ex': 'elixir', '.exs': 'elixir',
    '.sh': 'bash', '.bash': 'bash',
    # Data/config — skip function extraction
    '.json': None, '.yaml': None, '.yml': None,
    '.md': None, '.txt': None,
}

# tree-sitter configuration per language
# fn_types: node types representing functions/methods
# cls_types: node types representing classes/structs/interfaces
# name_field: tree-sitter field name for the identifier (None = search children)
# import_handler: key for the import extraction strategy
_LANG_CONFIGS: Dict[str, Any] = {
    'python': {
        'ts_module': 'tree_sitter_python',
        'fn_types': {'function_definition', 'async_function_definition'},
        'cls_types': {'class_definition'},
        'name_field': 'name',
        'import_handler': 'python',
    },
    'javascript': {
        'ts_module': 'tree_sitter_javascript',
        'fn_types': {'function_declaration', 'method_definition', 'generator_function_declaration'},
        'cls_types': {'class_declaration'},
        'name_field': 'name',
        'import_handler': 'js',
    },
    'typescript': {
        'ts_module': 'tree_sitter_typescript',
        'ts_func': 'language_typescript',
        'fn_types': {'function_declaration', 'method_definition', 'function_signature'},
        'cls_types': {'class_declaration', 'interface_declaration', 'type_alias_declaration'},
        'name_field': 'name',
        'import_handler': 'js',
    },
    'go': {
        'ts_module': 'tree_sitter_go',
        'fn_types': {'function_declaration', 'method_declaration'},
        'cls_types': {'type_declaration'},
        'name_field': 'name',
        'import_handler': 'go',
    },
    'rust': {
        'ts_module': 'tree_sitter_rust',
        'fn_types': {'function_item'},
        'cls_types': {'struct_item', 'enum_item', 'trait_item'},
        'name_field': 'name',
        'import_handler': 'rust',
    },
    'java': {
        'ts_module': 'tree_sitter_java',
        'fn_types': {'method_declaration', 'constructor_declaration'},
        'cls_types': {'class_declaration', 'interface_declaration', 'enum_declaration'},
        'name_field': 'name',
        'import_handler': 'java',
    },
    'c': {
        'ts_module': 'tree_sitter_c',
        'fn_types': {'function_definition'},
        'cls_types': {'struct_specifier', 'union_specifier', 'enum_specifier'},
        'name_field': None,
        'import_handler': 'c',
    },
    'cpp': {
        'ts_module': 'tree_sitter_cpp',
        'fn_types': {'function_definition'},
        'cls_types': {'class_specifier', 'struct_specifier', 'enum_specifier'},
        'name_field': None,
        'import_handler': 'c',
    },
    'ruby': {
        'ts_module': 'tree_sitter_ruby',
        'fn_types': {'method', 'singleton_method'},
        'cls_types': {'class', 'module'},
        'name_field': 'name',
        'import_handler': 'ruby',
    },
    'csharp': {
        'ts_module': 'tree_sitter_c_sharp',
        'fn_types': {'method_declaration', 'constructor_declaration'},
        'cls_types': {'class_declaration', 'interface_declaration', 'struct_declaration'},
        'name_field': 'name',
        'import_handler': 'csharp',
    },
    'kotlin': {
        'ts_module': 'tree_sitter_kotlin',
        'fn_types': {'function_declaration'},
        'cls_types': {'class_declaration', 'object_declaration', 'interface_declaration'},
        'name_field': 'simple_identifier',
        'import_handler': 'java',
    },
    'scala': {
        'ts_module': 'tree_sitter_scala',
        'fn_types': {'function_definition'},
        'cls_types': {'class_definition', 'object_definition', 'trait_definition'},
        'name_field': 'name',
        'import_handler': 'java',
    },
    'php': {
        'ts_module': 'tree_sitter_php',
        'ts_func': 'language_php',
        'fn_types': {'function_definition', 'method_declaration'},
        'cls_types': {'class_declaration', 'interface_declaration', 'trait_declaration'},
        'name_field': 'name',
        'import_handler': 'php',
    },
    'swift': {
        'ts_module': 'tree_sitter_swift',
        'fn_types': {'function_declaration'},
        'cls_types': {'class_declaration', 'struct_declaration', 'protocol_declaration'},
        'name_field': None,
        'import_handler': 'swift',
    },
    'lua': {
        'ts_module': 'tree_sitter_lua',
        'fn_types': {'function_definition'},
        'cls_types': set(),
        'name_field': 'name',
        'import_handler': 'lua',
    },
}

# Scan all supported code extensions by default (not just .py)
_DEFAULT_SCAN_PATTERNS = [
    "*.py", "*.js", "*.jsx", "*.ts", "*.tsx",
    "*.go", "*.rs", "*.java",
    "*.c", "*.h", "*.cpp", "*.cc", "*.hpp",
    "*.rb", "*.cs", "*.kt", "*.scala", "*.php",
    "*.swift", "*.lua", "*.r", "*.dart",
]

# Parser cache — avoid reloading for each file
_ts_parser_cache: Dict[str, Any] = {}


def _get_ts_parser(lang_name: str) -> Optional[Any]:
    """Load and cache a tree-sitter parser. Returns None if unavailable."""
    if lang_name in _ts_parser_cache:
        return _ts_parser_cache[lang_name]

    config = _LANG_CONFIGS.get(lang_name)
    if not config or not config.get('ts_module'):
        _ts_parser_cache[lang_name] = None
        return None

    try:
        from tree_sitter import Language, Parser  # type: ignore
        ts_mod = __import__(config['ts_module'])
        func_name = config.get('ts_func', 'language')
        if hasattr(ts_mod, func_name):
            lang = Language(getattr(ts_mod, func_name)())
        elif hasattr(ts_mod, 'language'):
            lang = Language(ts_mod.language())
        else:
            _ts_parser_cache[lang_name] = None
            return None
        parser = Parser(lang)
        _ts_parser_cache[lang_name] = parser
        return parser
    except Exception:
        _ts_parser_cache[lang_name] = None
        return None


def _walk_ts(node: Any):
    """Recursively yield every node in the tree."""
    yield node
    for child in node.children:
        yield from _walk_ts(child)


def _get_node_name(node: Any, content_bytes: bytes, name_field: Optional[str]) -> str:
    """Get identifier name from a tree-sitter node."""
    if name_field:
        name_node = node.child_by_field_name(name_field)
        if name_node:
            return content_bytes[name_node.start_byte:name_node.end_byte].decode('utf-8', errors='replace')
    # Fallback: first identifier-type child
    for child in node.children:
        if child.type in ('identifier', 'type_identifier', 'simple_identifier'):
            return content_bytes[child.start_byte:child.end_byte].decode('utf-8', errors='replace')
    return '<anonymous>'


def _extract_imports_ts(tree: Any, content_bytes: bytes, lang_name: str) -> List[str]:
    """Extract import paths from a parsed tree using language-specific rules."""
    imports: List[str] = []
    handler = _LANG_CONFIGS.get(lang_name, {}).get('import_handler', '')

    for node in _walk_ts(tree.root_node):
        try:
            if handler == 'python':
                if node.type == 'import_statement':
                    for child in node.children:
                        if child.type in ('dotted_name', 'identifier'):
                            imports.append(content_bytes[child.start_byte:child.end_byte].decode('utf-8', errors='replace'))
                elif node.type == 'import_from_statement':
                    mod = node.child_by_field_name('module_name')
                    if mod:
                        imports.append(content_bytes[mod.start_byte:mod.end_byte].decode('utf-8', errors='replace'))

            elif handler == 'js':
                if node.type == 'import_statement':
                    src = node.child_by_field_name('source')
                    if src:
                        raw = content_bytes[src.start_byte:src.end_byte].decode('utf-8', errors='replace')
                        imports.append(raw.strip('"\'`'))

            elif handler == 'go':
                if node.type == 'import_spec':
                    path = node.child_by_field_name('path')
                    if path:
                        raw = content_bytes[path.start_byte:path.end_byte].decode('utf-8', errors='replace')
                        imports.append(raw.strip('"'))

            elif handler == 'rust':
                if node.type == 'use_declaration':
                    arg = node.child_by_field_name('argument')
                    if arg:
                        imports.append(content_bytes[arg.start_byte:arg.end_byte].decode('utf-8', errors='replace'))

            elif handler in ('java', 'csharp'):
                if node.type in ('import_declaration', 'using_directive'):
                    for child in node.children:
                        if child.type not in ('import', 'using', ';', ',', '.'):
                            raw = content_bytes[child.start_byte:child.end_byte].decode('utf-8', errors='replace').strip()
                            if raw and raw not in ('import', 'using', ';', 'static'):
                                imports.append(raw)
                                break

            elif handler == 'c':
                if node.type == 'preproc_include':
                    for child in node.children:
                        if child.type in ('string_literal', 'system_lib_string'):
                            raw = content_bytes[child.start_byte:child.end_byte].decode('utf-8', errors='replace')
                            imports.append(raw.strip('<>"'))

            elif handler == 'ruby':
                if node.type == 'call':
                    method = node.child_by_field_name('method')
                    if method:
                        mname = content_bytes[method.start_byte:method.end_byte].decode('utf-8', errors='replace')
                        if mname in ('require', 'require_relative'):
                            args_node = node.child_by_field_name('arguments')
                            if args_node:
                                raw = content_bytes[args_node.start_byte:args_node.end_byte].decode('utf-8', errors='replace')
                                imports.append(raw.strip("()\"'"))

        except Exception:
            continue

    return imports


def _extract_ts_metadata(content: str, lang_name: str) -> Optional[Dict[str, Any]]:
    """
    Extract functions/classes/imports via tree-sitter.
    Returns None if tree-sitter is unavailable for this language.
    """
    parser = _get_ts_parser(lang_name)
    if parser is None:
        return None

    config = _LANG_CONFIGS[lang_name]
    content_bytes = bytes(content, 'utf-8')
    try:
        tree = parser.parse(content_bytes)
    except Exception:
        return None

    functions: List[Dict[str, Any]] = []
    classes: List[str] = []
    fn_types = config.get('fn_types', set())
    cls_types = config.get('cls_types', set())
    name_field = config.get('name_field')

    for node in _walk_ts(tree.root_node):
        try:
            if node.type in fn_types:
                name = _get_node_name(node, content_bytes, name_field)
                functions.append({
                    "name": name,
                    "signature": f"(line {node.start_point[0] + 1})",
                    "docstring": "",
                    "line": node.start_point[0] + 1,
                })
            elif node.type in cls_types:
                name = _get_node_name(node, content_bytes, name_field)
                if name != '<anonymous>':
                    classes.append(name)
        except Exception:
            continue

    imports = _extract_imports_ts(tree, content_bytes, lang_name)
    return {"functions": functions, "classes": classes, "imports": imports}


def _extract_regex_metadata(content: str, lang_name: str) -> Dict[str, Any]:
    """
    Regex-based fallback extraction (used when tree-sitter is not installed).
    Covers the most common patterns for each language.
    """
    _patterns: Dict[str, Dict[str, str]] = {
        'python':     {'fn': r'^\s*(?:async\s+)?def\s+(\w+)\s*\(', 'cls': r'^\s*class\s+(\w+)\s*[:(]', 'imp': r'^\s*(?:import|from)\s+([\w.]+)'},
        'javascript': {'fn': r'(?:function\s+(\w+)|(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[\w]+)\s*=>)', 'cls': r'\bclass\s+(\w+)', 'imp': r'(?:import|require)\s*\(?[\'"]([^\'"]+)[\'"]'},
        'typescript': {'fn': r'(?:function\s+(\w+)|(?:public|private|protected|async)?\s+(\w+)\s*\()', 'cls': r'\b(?:class|interface)\s+(\w+)', 'imp': r'(?:import|require)\s*\(?[\'"]([^\'"]+)[\'"]'},
        'go':         {'fn': r'^\s*func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(', 'cls': r'^\s*type\s+(\w+)\s+(?:struct|interface)', 'imp': r'"([^"]+)"'},
        'rust':       {'fn': r'^\s*(?:pub\s+)?(?:async\s+)?fn\s+(\w+)', 'cls': r'^\s*(?:pub\s+)?(?:struct|enum|trait)\s+(\w+)', 'imp': r'^\s*use\s+([\w:]+)'},
        'java':       {'fn': r'(?:public|private|protected|static|\s)+[\w<>\[\]]+\s+(\w+)\s*\(', 'cls': r'(?:public|private|\s)*(?:class|interface|enum)\s+(\w+)', 'imp': r'^\s*import\s+([\w.]+)'},
        'c':          {'fn': r'^[\w\s\*]+\s+(\w+)\s*\([^;{]*\)\s*\{', 'cls': r'^\s*(?:struct|union|enum)\s+(\w+)', 'imp': r'#include\s*[<"]([^>"]+)[>"]'},
        'cpp':        {'fn': r'^[\w\s\*:~<>]+\s+(\w+)\s*\([^;]*\)\s*(?:const\s*)?\{', 'cls': r'^\s*(?:class|struct|enum)\s+(\w+)', 'imp': r'#include\s*[<"]([^>"]+)[>"]'},
        'ruby':       {'fn': r'^\s*def\s+(\w+)', 'cls': r'^\s*(?:class|module)\s+(\w+)', 'imp': r'require(?:_relative)?\s+[\'"]([^\'"]+)[\'"]'},
        'csharp':     {'fn': r'(?:public|private|protected|static|\s)+\w[\w<>\[\]]*\s+(\w+)\s*\(', 'cls': r'(?:public|private|internal|\s)*(?:class|interface|struct)\s+(\w+)', 'imp': r'^\s*using\s+([\w.]+)'},
        'kotlin':     {'fn': r'^\s*(?:fun|override fun|suspend fun)\s+(\w+)\s*\(', 'cls': r'^\s*(?:class|interface|object|data class)\s+(\w+)', 'imp': r'^\s*import\s+([\w.]+)'},
        'scala':      {'fn': r'^\s*def\s+(\w+)', 'cls': r'^\s*(?:class|object|trait|case class)\s+(\w+)', 'imp': r'^\s*import\s+([\w.]+)'},
        'php':        {'fn': r'^\s*(?:public|private|protected)?\s*function\s+(\w+)\s*\(', 'cls': r'^\s*(?:abstract\s+)?(?:class|interface|trait)\s+(\w+)', 'imp': r'(?:use|require|include)\s+[\'"]?([^\'";\s]+)'},
        'swift':      {'fn': r'^\s*(?:func|override func|private func|public func|internal func)\s+(\w+)\s*\(', 'cls': r'^\s*(?:class|struct|protocol|enum)\s+(\w+)', 'imp': r'^\s*import\s+(\w+)'},
        'lua':        {'fn': r'(?:local\s+)?function\s+(\w+)\s*\(|(\w+)\s*=\s*function\s*\(', 'cls': r'', 'imp': r'require\s*\([\'"]([^\'"]+)[\'"]\)'},
        'elixir':     {'fn': r'^\s*def(?:p)?\s+(\w+)', 'cls': r'^\s*defmodule\s+([\w.]+)', 'imp': r'^\s*(?:import|alias|require|use)\s+([\w.]+)'},
        'bash':       {'fn': r'^(?:function\s+)?(\w+)\s*\(\s*\)', 'cls': r'', 'imp': r'^\s*source\s+([^\s]+)'},
    }
    generic = {'fn': r'(?:def|func|function|fn|sub)\s+(\w+)\s*[\(\{]', 'cls': r'(?:class|struct|type)\s+(\w+)', 'imp': r'(?:import|require|include|use)\s+[\'"]?([\w./]+)'}
    lang_p = _patterns.get(lang_name, generic)

    functions: List[Dict[str, Any]] = []
    classes: List[str] = []
    imports: List[str] = []

    for line_num, line in enumerate(content.split('\n'), 1):
        try:
            if lang_p.get('fn'):
                m = re.search(lang_p['fn'], line)
                if m:
                    name = next((g for g in m.groups() if g), None) if m.groups() else m.group(0)
                    if name:
                        functions.append({"name": name, "signature": f"(line {line_num})", "docstring": "", "line": line_num})
            if lang_p.get('cls'):
                m = re.search(lang_p['cls'], line)
                if m and m.group(1):
                    classes.append(m.group(1))
            if lang_p.get('imp'):
                m = re.search(lang_p['imp'], line)
                if m and m.group(1):
                    imports.append(m.group(1))
        except Exception:
            continue

    return {"functions": functions, "classes": list(dict.fromkeys(classes)), "imports": imports}


# ═══════════════════════════════════════════════════════════════════════
# CODEBASE ANALYSIS COMMANDS
# ═══════════════════════════════════════════════════════════════════════

def _load_ignore_patterns(ignore_file: str) -> List[str]:
    """
    Load ignore patterns from .agentic_ignore file.

    Args:
        ignore_file: Path to .agentic_ignore file

    Returns:
        List of patterns to ignore
    """
    patterns = []

    # Default patterns (always excluded)
    default_patterns = [
        "__pycache__",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        ".git",
        ".agentic_executor",
        "venv",
        "env",
        ".venv",
        "node_modules",
    ]
    patterns.extend(default_patterns)

    # Load from file if exists
    if os.path.exists(ignore_file):
        try:
            with open(ignore_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith("#"):
                        patterns.append(line)
        except:
            pass  # If can't read file, just use defaults

    return patterns


def _should_ignore(path: str, root_path: str, ignore_patterns: List[str]) -> bool:
    """
    Check if a path should be ignored based on patterns.

    Args:
        path: Full path to check
        root_path: Root directory being scanned
        ignore_patterns: List of patterns to match against

    Returns:
        True if path should be ignored, False otherwise
    """
    import fnmatch

    # Get relative path
    rel_path = os.path.relpath(path, root_path)
    parts = rel_path.split(os.sep)

    for pattern in ignore_patterns:
        # Remove trailing slash if present
        pattern = pattern.rstrip("/").rstrip("\\")

        # Check if pattern matches any part of the path
        for part in parts:
            # Exact match
            if part == pattern:
                return True
            # Glob pattern match (e.g., *.pyc)
            if fnmatch.fnmatch(part, pattern):
                return True

        # Check if pattern matches the full relative path
        if fnmatch.fnmatch(rel_path, pattern):
            return True

        # Check directory patterns (e.g., "dev work new/")
        if os.sep in pattern or "/" in pattern:
            normalized_pattern = pattern.replace("/", os.sep)
            if normalized_pattern in rel_path:
                return True

    return False


def scan_codebase(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scan codebase and generate metadata cache.

    Supports 20+ languages via tree-sitter (with ast/regex fallback).
    Supported: Python, JS, TS, Go, Rust, Java, C, C++, Ruby, C#,
               Kotlin, Scala, PHP, Swift, Lua, Elixir, Bash, and more.

    Args:
        path: Root directory to scan (default: ".")
        cache: Cache file path (default: ".agentic_executor/metadata.json")
        patterns: File patterns to include (default: all supported languages)
        ignore_file: Path to ignore patterns file

    Returns:
        {
            "files_scanned": int,
            "files_ignored": int,
            "languages": {"python": int, "go": int, ...},
            "cache_path": str,
            "cache_size_kb": float,
            "scan_duration_ms": float,
            "summary": {
                "total_files": int,
                "total_lines": int,
                "total_functions": int,
                "total_classes": int,
                "external_imports": list,
                "internal_modules": list
            }
        }
    """
    import time
    from glob import glob

    start_time = time.time()

    root_path = args.get("path", ".")
    cache_path = args.get("cache", ".agentic_executor/metadata.json")
    patterns = args.get("patterns", _DEFAULT_SCAN_PATTERNS)
    ignore_file = args.get("ignore_file", ".agentic_executor/.agentic_ignore")

    if not os.path.exists(root_path):
        return {"error": f"Directory not found: {root_path} (CWD: {os.getcwd()})"}

    try:
        ignore_patterns = _load_ignore_patterns(ignore_file)
        metadata: Dict[str, Any] = {
            "scan_timestamp": time.time(),
            "root_path": os.path.abspath(root_path),
            "files": {},
            "imports": {},
            "summary": {
                "total_files": 0,
                "total_lines": 0,
                "total_functions": 0,
                "total_classes": 0,
                "external_imports": set(),
                "internal_modules": set(),
            },
            "languages": {},
        }

        # Collect all matching files (deduplicated)
        seen: set = set()
        all_files: List[str] = []
        for pattern in patterns:
            for f in glob(os.path.join(root_path, "**", pattern), recursive=True):
                if f not in seen:
                    seen.add(f)
                    all_files.append(f)

        # Apply ignore rules
        filtered_files: List[str] = []
        ignored_count = 0
        for file_path in all_files:
            if _should_ignore(file_path, root_path, ignore_patterns):
                ignored_count += 1
            else:
                filtered_files.append(file_path)

        # Python stdlib set for import categorization
        _stdlib = {
            "os", "sys", "json", "time", "re", "ast", "pathlib", "typing",
            "subprocess", "shutil", "glob", "tempfile", "collections", "itertools",
            "functools", "io", "abc", "dataclasses", "enum", "math", "hashlib",
            "base64", "datetime", "copy", "threading", "logging", "unittest",
        }

        # Scan each file
        for file_path in filtered_files:
            try:
                ext = os.path.splitext(file_path)[1].lower()
                lang_name = _EXT_TO_LANG.get(ext)
                if lang_name is None:
                    continue  # explicitly skipped (data files, etc.)

                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                lines = content.split("\n")

                # Extraction priority: tree-sitter → Python ast → regex
                extracted: Optional[Dict[str, Any]] = None

                # 1. tree-sitter
                if lang_name in _LANG_CONFIGS:
                    extracted = _extract_ts_metadata(content, lang_name)

                # 2. Python ast fallback (richer signatures/docstrings)
                if extracted is None and lang_name == 'python':
                    try:
                        import ast as _ast
                        tree = _ast.parse(content, filename=file_path)
                        functions: List[Dict[str, Any]] = []
                        for node in _ast.walk(tree):
                            if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                                doc = (_ast.get_docstring(node) or "").split("\n")[0]
                                functions.append({
                                    "name": node.name,
                                    "signature": f"(line {node.lineno})",
                                    "docstring": doc,
                                    "line": node.lineno,
                                })
                        classes_list = [n.name for n in _ast.walk(tree) if isinstance(n, _ast.ClassDef)]
                        imports_list: List[str] = []
                        for node in _ast.walk(tree):
                            if isinstance(node, _ast.Import):
                                for alias in node.names:
                                    imports_list.append(alias.name)
                            elif isinstance(node, _ast.ImportFrom) and node.module:
                                imports_list.append(node.module)
                        extracted = {"functions": functions, "classes": classes_list, "imports": imports_list}
                    except SyntaxError:
                        pass

                # 3. Regex fallback
                if extracted is None:
                    extracted = _extract_regex_metadata(content, lang_name)

                functions = extracted.get("functions", [])
                classes_list = extracted.get("classes", [])
                imports_list = extracted.get("imports", [])

                rel_path = os.path.relpath(file_path, root_path)
                metadata["files"][rel_path] = {
                    "size_bytes": os.path.getsize(file_path),
                    "lines": len(lines),
                    "language": lang_name,
                    "functions": functions,
                    "classes": classes_list,
                    "imports": imports_list,
                }
                metadata["imports"][rel_path] = {"imports": imports_list, "imported_by": []}

                metadata["summary"]["total_files"] += 1
                metadata["summary"]["total_lines"] += len(lines)
                metadata["summary"]["total_functions"] += len(functions)
                metadata["summary"]["total_classes"] += len(classes_list)
                metadata["languages"][lang_name] = metadata["languages"].get(lang_name, 0) + 1

                # Categorize Python imports
                if lang_name == 'python':
                    for imp in imports_list:
                        root_mod = imp.split(".")[0]
                        if root_mod not in _stdlib:
                            internal_check = os.path.join(root_path, root_mod)
                            if os.path.exists(internal_check) or os.path.exists(internal_check + ".py"):
                                metadata["summary"]["internal_modules"].add(root_mod)
                            else:
                                metadata["summary"]["external_imports"].add(root_mod)

            except Exception:
                continue

        # Post-process: build reverse import graph (imported_by)
        for fp, fd in metadata["files"].items():
            for imp in fd["imports"]:
                for other in metadata["imports"]:
                    mod = other.replace(os.sep, ".").replace(".py", "")
                    if imp.startswith(mod) or mod.endswith(imp):
                        if fp not in metadata["imports"][other]["imported_by"]:
                            metadata["imports"][other]["imported_by"].append(fp)

        # Serialize sets
        metadata["summary"]["external_imports"] = sorted(list(metadata["summary"]["external_imports"]))
        metadata["summary"]["internal_modules"] = sorted(list(metadata["summary"]["internal_modules"]))

        # Write cache
        cache_dir = os.path.dirname(cache_path)
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        cache_size_kb = os.path.getsize(cache_path) / 1024
        duration_ms = (time.time() - start_time) * 1000

        return {
            "files_scanned": metadata["summary"]["total_files"],
            "files_ignored": ignored_count,
            "languages": metadata["languages"],
            "cache_path": cache_path,
            "cache_size_kb": round(cache_size_kb, 2),
            "scan_duration_ms": round(duration_ms, 2),
            "summary": metadata["summary"],
        }

    except Exception as e:
        return {"error": str(e)}


def get_metadata(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve cached codebase metadata.

    Args:
        cache: Cache file path (default: ".agentic_executor/metadata.json")
        type: Metadata type - "structure", "imports", "summary", or "all" (default: "all")
        filter: Optional filter dict (e.g., {"file": "path/to/file.py"})

    Returns:
        Requested metadata subset
    """
    cache_path = args.get("cache", ".agentic_executor/metadata.json")
    metadata_type = args.get("type", "all")
    filter_spec = args.get("filter", {})

    if not os.path.exists(cache_path):
        return {"error": f"Cache not found: {cache_path} (CWD: {os.getcwd()}). Run 'scan_codebase' first."}

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        # Check if cache is stale (files changed since scan)
        scan_time = metadata.get("scan_timestamp", 0)
        current_time = time.time()
        age_minutes = (current_time - scan_time) / 60
        is_stale = age_minutes > 60  # Stale if older than 1 hour

        result = {
            "cached_at": scan_time,
            "age_minutes": round(age_minutes, 2),
            "is_stale": is_stale
        }

        # Apply filters
        if filter_spec.get("file"):
            file_path = filter_spec["file"]
            if metadata_type == "structure" or metadata_type == "all":
                result["file_data"] = metadata["files"].get(file_path, {})
            if metadata_type == "imports" or metadata_type == "all":
                result["import_data"] = metadata["imports"].get(file_path, {})
            return result

        # Return full metadata by type
        if metadata_type == "structure":
            result["files"] = metadata["files"]
        elif metadata_type == "imports":
            result["imports"] = metadata["imports"]
        elif metadata_type == "summary":
            result["summary"] = metadata["summary"]
        else:  # "all"
            result["files"] = metadata["files"]
            result["imports"] = metadata["imports"]
            result["summary"] = metadata["summary"]

        return result

    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# COMMAND REGISTRY
# ═══════════════════════════════════════════════════════════════════════

COMMANDS = {
    # Filesystem
    "read": read_file,
    "write": write_file,
    "copy": copy_file,
    "move": move_file,
    "delete": delete_file,
    "mkdir": make_directory,
    "ls": list_directory,
    "replace": replace_in_file,

    # Process execution
    "run": run_command,

    # Utilities
    "search": search_files,
    "info": get_file_info,
    "grep": grep_files,

    # Codebase analysis
    "scan_codebase": scan_codebase,
    "get_metadata": get_metadata,
}

COMMAND_DESCRIPTIONS = {
    "read": "Read file contents",
    "write": "Write content to file",
    "copy": "Copy file or directory",
    "move": "Move/rename file or directory",
    "delete": "Delete file or directory",
    "mkdir": "Create directory",
    "ls": "List directory contents",
    "replace": "Replace text in file",
    "run": "Execute shell command",
    "search": "Search for files by pattern",
    "info": "Get file/directory metadata",
    "grep": "Search for text in files",
    "scan_codebase": "Scan codebase and generate metadata cache",
    "get_metadata": "Retrieve cached codebase metadata",
}


# ═══════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════

__all__ = ['COMMANDS', 'COMMAND_DESCRIPTIONS']
