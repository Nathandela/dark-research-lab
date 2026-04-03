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
        for section in ["## Context", "## Decision", "## Consequences", "## Alternatives Considered"]:
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
            phase_state = claude_dir / ".ca-phase-state.json"
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
            phase_state = claude_dir / ".ca-phase-state.json"
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
            phase_state = claude_dir / ".ca-phase-state.json"
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
        for role in ["Research Architect", "Data Analyst", "Paper Writer", "Methodology Auditor"]:
            assert role in content, f"Missing agent role: {role}"

    def test_has_decision_logging_guidance(self):
        content = self.AGENTS_MD.read_text()
        assert "docs/decisions/" in content

    def test_has_research_phases(self):
        content = self.AGENTS_MD.read_text()
        for phase in ["Spec-Dev", "Plan", "Work", "Review", "Compound"]:
            assert phase in content, f"Missing research phase: {phase}"

    def test_preserves_beads_integration(self):
        content = self.AGENTS_MD.read_text()
        assert "bd" in content
        assert "beads" in content.lower()
