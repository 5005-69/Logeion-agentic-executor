#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
AGENTIC EXECUTOR - CLI INTERFACE
═══════════════════════════════════════════════════════════════════════

Single interface: --thought (Python code execution με execute() function)

Usage:
    # Single command
    python -m agentic_executor.cli --thought "
    result = execute('read', {'path': 'file.txt'})
    print(result)
    "

    # Multiple commands
    python -m agentic_executor.cli --thought "
    execute('scan_codebase', {'path': '.'})
    metadata = execute('get_metadata', {'type': 'summary'})
    print(metadata['data'])
    "

    # Complex workflow via stdin (recommended for multi-line)
    python -m agentic_executor.cli --thought-stdin <<'EOF'
    files = execute('search', {'pattern': '*.py'})
    for f in files['data']['files'][:5]:
        content = execute('read', {'path': f, 'lines': 10})
        print(f'=== {f} ===')
        print(content['data'])
    EOF

    # Show available commands
    python -m agentic_executor.cli --help-commands

VERSION: v1.0.0 (Pure Thought Execution)
"""

import sys
import argparse
import json
import os
import io

# ═══════════════════════════════════════════════════════════════════════
# AUTO-FIX: Force UTF-8 encoding ALWAYS (cross-platform consistency)
# ═══════════════════════════════════════════════════════════════════════

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    sys.stdin.reconfigure(encoding='utf-8', errors='replace')
elif hasattr(sys.stdout, 'buffer'):
    if not isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    if not isinstance(sys.stderr, io.TextIOWrapper):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    if not isinstance(sys.stdin, io.TextIOWrapper):
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace', line_buffering=True)

from .code_parts.executor import execute, get_available_commands


# ═══════════════════════════════════════════════════════════════════════
# THOUGHT EXECUTION
# ═══════════════════════════════════════════════════════════════════════

def execute_thought(thought_code: str, verbose: bool = True):
    """
    Execute Python code with execute() function available.

    This is the CORE of the CLI - executes arbitrary Python code
    with access to the execute() function for running commands.

    Args:
        thought_code: Python code string
        verbose: Print execution details
    """
    if verbose:
        print(f"\n{'='*70}")
        print(f"EXECUTING THOUGHT")
        print(f"{'='*70}\n")

    def safe_print(*args, **kwargs):
        """Print with UTF-8 encoding for Greek/emoji characters"""
        try:
            print(*args, **kwargs)
        except UnicodeEncodeError:
            safe_args = []
            for arg in args:
                if isinstance(arg, str):
                    safe_args.append(arg.encode('utf-8', errors='replace').decode('utf-8'))
                else:
                    safe_args.append(arg)
            print(*safe_args, **kwargs)

    namespace = {
        'execute': execute,
        'get_available_commands': get_available_commands,
        'json': json,
        'os': os,
        'print': safe_print,
    }

    try:
        exec(thought_code, namespace)

        if verbose:
            print(f"\n{'='*70}")
            print(f"THOUGHT EXECUTED SUCCESSFULLY")
            print(f"{'='*70}\n")

    except Exception as e:
        if verbose:
            print(f"\n{'='*70}")
            print(f"EXECUTION ERROR")
            print(f"{'='*70}")
            print(f"\nError: {e}\n")

        import traceback
        traceback.print_exc()

        error_msg = str(e)
        if "SyntaxError" in error_msg or "EOF" in error_msg:
            if "'" in thought_code and '"' in thought_code:
                print("\nSUGGESTION: Quote Escaping Issue Detected")
                print("   Your code has both single (') and double (\") quotes.")
                print("   Use --thought-stdin with <<'EOF' to avoid bash parsing issues.")

        if verbose:
            print(f"\n{'='*70}\n")

        raise


def show_available_commands():
    """Show all available execute() commands."""
    print("\n" + "="*70)
    print("AVAILABLE COMMANDS")
    print("="*70 + "\n")

    commands = get_available_commands()

    categories = {
        "Filesystem": ["read", "write", "copy", "move", "delete", "mkdir", "ls", "replace"],
        "Process": ["run"],
        "Search": ["search", "info", "grep"],
        "Metadata": ["scan_codebase", "get_metadata"]
    }

    for category, cmd_list in categories.items():
        print(f"  {category}:")
        for cmd in cmd_list:
            if cmd in commands:
                print(f"    {cmd:20} - {commands[cmd]}")
        print()

    print("="*70)
    print("\nUsage:")
    print("  result = execute('command_name', {'arg': 'value'})")
    print("\nExample:")
    print("  result = execute('read', {'path': 'file.txt', 'lines': 10})")
    print("  print(result['data'])")
    print("\n" + "="*70 + "\n")


# ═══════════════════════════════════════════════════════════════════════
# JSON OUTPUT MODE - Subprocess interface
# ═══════════════════════════════════════════════════════════════════════

def _execute_thought_json(thought_code: str):
    """
    Execute thought and emit a single JSON result to stdout.

    Output format:
        {"success": true, "output": "...", "error": null}
        {"success": false, "output": "", "error": "..."}
    """
    import io as _io
    import traceback as _traceback

    captured = _io.StringIO()

    namespace = {
        'execute': execute,
        'get_available_commands': get_available_commands,
        'json': json,
        'os': os,
        'print': lambda *a, **kw: print(*a, **kw, file=captured),
    }

    try:
        exec(thought_code, namespace)
        output = captured.getvalue()
        result = {"success": True, "output": output, "error": None}
    except Exception as e:
        output = captured.getvalue()
        result = {
            "success": False,
            "output": output,
            "error": f"{type(e).__name__}: {str(e)}",
            "traceback": _traceback.format_exc()
        }

    print(json.dumps(result, ensure_ascii=False), flush=True)


# ═══════════════════════════════════════════════════════════════════════
# MAIN CLI
# ═══════════════════════════════════════════════════════════════════════

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Agentic Executor - Execute Python code with execute() function",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES
═══════════════════════════════════════════════════════════════════════

1. Single Command:
   python -m agentic_executor.cli --thought "
   result = execute('read', {'path': 'README.md', 'lines': 10})
   print(result['data'])
   "

2. Scan Codebase:
   python -m agentic_executor.cli --thought "
   execute('scan_codebase', {'path': '.'})
   meta = execute('get_metadata', {'type': 'summary'})
   print(meta['data'])
   "

3. Complex Workflow (recommended for multi-line):
   python -m agentic_executor.cli --thought-stdin <<'EOF'
   files = execute('search', {'pattern': '*.py'})
   for f in files['data']['files'][:5]:
       content = execute('read', {'path': f, 'lines': 10})
       print(f'=== {f} ===')
       print(content['data'])
   EOF

4. Show Commands:
   python -m agentic_executor.cli --help-commands

═══════════════════════════════════════════════════════════════════════
        """
    )

    parser.add_argument(
        "--thought",
        help="Python code to execute (use execute() function for commands)"
    )

    parser.add_argument(
        "--thought-stdin",
        action="store_true",
        help="Read thought from stdin (avoids bash quote issues)"
    )

    parser.add_argument(
        "--help-commands",
        action="store_true",
        help="Show all available execute() commands"
    )

    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Emit result as a single JSON object to stdout"
    )

    args = parser.parse_args()

    # Read from stdin if --thought-stdin specified
    if args.thought_stdin:
        if hasattr(sys.stdin, 'reconfigure'):
            sys.stdin.reconfigure(encoding='utf-8', errors='replace')

        raw_input = sys.stdin.read()

        import re
        lines = raw_input.split('\n')
        fixed_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                fixed_lines.append(line)
                continue

            if stripped.endswith(':")') or stripped.endswith("':"):
                if fixed_lines and 'print("' in fixed_lines[-1]:
                    fixed_lines[-1] = fixed_lines[-1].rstrip() + '\\n' + stripped
                    continue

            fixed_lines.append(line)

        args.thought = '\n'.join(fixed_lines)

    if args.help_commands:
        show_available_commands()
        return

    if args.thought:
        if args.json_output:
            _execute_thought_json(args.thought)
        else:
            execute_thought(args.thought, verbose=True)
        return

    parser.print_help()


if __name__ == "__main__":
    main()


__all__ = ['main', 'execute_thought', 'show_available_commands']
