"""Verification tests for Epic 2: Workflow Infrastructure.

Tests the ADR template, hooks configuration, CLAUDE.md instructions,
and AGENTS.md agent roles against acceptance criteria AC-1 through AC-7.
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent


class TestADRTemplate:
    """AC-1: docs/decisions/ exists with 0000-template.md containing required YAML fields."""

    TEMPLATE = REPO_ROOT / "docs" / "decisions" / "0000-template.md"

    def test_directory_exists(self):
        assert (REPO_ROOT / "docs" / "decisions").is_dir()

    def test_template_exists(self):
        assert self.TEMPLATE.is_file()

    def test_template_has_yaml_frontmatter(self):
        content = self.TEMPLATE.read_text()
        assert content.startswith("---"), "Template must start with YAML frontmatter"
        parts = content.split("---", 2)
        assert len(parts) >= 3, "Template must have opening and closing --- delimiters"
        frontmatter = yaml.safe_load(parts[1])
        assert isinstance(frontmatter, dict)

    def test_template_yaml_has_required_fields(self):
        content = self.TEMPLATE.read_text()
        frontmatter = yaml.safe_load(content.split("---", 2)[1])
        required = {"title", "status", "date", "deciders"}
        assert required.issubset(frontmatter.keys()), (
            f"Missing YAML fields: {required - frontmatter.keys()}"
        )

    def test_template_body_has_required_sections(self):
        content = self.TEMPLATE.read_text()
        for section in ["## Context", "## Decision", "## Rationale", "## Consequences", "## Alternatives Considered"]:
            assert section in content, f"Template missing section: {section}"


class TestDecisionReminderHook:
    """AC-2: Decision reminder hook fires on phase transition."""

    HOOK_SCRIPT = REPO_ROOT / "scripts" / "hooks" / "decision-reminder.sh"

    def test_hook_script_exists(self):
        assert self.HOOK_SCRIPT.is_file()

    def test_hook_script_is_executable(self):
        assert os.access(self.HOOK_SCRIPT, os.X_OK)

    def _run_hook(self, cwd, env_override=None):
        """Run the hook script with DRL_REPO_ROOT pointing to cwd."""
        env = os.environ.copy()
        env["DRL_REPO_ROOT"] = str(cwd)
        if env_override:
            env.update(env_override)
        return subprocess.run(
            ["bash", str(self.HOOK_SCRIPT)],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )

    def test_hook_exits_zero_without_phase_state(self):
        """Hook should exit silently when no cook-it session is active."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, ".claude").mkdir()
            result = self._run_hook(tmpdir)
            assert result.returncode == 0
            assert result.stdout.strip() == ""

    def test_hook_emits_reminder_on_phase_change(self):
        """Hook should output reminder when phase transitions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = Path(tmpdir) / ".claude"
            claude_dir.mkdir()
            phase_state = claude_dir / ".drl-phase-state.json"
            phase_state.write_text(json.dumps({
                "cookit_active": True,
                "current_phase": "work",
                "phase_index": 3,
            }))
            result = self._run_hook(tmpdir)
            assert result.returncode == 0
            assert "Phase detected" in result.stdout
            assert "docs/decisions/" in result.stdout

    def test_hook_silent_when_cookit_inactive(self):
        """Hook should exit silently when cookit_active is false."""
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = Path(tmpdir) / ".claude"
            claude_dir.mkdir()
            phase_state = claude_dir / ".drl-phase-state.json"
            phase_state.write_text(json.dumps({
                "cookit_active": False,
                "current_phase": "work",
                "phase_index": 3,
            }))
            result = self._run_hook(tmpdir)
            assert result.returncode == 0
            assert result.stdout.strip() == ""

    def test_hook_silent_on_same_phase(self):
        """Hook should not repeat reminder for same phase."""
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = Path(tmpdir) / ".claude"
            claude_dir.mkdir()
            phase_state = claude_dir / ".drl-phase-state.json"
            phase_state.write_text(json.dumps({
                "cookit_active": True,
                "current_phase": "work",
                "phase_index": 3,
            }))
            # First run: triggers reminder
            self._run_hook(tmpdir)
            # Second run: same phase, should be silent
            result = self._run_hook(tmpdir)
            assert result.returncode == 0
            assert result.stdout.strip() == ""


class TestSettingsJson:
    """AC-3, AC-5: settings.json has all required hooks."""

    SETTINGS = REPO_ROOT / ".claude" / "settings.json"

    def test_settings_is_valid_json(self):
        with open(self.SETTINGS) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_has_all_hook_events(self):
        with open(self.SETTINGS) as f:
            data = json.load(f)
        hooks = data.get("hooks", {})
        required_events = {
            "PreToolUse", "PostToolUse", "PostToolUseFailure",
            "SessionStart", "PreCompact", "Stop", "UserPromptSubmit",
        }
        assert required_events.issubset(hooks.keys()), (
            f"Missing hook events: {required_events - hooks.keys()}"
        )

    def test_pretooluse_has_phase_guard(self):
        with open(self.SETTINGS) as f:
            data = json.load(f)
        pre_hooks = data["hooks"]["PreToolUse"]
        commands = [
            h["command"]
            for entry in pre_hooks
            for h in entry.get("hooks", [])
        ]
        assert any("phase-guard" in cmd for cmd in commands), (
            "PreToolUse must contain phase-guard hook"
        )

    def test_pretooluse_phase_guard_matches_edit_write(self):
        with open(self.SETTINGS) as f:
            data = json.load(f)
        pre_hooks = data["hooks"]["PreToolUse"]
        for entry in pre_hooks:
            cmds = [h["command"] for h in entry.get("hooks", [])]
            if any("phase-guard" in c for c in cmds):
                assert "Edit" in entry.get("matcher", "")
                assert "Write" in entry.get("matcher", "")

    def test_userpromptsubmit_has_decision_reminder(self):
        with open(self.SETTINGS) as f:
            data = json.load(f)
        ups_hooks = data["hooks"]["UserPromptSubmit"]
        commands = [
            h["command"]
            for entry in ups_hooks
            for h in entry.get("hooks", [])
        ]
        assert any("decision-reminder" in cmd for cmd in commands), (
            "UserPromptSubmit must contain decision-reminder hook"
        )

    def test_session_start_has_prime(self):
        with open(self.SETTINGS) as f:
            data = json.load(f)
        ss_hooks = data["hooks"]["SessionStart"]
        commands = [
            h["command"]
            for entry in ss_hooks
            for h in entry.get("hooks", [])
        ]
        assert any("prime" in cmd for cmd in commands)

    def test_precompact_has_prime(self):
        with open(self.SETTINGS) as f:
            data = json.load(f)
        pc_hooks = data["hooks"]["PreCompact"]
        commands = [
            h["command"]
            for entry in pc_hooks
            for h in entry.get("hooks", [])
        ]
        assert any("prime" in cmd for cmd in commands)


class TestCLAUDEmd:
    """AC-4, AC-6: CLAUDE.md contains DRL instructions."""

    CLAUDE_MD = REPO_ROOT / ".claude" / "CLAUDE.md"

    def test_file_exists(self):
        assert self.CLAUDE_MD.is_file()

    def test_has_drl_section(self):
        content = self.CLAUDE_MD.read_text()
        assert "## Dark Research Lab" in content

    def test_has_decision_logging_section(self):
        content = self.CLAUDE_MD.read_text()
        assert "Decision Logging" in content
        assert "docs/decisions/" in content

    def test_has_research_spec_gate(self):
        """AC-4: CLAUDE.md contains research-spec approval instruction."""
        content = self.CLAUDE_MD.read_text()
        assert "Research-Spec Approval" in content
        assert "approved" in content.lower()

    def test_has_namespace_section(self):
        content = self.CLAUDE_MD.read_text()
        assert "/drl:" in content

    def test_preserves_compound_agent_section(self):
        content = self.CLAUDE_MD.read_text()
        assert "compound-agent:claude-ref:start" in content
        assert "compound-agent:claude-ref:end" in content


class TestDecisionReminderDocumentation:
    """Epic-eng AC-2: decision-reminder.sh documents .drl-phase-state.json format."""

    HOOK_SCRIPT = REPO_ROOT / "scripts" / "hooks" / "decision-reminder.sh"

    def test_documents_phase_state_json_keys(self):
        """Header comment documents the three required keys."""
        content = self.HOOK_SCRIPT.read_text()
        for key in ["cookit_active", "current_phase", "epic_id"]:
            assert key in content, (
                f"decision-reminder.sh must document .drl-phase-state.json key: {key}"
            )

    def test_documents_drl_last_phase_lifecycle(self):
        """Header comment documents the .drl-last-phase file lifecycle."""
        content = self.HOOK_SCRIPT.read_text()
        assert ".drl-last-phase" in content
        # Must explain what the file does (tracks last seen phase to detect transitions)
        assert "transition" in content.lower() or "track" in content.lower()


class TestCookItFailureRecovery:
    """Epic-eng AC-3: cook-it SKILL.md has Phase Failure Recovery section."""

    SKILL = REPO_ROOT / ".claude" / "skills" / "drl" / "cook-it" / "SKILL.md"

    def test_has_failure_recovery_section(self):
        content = self.SKILL.read_text()
        assert "## Phase Failure Recovery" in content

    def test_failure_recovery_covers_save_state(self):
        content = self.SKILL.read_text()
        # Must mention saving state on failure
        assert "save" in content.lower() and "state" in content.lower()

    def test_failure_recovery_covers_recovery_bead(self):
        content = self.SKILL.read_text()
        assert "recovery" in content.lower()
        assert "bd create" in content or "bead" in content.lower()

    def test_failure_recovery_covers_resume_guidance(self):
        content = self.SKILL.read_text()
        assert "resume" in content.lower()


class TestResearchWorkSpecApproval:
    """Epic-eng AC-4: research-work SKILL.md uses bd show for spec approval."""

    SKILL = REPO_ROOT / ".claude" / "skills" / "drl" / "research-work" / "SKILL.md"

    def test_spec_approval_uses_bd_show(self):
        """Spec approval check must use bd show, not just advisory text."""
        content = self.SKILL.read_text()
        # Must contain a bd show command in the spec approval context
        assert "bd show" in content
        # Must reference checking the spec phase status
        assert "spec" in content.lower() and ("status" in content.lower() or "phase" in content.lower())

    def test_spec_approval_is_verifiable(self):
        """Spec approval must include a concrete verification command."""
        content = self.SKILL.read_text()
        # The gate checklist should include a verification command for spec approval
        assert "bd show" in content


class TestLitReviewIterationCap:
    """Epic-eng AC-5: lit-review has max_iterations=3 guard with proceed-with-warning."""

    SKILL = REPO_ROOT / ".claude" / "skills" / "drl" / "lit-review" / "SKILL.md"

    def test_has_explicit_max_iterations(self):
        content = self.SKILL.read_text()
        assert "max_iterations" in content.lower() or "max iterations" in content.lower() or "MAX_ITERATIONS" in content

    def test_has_proceed_with_warning(self):
        """After exhaustion, must proceed with warning, not hard-fail."""
        content = self.SKILL.read_text()
        lower = content.lower()
        assert "proceed" in lower and "warning" in lower

    def test_iteration_cap_is_three(self):
        content = self.SKILL.read_text()
        # Must mention 3 as the cap
        assert "3" in content


class TestCompileToolAvailability:
    """Epic-eng AC-6: compile SKILL.md checks for pdflatex/bibtex availability."""

    SKILL = REPO_ROOT / ".claude" / "skills" / "drl" / "compile" / "SKILL.md"

    def test_checks_pdflatex_availability(self):
        content = self.SKILL.read_text()
        assert "pdflatex" in content.lower()
        # Must include a check command like `which pdflatex` or `command -v pdflatex`
        assert "which pdflatex" in content or "command -v pdflatex" in content

    def test_checks_bibtex_availability(self):
        content = self.SKILL.read_text()
        assert "bibtex" in content.lower()
        assert "which bibtex" in content or "command -v bibtex" in content

    def test_has_actionable_error_messages(self):
        """Must include actionable install guidance if tools are missing."""
        content = self.SKILL.read_text()
        lower = content.lower()
        assert "install" in lower or "brew" in lower or "tlmgr" in lower or "apt" in lower


class TestGateVerificationCommands:
    """Epic-eng AC-7: All phase gate checklists include a verification command column."""

    SKILL_PATHS = [
        REPO_ROOT / ".claude" / "skills" / "drl" / "research-spec" / "SKILL.md",
        REPO_ROOT / ".claude" / "skills" / "drl" / "research-plan" / "SKILL.md",
        REPO_ROOT / ".claude" / "skills" / "drl" / "research-work" / "SKILL.md",
        REPO_ROOT / ".claude" / "skills" / "drl" / "methodology-review" / "SKILL.md",
        REPO_ROOT / ".claude" / "skills" / "drl" / "synthesis" / "SKILL.md",
    ]

    def test_each_skill_has_verification_table(self):
        """Gate checklists must include a Verification column with exact commands."""
        for path in self.SKILL_PATHS:
            content = path.read_text()
            assert "| Criterion" in content or "| Check" in content or "Verification" in content, (
                f"{path.name} gate checklist missing verification command column"
            )

    def test_verification_commands_are_executable(self):
        """Verification commands should be actual shell commands, not prose."""
        for path in self.SKILL_PATHS:
            content = path.read_text()
            # At least one backtick-enclosed command in the gate section
            gate_section = content.split("## Gate")[1] if "## Gate" in content else content
            assert "`" in gate_section, (
                f"{path.name} gate section must contain backtick-enclosed verification commands"
            )


class TestAGENTSmd:
    """AC-7: AGENTS.md contains DRL agent roles."""

    AGENTS_MD = REPO_ROOT / "AGENTS.md"

    def test_file_exists(self):
        assert self.AGENTS_MD.is_file()

    def test_has_drl_research_workflow(self):
        content = self.AGENTS_MD.read_text()
        assert "## DRL Research Workflow" in content

    def test_has_agent_roles_table(self):
        content = self.AGENTS_MD.read_text()
        for role in [
            "Research Architect",
            "Research Analyst",
            "Literature Analyst",
            "Methodology Reviewer",
            "Robustness Checker",
            "Coherence Reviewer",
            "Reproducibility Verifier",
            "Citation Checker",
            "Writing Quality Reviewer",
        ]:
            assert role in content, f"Missing agent role: {role}"

    def test_has_decision_logging_guidance(self):
        content = self.AGENTS_MD.read_text()
        assert "docs/decisions/" in content

    def test_has_research_phases(self):
        content = self.AGENTS_MD.read_text()
        for phase in ["Spec", "Plan", "Work", "Review", "Synthesis"]:
            assert phase in content, f"Missing research phase: {phase}"

    def test_preserves_beads_integration(self):
        content = self.AGENTS_MD.read_text()
        assert "bd" in content
        assert "beads" in content.lower()


# ---------------------------------------------------------------------------
# Epic 4th: Infrastructure state management and hook resilience
# ---------------------------------------------------------------------------


class TestCookItPhaseStateSchema:
    """AC-1: cook-it/SKILL.md documents .drl-phase-state.json schema."""

    SKILL = REPO_ROOT / ".claude" / "skills" / "drl" / "cook-it" / "SKILL.md"

    def test_documents_all_schema_fields(self):
        """Must document all three fields of .drl-phase-state.json."""
        content = self.SKILL.read_text()
        for field in ["cookit_active", "current_phase", "epic_id"]:
            assert field in content, (
                f"cook-it/SKILL.md must document .drl-phase-state.json field: {field}"
            )

    def test_documents_field_types(self):
        """Must document field types (bool, string)."""
        content = self.SKILL.read_text().lower()
        assert "bool" in content, "Must document cookit_active as boolean type"
        assert "string" in content, "Must document string-typed fields"

    def test_documents_valid_phase_values(self):
        """Must list valid values for current_phase."""
        content = self.SKILL.read_text()
        # At minimum should list the phases as valid values
        for phase in ["spec", "plan", "work", "review", "synthesis"]:
            assert phase in content.lower()

    def test_documents_who_creates_and_reads(self):
        """Must explain who creates and who reads the state file."""
        content = self.SKILL.read_text().lower()
        # Must mention creation/writing
        assert "create" in content or "write" in content or "written" in content
        # Must mention reading
        assert "read" in content


class TestCookItPrerequisites:
    """AC-2: cook-it/SKILL.md has Prerequisites section with verification."""

    SKILL = REPO_ROOT / ".claude" / "skills" / "drl" / "cook-it" / "SKILL.md"

    def test_has_prerequisites_section(self):
        content = self.SKILL.read_text()
        assert "## Prerequisites" in content

    def test_lists_required_hooks(self):
        content = self.SKILL.read_text()
        section = content.split("## Prerequisites")[1].split("\n## ")[0]
        assert "decision-reminder" in section.lower()

    def test_lists_required_files(self):
        content = self.SKILL.read_text()
        section = content.split("## Prerequisites")[1].split("\n## ")[0]
        assert "settings.json" in section

    def test_has_verification_command(self):
        """Prerequisites section must include a backtick-enclosed verification command."""
        content = self.SKILL.read_text()
        section = content.split("## Prerequisites")[1].split("\n## ")[0]
        assert "`" in section, "Prerequisites must include verification commands"


class TestDecisionReminderCleanup:
    """AC-3: decision-reminder.sh cleans up .drl-last-phase when session ends."""

    HOOK_SCRIPT = REPO_ROOT / "scripts" / "hooks" / "decision-reminder.sh"

    def test_cleans_up_last_phase_when_cookit_inactive(self):
        """When cookit_active is false and .drl-last-phase exists, should clean up."""
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = Path(tmpdir) / ".claude"
            claude_dir.mkdir()
            phase_state = claude_dir / ".drl-phase-state.json"
            phase_state.write_text(json.dumps({
                "cookit_active": False,
                "current_phase": "work",
            }))
            last_phase = claude_dir / ".drl-last-phase"
            last_phase.write_text("spec")
            env = os.environ.copy()
            env["DRL_REPO_ROOT"] = str(tmpdir)
            subprocess.run(
                ["bash", str(self.HOOK_SCRIPT)],
                cwd=str(tmpdir),
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
            )
            assert not last_phase.exists(), (
                ".drl-last-phase should be cleaned up when cookit_active is false"
            )

    def test_no_cleanup_when_no_phase_state(self):
        """Without phase state file, .drl-last-phase should remain untouched."""
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = Path(tmpdir) / ".claude"
            claude_dir.mkdir()
            last_phase = claude_dir / ".drl-last-phase"
            last_phase.write_text("spec")
            env = os.environ.copy()
            env["DRL_REPO_ROOT"] = str(tmpdir)
            subprocess.run(
                ["bash", str(self.HOOK_SCRIPT)],
                cwd=str(tmpdir),
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
            )
            assert last_phase.exists(), (
                ".drl-last-phase should not be touched when no phase state exists"
            )


class TestFlavorAtomicWriteSimplified:
    """AC-4: flavor/SKILL.md atomic write uses standard shell mv."""

    SKILL = REPO_ROOT / ".claude" / "skills" / "drl" / "flavor" / "SKILL.md"

    def test_uses_mv_pattern(self):
        content = self.SKILL.read_text()
        assert "mv " in content, "Atomic write must use mv command"

    def test_mentions_edit_tool_as_primary(self):
        """Should mention Claude's Edit tool as the primary editing method."""
        content = self.SKILL.read_text()
        assert "Edit" in content, "Should reference Claude's Edit tool"

    def test_no_special_tooling_expected(self):
        """Should not imply special tooling is needed beyond standard shell."""
        content = self.SKILL.read_text().lower()
        assert "special tool" not in content
        assert "external tool" not in content


class TestOnboardHookValidation:
    """AC-5: onboard skill verifies hooks are configured correctly."""

    SKILL = REPO_ROOT / ".claude" / "skills" / "drl" / "onboard" / "SKILL.md"

    def test_has_hook_validation(self):
        content = self.SKILL.read_text().lower()
        assert "hook" in content and (
            "verify" in content or "check" in content or "validate" in content
        ), "onboard/SKILL.md must verify hook configuration"

    def test_checks_settings_json(self):
        content = self.SKILL.read_text()
        assert "settings.json" in content, (
            "onboard/SKILL.md must check settings.json"
        )

    def test_checks_decision_reminder_hook(self):
        content = self.SKILL.read_text()
        assert "decision-reminder" in content, (
            "onboard/SKILL.md must check decision-reminder hook"
        )
