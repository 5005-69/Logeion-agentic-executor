#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
AGENTIC EXECUTOR
═══════════════════════════════════════════════════════════════════════

Generic agentic system for autonomous task execution.

Philosophy:
- Model thinks in high-level commands
- Executor translates to real operations
- Domain-agnostic, works everywhere
- Simple, safe, extensible

QUICK START:

    # Execute single command
    from agentic_executor import execute
    result = execute("read", {"path": "file.txt"})

    # Execute thought with commands (Python code)
    from agentic_executor import execute_thought
    execute_thought('''
    result = execute('scan_codebase', {'path': '.'})
    print(result)
    ''')

    # CLI usage
    python -m agentic_executor.cli --thought "
    result = execute('read', {'path': 'file.txt'})
    print(result['data'])
    "

ARCHITECTURE:

    agentic_executor/
    ├── cli.py                    # Single --thought interface
    ├── code_parts/
    │   ├── executor.py           # Core execute() function
    │   └── commands.py           # Commands (filesystem + multi-lang metadata)
    └── __init__.py               # Public API

VERSION: v1.0.0 (Pure Thought Execution)
"""

from .code_parts.executor import execute, execute_batch, get_available_commands

__version__ = "1.0.0"

__all__ = [
    'execute',
    'execute_batch',
    'get_available_commands',
    '__version__',
]
