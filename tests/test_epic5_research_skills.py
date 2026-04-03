"""Verification tests for Epic 5: Core Research Skills.

Tests that all 5 research phase SKILL.md files exist at the correct paths,
follow the skill-as-instruction-file pattern, and satisfy the epic's
verification contract.
"""
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
DRL_SKILLS_DIR = REPO_ROOT / ".claude" / "skills" / "drl"

# The 5 research phases and their expected directory names + phase values
RESEARCH_PHASES = {
    "research-spec": "spec",
    "research-plan": "plan",
    "research-work": "work",
    "methodology-review": "review",
    "synthesis": "synthesis",
}

# Agent names from Epic 6 contract (AGENTS.md)
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


class TestSkillDirectoryStructure:
    """Each SKILL.md exists at .claude/skills/drl/{phase-name}/SKILL.md."""

    def test_drl_skills_directory_exists(self):
        assert DRL_SKILLS_DIR.is_dir(), f"Missing directory: {DRL_SKILLS_DIR}"

    def test_all_phase_directories_exist(self):
        for phase_dir in RESEARCH_PHASES:
            path = DRL_SKILLS_DIR / phase_dir
            assert path.is_dir(), f"Missing phase directory: {path}"

    def test_all_skill_files_exist(self):
        for phase_dir in RESEARCH_PHASES:
            skill = DRL_SKILLS_DIR / phase_dir / "SKILL.md"
            assert skill.is_file(), f"Missing SKILL.md: {skill}"


class TestSkillFrontmatter:
    """YAML frontmatter with name, description, phase fields."""

    def test_all_skills_have_valid_frontmatter(self):
        for phase_dir in RESEARCH_PHASES:
            fm = _parse_frontmatter(DRL_SKILLS_DIR / phase_dir / "SKILL.md")
            assert isinstance(fm, dict), f"{phase_dir}/SKILL.md frontmatter is not a dict"

    def test_all_skills_have_name_field(self):
        for phase_dir in RESEARCH_PHASES:
            fm = _parse_frontmatter(DRL_SKILLS_DIR / phase_dir / "SKILL.md")
            assert "name" in fm, f"{phase_dir}/SKILL.md missing 'name' field"
            assert isinstance(fm["name"], str) and len(fm["name"]) > 0

    def test_all_skills_have_description_field(self):
        for phase_dir in RESEARCH_PHASES:
            fm = _parse_frontmatter(DRL_SKILLS_DIR / phase_dir / "SKILL.md")
            assert "description" in fm, f"{phase_dir}/SKILL.md missing 'description' field"
            assert isinstance(fm["description"], str) and len(fm["description"]) > 0

    def test_all_skills_have_correct_phase_field(self):
        for phase_dir, expected_phase in RESEARCH_PHASES.items():
            fm = _parse_frontmatter(DRL_SKILLS_DIR / phase_dir / "SKILL.md")
            assert "phase" in fm, f"{phase_dir}/SKILL.md missing 'phase' field"
            assert fm["phase"] == expected_phase, (
                f"{phase_dir}/SKILL.md phase is '{fm['phase']}', expected '{expected_phase}'"
            )


class TestSkillBodyContent:
    """Skills have substantial body content with required sections."""

    def test_all_skills_have_body_content(self):
        for phase_dir in RESEARCH_PHASES:
            body = _read_body(DRL_SKILLS_DIR / phase_dir / "SKILL.md")
            assert len(body.strip()) > 200, (
                f"{phase_dir}/SKILL.md body too short (likely empty)"
            )

    def test_all_skills_have_gate_criteria(self):
        """Gate criteria are explicit and testable."""
        for phase_dir in RESEARCH_PHASES:
            body = _read_body(DRL_SKILLS_DIR / phase_dir / "SKILL.md").lower()
            assert "gate" in body, (
                f"{phase_dir}/SKILL.md missing gate criteria"
            )


class TestAgentReferences:
    """Agent references use correct names from Epic 6 contract."""

    def test_research_spec_references_literature_analyst(self):
        body = _read_body(DRL_SKILLS_DIR / "research-spec" / "SKILL.md").lower()
        assert "literature-analyst" in body or "literature analyst" in body

    def test_research_work_references_analyst(self):
        body = _read_body(DRL_SKILLS_DIR / "research-work" / "SKILL.md").lower()
        assert "analyst" in body

    def test_methodology_review_references_reviewers(self):
        body = _read_body(DRL_SKILLS_DIR / "methodology-review" / "SKILL.md").lower()
        expected_refs = [
            "methodology-reviewer",
            "coherence-reviewer",
            "citation-checker",
            "reproducibility-verifier",
            "writing-quality-reviewer",
        ]
        for ref in expected_refs:
            assert ref in body, (
                f"methodology-review/SKILL.md missing agent reference: {ref}"
            )

    def test_methodology_review_references_robustness_checker(self):
        body = _read_body(DRL_SKILLS_DIR / "methodology-review" / "SKILL.md").lower()
        assert "robustness-checker" in body


class TestDecisionLogging:
    """Work skill integrates decision logging (Epic 2 contract)."""

    def test_work_skill_references_decision_logging(self):
        body = _read_body(DRL_SKILLS_DIR / "research-work" / "SKILL.md").lower()
        assert "docs/decisions/" in body or "decision" in body

    def test_work_skill_references_adr(self):
        body = _read_body(DRL_SKILLS_DIR / "research-work" / "SKILL.md").lower()
        assert "adr" in body or "decision log" in body


class TestLatexCompileGate:
    """Synthesis skill includes LaTeX compile as gate (H4 mitigation)."""

    def test_synthesis_references_latex_compilation(self):
        body = _read_body(DRL_SKILLS_DIR / "synthesis" / "SKILL.md").lower()
        assert "latex" in body or "pdflatex" in body

    def test_synthesis_references_compile_script(self):
        body = _read_body(DRL_SKILLS_DIR / "synthesis" / "SKILL.md").lower()
        assert "compile" in body

    def test_synthesis_references_refs_resolve(self):
        body = _read_body(DRL_SKILLS_DIR / "synthesis" / "SKILL.md").lower()
        assert "ref" in body


class TestPaperPathReferences:
    """Skills reference paper/src paths from Epic 3 contract."""

    def test_work_skill_references_paper_outputs(self):
        body = _read_body(DRL_SKILLS_DIR / "research-work" / "SKILL.md")
        assert "paper/outputs/tables/" in body or "paper/outputs/figures/" in body

    def test_synthesis_references_paper_main(self):
        body = _read_body(DRL_SKILLS_DIR / "synthesis" / "SKILL.md")
        assert "paper/main.tex" in body or "paper/" in body


class TestPhaseGateSpecificity:
    """Each phase has specific, testable gate criteria."""

    def test_spec_gate_rq_and_hypotheses(self):
        body = _read_body(DRL_SKILLS_DIR / "research-spec" / "SKILL.md").lower()
        assert "research question" in body or "rq" in body
        assert "hypothes" in body

    def test_plan_gate_methodology_approved(self):
        body = _read_body(DRL_SKILLS_DIR / "research-plan" / "SKILL.md").lower()
        assert "methodolog" in body

    def test_work_gate_analyses_complete(self):
        body = _read_body(DRL_SKILLS_DIR / "research-work" / "SKILL.md").lower()
        assert "analy" in body

    def test_review_gate_checks_pass(self):
        body = _read_body(DRL_SKILLS_DIR / "methodology-review" / "SKILL.md").lower()
        assert "check" in body or "pass" in body

    def test_synthesis_gate_compiles(self):
        body = _read_body(DRL_SKILLS_DIR / "synthesis" / "SKILL.md").lower()
        assert "compile" in body


class TestResearchSpecificity:
    """Skills use research vocabulary, not software dev."""

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

    def test_skills_avoid_software_dev_vocabulary(self):
        for phase_dir in RESEARCH_PHASES:
            content = (DRL_SKILLS_DIR / phase_dir / "SKILL.md").read_text().lower()
            found = [t for t in self.SOFTWARE_DEV_TERMS if t in content]
            assert not found, (
                f"{phase_dir}/SKILL.md contains software dev terms: {found}"
            )

    def test_skills_use_research_vocabulary(self):
        research_terms = [
            "research",
            "methodolog",
            "statistical",
            "hypothesis",
            "analysis",
            "paper",
        ]
        for phase_dir in RESEARCH_PHASES:
            content = (DRL_SKILLS_DIR / phase_dir / "SKILL.md").read_text().lower()
            has_research = any(term in content for term in research_terms)
            assert has_research, (
                f"{phase_dir}/SKILL.md lacks research-specific vocabulary"
            )


class TestResearchPlanContent:
    """Research-plan skill has required planning elements."""

    def test_plan_references_variable_operationalization(self):
        body = _read_body(DRL_SKILLS_DIR / "research-plan" / "SKILL.md").lower()
        assert "operationaliz" in body

    def test_plan_references_model_equations(self):
        body = _read_body(DRL_SKILLS_DIR / "research-plan" / "SKILL.md").lower()
        assert "equation" in body or "model" in body

    def test_plan_references_robustness(self):
        body = _read_body(DRL_SKILLS_DIR / "research-plan" / "SKILL.md").lower()
        assert "robustness" in body

    def test_plan_references_traceability_mapping(self):
        body = _read_body(DRL_SKILLS_DIR / "research-plan" / "SKILL.md").lower()
        assert "hypothesis" in body and ("section" in body or "mapping" in body)
