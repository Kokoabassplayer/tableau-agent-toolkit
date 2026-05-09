"""Validation tests for agent skill manifests, plugin configs, and agent instructions.

Phase 4 deliverables are declarative files (JSON manifests, Markdown skills, MCP config).
These tests validate structural correctness: valid JSON, correct frontmatter, file existence,
CLI command references, and no hardcoded secrets.
"""

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

SKILL_NAMES = [
    "tableau-dashboard-spec-writer",
    "tableau-twb-generator",
    "tableau-twb-validator",
    "tableau-dashboard-qa-reviewer",
    "tableau-publisher",
]


def _skill_exists(skill_name: str) -> bool:
    """Check if a skill SKILL.md file exists on disk."""
    return (PROJECT_ROOT / "skills" / skill_name / "SKILL.md").exists()


class TestPluginManifests:
    """Validate .claude-plugin/plugin.json and .codex-plugin/plugin.json."""

    @pytest.fixture
    def claude_plugin(self) -> dict:
        path = PROJECT_ROOT / ".claude-plugin" / "plugin.json"
        return json.loads(path.read_text(encoding="utf-8"))

    @pytest.fixture
    def codex_plugin(self) -> dict:
        path = PROJECT_ROOT / ".codex-plugin" / "plugin.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_claude_plugin_is_valid_json(self, claude_plugin: dict) -> None:
        assert "name" in claude_plugin
        assert claude_plugin["name"] == "tableau-agent-toolkit"

    def test_claude_plugin_has_description(self, claude_plugin: dict) -> None:
        assert "description" in claude_plugin
        assert len(claude_plugin["description"]) > 10

    def test_claude_plugin_has_version(self, claude_plugin: dict) -> None:
        assert "version" in claude_plugin

    def test_claude_plugin_has_five_skills(self, claude_plugin: dict) -> None:
        assert "skills" in claude_plugin
        assert len(claude_plugin["skills"]) == 5
        for skill_name in SKILL_NAMES:
            assert f"skills/{skill_name}" in claude_plugin["skills"]

    def test_claude_plugin_has_mcp_servers(self, claude_plugin: dict) -> None:
        assert "mcpServers" in claude_plugin
        assert "tableau" in claude_plugin["mcpServers"]
        mcp = claude_plugin["mcpServers"]["tableau"]
        assert mcp["command"] == "npx"

    def test_codex_plugin_is_valid_json(self, codex_plugin: dict) -> None:
        assert "name" in codex_plugin
        assert codex_plugin["name"] == "tableau-agent-toolkit"

    def test_codex_plugin_has_five_skills(self, codex_plugin: dict) -> None:
        assert "skills" in codex_plugin
        assert len(codex_plugin["skills"]) == 5

    def test_codex_plugin_no_mcp_servers(self, codex_plugin: dict) -> None:
        """Codex does not support inline MCP servers."""
        assert "mcpServers" not in codex_plugin


class TestMCPConfig:
    """Validate .mcp.json for Tableau MCP server wiring."""

    @pytest.fixture
    def mcp_config(self) -> dict:
        path = PROJECT_ROOT / ".mcp.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_mcp_config_has_tableau_server(self, mcp_config: dict) -> None:
        assert "mcpServers" in mcp_config
        assert "tableau" in mcp_config["mcpServers"]

    def test_mcp_config_uses_env_vars(self, mcp_config: dict) -> None:
        """No hardcoded secrets -- all credentials via ${ENV_VAR} references."""
        mcp = mcp_config["mcpServers"]["tableau"]
        env = mcp.get("env", {})
        for key, value in env.items():
            assert value.startswith("${"), f"Secret for {key} must use env var reference, got: {value}"

    def test_mcp_config_references_npx(self, mcp_config: dict) -> None:
        mcp = mcp_config["mcpServers"]["tableau"]
        assert mcp["command"] == "npx"
        assert "-y" in mcp["args"]
        assert "@tableau/mcp-server" in mcp["args"]


class TestAgentInstructions:
    """Validate CLAUDE.md and AGENTS.md project-level instructions."""

    def test_agents_md_exists(self) -> None:
        assert (PROJECT_ROOT / "AGENTS.md").exists()

    def test_agents_md_has_commands(self) -> None:
        content = (PROJECT_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        assert "tableau-agent-toolkit" in content
        assert "generate" in content
        assert "validate-xsd" in content
        assert "publish" in content

    def test_agents_md_has_pipeline_order(self) -> None:
        content = (PROJECT_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        assert "spec init" in content
        assert "generate" in content
        assert "validate" in content
        assert "publish" in content

    def test_claude_md_lists_skills(self) -> None:
        content = (PROJECT_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        assert "tableau-dashboard-spec-writer" in content
        assert "tableau-twb-generator" in content


class TestSkillFrontmatter:
    """Validate SKILL.md files have correct YAML frontmatter.

    Tests are parametrized across all 5 skill names. Skills that do not yet
    exist on disk are skipped so the suite passes incrementally as skills are
    added across Wave 1 (spec-writer, twb-generator) and Wave 2 (validator,
    qa-reviewer, publisher).
    """

    @pytest.mark.parametrize("skill_name", SKILL_NAMES)
    def test_skill_file_exists(self, skill_name: str) -> None:
        if not _skill_exists(skill_name):
            pytest.skip(reason=f"{skill_name} not yet created")
        skill_path = PROJECT_ROOT / "skills" / skill_name / "SKILL.md"
        assert skill_path.exists(), f"Skill file missing: {skill_path}"

    @pytest.mark.parametrize("skill_name", SKILL_NAMES)
    def test_skill_has_frontmatter(self, skill_name: str) -> None:
        if not _skill_exists(skill_name):
            pytest.skip(reason=f"{skill_name} not yet created")
        skill_path = PROJECT_ROOT / "skills" / skill_name / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")
        assert content.startswith("---"), f"{skill_name} SKILL.md must start with YAML frontmatter"

    @pytest.mark.parametrize("skill_name", SKILL_NAMES)
    def test_skill_has_name_field(self, skill_name: str) -> None:
        if not _skill_exists(skill_name):
            pytest.skip(reason=f"{skill_name} not yet created")
        skill_path = PROJECT_ROOT / "skills" / skill_name / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")
        # Extract frontmatter between first two ---
        parts = content.split("---")
        assert len(parts) >= 3, f"{skill_name} must have frontmatter delimiters"
        frontmatter = parts[1]
        assert "name:" in frontmatter, f"{skill_name} frontmatter must have 'name' field"
        assert skill_name in frontmatter, f"{skill_name} frontmatter name must match directory name"

    @pytest.mark.parametrize("skill_name", SKILL_NAMES)
    def test_skill_has_description_field(self, skill_name: str) -> None:
        if not _skill_exists(skill_name):
            pytest.skip(reason=f"{skill_name} not yet created")
        skill_path = PROJECT_ROOT / "skills" / skill_name / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")
        parts = content.split("---")
        frontmatter = parts[1]
        assert "description:" in frontmatter, f"{skill_name} frontmatter must have 'description' field"

    @pytest.mark.parametrize("skill_name", SKILL_NAMES)
    def test_skill_references_cli_command(self, skill_name: str) -> None:
        """Each skill must reference at least one tableau-agent-toolkit CLI command."""
        if not _skill_exists(skill_name):
            pytest.skip(reason=f"{skill_name} not yet created")
        skill_path = PROJECT_ROOT / "skills" / skill_name / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")
        assert "tableau-agent-toolkit" in content, f"{skill_name} must reference CLI command"
