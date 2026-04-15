#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════
AGENTIC EXECUTOR — INSTALLER
═══════════════════════════════════════════════════════════════════════

One-stop installer: downloads language parsers and activates the
/exec skill in your AI agent of choice.

QUICK START (after pip install):
    exec-install                        # Install for Claude Code
    exec-install --agent cursor         # Install for Cursor
    exec-install --agent all            # Install for all agents
    exec-install --languages            # Install tree-sitter parsers
    exec-install --full                 # Languages + Claude Code skill
    exec-install --list                 # Show status

SUPPORTED AGENTS:
    claude-code     ~/.claude/skills/exec/skill.md
    cursor          ~/.cursor/rules/exec.mdc           (alwaysApply: false)
    windsurf        ~/.windsurf/memories/exec.md
    kiro            ~/.kiro/skills/exec/skill.md       (inclusion: always)
    codex           ~/.agents/skills/exec/skill.md
    copilot         ~/.copilot/skills/exec/skill.md
    opencode        ~/.config/opencode/skills/exec/skill.md
    aider           ~/.aider/skills/exec/skill.md
    claw            ~/.openclaw/skills/exec/skill.md
    hermes          ~/.hermes/skills/exec/skill.md
    trae            ~/.trae/skills/exec/skill.md
    droid           ~/.factory/skills/exec/skill.md
    global          ~/.agentic/skills/exec/skill.md

═══════════════════════════════════════════════════════════════════════
"""

import os
import sys
import shutil
import argparse
import subprocess
from pathlib import Path


# ── Skill sources ─────────────────────────────────────────────────────
_ROOT = Path(__file__).parent
_SKILL_DIR = _ROOT / "skills" / "exec"

_SKILL_FILES = {
    "default": _SKILL_DIR / "skill.md",
    "cursor":  _SKILL_DIR / "skill-cursor.mdc",
    "kiro":    _SKILL_DIR / "skill-kiro.md",
}

# ── Agent destinations ─────────────────────────────────────────────────
_AGENTS = {
    "claude-code": {
        "skill": "default",
        "path": Path.home() / ".claude" / "skills" / "exec" / "skill.md",
        "label": "Claude Code",
        "activate": "Type /exec in Claude Code",
    },
    "cursor": {
        "skill": "cursor",
        "path": Path.home() / ".cursor" / "rules" / "exec.mdc",
        "label": "Cursor",
        "activate": "Available automatically in every Cursor project",
    },
    "windsurf": {
        "skill": "default",
        "path": Path.home() / ".windsurf" / "memories" / "exec.md",
        "label": "Windsurf",
        "activate": "Available automatically in Windsurf",
    },
    "kiro": {
        "skill": "kiro",
        "path": Path.home() / ".kiro" / "skills" / "exec" / "skill.md",
        "label": "Kiro",
        "activate": "Available automatically in every Kiro project",
    },
    "codex": {
        "skill": "default",
        "path": Path.home() / ".agents" / "skills" / "exec" / "skill.md",
        "label": "Codex",
        "activate": "Type /exec in Codex",
    },
    "copilot": {
        "skill": "default",
        "path": Path.home() / ".copilot" / "skills" / "exec" / "skill.md",
        "label": "GitHub Copilot",
        "activate": "Type /exec in Copilot",
    },
    "opencode": {
        "skill": "default",
        "path": Path.home() / ".config" / "opencode" / "skills" / "exec" / "skill.md",
        "label": "OpenCode",
        "activate": "Type /exec in OpenCode",
    },
    "aider": {
        "skill": "default",
        "path": Path.home() / ".aider" / "skills" / "exec" / "skill.md",
        "label": "Aider",
        "activate": "Type /exec in Aider",
    },
    "claw": {
        "skill": "default",
        "path": Path.home() / ".openclaw" / "skills" / "exec" / "skill.md",
        "label": "OpenClaw",
        "activate": "Type /exec in OpenClaw",
    },
    "hermes": {
        "skill": "default",
        "path": Path.home() / ".hermes" / "skills" / "exec" / "skill.md",
        "label": "Hermes",
        "activate": "Type /exec in Hermes",
    },
    "trae": {
        "skill": "default",
        "path": Path.home() / ".trae" / "skills" / "exec" / "skill.md",
        "label": "Trae",
        "activate": "Type /exec in Trae",
    },
    "droid": {
        "skill": "default",
        "path": Path.home() / ".factory" / "skills" / "exec" / "skill.md",
        "label": "Factory Droid",
        "activate": "Type /exec in Factory Droid",
    },
    "global": {
        "skill": "default",
        "path": Path.home() / ".agentic" / "skills" / "exec" / "skill.md",
        "label": "Global (~/.agentic/)",
        "activate": "Point any agent to ~/.agentic/skills/exec/skill.md",
    },
}

# ── Tree-sitter language packages ──────────────────────────────────────
# Basic: the languages most repos use
_LANGUAGES_BASIC = [
    "tree-sitter>=0.23.0",
    "tree-sitter-python",
    "tree-sitter-javascript",
    "tree-sitter-typescript",
    "tree-sitter-go",
    "tree-sitter-rust",
    "tree-sitter-java",
    "tree-sitter-c",
    "tree-sitter-cpp",
]

# Full: all supported languages
_LANGUAGES_FULL = _LANGUAGES_BASIC + [
    "tree-sitter-ruby",
    "tree-sitter-c-sharp",
    "tree-sitter-kotlin",
    "tree-sitter-scala",
    "tree-sitter-php",
    "tree-sitter-swift",
    "tree-sitter-lua",
]


# ── Colours (optional, degrades gracefully) ────────────────────────────
def _c(text: str, code: str) -> str:
    if sys.stdout.isatty():
        return f"\033[{code}m{text}\033[0m"
    return text

OK   = lambda t: _c(t, "32")   # green
ERR  = lambda t: _c(t, "31")   # red
DIM  = lambda t: _c(t, "2")    # dim
BOLD = lambda t: _c(t, "1")    # bold
HEAD = lambda t: _c(t, "36")   # cyan


def _check(ok: bool) -> str:
    return OK("+") if ok else ERR("-")


# ── Language installer ─────────────────────────────────────────────────

def install_languages(full: bool = False, quiet: bool = False) -> bool:
    """
    Install tree-sitter language packages via pip.

    Args:
        full:  Install all 16 languages (default: 9 basic ones)
        quiet: Suppress verbose output

    Returns:
        True if all packages installed successfully
    """
    pkgs = _LANGUAGES_FULL if full else _LANGUAGES_BASIC
    level = "full (16 languages)" if full else "basic (9 languages)"

    if not quiet:
        print(f"\n{BOLD('Installing tree-sitter language parsers')} [{level}]")
        print(DIM("  This enables accurate code analysis for 20+ languages.\n"))

    cmd = [sys.executable, "-m", "pip", "install", "--quiet"] + pkgs

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            if not quiet:
                print(f"  [{OK('+')}] Installed {len(pkgs)} packages")
                print(DIM(f"  Packages: {', '.join(p.split('>=')[0].split('[')[0] for p in pkgs)}"))
            return True
        else:
            print(f"  [{ERR('-')}] pip failed:\n{result.stderr[:400]}")
            return False
    except Exception as e:
        print(f"  [{ERR('-')}] Error: {e}")
        return False


def check_languages() -> dict:
    """Return dict of {package: installed} for all language packages."""
    status = {}
    for pkg in _LANGUAGES_FULL:
        name = pkg.split(">=")[0]
        import_name = name.replace("-", "_")
        try:
            __import__(import_name)
            status[name] = True
        except ImportError:
            status[name] = False
    return status


# ── Skill installer ────────────────────────────────────────────────────

def install_skill(agent: str = "claude-code", quiet: bool = False) -> bool:
    """Install the /exec skill for the specified agent."""
    config = _AGENTS.get(agent)
    if not config:
        print(f"  [{ERR('-')}] Unknown agent: {agent}. Choices: {', '.join(_AGENTS)}")
        return False

    skill_src = _SKILL_FILES[config["skill"]]
    if not skill_src.exists():
        print(f"  [{ERR('-')}] skill file not found at {skill_src}")
        print("  Make sure you installed from source: git clone + pip install -e .")
        return False

    dest: Path = config["path"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(skill_src, dest)

    if not quiet:
        print(f"  [{OK('+')}] {config['label']:14}  →  {dest}")
        print(f"  {DIM('Activate:')} {config['activate']}")

    return True


def uninstall_skill(agent: str = "claude-code", quiet: bool = False) -> bool:
    """Remove the /exec skill from the specified agent."""
    config = _AGENTS.get(agent)
    if not config:
        print(f"  [{ERR('-')}] Unknown agent: {agent}")
        return False

    dest: Path = config["path"]
    if not dest.exists():
        if not quiet:
            print(f"  [=] {config['label']:12}  not installed (nothing to remove)")
        return True

    dest.unlink()
    if not quiet:
        print(f"  [{OK('+')}] Removed from {config['label']} ({dest})")
    return True


# ── Status display ─────────────────────────────────────────────────────

def show_status():
    """Print a full status report: skills + language parsers."""
    print(f"\n{HEAD(BOLD('Agentic Executor — /exec status'))}\n")

    # Skills
    print(BOLD("  Skill installations:"))
    for agent, config in _AGENTS.items():
        installed = config["path"].exists()
        print(f"    [{_check(installed)}] {agent:12}  {DIM(str(config['path']))}")

    # Languages
    print(f"\n{BOLD('  Language parsers (tree-sitter):')}")
    lang_status = check_languages()
    installed_count = sum(lang_status.values())
    for pkg, ok in lang_status.items():
        print(f"    [{_check(ok)}] {pkg}")
    print(f"\n    {installed_count}/{len(lang_status)} parsers installed")
    if installed_count == 0:
        print(DIM("    Run: exec-install --languages   (or --full for all 16)"))
    print()


# ── Main ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="exec-install",
        description="Install the /exec skill and language parsers for AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{BOLD('Examples:')}
  exec-install                          Install for Claude Code (default)
  exec-install --agent cursor           Install for Cursor
  exec-install --agent kiro             Install for Kiro
  exec-install --agent all              Install for all agents
  exec-install --languages              Install 9 basic tree-sitter parsers
  exec-install --languages --full       Install all 16 parsers
  exec-install --full                   Languages + Claude Code skill
  exec-install --list                   Show installation status
  exec-install --uninstall              Remove from Claude Code
  exec-install --uninstall --agent all  Remove from all agents

{BOLD('Supported agents:')}
  claude-code  cursor  windsurf  kiro  codex  copilot
  opencode  aider  claw  hermes  trae  droid  global

{BOLD('After install, use the skill:')}
  python -m agentic_executor.cli --thought-stdin <<'EOF'
  result = execute('scan_codebase', {{'path': '.'}})
  print(result['data']['languages'])
  EOF
        """,
    )

    parser.add_argument(
        "--agent", "-a",
        default="claude-code",
        choices=list(_AGENTS.keys()) + ["all"],
        metavar="AGENT",
        help=f"Target agent: {', '.join(_AGENTS)} or 'all'  (default: claude-code)",
    )
    parser.add_argument(
        "--languages", "-l",
        action="store_true",
        help="Install tree-sitter language parsers (9 basic languages)",
    )
    parser.add_argument(
        "--full", "-f",
        action="store_true",
        help="Install ALL 16 tree-sitter parsers + skill (implies --languages)",
    )
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Remove the skill instead of installing it",
    )
    parser.add_argument(
        "--list", "--status",
        action="store_true",
        dest="status",
        help="Show installation status for skills and parsers",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress output",
    )
    parser.add_argument(
        "--no-skill",
        action="store_true",
        help="Install languages only, skip skill deployment",
    )

    args = parser.parse_args()

    # ── Status ───────────────────────────────────────────────────────
    if args.status:
        show_status()
        return

    success = True

    # ── Language parsers ─────────────────────────────────────────────
    if args.languages or args.full:
        ok = install_languages(full=args.full, quiet=args.quiet)
        if not ok:
            success = False

    # ── Skill deployment ─────────────────────────────────────────────
    if not args.no_skill:
        targets = list(_AGENTS.keys()) if args.agent == "all" else [args.agent]

        if not args.quiet and not args.uninstall:
            print(f"\n{BOLD('Installing /exec skill:')}")

        for target in targets:
            if args.uninstall:
                ok = uninstall_skill(target, quiet=args.quiet)
            else:
                ok = install_skill(target, quiet=args.quiet)
            if not ok:
                success = False

    # ── Success banner ───────────────────────────────────────────────
    if success and not args.quiet and not args.uninstall and not args.status:
        print(f"\n{OK(BOLD('Done!'))} Agentic Executor is ready.\n")
        if not args.no_skill:
            agent_label = "all agents" if args.agent == "all" else _AGENTS.get(args.agent, {}).get("label", args.agent)
            print(f"  Skill activated for: {agent_label}")
        if args.languages or args.full:
            print(f"  Language parsers: installed")
        print(f"\n  Quick test:")
        print(DIM("  python -m agentic_executor.cli --thought-stdin <<'EOF'"))
        print(DIM("  result = execute('scan_codebase', {'path': '.'})"))
        print(DIM("  print(result['data']['languages'])"))
        print(DIM("  EOF"))
        print()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
