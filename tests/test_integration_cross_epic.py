"""Cross-epic integration tests for DRL (Epic IV).

Verifies that interfaces between epics are wired correctly:
  1. drl setup installs all expected files (Epic 1 -> All)
  2. Phase guard hook is wired in settings.json (Epic 2 -> Epic 5)
  3. Decision reminder is wired and executable (Epic 2 -> Epic 5)
  4. Skills reference valid paper/src paths (Epic 3 -> Epic 5)
  5. drl knowledge subcommand exists (Epic 4 -> Epic 5)
  6. Skills reference valid agent files (Epic 5 -> Epic 6)
  7. Commands target existing SKILL.md files (Epic 5 -> Epic 7)
  8. All skill files have valid YAML frontmatter (Epic 7 -> Epic 5)
  9. Flavor skill mandates git commit before edit (Epic 7 -> Git)
"""
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent
GO_DIR = REPO_ROOT / "go"
DRL_SKILLS_DIR = REPO_ROOT / ".claude" / "skills" / "drl"
DRL_AGENTS_DIR = REPO_ROOT / ".claude" / "agents" / "drl"
DRL_COMMANDS_DIR = REPO_ROOT / ".claude" / "commands" / "drl"
SETTINGS_PATH = REPO_ROOT / ".claude" / "settings.json"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def drl_binary():
    """Build the drl binary once for all tests."""
    binary = GO_DIR / "drl"
    subprocess.run(
        ["go", "build", "-o", str(binary), "./cmd/drl/"],
        cwd=str(GO_DIR),
        check=True,
        capture_output=True,
    )
    assert binary.is_file()
    return binary


def _run_drl(binary, args, cwd=None):
    """Run drl binary with args."""
    return subprocess.run(
        [str(binary)] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _read_body(path: Path) -> str:
    """Extract body content after frontmatter."""
    content = path.read_text()
    parts = content.split("---", 2)
    return parts[2] if len(parts) >= 3 else ""


# ---------------------------------------------------------------------------
# Shared fixture: single drl setup for Contract 1 tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def setup_tmpdir(drl_binary, tmp_path_factory):
    """Run drl setup once in a shared temp repo for all Contract 1 tests."""
    tmpdir = tmp_path_factory.mktemp("drl_setup")
    subprocess.run(
        ["git", "init"], cwd=str(tmpdir), capture_output=True, check=True
    )
    result = _run_drl(
        drl_binary,
        ["setup", "--skip-hooks", "--all-skill", "--repo-root", str(tmpdir)],
    )
    assert result.returncode == 0, f"setup failed: {result.stderr}"
    return tmpdir


# ---------------------------------------------------------------------------
# Contract 1: drl setup installs correct files (Epic 1 -> All)
# ---------------------------------------------------------------------------

class TestSetupInstallsAllFiles:
    """Integration: run drl setup in temp repo, verify all paths exist."""

    def test_setup_creates_complete_structure(self, setup_tmpdir):
        base = setup_tmpdir / ".claude"
        # DRL directories (installed by drl setup)
        assert (base / "skills" / "drl").is_dir(), "Missing drl skills"
        assert (base / "agents" / "drl").is_dir(), "Missing drl agents"
        assert (base / "commands" / "drl").is_dir(), "Missing drl commands"

    def test_drl_directories_exist_in_repo(self):
        """DRL-specific scaffolding exists in the repository."""
        assert DRL_SKILLS_DIR.is_dir(), "Missing drl skills dir"
        assert DRL_AGENTS_DIR.is_dir(), "Missing drl agents dir"
        assert DRL_COMMANDS_DIR.is_dir(), "Missing drl commands dir"

    def test_setup_creates_skills_index(self, setup_tmpdir):
        index = setup_tmpdir / ".claude" / "skills" / "drl" / "skills_index.json"
        assert index.is_file(), "Missing skills_index.json"
        data = json.loads(index.read_text())
        assert len(data.get("skills", [])) > 0, "skills_index.json is empty"


# ---------------------------------------------------------------------------
# Contract 2: Phase guard blocks edit before skill read (Epic 2 -> Epic 5)
# ---------------------------------------------------------------------------

class TestPhaseGuardWiring:
    """Verify hooks in settings.json wire phase-guard to Edit/Write."""

    def test_settings_has_phase_guard_hook(self):
        settings = json.loads(SETTINGS_PATH.read_text())
        hooks = settings.get("hooks", {})
        pre_tool = hooks.get("PreToolUse", [])

        found_phase_guard = False
        for entry in pre_tool:
            matcher = entry.get("matcher", "")
            if "Edit" in matcher or "Write" in matcher:
                for h in entry.get("hooks", []):
                    cmd = h.get("command", "")
                    if "phase-guard" in cmd:
                        found_phase_guard = True
                        break

        assert found_phase_guard, (
            "settings.json must wire phase-guard hook on PreToolUse for Edit|Write"
        )

    def test_phase_guard_hook_references_valid_binary(self):
        """The phase-guard hook command should reference an absolute path to a binary."""
        settings = json.loads(SETTINGS_PATH.read_text())
        pre_tool = settings.get("hooks", {}).get("PreToolUse", [])

        found = False
        for entry in pre_tool:
            for h in entry.get("hooks", []):
                cmd = h.get("command", "")
                if "phase-guard" in cmd:
                    match = re.search(r"""['"]([^'"]+)['"]""", cmd)
                    assert match, (
                        f"Could not extract binary path from phase-guard command: {cmd}"
                    )
                    binary_path = match.group(1)
                    assert Path(binary_path).is_absolute(), (
                        f"Phase-guard binary path must be absolute: {binary_path}"
                    )
                    assert binary_path.endswith("/ca") or binary_path.endswith("/ca.exe"), (
                        f"Phase-guard binary should be 'ca': {binary_path}"
                    )
                    found = True

        assert found, "No phase-guard hook found in PreToolUse"


# ---------------------------------------------------------------------------
# Contract 3: Decision reminder fires at phase transition (Epic 2 -> Epic 5)
# ---------------------------------------------------------------------------

class TestDecisionReminderWiring:
    """Verify decision-reminder hook is wired and executable."""

    def test_decision_reminder_script_exists(self):
        script = REPO_ROOT / "scripts" / "hooks" / "decision-reminder.sh"
        assert script.is_file(), "Missing decision-reminder.sh"

    def test_decision_reminder_is_executable(self):
        script = REPO_ROOT / "scripts" / "hooks" / "decision-reminder.sh"
        assert os.access(script, os.X_OK), "decision-reminder.sh must be executable"

    def test_decision_reminder_in_settings(self):
        settings = json.loads(SETTINGS_PATH.read_text())
        hooks = settings.get("hooks", {})
        user_prompt = hooks.get("UserPromptSubmit", [])

        found = False
        for entry in user_prompt:
            for h in entry.get("hooks", []):
                cmd = h.get("command", "")
                if "decision-reminder" in cmd:
                    found = True
                    break

        assert found, (
            "settings.json must wire decision-reminder.sh on UserPromptSubmit"
        )

    def test_decision_reminder_references_adr_template(self):
        """The script should reference ADR template for decision logging."""
        script = REPO_ROOT / "scripts" / "hooks" / "decision-reminder.sh"
        content = script.read_text()
        assert "0000-template" in content or "ADR" in content or "decisions/" in content, (
            "decision-reminder.sh should reference the ADR template or decisions dir"
        )


# ---------------------------------------------------------------------------
# Contract 4: Skills reference correct paper/src paths (Epic 3 -> Epic 5)
# ---------------------------------------------------------------------------

class TestSkillPathReferences:
    """Grep skills for paper/ and src/ references, verify paths exist in repo."""

    PATH_PATTERNS = [
        re.compile(r'(paper/[a-zA-Z0-9_./-]+)'),
        re.compile(r'(src/[a-zA-Z0-9_./-]+)'),
    ]

    # Build artifacts referenced in instructions but not present at rest
    BUILD_ARTIFACTS = {
        "paper/main.log", "paper/main.pdf", "paper/main.aux",
        "paper/main.bbl", "paper/main.blg", "paper/main.out",
    }

    def _collect_path_refs(self):
        """Grep all skill files for paper/ and src/ path references."""
        refs = set()
        for skill_file in DRL_SKILLS_DIR.glob("*/SKILL.md"):
            content = skill_file.read_text()
            for pattern in self.PATH_PATTERNS:
                for match in pattern.finditer(content):
                    refs.add((match.group(1), skill_file.parent.name))
        return refs

    def test_all_referenced_paths_exist(self):
        """Every paper/ and src/ path mentioned in skills must exist in the repo."""
        refs = self._collect_path_refs()
        assert len(refs) > 0, "No paper/ or src/ references found in any skill"
        for path_ref, skill_name in refs:
            # Strip trailing punctuation from markdown
            clean = path_ref.rstrip(".,;:)")
            if clean in self.BUILD_ARTIFACTS:
                continue
            full = REPO_ROOT / clean
            assert full.exists(), (
                f"Skill {skill_name} references '{clean}' but it does not exist"
            )

    def test_paper_outputs_subdirs_exist(self):
        assert (REPO_ROOT / "paper" / "outputs" / "tables").is_dir()
        assert (REPO_ROOT / "paper" / "outputs" / "figures").is_dir()

    def test_compile_script_exists(self):
        """Skills reference paper/compile.sh."""
        assert (REPO_ROOT / "paper" / "compile.sh").is_file()


# ---------------------------------------------------------------------------
# Contract 5: drl knowledge returns valid results (Epic 4 -> Epic 5)
# ---------------------------------------------------------------------------

class TestKnowledgeCommand:
    """Integration: drl knowledge subcommand exists and is callable."""

    def test_knowledge_help_works(self, drl_binary):
        result = _run_drl(drl_binary, ["knowledge", "--help"])
        assert result.returncode == 0, f"knowledge --help failed: {result.stderr}"
        assert "query" in result.stdout.lower() or "search" in result.stdout.lower()

    def test_knowledge_with_no_index_returns_gracefully(self, drl_binary):
        """Running knowledge with no indexed docs should not crash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(
                ["git", "init"], cwd=tmpdir, capture_output=True, check=True
            )
            result = _run_drl(drl_binary, ["knowledge", "test query"], cwd=tmpdir)
            # Should exit 0 or 1 with a message, not crash
            assert result.returncode in (0, 1), (
                f"knowledge crashed with code {result.returncode}: {result.stderr}"
            )

    def test_index_command_exists(self, drl_binary):
        """drl index subcommand exists for indexing PDFs."""
        result = _run_drl(drl_binary, ["index", "--help"])
        assert result.returncode == 0, f"index --help failed: {result.stderr}"


# ---------------------------------------------------------------------------
# Contract 6: Skills reference correct agent names (Epic 5 -> Epic 6)
# ---------------------------------------------------------------------------

class TestSkillAgentReferences:
    """Grep skills for agent refs, verify agent files exist."""

    EXPECTED_AGENT_REFS = {
        "research-work": ["analyst.md"],
        "lit-review": ["literature-analyst.md"],
        "research-spec": ["literature-analyst.md"],
        "methodology-review": [
            "methodology-reviewer.md",
            "robustness-checker.md",
            "coherence-reviewer.md",
            "citation-checker.md",
            "reproducibility-verifier.md",
            "writing-quality-reviewer.md",
        ],
    }

    def test_all_referenced_agents_exist(self):
        """Every agent file referenced in skills must exist."""
        for skill_dir, agents in self.EXPECTED_AGENT_REFS.items():
            skill_file = DRL_SKILLS_DIR / skill_dir / "SKILL.md"
            assert skill_file.is_file(), f"Missing skill: {skill_file}"
            content = skill_file.read_text()

            for agent in agents:
                expected_path = f".claude/agents/drl/{agent}"
                assert expected_path in content, (
                    f"Skill {skill_dir} should reference {expected_path}"
                )
                actual_file = REPO_ROOT / ".claude" / "agents" / "drl" / agent
                assert actual_file.is_file(), (
                    f"Agent file referenced by {skill_dir} does not exist: {actual_file}"
                )

    def test_agents_match_agents_md_table(self):
        """All agents in .claude/agents/drl/ should be listed in AGENTS.md."""
        agents_md = (REPO_ROOT / "AGENTS.md").read_text()
        agent_files = list(DRL_AGENTS_DIR.glob("*.md"))
        assert len(agent_files) > 0, "No agent files found"

        for af in agent_files:
            assert af.name in agents_md, (
                f"Agent {af.name} exists but is not listed in AGENTS.md"
            )


# ---------------------------------------------------------------------------
# Contract 7: Commands read correct SKILL.md paths (Epic 5 -> Epic 7)
# ---------------------------------------------------------------------------

class TestCommandSkillPaths:
    """Verify each command targets an existing SKILL.md file."""

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

    def test_all_commands_reference_existing_skills(self):
        """Each command file references a SKILL.md that actually exists."""
        for cmd, skill_dir in self.COMMAND_SKILL_MAP.items():
            cmd_file = DRL_COMMANDS_DIR / f"{cmd}.md"
            assert cmd_file.is_file(), f"Missing command: {cmd_file}"

            content = cmd_file.read_text()
            expected_path = f".claude/skills/drl/{skill_dir}/SKILL.md"
            assert expected_path in content, (
                f"Command {cmd} does not reference {expected_path}"
            )

            actual_skill = DRL_SKILLS_DIR / skill_dir / "SKILL.md"
            assert actual_skill.is_file(), (
                f"Command {cmd} references {expected_path} but file does not exist"
            )

    def test_no_dangling_skill_references(self):
        """Grep all commands for SKILL.md paths, verify they all resolve."""
        for cmd_file in DRL_COMMANDS_DIR.glob("*.md"):
            content = cmd_file.read_text()
            refs = re.findall(r'\.claude/skills/drl/([^/]+)/SKILL\.md', content)
            for ref in refs:
                actual = DRL_SKILLS_DIR / ref / "SKILL.md"
                assert actual.is_file(), (
                    f"Command {cmd_file.name} references non-existent skill: {ref}"
                )


# ---------------------------------------------------------------------------
# Contract 8: Flavor edits don't corrupt skills (Epic 7 -> Epic 5)
# ---------------------------------------------------------------------------

class TestSkillFileIntegrity:
    """Verify all DRL skill files have valid YAML frontmatter and body."""

    def _all_skill_files(self):
        return list(DRL_SKILLS_DIR.glob("*/SKILL.md"))

    def test_all_skills_have_valid_frontmatter(self):
        """Every SKILL.md must parse as valid YAML frontmatter + markdown body."""
        for skill in self._all_skill_files():
            content = skill.read_text()
            assert content.startswith("---"), f"{skill} missing YAML frontmatter"
            parts = content.split("---", 2)
            assert len(parts) >= 3, f"{skill} malformed frontmatter"

            fm = yaml.safe_load(parts[1])
            assert isinstance(fm, dict), f"{skill} frontmatter is not a dict"
            assert "name" in fm, f"{skill} missing 'name' field"
            assert "description" in fm, f"{skill} missing 'description' field"

    def test_all_skills_have_nonempty_body(self):
        """Each skill should have meaningful content."""
        for skill in self._all_skill_files():
            body = _read_body(skill)
            assert len(body.strip()) > 100, (
                f"{skill.parent.name}/SKILL.md body too short ({len(body.strip())} chars)"
            )

    def test_skill_count_matches_expected(self):
        """Verify we have all expected DRL skills."""
        expected_skills = {
            "compile", "cook-it", "decision", "flavor", "lit-review",
            "methodology-review", "onboard", "research-architect",
            "research-plan", "research-spec", "research-work", "status",
            "synthesis",
        }
        actual_skills = {p.parent.name for p in self._all_skill_files()}
        missing = expected_skills - actual_skills
        assert not missing, f"Missing DRL skills: {missing}"


# ---------------------------------------------------------------------------
# Contract 9: Git commit before flavor edit (Epic 7 -> Git)
# ---------------------------------------------------------------------------

class TestFlavorGitSafety:
    """Flavor skill mandates git commit before editing skill files."""

    def test_flavor_mandates_git_commit(self):
        body = _read_body(DRL_SKILLS_DIR / "flavor" / "SKILL.md").lower()
        assert "git commit" in body or "git add" in body, (
            "flavor/SKILL.md must instruct git commit before editing"
        )

    def test_flavor_mentions_atomic_write(self):
        body = _read_body(DRL_SKILLS_DIR / "flavor" / "SKILL.md").lower()
        assert "atomic" in body or ("temp" in body and "rename" in body), (
            "flavor/SKILL.md must use atomic write pattern"
        )


# ---------------------------------------------------------------------------
# Cross-cutting: AGENTS.md consistency with actual files
# ---------------------------------------------------------------------------

class TestAgentsMdConsistency:
    """AGENTS.md must accurately reflect the agent and skill files on disk."""

    def test_research_phases_table_references_existing_skills(self):
        """Research Phases table in AGENTS.md references real skill files."""
        agents_md = (REPO_ROOT / "AGENTS.md").read_text()
        skill_refs = re.findall(
            r'`\.claude/skills/drl/([^/]+)/SKILL\.md`', agents_md
        )
        for ref in skill_refs:
            actual = DRL_SKILLS_DIR / ref / "SKILL.md"
            assert actual.is_file(), (
                f"AGENTS.md references skill {ref} but file does not exist"
            )

    def test_agent_role_table_references_existing_agents(self):
        """Research Agent Roles table in AGENTS.md references real agent files."""
        agents_md = (REPO_ROOT / "AGENTS.md").read_text()
        agent_refs = re.findall(
            r'`\.claude/agents/drl/([^`]+)`', agents_md
        )
        for ref in agent_refs:
            actual = REPO_ROOT / ".claude" / "agents" / "drl" / ref
            assert actual.is_file(), (
                f"AGENTS.md references agent {ref} but file does not exist"
            )


# ---------------------------------------------------------------------------
# Contract 10: drl setup scaffolding produces complete structure (E6)
# ---------------------------------------------------------------------------

class TestSetupScaffolding:
    """Verify drl setup installs complete scaffolding structure."""

    def test_creates_docs_decisions_template(self, setup_tmpdir):
        assert (setup_tmpdir / "docs" / "decisions" / "0000-template.md").is_file()

    def test_creates_docs_agent_notes(self, setup_tmpdir):
        assert (setup_tmpdir / "docs" / "agent_notes").is_dir()

    def test_creates_docs_researcher_notes(self, setup_tmpdir):
        assert (setup_tmpdir / "docs" / "researcher_notes").is_dir()

    def test_creates_literature_dirs(self, setup_tmpdir):
        assert (setup_tmpdir / "literature" / "pdfs").is_dir()
        assert (setup_tmpdir / "literature" / "notes").is_dir()

    def test_creates_paper_structure(self, setup_tmpdir):
        paper = setup_tmpdir / "paper"
        assert (paper / "main.tex").is_file()
        assert (paper / "Ref.bib").is_file()
        assert (paper / "compile.sh").is_file()
        assert os.access(paper / "compile.sh", os.X_OK)
        assert (paper / "outputs" / "figures").is_dir()
        assert (paper / "outputs" / "tables").is_dir()

    def test_creates_paper_sections(self, setup_tmpdir):
        sections = setup_tmpdir / "paper" / "sections"
        assert sections.is_dir()
        tex_files = sorted(f.name for f in sections.glob("*.tex"))
        expected = [
            "conclusion.tex", "data.tex", "intro.tex",
            "literature.tex", "methodology.tex", "results.tex",
            "robustness.tex",
        ]
        assert tex_files == expected

    def test_creates_src_structure(self, setup_tmpdir):
        src = setup_tmpdir / "src"
        assert (src / "__init__.py").is_file()
        assert (src / "config.py").is_file()
        assert (src / "data" / "loaders.py").is_file()
        assert (src / "data" / "cleaners.py").is_file()
        assert (src / "analysis" / "econometrics.py").is_file()
        assert (src / "analysis" / "descriptive.py").is_file()
        assert (src / "analysis" / "robustness.py").is_file()
        assert (src / "visualization" / "plots.py").is_file()
        assert (src / "orchestrators" / "repro.py").is_file()
        assert (src / "literature" / "extract.py").is_file()

    def test_creates_scaffolding_tests(self, setup_tmpdir):
        tests = setup_tmpdir / "tests"
        assert (tests / "conftest.py").is_file()
        assert (tests / "test_config.py").is_file()

    def test_creates_drl_docs(self, setup_tmpdir):
        docs = setup_tmpdir / "docs" / "drl"
        assert docs.is_dir()
        assert (docs / "research").is_dir()


class TestSetupCLAUDEMdContent:
    """Verify drl setup produces CLAUDE.md with correct markers."""

    def test_claudemd_has_drl_markers(self, setup_tmpdir):
        claude_md = setup_tmpdir / ".claude" / "CLAUDE.md"
        assert claude_md.is_file()
        content = claude_md.read_text()
        assert "dark-research-lab:claude-ref:start" in content
        assert "dark-research-lab:claude-ref:end" in content

    def test_claudemd_has_no_stale_compound_markers(self, setup_tmpdir):
        claude_md = setup_tmpdir / ".claude" / "CLAUDE.md"
        content = claude_md.read_text()
        assert "compound-agent:claude-ref:start" not in content

    def test_claudemd_has_drl_section(self, setup_tmpdir):
        claude_md = setup_tmpdir / ".claude" / "CLAUDE.md"
        content = claude_md.read_text()
        # Extract content between markers to avoid matching top-level heading
        start = content.find("dark-research-lab:claude-ref:start")
        end = content.find("dark-research-lab:claude-ref:end")
        assert start != -1 and end != -1, "Missing DRL marker block"
        block = content[start:end]
        assert "## Dark Research Lab" in block


# ---------------------------------------------------------------------------
# Contract 11: Infinity loop uses /drl:cook-it (AC-3)
# ---------------------------------------------------------------------------

class TestInfinityLoopNamespace:
    """Verify infinity-loop.sh uses DRL namespace, not compound."""

    def test_infinity_loop_uses_drl_cook_it(self):
        script = REPO_ROOT / "infinity-loop.sh"
        assert script.is_file(), "infinity-loop.sh not found"
        content = script.read_text()
        assert "/drl:cook-it" in content, (
            "infinity-loop.sh must use /drl:cook-it"
        )

    def test_infinity_loop_has_no_compound_cook_it(self):
        script = REPO_ROOT / "infinity-loop.sh"
        content = script.read_text()
        assert "/compound:cook-it" not in content, (
            "infinity-loop.sh must not reference /compound:cook-it"
        )


# ---------------------------------------------------------------------------
# Contract 12: Zero /compound: in shipped DRL templates (AC-4)
# ---------------------------------------------------------------------------

class TestZeroCompoundInDRLTemplates:
    """No /compound: namespace references in shipped DRL templates."""

    TEMPLATE_DIRS = [DRL_SKILLS_DIR, DRL_COMMANDS_DIR, DRL_AGENTS_DIR]

    def _scan_for_compound_refs(self):
        """Find all /compound: references in DRL template files."""
        hits = []
        for template_dir in self.TEMPLATE_DIRS:
            if not template_dir.is_dir():
                continue
            for md_file in template_dir.rglob("*.md"):
                content = md_file.read_text()
                for i, line in enumerate(content.splitlines(), 1):
                    if "/compound:" in line:
                        hits.append((md_file.relative_to(REPO_ROOT), i, line.strip()))
        return hits

    def test_no_compound_namespace_in_drl_skills(self):
        hits = self._scan_for_compound_refs()
        assert len(hits) == 0, (
            "Found /compound: references in DRL templates:\n"
            + "\n".join(f"  {f}:{ln}: {line}" for f, ln, line in hits)
        )
