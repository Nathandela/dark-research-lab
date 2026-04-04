package templates

import (
	"strings"
	"testing"
)

// requireSkill loads a phase skill template, failing the test if missing.
func requireSkill(t *testing.T, skills map[string]string, name string) string {
	t.Helper()
	content, ok := skills[name]
	if !ok {
		t.Fatalf("missing %s skill template", name)
	}
	return content
}

// assertContains checks that content contains substr, reporting msg on failure.
func assertContains(t *testing.T, content, substr, msg string) {
	t.Helper()
	if !strings.Contains(content, substr) {
		t.Error(msg)
	}
}

// TestIntegrationVerification_GateCriteriaFlowContract verifies the behavioral
// contract between research phases: plan generates methodology tables, review
// checks them, work executes them.
func TestIntegrationVerification_GateCriteriaFlowContract(t *testing.T) {
	skills := PhaseSkills()
	plan := requireSkill(t, skills, "plan")
	review := requireSkill(t, skills, "review")
	work := requireSkill(t, skills, "work")

	t.Run("plan_generates_methodology_tables", func(t *testing.T) {
		assertContains(t, plan, "Variable Operationalization", "missing variable operationalization section")
		assertContains(t, plan, "Model Equations", "missing model equations section")
		assertContains(t, plan, "Robustness Plan", "missing robustness plan section")
		assertContains(t, plan, "Hypothesis-Analysis-Output-Section Mapping", "missing traceability mapping")
	})

	t.Run("review_checks_methodology", func(t *testing.T) {
		// The review skill's Paper Review Fleet covers these dimensions via named reviewers
		assertContains(t, review, "methodology-reviewer", "missing methodology-reviewer (statistical validity)")
		assertContains(t, review, "robustness-checker", "missing robustness-checker (robustness assessment)")
		assertContains(t, review, "coherence-reviewer", "missing coherence-reviewer (logical consistency)")
		assertContains(t, review, "citation-checker", "missing citation-checker (citation accuracy)")
	})

	t.Run("work_executes_plan", func(t *testing.T) {
		// The work router delegates analysis to work-analysis sub-skill;
		// verify the sub-skill has the plan execution details.
		workAnalysis := requireSkill(t, skills, "work-analysis")
		assertContains(t, workAnalysis, "operationalization", "missing operationalization reference")
		assertContains(t, workAnalysis, "paper/outputs/tables/", "missing tables output path")
		// Router itself must reference sub-skills
		assertContains(t, work, "work-analysis", "work router missing work-analysis reference")
	})

	t.Run("gate_criteria_consistency", func(t *testing.T) {
		header := "## Gate Criteria"
		assertContains(t, plan, header, "plan missing Gate Criteria")
		assertContains(t, review, header, "review missing Gate Criteria")
		assertContains(t, work, header, "work missing Gate Criteria")
	})
}

// TestIntegrationVerification_LessonStoreContract verifies that the review
// template references lesson search for calibration.
func TestIntegrationVerification_LessonStoreContract(t *testing.T) {
	skills := PhaseSkills()
	review := skills["review"]

	t.Run("review_template_references_lesson_search", func(t *testing.T) {
		assertContains(t, review, "drl search", "review missing drl search reference")
	})

	t.Run("review_template_references_lesson_learn", func(t *testing.T) {
		assertContains(t, review, "drl learn", "review missing drl learn reference")
	})
}

// TestIntegrationVerification_ReviewFleetContract verifies that the review
// skill references the 6 specialized reviewer agents used in methodology review.
func TestIntegrationVerification_ReviewFleetContract(t *testing.T) {
	skills := PhaseSkills()
	review := requireSkill(t, skills, "review")

	t.Run("six_reviewer_dimensions", func(t *testing.T) {
		assertContains(t, review, "methodology-reviewer", "missing methodology-reviewer agent reference")
		assertContains(t, review, "robustness-checker", "missing robustness-checker agent reference")
		assertContains(t, review, "coherence-reviewer", "missing coherence-reviewer agent reference")
		assertContains(t, review, "citation-checker", "missing citation-checker agent reference")
		assertContains(t, review, "reproducibility-verifier", "missing reproducibility-verifier agent reference")
		assertContains(t, review, "writing-quality-reviewer", "missing writing-quality-reviewer agent reference")
	})

	t.Run("severity_classification", func(t *testing.T) {
		assertContains(t, review, "Critical", "missing critical severity level")
		assertContains(t, review, "Major", "missing major severity level")
		assertContains(t, review, "Minor", "missing minor severity level")
	})

	t.Run("test_requirement", func(t *testing.T) {
		assertContains(t, review, "uv run python -m pytest", "missing pytest execution reference")
	})
}

// TestIntegrationVerification_DecisionLogContract verifies that work and review
// phases reference ADR decision logging.
func TestIntegrationVerification_DecisionLogContract(t *testing.T) {
	skills := PhaseSkills()
	work := requireSkill(t, skills, "work")
	review := requireSkill(t, skills, "review")
	compound := requireSkill(t, skills, "compound")

	t.Run("work_logs_decisions", func(t *testing.T) {
		assertContains(t, work, "docs/decisions/", "work missing decision log path")
		assertContains(t, work, "ADR", "work missing ADR reference")
	})

	t.Run("review_checks_decisions", func(t *testing.T) {
		assertContains(t, review, "docs/decisions/", "review missing decision log path")
	})

	t.Run("compound_reviews_decisions", func(t *testing.T) {
		assertContains(t, compound, "docs/decisions/", "compound missing decision log path")
	})
}
