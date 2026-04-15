"""
Tests for exec-install skill deployment.

Verifies that:
- The correct target path for Claude Code is ~/.claude/commands/exec.md
- install_skill() copies the skill file to the right place
- The installed content is valid (has the expected frontmatter)
- uninstall_skill() removes the file cleanly
- Re-install over an existing file succeeds
"""

import shutil
from pathlib import Path

import pytest

from agentic_executor.install import _AGENTS, _SKILL_FILES, install_skill, uninstall_skill


# ── helpers ────────────────────────────────────────────────────────────────

def _patch_agent_path(monkeypatch, agent: str, tmp_path: Path) -> Path:
    """Redirect the agent's install path into a temp directory."""
    original = _AGENTS[agent]["path"]
    fake = tmp_path / original.relative_to(Path.home())
    new_agents = {k: dict(v) for k, v in _AGENTS.items()}
    new_agents[agent]["path"] = fake
    monkeypatch.setattr("agentic_executor.install._AGENTS", new_agents)
    return fake


# ── path contract ──────────────────────────────────────────────────────────

def test_claude_code_target_path():
    """Claude Code skill must land in ~/.claude/commands/exec.md — not skills/."""
    path = _AGENTS["claude-code"]["path"]
    assert path == Path.home() / ".claude" / "commands" / "exec.md", (
        f"Wrong install path: {path}\n"
        "Claude Code reads slash commands from ~/.claude/commands/, not ~/.claude/skills/"
    )


def test_claude_code_path_is_flat_md():
    """The target file must be a plain .md file, not nested under a subdirectory."""
    path = _AGENTS["claude-code"]["path"]
    # parent should be ~/.claude/commands  (no extra subfolder)
    assert path.parent == Path.home() / ".claude" / "commands"
    assert path.suffix == ".md"
    assert path.name == "exec.md"


# ── source file ────────────────────────────────────────────────────────────

def test_skill_source_exists():
    """The skill.md file must exist inside the installed package."""
    src = _SKILL_FILES["default"]
    assert src.exists(), f"Skill source not found: {src}"


def test_skill_source_has_frontmatter():
    """skill.md must start with valid YAML frontmatter containing 'name: exec'."""
    src = _SKILL_FILES["default"]
    content = src.read_text(encoding="utf-8")
    assert content.startswith("---"), "skill.md must start with '---' frontmatter"
    assert "name: exec" in content, "skill.md frontmatter must declare 'name: exec'"


# ── install / uninstall ────────────────────────────────────────────────────

def test_install_creates_file(monkeypatch, tmp_path):
    """install_skill() must create the destination file."""
    dest = _patch_agent_path(monkeypatch, "claude-code", tmp_path)
    result = install_skill("claude-code", quiet=True)
    assert result is True
    assert dest.exists(), f"Expected skill file at {dest}"


def test_install_creates_parent_dirs(monkeypatch, tmp_path):
    """install_skill() must create all parent directories automatically."""
    dest = _patch_agent_path(monkeypatch, "claude-code", tmp_path)
    assert not dest.parent.exists()
    install_skill("claude-code", quiet=True)
    assert dest.parent.is_dir()


def test_installed_content_matches_source(monkeypatch, tmp_path):
    """The installed file must be a byte-for-byte copy of the source skill."""
    dest = _patch_agent_path(monkeypatch, "claude-code", tmp_path)
    install_skill("claude-code", quiet=True)
    src = _SKILL_FILES["default"]
    assert dest.read_text(encoding="utf-8") == src.read_text(encoding="utf-8")


def test_install_overwrites_existing(monkeypatch, tmp_path):
    """Re-installing must silently overwrite a stale or corrupt existing file."""
    dest = _patch_agent_path(monkeypatch, "claude-code", tmp_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("stale content", encoding="utf-8")
    result = install_skill("claude-code", quiet=True)
    assert result is True
    src = _SKILL_FILES["default"]
    assert dest.read_text(encoding="utf-8") == src.read_text(encoding="utf-8")


def test_uninstall_removes_file(monkeypatch, tmp_path):
    """uninstall_skill() must delete the installed file."""
    dest = _patch_agent_path(monkeypatch, "claude-code", tmp_path)
    install_skill("claude-code", quiet=True)
    assert dest.exists()
    result = uninstall_skill("claude-code", quiet=True)
    assert result is True
    assert not dest.exists()


def test_uninstall_is_idempotent(monkeypatch, tmp_path):
    """Calling uninstall when nothing is installed must succeed without error."""
    _patch_agent_path(monkeypatch, "claude-code", tmp_path)
    result = uninstall_skill("claude-code", quiet=True)
    assert result is True


# ── unknown agent ──────────────────────────────────────────────────────────

def test_install_unknown_agent(capsys):
    """install_skill() must return False and print an error for unknown agents."""
    result = install_skill("nonexistent-agent", quiet=False)
    assert result is False
    captured = capsys.readouterr()
    assert "Unknown agent" in captured.out


# ── all agents have required keys ─────────────────────────────────────────

@pytest.mark.parametrize("agent", list(_AGENTS.keys()))
def test_all_agents_have_required_keys(agent):
    """Every agent entry must have skill, path, label, and activate keys."""
    config = _AGENTS[agent]
    for key in ("skill", "path", "label", "activate"):
        assert key in config, f"Agent '{agent}' missing key '{key}'"


@pytest.mark.parametrize("agent", list(_AGENTS.keys()))
def test_all_agents_reference_valid_skill_file(agent):
    """Every agent must reference a skill variant that actually exists on disk."""
    config = _AGENTS[agent]
    skill_key = config["skill"]
    assert skill_key in _SKILL_FILES, (
        f"Agent '{agent}' references unknown skill variant '{skill_key}'"
    )
    src = _SKILL_FILES[skill_key]
    assert src.exists(), f"Skill file for variant '{skill_key}' not found: {src}"
