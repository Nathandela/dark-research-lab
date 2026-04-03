package templates

import (
	"strings"
	"testing"
)

// TestIntegrationVerification_LiteratureSufficiencyGate verifies the research
// sufficiency gate in architect Phase 1.
func TestIntegrationVerification_LiteratureSufficiencyGate(t *testing.T) {
	architect := requireSkill(t, PhaseSkills(), "architect")

	t.Run("gate_exists", func(t *testing.T) {
		assertContains(t, architect, "Literature Sufficiency Gate", "missing gate section")
	})
	t.Run("3_source_minimum", func(t *testing.T) {
		assertContains(t, architect, "fewer than 3", "missing 3-source minimum")
	})
	t.Run("search_round_cap", func(t *testing.T) {
		assertContains(t, architect, "3 search rounds", "missing search round limit")
	})
}

// TestIntegrationVerification_IVCreationContract verifies that architect Phase 4
// creates an Integration Verification epic with dependency wiring.
func TestIntegrationVerification_IVCreationContract(t *testing.T) {
	architect := requireSkill(t, PhaseSkills(), "architect")

	t.Run("IV_section_exists", func(t *testing.T) {
		assertContains(t, architect, "Integration Verification", "missing IV section")
	})
	t.Run("IV_in_phase_4", func(t *testing.T) {
		phase4Idx := strings.Index(architect, "## Phase 4")
		ivIdx := strings.Index(architect, "Integration Verification")
		if phase4Idx < 0 || ivIdx < 0 {
			t.Fatal("missing Phase 4 or IV section")
		}
		if ivIdx < phase4Idx {
			t.Error("IV section appears before Phase 4")
		}
	})
	t.Run("dependency_wiring", func(t *testing.T) {
		assertContains(t, architect, "bd dep add", "missing dep wiring instruction")
	})
	t.Run("cook_it_pipeline", func(t *testing.T) {
		assertContains(t, architect, "cook-it", "missing cook-it reference")
	})
}

// TestIntegrationVerification_ReviewCoherence verifies that the review SKILL.md
// is internally consistent with 6 reviewer fleet and severity classification.
func TestIntegrationVerification_ReviewCoherence(t *testing.T) {
	review := requireSkill(t, PhaseSkills(), "review")

	t.Run("methodology_steps_sequential", func(t *testing.T) {
		// Verify all 4 steps exist AND are in sequential order
		steps := []string{"### Step 1", "### Step 2", "### Step 3", "### Step 4"}
		prevIdx := -1
		for i, step := range steps {
			idx := strings.Index(review, step)
			if idx < 0 {
				t.Fatalf("missing %s", step)
			}
			if idx <= prevIdx {
				t.Errorf("Step %d (pos %d) is not after Step %d (pos %d)", i+1, idx, i, prevIdx)
			}
			prevIdx = idx
		}
		t.Logf("verified %d methodology steps in sequential order", len(steps))
	})
	t.Run("six_reviewers_present", func(t *testing.T) {
		assertContains(t, review, "methodology-reviewer", "missing methodology-reviewer")
		assertContains(t, review, "robustness-checker", "missing robustness-checker")
		assertContains(t, review, "coherence-reviewer", "missing coherence-reviewer")
		assertContains(t, review, "citation-checker", "missing citation-checker")
		assertContains(t, review, "reproducibility-verifier", "missing reproducibility-verifier")
		assertContains(t, review, "writing-quality-reviewer", "missing writing-quality-reviewer")
	})
	t.Run("severity_classification_present", func(t *testing.T) {
		assertContains(t, review, "Critical", "missing Critical severity")
		assertContains(t, review, "Major", "missing Major severity")
		assertContains(t, review, "Minor", "missing Minor severity")
	})
	t.Run("no_duplicate_sections", func(t *testing.T) {
		for _, section := range []string{
			"## Gate Criteria", "## Quality Criteria",
			"## Common Pitfalls", "## Memory Integration",
		} {
			if c := strings.Count(review, section); c > 1 {
				t.Errorf("duplicate section: %s (found %d times)", section, c)
			}
		}
	})
}

// TestIntegrationVerification_SmokeTestMarkers verifies that each DRL phase
// skill has key verifiable markers.
func TestIntegrationVerification_SmokeTestMarkers(t *testing.T) {
	skills := PhaseSkills()

	t.Run("spec_has_hypothesis_generation", func(t *testing.T) {
		assertContains(t, skills["spec-dev"], "Hypothesis Generation", "spec missing hypothesis generation")
	})
	t.Run("plan_has_variable_operationalization", func(t *testing.T) {
		assertContains(t, skills["plan"], "Variable Operationalization", "plan missing operationalization")
	})
	t.Run("work_has_analysis_pipeline", func(t *testing.T) {
		assertContains(t, skills["work"], "Analysis Pipeline", "work missing analysis pipeline")
	})
	t.Run("review_has_review_fleet", func(t *testing.T) {
		assertContains(t, skills["review"], "Spawn Review Fleet", "review missing review fleet")
	})
	t.Run("compound_has_latex_compile", func(t *testing.T) {
		assertContains(t, skills["compound"], "LaTeX Compilation", "compound missing LaTeX compilation")
	})
	t.Run("architect_has_socratic_phase", func(t *testing.T) {
		assertContains(t, skills["architect"], "Socratic", "architect missing Socratic phase")
	})
	t.Run("cook_it_has_five_phases", func(t *testing.T) {
		assertContains(t, skills["cook-it"], "Phase 1: Specification", "cook-it missing Phase 1")
		assertContains(t, skills["cook-it"], "Phase 5: Synthesis", "cook-it missing Phase 5")
	})
}

// TestIntegrationVerification_CookItGatesBetweenPhases verifies that cook-it
// has gate criteria between research phases.
func TestIntegrationVerification_CookItGatesBetweenPhases(t *testing.T) {
	cookIt := requireSkill(t, PhaseSkills(), "cook-it")

	t.Run("gate_criteria_mentioned", func(t *testing.T) {
		assertContains(t, cookIt, "Gate", "missing gate references")
	})
	t.Run("phases_in_order", func(t *testing.T) {
		specIdx := strings.Index(cookIt, "Phase 1: Specification")
		planIdx := strings.Index(cookIt, "Phase 2: Planning")
		workIdx := strings.Index(cookIt, "Phase 3: Work")
		reviewIdx := strings.Index(cookIt, "Phase 4: Review")
		synthIdx := strings.Index(cookIt, "Phase 5: Synthesis")

		if specIdx < 0 || planIdx < 0 || workIdx < 0 || reviewIdx < 0 || synthIdx < 0 {
			t.Fatal("missing one or more phase section headers")
		}
		if specIdx > planIdx || planIdx > workIdx || workIdx > reviewIdx || reviewIdx > synthIdx {
			t.Error("phases are not in expected order: spec -> plan -> work -> review -> synthesis")
		}
	})
	t.Run("decision_logging_integration", func(t *testing.T) {
		assertContains(t, cookIt, "docs/decisions/", "cook-it missing decision log path")
	})
}
