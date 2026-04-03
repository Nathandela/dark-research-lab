package templates

import (
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"testing"
)

// findRepoRoot walks up from the test directory to find the repository root.
// It looks for go.mod (inside go/) then goes one level up.
func findRepoRoot(t *testing.T) string {
	t.Helper()
	wd, err := os.Getwd()
	if err != nil {
		t.Fatalf("Getwd: %v", err)
	}
	dir := wd
	for {
		if _, err := os.Stat(filepath.Join(dir, "go.mod")); err == nil {
			return filepath.Dir(dir) // go.mod is inside go/, repo root is one up
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			t.Skip("could not find repo root (go.mod)")
			return ""
		}
		dir = parent
	}
}

// TestTemplateDrift_ReviewFleetAgentsExist verifies that the DRL review
// skill references reviewer agent files that actually exist in the embedded
// agent templates. This catches drift where the review skill names agents
// that were renamed or removed from the embedded FS.
func TestTemplateDrift_ReviewFleetAgentsExist(t *testing.T) {
	review := requireSkill(t, PhaseSkills(), "review")
	agents := AgentTemplates()

	// DRL methodology review references 6 agent paths
	expectedAgents := []string{
		"methodology-reviewer",
		"robustness-checker",
		"coherence-reviewer",
		"citation-checker",
		"reproducibility-verifier",
		"writing-quality-reviewer",
	}

	for _, name := range expectedAgents {
		if !strings.Contains(review, name) {
			t.Errorf("review SKILL.md missing reference to %s agent", name)
		}
		// Verify the referenced agent actually exists in the embedded templates
		agentFile := name + ".md"
		if _, ok := agents[agentFile]; !ok {
			t.Errorf("review references agent %s but %s is missing from embedded agent templates", name, agentFile)
		}
	}

	t.Logf("verified %d reviewer agent references exist in embedded templates", len(expectedAgents))
}

// TestTemplateDrift_ResearchSourceMatchesEmbed verifies that the source
// research tree (docs/drl/research/) and the embedded copy
// (go/internal/setup/templates/docs/research/) contain exactly the same
// set of files. Catches drift when a file is added to the source but not
// copied into the embedded templates (or vice versa).
func TestTemplateDrift_ResearchSourceMatchesEmbed(t *testing.T) {
	repoRoot := findRepoRoot(t)

	sourceDir := filepath.Join(repoRoot, "docs", "drl", "research")
	if _, err := os.Stat(sourceDir); os.IsNotExist(err) {
		t.Skip("source research dir not found (running outside repo)")
		return
	}

	// Collect source files
	sourceFiles := make(map[string]bool)
	walkErr := filepath.Walk(sourceDir, func(p string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() {
			return err
		}
		rel, _ := filepath.Rel(sourceDir, p)
		sourceFiles[filepath.ToSlash(rel)] = true
		return nil
	})
	if walkErr != nil {
		t.Fatalf("walk source: %v", walkErr)
	}

	// Collect embedded files
	embeddedFiles := ResearchDocs()

	// Check source -> embedded
	for f := range sourceFiles {
		if _, ok := embeddedFiles[f]; !ok {
			t.Errorf("source file %q exists in docs/drl/research/ but not in embedded templates", f)
		}
	}

	// Check embedded -> source
	for f := range embeddedFiles {
		if !sourceFiles[f] {
			t.Errorf("embedded file %q exists in templates but not in docs/drl/research/", f)
		}
	}

	t.Logf("verified %d source files match %d embedded files", len(sourceFiles), len(embeddedFiles))
}

// TestTemplateDrift_ResearchReferencesResolve verifies that all
// docs/drl/research/ path references in skill and agent-role-skill
// templates point to files that exist in the embedded research tree.
// DRL skills primarily reference .claude/agents/drl/ and paper/ paths
// rather than docs/drl/research/, so this test validates any such
// references if present, but does not require them.
func TestTemplateDrift_ResearchReferencesResolve(t *testing.T) {
	researchDocs := ResearchDocs()

	// Build set of known research directories
	researchDirs := make(map[string]bool)
	for relPath := range researchDocs {
		for dir := filepath.Dir(relPath); dir != "." && dir != ""; dir = filepath.Dir(dir) {
			researchDirs[dir] = true
		}
	}

	// Pattern: docs/drl/research/some/path
	refRe := regexp.MustCompile("`docs/drl/research/([^`]+)`")

	matchCount := 0

	// Check all phase skills
	for phase, content := range PhaseSkills() {
		for _, m := range refRe.FindAllStringSubmatch(content, -1) {
			matchCount++
			checkResearchRef(t, "skill:"+phase, m[1], researchDocs, researchDirs)
		}
	}
	for relPath, content := range PhaseSkillReferences() {
		for _, m := range refRe.FindAllStringSubmatch(content, -1) {
			matchCount++
			checkResearchRef(t, "skill-ref:"+relPath, m[1], researchDocs, researchDirs)
		}
	}

	// Check all agent role skills
	for role, content := range AgentRoleSkills() {
		for _, m := range refRe.FindAllStringSubmatch(content, -1) {
			matchCount++
			checkResearchRef(t, "role:"+role, m[1], researchDocs, researchDirs)
		}
	}
	for relPath, content := range AgentRoleSkillReferences() {
		for _, m := range refRe.FindAllStringSubmatch(content, -1) {
			matchCount++
			checkResearchRef(t, "role-ref:"+relPath, m[1], researchDocs, researchDirs)
		}
	}

	if matchCount > 0 {
		t.Logf("validated %d research path references", matchCount)
	} else {
		// DRL skills reference .claude/agents/drl/ paths, not docs/drl/research/
		t.Skip("no docs/drl/research/ references in templates (DRL uses .claude/agents/drl/ paths)")
	}
}

// TestTemplateDrift_NoStaleCompoundPaths ensures that no embedded templates
// still reference the old compound/ namespace paths. This is a regression
// guard for the compound->drl namespace migration.
func TestTemplateDrift_NoStaleCompoundPaths(t *testing.T) {
	staleRe := regexp.MustCompile(`(?:skills|agents|commands|docs)/compound/`)

	check := func(label, content string) {
		for _, m := range staleRe.FindAllString(content, -1) {
			t.Errorf("%s contains stale compound namespace reference: %s", label, m)
		}
	}

	for phase, content := range PhaseSkills() {
		check("skill:"+phase, content)
	}
	for relPath, content := range PhaseSkillReferences() {
		check("skill-ref:"+relPath, content)
	}
	for role, content := range AgentRoleSkills() {
		check("role:"+role, content)
	}
	for relPath, content := range AgentRoleSkillReferences() {
		check("role-ref:"+relPath, content)
	}
	for name, content := range CommandTemplates() {
		check("command:"+name, content)
	}
	for name, content := range AgentTemplates() {
		check("agent:"+name, content)
	}
	for name, content := range DocTemplates() {
		check("doc:"+name, content)
	}
	for name, content := range ResearchDocs() {
		check("research:"+name, content)
	}
}

// checkResearchRef validates a single research path reference.
func checkResearchRef(t *testing.T, source, ref string, docs map[string]string, dirs map[string]bool) {
	t.Helper()
	ref = strings.TrimSuffix(ref, "/")
	// Could be a file or directory reference
	if _, ok := docs[ref]; ok {
		return // exact file match
	}
	if dirs[ref] {
		return // directory reference
	}
	t.Errorf("%s references docs/drl/research/%s which does not exist in embedded research tree", source, ref)
}
