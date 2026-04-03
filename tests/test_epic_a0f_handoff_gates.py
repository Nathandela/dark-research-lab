"""Verification tests for Epic a0f: Phase handoff precision and gate testability.

Tests the 5 acceptance criteria:
  AC1: Every phase skill has a Handoff Checklist section
  AC2: Subjective gate criteria have measurable sub-criteria
  AC3: cook-it has Phase 0: Architecture section
  AC4: Consistent gate numbering (Gate 1 through Gate 5)
  AC5: research-architect specifies structured epic description format
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DRL_SKILLS_DIR = REPO_ROOT / ".claude" / "skills" / "drl"

RESEARCH_PHASES = {
    "research-spec": "spec",
    "research-plan": "plan",
    "research-work": "work",
    "methodology-review": "review",
    "synthesis": "synthesis",
}

GATE_NUMBERS = {
    "research-spec": "Gate 1",
    "research-plan": "Gate 2",
    "methodology-review": "Gate 4",
    "synthesis": "Gate 5",
}


def _read_body(path: Path) -> str:
    content = path.read_text()
    parts = content.split("---", 2)
    return parts[2] if len(parts) >= 3 else ""


# ---------------------------------------------------------------------------
# AC1: Handoff Checklist in every phase skill
# ---------------------------------------------------------------------------

class TestHandoffChecklist:
    """Every phase skill has a Handoff Checklist section."""

    def test_all_phases_have_handoff_checklist_section(self):
        for phase_dir in RESEARCH_PHASES:
            body = _read_body(DRL_SKILLS_DIR / phase_dir / "SKILL.md")
            assert "## Handoff Checklist" in body or "### Handoff Checklist" in body, (
                f"{phase_dir}/SKILL.md missing Handoff Checklist section"
            )

    def test_handoff_lists_output_files(self):
        """Handoff Checklist mentions output files or locations."""
        for phase_dir in RESEARCH_PHASES:
            body = _read_body(DRL_SKILLS_DIR / phase_dir / "SKILL.md")
            # Find the handoff section
            idx = body.lower().find("handoff checklist")
            assert idx >= 0, f"{phase_dir} missing handoff checklist"
            handoff_section = body[idx:]
            # Must mention files/paths/outputs
            assert any(kw in handoff_section.lower() for kw in [
                "output", "file", "path", "location", "/", "docs/", "paper/"
            ]), f"{phase_dir} handoff checklist doesn't mention output files"

    def test_handoff_mentions_next_phase_retrieval(self):
        """Handoff Checklist explains how the next phase retrieves outputs."""
        # Only applies to phases 1-4 (synthesis has no next phase)
        non_terminal = ["research-spec", "research-plan", "research-work", "methodology-review"]
        for phase_dir in non_terminal:
            body = _read_body(DRL_SKILLS_DIR / phase_dir / "SKILL.md")
            idx = body.lower().find("handoff checklist")
            assert idx >= 0
            handoff_section = body[idx:]
            assert any(kw in handoff_section.lower() for kw in [
                "next phase", "retriev", "reads", "consumes", "picks up",
                "research-plan", "research-work", "methodology-review", "synthesis",
            ]), f"{phase_dir} handoff doesn't explain how next phase retrieves outputs"


# ---------------------------------------------------------------------------
# AC2: Measurable sub-criteria for subjective gates
# ---------------------------------------------------------------------------

class TestMeasurableGateCriteria:
    """Subjective gate criteria have measurable sub-criteria added."""

    def test_spec_gate_has_measurable_rq_check(self):
        """'Research question is specific' must have grep-checkable or checklist criteria."""
        body = _read_body(DRL_SKILLS_DIR / "research-spec" / "SKILL.md")
        gate_idx = body.lower().find("gate")
        gate_section = body[gate_idx:]
        # Must have concrete verification beyond just "review"
        assert any(kw in gate_section.lower() for kw in [
            "grep", "checklist", "contains", "pattern", "must include",
            "answerable", "measurable", "falsifiable",
        ]), "Spec gate 'RQ is specific' needs measurable sub-criteria"

    def test_review_gate_has_measurable_methodology_check(self):
        """'Statistical methodology sound' must have enumerated checks."""
        body = _read_body(DRL_SKILLS_DIR / "methodology-review" / "SKILL.md")
        gate_idx = body.lower().find("gate")
        gate_section = body[gate_idx:]
        # Must enumerate specific checks, not just "subagent approved"
        assert any(kw in gate_section.lower() for kw in [
            "assumption", "identification", "standard error", "coefficient",
            "endogeneity", "p0", "critical",
        ]), "Review gate 'methodology sound' needs enumerated checks"

    def test_plan_gate_has_measurable_robustness_check(self):
        """Robustness plan criterion must have a countable check."""
        body = _read_body(DRL_SKILLS_DIR / "research-plan" / "SKILL.md")
        gate_idx = body.lower().find("gate")
        gate_section = body[gate_idx:]
        assert any(kw in gate_section.lower() for kw in [
            "count", "2+", "at least", "minimum", ">=",
        ]), "Plan gate robustness criterion needs countable check"


# ---------------------------------------------------------------------------
# AC3: cook-it includes Phase 0: Architecture
# ---------------------------------------------------------------------------

class TestCookItPhaseZero:
    """cook-it/SKILL.md includes Phase 0: Architecture."""

    def test_cook_it_has_phase_zero(self):
        body = _read_body(DRL_SKILLS_DIR / "cook-it" / "SKILL.md")
        assert "Phase 0" in body, "cook-it missing Phase 0"

    def test_phase_zero_references_architect(self):
        body = _read_body(DRL_SKILLS_DIR / "cook-it" / "SKILL.md")
        # Find Phase 0 section
        idx = body.find("Phase 0")
        assert idx >= 0
        phase0_section = body[idx:idx + 500]
        assert any(kw in phase0_section for kw in [
            "drl:architect", "research-architect", "architect",
        ]), "Phase 0 must reference /drl:architect as entry point"

    def test_phase_zero_is_before_phase_one(self):
        body = _read_body(DRL_SKILLS_DIR / "cook-it" / "SKILL.md")
        idx0 = body.find("Phase 0")
        idx1 = body.find("Phase 1")
        assert idx0 < idx1, "Phase 0 must appear before Phase 1"


# ---------------------------------------------------------------------------
# AC4: Consistent gate numbering
# ---------------------------------------------------------------------------

class TestConsistentGateNumbering:
    """All phases use Gate 1 through Gate 5 consistently."""

    def test_spec_uses_gate_1(self):
        body = _read_body(DRL_SKILLS_DIR / "research-spec" / "SKILL.md")
        assert "Gate 1" in body, "research-spec should use Gate 1"

    def test_plan_uses_gate_2(self):
        body = _read_body(DRL_SKILLS_DIR / "research-plan" / "SKILL.md")
        assert "Gate 2" in body, "research-plan should use Gate 2"

    def test_work_uses_gate_3(self):
        body = _read_body(DRL_SKILLS_DIR / "research-work" / "SKILL.md")
        assert "Gate 3" in body, "research-work should use Gate 3"

    def test_review_uses_gate_4(self):
        body = _read_body(DRL_SKILLS_DIR / "methodology-review" / "SKILL.md")
        assert "Gate 4" in body, "methodology-review should use Gate 4"

    def test_synthesis_uses_gate_5(self):
        body = _read_body(DRL_SKILLS_DIR / "synthesis" / "SKILL.md")
        assert "Gate 5" in body, "synthesis should use Gate 5"

    def test_cook_it_uses_all_gate_numbers(self):
        """cook-it references Gate 1 through Gate 5."""
        body = _read_body(DRL_SKILLS_DIR / "cook-it" / "SKILL.md")
        for i in range(1, 6):
            assert f"Gate {i}" in body, f"cook-it missing Gate {i}"


# ---------------------------------------------------------------------------
# AC5: Structured epic description format in research-architect
# ---------------------------------------------------------------------------

class TestStructuredEpicFormat:
    """research-architect specifies structured format for epic descriptions."""

    REQUIRED_SECTIONS = [
        "Scope",
        "EARS",
        "Contracts",
        "Assumptions",
        "Roles",
        "Decisions",
    ]

    def test_architect_specifies_epic_format(self):
        body = _read_body(DRL_SKILLS_DIR / "research-architect" / "SKILL.md")
        for section in self.REQUIRED_SECTIONS:
            assert section in body, (
                f"research-architect missing '{section}' in epic description format"
            )

    def test_architect_has_structured_format_section(self):
        """There is an explicit section describing the epic format."""
        body = _read_body(DRL_SKILLS_DIR / "research-architect" / "SKILL.md").lower()
        assert any(kw in body for kw in [
            "epic description format", "structured format", "epic structure",
            "description template", "epic template",
        ]), "research-architect missing explicit epic description format section"
