"""Verification tests for Epic 6: Research Architect + Agent Definitions.

Tests that all 8 agent definition files and the research-architect SKILL.md
follow the correct format, naming contract, and are research-specific.
"""
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent

AGENT_NAMES = [
    "analyst",
    "robustness-checker",
    "methodology-reviewer",
    "coherence-reviewer",
    "reproducibility-verifier",
    "literature-analyst",
    "citation-checker",
    "writing-quality-reviewer",
]

DRL_AGENTS_DIR = REPO_ROOT / ".claude" / "agents" / "drl"
DRL_SKILLS_DIR = REPO_ROOT / ".claude" / "skills" / "drl"
ARCHITECT_SKILL = DRL_SKILLS_DIR / "research-architect" / "SKILL.md"


def _parse_frontmatter(path: Path) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    content = path.read_text()
    assert content.startswith("---"), f"{path.name} must start with YAML frontmatter"
    parts = content.split("---", 2)
    assert len(parts) >= 3, f"{path.name} must have opening and closing --- delimiters"
    return yaml.safe_load(parts[1])


class TestAgentDirectoryStructure:
    """AC-3: All 8 agent files exist at the correct paths."""

    def test_drl_agents_directory_exists(self):
        assert DRL_AGENTS_DIR.is_dir(), f"Missing directory: {DRL_AGENTS_DIR}"

    def test_all_agent_files_exist(self):
        for name in AGENT_NAMES:
            agent_file = DRL_AGENTS_DIR / f"{name}.md"
            assert agent_file.is_file(), f"Missing agent file: {agent_file}"

    def test_no_extra_agent_files(self):
        """Only the 8 contracted agents should exist."""
        expected = {f"{name}.md" for name in AGENT_NAMES}
        actual = {f.name for f in DRL_AGENTS_DIR.glob("*.md")}
        extra = actual - expected
        assert not extra, f"Unexpected agent files: {extra}"


class TestAgentFormatConsistency:
    """AC-1, AC-4: All agents follow YAML frontmatter + markdown pattern
    with consistent sections."""

    def test_all_agents_have_valid_frontmatter(self):
        for name in AGENT_NAMES:
            fm = _parse_frontmatter(DRL_AGENTS_DIR / f"{name}.md")
            assert isinstance(fm, dict), f"{name}.md frontmatter is not a dict"

    def test_all_agents_have_name_field(self):
        for name in AGENT_NAMES:
            fm = _parse_frontmatter(DRL_AGENTS_DIR / f"{name}.md")
            assert "name" in fm, f"{name}.md missing 'name' field"
            assert isinstance(fm["name"], str) and len(fm["name"]) > 0

    def test_all_agents_have_description_field(self):
        for name in AGENT_NAMES:
            fm = _parse_frontmatter(DRL_AGENTS_DIR / f"{name}.md")
            assert "description" in fm, f"{name}.md missing 'description' field"
            assert isinstance(fm["description"], str) and len(fm["description"]) > 0

    def test_all_agents_have_body_content(self):
        for name in AGENT_NAMES:
            content = (DRL_AGENTS_DIR / f"{name}.md").read_text()
            body = content.split("---", 2)[2].strip()
            assert len(body) > 50, f"{name}.md body too short (likely empty)"

    def test_all_agents_have_capabilities_section(self):
        for name in AGENT_NAMES:
            content = (DRL_AGENTS_DIR / f"{name}.md").read_text()
            body = content.split("---", 2)[2]
            assert "capabilities" in body.lower() or "Capabilities" in body, (
                f"{name}.md missing capabilities section"
            )

    def test_all_agents_have_constraints_section(self):
        for name in AGENT_NAMES:
            content = (DRL_AGENTS_DIR / f"{name}.md").read_text()
            body = content.split("---", 2)[2]
            assert "constraints" in body.lower() or "Constraints" in body, (
                f"{name}.md missing constraints section"
            )


class TestAgentResearchSpecificity:
    """AC-6: Agent definitions are research-specific, not software dev."""

    SOFTWARE_DEV_TERMS = [
        "pull request",
        "deploy",
        "CI/CD",
        "kubernetes",
        "docker",
        "sprint",
        "user story",
        "microservice",
    ]

    RESEARCH_TERMS = [
        "research",
        "methodolog",
        "statistical",
        "hypothesis",
        "literature",
        "paper",
        "analysis",
        "citation",
        "reproducib",
        "academic",
    ]

    def test_agents_use_research_vocabulary(self):
        for name in AGENT_NAMES:
            content = (DRL_AGENTS_DIR / f"{name}.md").read_text().lower()
            has_research = any(term in content for term in self.RESEARCH_TERMS)
            assert has_research, (
                f"{name}.md lacks research-specific vocabulary"
            )

    def test_agents_avoid_software_dev_vocabulary(self):
        for name in AGENT_NAMES:
            content = (DRL_AGENTS_DIR / f"{name}.md").read_text().lower()
            found = [t for t in self.SOFTWARE_DEV_TERMS if t in content]
            assert not found, (
                f"{name}.md contains software dev terms: {found}"
            )


class TestArchitectSkill:
    """AC-2, AC-5, AC-7: Research architect SKILL.md format and content."""

    def test_skill_directory_exists(self):
        assert (DRL_SKILLS_DIR / "research-architect").is_dir()

    def test_skill_file_exists(self):
        assert ARCHITECT_SKILL.is_file()

    def test_skill_has_valid_frontmatter(self):
        fm = _parse_frontmatter(ARCHITECT_SKILL)
        assert isinstance(fm, dict)

    def test_skill_frontmatter_has_name(self):
        fm = _parse_frontmatter(ARCHITECT_SKILL)
        assert "name" in fm
        assert isinstance(fm["name"], str)

    def test_skill_frontmatter_has_description(self):
        fm = _parse_frontmatter(ARCHITECT_SKILL)
        assert "description" in fm

    def test_skill_frontmatter_has_phase(self):
        fm = _parse_frontmatter(ARCHITECT_SKILL)
        assert "phase" in fm
        assert fm["phase"] == "architect"

    def test_skill_defines_six_subagents(self):
        """AC-5: 6 research subagents are defined."""
        content = ARCHITECT_SKILL.read_text().lower()
        subagents = [
            "literature mapper",
            "methodology analyst",
            "data requirements analyst",
            "scope sizer",
            "traceability designer",
            "risk analyst",
        ]
        for sa in subagents:
            assert sa in content, f"Missing subagent: {sa}"

    def test_skill_has_socratic_phase(self):
        content = ARCHITECT_SKILL.read_text().lower()
        assert "socratic" in content, "Missing Socratic phase"

    def test_skill_has_epic_materialization(self):
        content = ARCHITECT_SKILL.read_text()
        assert "bd create" in content, "Missing epic materialization (bd create)"

    def test_skill_is_research_specific(self):
        content = ARCHITECT_SKILL.read_text().lower()
        research_terms = ["research question", "hypothesis", "methodology", "literature"]
        found = sum(1 for t in research_terms if t in content)
        assert found >= 3, "Architect skill lacks research-specific content"

    def test_skill_references_advisory_fleet(self):
        """AC-7: Advisory fleet integration."""
        content = ARCHITECT_SKILL.read_text().lower()
        assert "advisory" in content, "Missing advisory fleet reference"
