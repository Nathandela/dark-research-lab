"""Verification tests for Epic 7: Commands + Flavor + Onboarding.

Tests that all 8 /drl:* slash commands exist as thin wrappers,
the flavor and onboard SKILL.md files exist with proper content,
and all files follow the established patterns.
"""
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
DRL_COMMANDS_DIR = REPO_ROOT / ".claude" / "commands" / "drl"
DRL_SKILLS_DIR = REPO_ROOT / ".claude" / "skills" / "drl"

# All 8 commands from the epic specification
DRL_COMMANDS = [
    "onboard",
    "flavor",
    "cook-it",
    "architect",
    "lit-review",
    "decision",
    "compile",
    "status",
]

# Commands that need NEW skill directories (not already existing from Epics 5/6)
NEW_SKILL_DIRS = [
    "onboard",
    "flavor",
    "cook-it",
    "lit-review",
    "decision",
    "compile",
    "status",
]

# Command -> skill path mapping
COMMAND_SKILL_MAP = {
    "onboard": "onboard",
    "flavor": "flavor",
    "cook-it": "cook-it",
    "architect": "research-architect",
    "lit-review": "lit-review",
    "decision": "decision",
    "compile": "compile",
    "status": "status",
}


def _parse_frontmatter(path: Path) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    content = path.read_text()
    assert content.startswith("---"), f"{path.name} must start with YAML frontmatter"
    parts = content.split("---", 2)
    assert len(parts) >= 3, f"{path.name} must have opening and closing --- delimiters"
    return yaml.safe_load(parts[1])


def _read_body(path: Path) -> str:
    """Extract body content (after frontmatter) from a markdown file."""
    content = path.read_text()
    parts = content.split("---", 2)
    return parts[2] if len(parts) >= 3 else ""


# ---------------------------------------------------------------------------
# Command file tests
# ---------------------------------------------------------------------------

class TestCommandDirectoryStructure:
    """All 8 /drl:* command files exist at .claude/commands/drl/."""

    def test_drl_commands_directory_exists(self):
        assert DRL_COMMANDS_DIR.is_dir(), f"Missing directory: {DRL_COMMANDS_DIR}"

    def test_all_command_files_exist(self):
        for cmd in DRL_COMMANDS:
            cmd_file = DRL_COMMANDS_DIR / f"{cmd}.md"
            assert cmd_file.is_file(), f"Missing command file: {cmd_file}"

    def test_no_extra_command_files(self):
        """Only the 8 contracted commands should exist."""
        expected = {f"{cmd}.md" for cmd in DRL_COMMANDS}
        actual = {f.name for f in DRL_COMMANDS_DIR.glob("*.md")}
        extra = actual - expected
        assert not extra, f"Unexpected command files: {extra}"


class TestCommandFormat:
    """All commands follow the thin-wrapper pattern with YAML frontmatter."""

    def test_all_commands_have_valid_frontmatter(self):
        for cmd in DRL_COMMANDS:
            fm = _parse_frontmatter(DRL_COMMANDS_DIR / f"{cmd}.md")
            assert isinstance(fm, dict), f"{cmd}.md frontmatter is not a dict"

    def test_all_commands_have_name_field(self):
        for cmd in DRL_COMMANDS:
            fm = _parse_frontmatter(DRL_COMMANDS_DIR / f"{cmd}.md")
            assert "name" in fm, f"{cmd}.md missing 'name' field"
            assert fm["name"].startswith("drl:"), (
                f"{cmd}.md name must use drl:* namespace, got '{fm['name']}'"
            )

    def test_all_commands_have_description_field(self):
        for cmd in DRL_COMMANDS:
            fm = _parse_frontmatter(DRL_COMMANDS_DIR / f"{cmd}.md")
            assert "description" in fm, f"{cmd}.md missing 'description' field"
            assert isinstance(fm["description"], str) and len(fm["description"]) > 0

    def test_all_commands_pass_arguments(self):
        """Thin wrappers must include $ARGUMENTS."""
        for cmd in DRL_COMMANDS:
            body = _read_body(DRL_COMMANDS_DIR / f"{cmd}.md")
            assert "$ARGUMENTS" in body, f"{cmd}.md must include $ARGUMENTS"

    def test_all_commands_reference_skill_file(self):
        """Each command references its corresponding SKILL.md."""
        for cmd in DRL_COMMANDS:
            body = _read_body(DRL_COMMANDS_DIR / f"{cmd}.md")
            skill_dir = COMMAND_SKILL_MAP[cmd]
            expected_path = f".claude/skills/drl/{skill_dir}/SKILL.md"
            assert expected_path in body, (
                f"{cmd}.md must reference {expected_path}"
            )

    def test_all_commands_have_mandatory_read_instruction(self):
        """Thin wrappers must instruct to read the skill file."""
        for cmd in DRL_COMMANDS:
            body = _read_body(DRL_COMMANDS_DIR / f"{cmd}.md").lower()
            assert "read" in body and "skill.md" in body, (
                f"{cmd}.md must instruct to read SKILL.md"
            )


# ---------------------------------------------------------------------------
# New skill file tests
# ---------------------------------------------------------------------------

class TestNewSkillDirectories:
    """New skill directories exist for commands that need them."""

    def test_all_new_skill_directories_exist(self):
        for skill_dir in NEW_SKILL_DIRS:
            path = DRL_SKILLS_DIR / skill_dir
            assert path.is_dir(), f"Missing skill directory: {path}"

    def test_all_new_skill_files_exist(self):
        for skill_dir in NEW_SKILL_DIRS:
            skill = DRL_SKILLS_DIR / skill_dir / "SKILL.md"
            assert skill.is_file(), f"Missing SKILL.md: {skill}"


class TestNewSkillFrontmatter:
    """New skills have proper YAML frontmatter."""

    def test_all_new_skills_have_valid_frontmatter(self):
        for skill_dir in NEW_SKILL_DIRS:
            fm = _parse_frontmatter(DRL_SKILLS_DIR / skill_dir / "SKILL.md")
            assert isinstance(fm, dict), f"{skill_dir}/SKILL.md frontmatter invalid"

    def test_all_new_skills_have_name_field(self):
        for skill_dir in NEW_SKILL_DIRS:
            fm = _parse_frontmatter(DRL_SKILLS_DIR / skill_dir / "SKILL.md")
            assert "name" in fm, f"{skill_dir}/SKILL.md missing 'name' field"
            assert isinstance(fm["name"], str) and len(fm["name"]) > 0

    def test_all_new_skills_have_description_field(self):
        for skill_dir in NEW_SKILL_DIRS:
            fm = _parse_frontmatter(DRL_SKILLS_DIR / skill_dir / "SKILL.md")
            assert "description" in fm, f"{skill_dir}/SKILL.md missing 'description'"
            assert isinstance(fm["description"], str) and len(fm["description"]) > 0

    def test_all_new_skills_have_body_content(self):
        for skill_dir in NEW_SKILL_DIRS:
            body = _read_body(DRL_SKILLS_DIR / skill_dir / "SKILL.md")
            assert len(body.strip()) > 200, (
                f"{skill_dir}/SKILL.md body too short (likely empty)"
            )


# ---------------------------------------------------------------------------
# Flavor skill-specific tests
# ---------------------------------------------------------------------------

class TestFlavorSkillContent:
    """Flavor skill has interactive interview, git safety, and atomic write."""

    def test_flavor_references_interview(self):
        body = _read_body(DRL_SKILLS_DIR / "flavor" / "SKILL.md").lower()
        assert "interview" in body, "flavor/SKILL.md must mention interview"

    def test_flavor_references_field_customization(self):
        body = _read_body(DRL_SKILLS_DIR / "flavor" / "SKILL.md").lower()
        assert "field" in body and ("methodology" in body or "journal" in body), (
            "flavor/SKILL.md must cover field/methodology/journal customization"
        )

    def test_flavor_references_citation_style(self):
        body = _read_body(DRL_SKILLS_DIR / "flavor" / "SKILL.md").lower()
        assert "citation" in body, "flavor/SKILL.md must mention citation style"

    def test_flavor_has_git_commit_before_edit(self):
        """H2 mitigation: git commit before editing skill files."""
        body = _read_body(DRL_SKILLS_DIR / "flavor" / "SKILL.md").lower()
        assert "git commit" in body or "git add" in body, (
            "flavor/SKILL.md must commit before editing (H2 mitigation)"
        )

    def test_flavor_has_atomic_write(self):
        """H2 mitigation: atomic write via temp file + rename."""
        body = _read_body(DRL_SKILLS_DIR / "flavor" / "SKILL.md").lower()
        assert "atomic" in body or ("temp" in body and "rename" in body), (
            "flavor/SKILL.md must use atomic write (temp+rename)"
        )

    def test_flavor_edits_skill_files(self):
        body = _read_body(DRL_SKILLS_DIR / "flavor" / "SKILL.md").lower()
        assert "skill" in body and "edit" in body, (
            "flavor/SKILL.md must describe editing skill files"
        )

    def test_flavor_uses_web_search(self):
        """Flavor should search for field conventions."""
        body = _read_body(DRL_SKILLS_DIR / "flavor" / "SKILL.md").lower()
        assert "web" in body or "search" in body, (
            "flavor/SKILL.md must reference web search for conventions"
        )


# ---------------------------------------------------------------------------
# Onboard skill-specific tests
# ---------------------------------------------------------------------------

class TestOnboardSkillContent:
    """Onboard skill guides through complete setup flow."""

    def test_onboard_explains_framework(self):
        body = _read_body(DRL_SKILLS_DIR / "onboard" / "SKILL.md").lower()
        assert "framework" in body or "dark research lab" in body, (
            "onboard/SKILL.md must explain the DRL framework"
        )

    def test_onboard_asks_research_question(self):
        body = _read_body(DRL_SKILLS_DIR / "onboard" / "SKILL.md").lower()
        assert "research question" in body or "rq" in body, (
            "onboard/SKILL.md must ask about the research question"
        )

    def test_onboard_asks_about_data(self):
        body = _read_body(DRL_SKILLS_DIR / "onboard" / "SKILL.md").lower()
        assert "data" in body, "onboard/SKILL.md must ask about data"

    def test_onboard_suggests_flavor(self):
        body = _read_body(DRL_SKILLS_DIR / "onboard" / "SKILL.md").lower()
        assert "flavor" in body, "onboard/SKILL.md must suggest flavor configuration"

    def test_onboard_guides_pdf_drops(self):
        body = _read_body(DRL_SKILLS_DIR / "onboard" / "SKILL.md").lower()
        assert "pdf" in body, "onboard/SKILL.md must guide PDF drops"

    def test_onboard_suggests_architect(self):
        body = _read_body(DRL_SKILLS_DIR / "onboard" / "SKILL.md").lower()
        assert "architect" in body, "onboard/SKILL.md must suggest architect next"

    def test_onboard_explains_monitoring(self):
        body = _read_body(DRL_SKILLS_DIR / "onboard" / "SKILL.md").lower()
        assert "monitor" in body or "status" in body, (
            "onboard/SKILL.md must explain monitoring"
        )

    def test_onboard_references_flavor_command(self):
        body = _read_body(DRL_SKILLS_DIR / "onboard" / "SKILL.md")
        assert "/drl:flavor" in body, (
            "onboard/SKILL.md must reference /drl:flavor command"
        )


# ---------------------------------------------------------------------------
# Cook-it orchestrator tests
# ---------------------------------------------------------------------------

class TestCookItSkillContent:
    """Cook-it skill orchestrates the DRL research workflow."""

    def test_cook_it_references_research_phases(self):
        body = _read_body(DRL_SKILLS_DIR / "cook-it" / "SKILL.md").lower()
        phases = ["spec", "plan", "work", "review", "synthesis"]
        for phase in phases:
            assert phase in body, f"cook-it/SKILL.md must reference phase: {phase}"

    def test_cook_it_references_compound_workflow(self):
        body = _read_body(DRL_SKILLS_DIR / "cook-it" / "SKILL.md").lower()
        assert "compound" in body or "cook-it" in body


# ---------------------------------------------------------------------------
# Namespace consistency
# ---------------------------------------------------------------------------

class TestNamespaceConsistency:
    """All commands use /drl:* namespace (U2 from EARS)."""

    def test_all_command_names_use_drl_namespace(self):
        for cmd in DRL_COMMANDS:
            fm = _parse_frontmatter(DRL_COMMANDS_DIR / f"{cmd}.md")
            assert fm["name"].startswith("drl:"), (
                f"{cmd}.md name '{fm['name']}' must use drl:* namespace"
            )

    def test_command_name_matches_filename(self):
        """Command name slug should match filename."""
        for cmd in DRL_COMMANDS:
            fm = _parse_frontmatter(DRL_COMMANDS_DIR / f"{cmd}.md")
            expected_name = f"drl:{cmd}"
            assert fm["name"] == expected_name, (
                f"{cmd}.md name '{fm['name']}' should be '{expected_name}'"
            )


# ---------------------------------------------------------------------------
# Research vocabulary (no software dev terms)
# ---------------------------------------------------------------------------

class TestSkillResearchVocabulary:
    """New skills use research vocabulary, not software dev."""

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

    def test_flavor_avoids_software_dev_terms(self):
        content = (DRL_SKILLS_DIR / "flavor" / "SKILL.md").read_text().lower()
        found = [t for t in self.SOFTWARE_DEV_TERMS if t in content]
        assert not found, f"flavor/SKILL.md contains software dev terms: {found}"

    def test_onboard_avoids_software_dev_terms(self):
        content = (DRL_SKILLS_DIR / "onboard" / "SKILL.md").read_text().lower()
        found = [t for t in self.SOFTWARE_DEV_TERMS if t in content]
        assert not found, f"onboard/SKILL.md contains software dev terms: {found}"
