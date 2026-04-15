#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
AGENTIC EXECUTOR - CORE EXECUTOR
═══════════════════════════════════════════════════════════════════════

Generic command executor for agentic systems.

Philosophy:
- Model thinks in high-level commands: execute("read", {...})
- Executor translates to real operations
- Domain-agnostic, works everywhere
- Simple, safe, extensible

VERSION: v0.1.0 (Initial Implementation)
"""

from typing import Dict, Any, Optional
from .commands import COMMANDS


def execute(command: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a high-level command.

    This is the CORE function that agentic systems use.

    Args:
        command: Command name (e.g., "read", "write", "run")
        args: Command arguments as dict

    Returns:
        Result dict με structure:
        {
            "success": bool,
            "data": Any,           # Command-specific data
            "error": str | None,   # Error message if failed
            "command": str,        # Echo of command
            "args": dict           # Echo of args
        }

    Examples:
        >>> execute("read", {"path": "file.txt", "lines": 10})
        {"success": True, "data": {"lines": [...]}, "error": None}

        >>> execute("run", {"cmd": "python script.py"})
        {"success": True, "data": {"stdout": "..."}, "error": None}

        >>> execute("copy", {"src": "a.txt", "dst": "b.txt"})
        {"success": True, "data": {"status": "ok"}, "error": None}
    """
    # Validate command exists
    if command not in COMMANDS:
        return {
            "success": False,
            "data": None,
            "error": f"Unknown command '{command}'. Available: {list(COMMANDS.keys())}",
            "command": command,
            "args": args
        }

    # Execute command
    try:
        command_func = COMMANDS[command]
        result = command_func(args)

        # Check if command returned an error
        if isinstance(result, dict) and "error" in result and result["error"]:
            # Command failed gracefully - return as error
            return {
                "success": False,
                "data": None,
                "error": result["error"],
                "command": command,
                "args": args
            }

        # Wrap result in standard format
        return {
            "success": True,
            "data": result,
            "error": None,
            "command": command,
            "args": args
        }

    except Exception as e:
        # Catch any execution errors
        return {
            "success": False,
            "data": None,
            "error": f"{type(e).__name__}: {str(e)}",
            "command": command,
            "args": args
        }


def execute_batch(commands: list) -> list:
    """
    Execute multiple commands in sequence.

    Args:
        commands: List of (command, args) tuples

    Returns:
        List of results (one per command)

    Example:
        >>> execute_batch([
        ...     ("read", {"path": "file.txt"}),
        ...     ("copy", {"src": "a.txt", "dst": "b.txt"}),
        ...     ("run", {"cmd": "python test.py"})
        ... ])
    """
    results = []
    for cmd, args in commands:
        result = execute(cmd, args)
        results.append(result)

        # Stop on first error (optional behavior)
        if not result["success"]:
            break

    return results


def get_available_commands() -> Dict[str, str]:
    """
    Get list of available commands με descriptions.

    Returns:
        Dict mapping command name to description
    """
    from .commands import COMMAND_DESCRIPTIONS
    return COMMAND_DESCRIPTIONS


# ═══════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════

__all__ = ['execute', 'execute_batch', 'get_available_commands']
