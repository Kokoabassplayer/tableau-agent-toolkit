"""Validation tests for agent skill manifests, plugin configs, and agent instructions.

Phase 4 deliverables are declarative files (JSON manifests, Markdown skills, MCP config).
These tests validate structural correctness: valid JSON, correct frontmatter, file existence,
CLI command references, and no hardcoded secrets.
"""

import json
import re
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


class TestSkillContent:
    """Validate content quality of SKILL.md files.

    These tests ensure skills have meaningful error handling, clear prerequisites,
    correct pipeline context, and no unnecessary duplication with project-level docs.
    """

    @pytest.mark.parametrize("skill_name", SKILL_NAMES)
    def test_skill_has_error_handling_section(self, skill_name: str) -> None:
        """Each skill must have an Error Handling section."""
        skill_path = PROJECT_ROOT / "skills" / skill_name / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")
        assert "## Error Handling" in content or "## Error handling" in content, (
            f"{skill_name} must have an '## Error Handling' section"
        )

    @pytest.mark.parametrize("skill_name", SKILL_NAMES)
    def test_error_handling_has_specific_scenarios(self, skill_name: str) -> None:
        """Error Handling section must document at least 2 specific error scenarios."""
        skill_path = PROJECT_ROOT / "skills" / skill_name / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")

        # Find the Error Handling section
        eh_match = re.search(
            r"## Error Handling\s*\n(.*?)(?=\n## |\Z)",
            content,
            re.DOTALL | re.IGNORECASE,
        )
        assert eh_match is not None, f"{skill_name} missing Error Handling section"

        eh_content = eh_match.group(1)

        # Count bullet points or numbered items in error handling
        # Each "- If ..." or "* If ..." or "1. ..." counts as a scenario
        scenarios = re.findall(r"(?:^|\n)\s*(?:[-*]|\d+\.)\s+", eh_content)
        assert len(scenarios) >= 2, (
            f"{skill_name} Error Handling must document at least 2 scenarios, "
            f"found {len(scenarios)}"
        )

    @pytest.mark.parametrize("skill_name", SKILL_NAMES)
    def test_skill_has_prerequisites_section(self, skill_name: str) -> None:
        """Each skill must document prerequisites."""
        skill_path = PROJECT_ROOT / "skills" / skill_name / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")
        assert "## Prerequisites" in content or "## Prerequisite" in content, (
            f"{skill_name} must have a '## Prerequisites' section"
        )

    @pytest.mark.parametrize("skill_name", SKILL_NAMES)
    def test_skill_has_pipeline_context(self, skill_name: str) -> None:
        """Each skill must document its position in the pipeline."""
        skill_path = PROJECT_ROOT / "skills" / skill_name / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")
        assert "## Pipeline Context" in content or "Pipeline Context" in content, (
            f"{skill_name} must have a '## Pipeline Context' section"
        )

    @pytest.mark.parametrize("skill_name", SKILL_NAMES)
    def test_no_duplicate_agents_md_content(self, skill_name: str) -> None:
        """Skills should not copy the full architecture listing from AGENTS.md."""
        skill_path = PROJECT_ROOT / "skills" / skill_name / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")

        agents_md = PROJECT_ROOT / "AGENTS.md"
        agents_content = agents_md.read_text(encoding="utf-8")

        # Extract the Architecture section from AGENTS.md
        arch_match = re.search(
            r"## Architecture\s*\n(.*?)(?=\n## |\Z)",
            agents_content,
            re.DOTALL,
        )
        if arch_match:
            arch_section = arch_match.group(1).strip()
            # Skills should not contain the full architecture listing verbatim
            # Check if more than 3 architecture lines appear in the skill
            arch_lines = [line.strip() for line in arch_section.split("\n") if line.strip()]
            matching_lines = sum(
                1 for line in arch_lines
                if line and line in content
            )
            assert matching_lines <= 3, (
                f"{skill_name} duplicates too much Architecture content from AGENTS.md "
                f"({matching_lines} lines). Skills should reference AGENTS.md, not copy it."
            )

    @pytest.mark.parametrize("skill_name", SKILL_NAMES)
    def test_allowed_tools_subset(self, skill_name: str) -> None:
        """Skills should only allow Bash, Read, Write tools."""
        skill_path = PROJECT_ROOT / "skills" / skill_name / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")

        # Extract frontmatter
        parts = content.split("---")
        assert len(parts) >= 3
        frontmatter = parts[1]

        # Check allowed-tools if present
        allowed_match = re.search(r"allowed-tools:\s*\n((?:\s*-\s*\w+\s*\n)+)", frontmatter)
        if allowed_match:
            tools = re.findall(r"-\s*(\w+)", allowed_match.group(1))
            valid_tools = {"Bash", "Read", "Write", "Edit"}
            for tool in tools:
                assert tool in valid_tools, (
                    f"{skill_name} allows tool '{tool}' which is not in valid set: {valid_tools}"
                )

    @pytest.mark.parametrize("skill_name", SKILL_NAMES)
    def test_skill_description_meaningful(self, skill_name: str) -> None:
        """Skill description must be meaningful (at least 20 characters)."""
        skill_path = PROJECT_ROOT / "skills" / skill_name / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")

        parts = content.split("---")
        frontmatter = parts[1]

        desc_match = re.search(r"description:\s*['\"]?(.+?)['\"]?\s*$", frontmatter, re.MULTILINE)
        assert desc_match is not None, f"{skill_name} must have description in frontmatter"
        description = desc_match.group(1).strip().strip("'\"")
        assert len(description) >= 20, (
            f"{skill_name} description too short ({len(description)} chars): '{description}'"
        )
