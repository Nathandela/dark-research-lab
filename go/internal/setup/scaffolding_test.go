package setup

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/nathandelacretaz/dark-research-lab/internal/setup/templates"
)

func TestInstallPaperScaffolding(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()

	created, updated, err := InstallPaperScaffolding(dir)
	if err != nil {
		t.Fatalf("InstallPaperScaffolding: %v", err)
	}
	if created == 0 {
		t.Error("expected files to be created")
	}
	if updated != 0 {
		t.Errorf("expected 0 updated on first run, got %d", updated)
	}

	// Verify key files exist
	for _, rel := range []string{
		"paper/main.tex",
		"paper/compile.sh",
		"paper/Ref.bib",
		"paper/sections/intro.tex",
		"paper/sections/conclusion.tex",
		"paper/outputs/figures/.gitkeep",
		"paper/outputs/tables/.gitkeep",
	} {
		path := filepath.Join(dir, rel)
		if _, err := os.Stat(path); os.IsNotExist(err) {
			t.Errorf("expected %s to exist", rel)
		}
	}

	// Verify count matches template map
	expected := len(templates.PaperScaffolding())
	if created != expected {
		t.Errorf("created %d files, expected %d", created, expected)
	}
}

func TestInstallPaperScaffolding_Idempotent(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()

	if _, _, err := InstallPaperScaffolding(dir); err != nil {
		t.Fatalf("first call: %v", err)
	}

	created, updated, err := InstallPaperScaffolding(dir)
	if err != nil {
		t.Fatalf("second call: %v", err)
	}
	if created != 0 {
		t.Errorf("expected 0 created on second run, got %d", created)
	}
	if updated != 0 {
		t.Errorf("expected 0 updated on second run, got %d", updated)
	}
}

func TestInstallSrcScaffolding(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()

	created, updated, err := InstallSrcScaffolding(dir)
	if err != nil {
		t.Fatalf("InstallSrcScaffolding: %v", err)
	}
	if created == 0 {
		t.Error("expected files to be created")
	}
	if updated != 0 {
		t.Errorf("expected 0 updated on first run, got %d", updated)
	}

	// Verify key files exist
	for _, rel := range []string{
		"src/__init__.py",
		"src/config.py",
		"src/data/loaders.py",
		"src/data/cleaners.py",
		"src/analysis/descriptive.py",
		"src/analysis/econometrics.py",
		"src/visualization/plots.py",
		"src/literature/extract.py",
		"src/orchestrators/repro.py",
	} {
		path := filepath.Join(dir, rel)
		if _, err := os.Stat(path); os.IsNotExist(err) {
			t.Errorf("expected %s to exist", rel)
		}
	}

	expected := len(templates.SrcScaffolding())
	if created != expected {
		t.Errorf("created %d files, expected %d", created, expected)
	}
}

func TestInstallSrcScaffolding_Idempotent(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()

	if _, _, err := InstallSrcScaffolding(dir); err != nil {
		t.Fatalf("first call: %v", err)
	}

	created, updated, err := InstallSrcScaffolding(dir)
	if err != nil {
		t.Fatalf("second call: %v", err)
	}
	if created != 0 {
		t.Errorf("expected 0 created on second run, got %d", created)
	}
	if updated != 0 {
		t.Errorf("expected 0 updated on second run, got %d", updated)
	}
}

func TestInstallLiteratureSetup(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()

	created, updated, err := InstallLiteratureSetup(dir)
	if err != nil {
		t.Fatalf("InstallLiteratureSetup: %v", err)
	}
	if created == 0 {
		t.Error("expected files to be created")
	}
	if updated != 0 {
		t.Errorf("expected 0 updated on first run, got %d", updated)
	}

	for _, rel := range []string{
		"literature/pdfs/.gitkeep",
		"literature/notes/.gitkeep",
	} {
		path := filepath.Join(dir, rel)
		if _, err := os.Stat(path); os.IsNotExist(err) {
			t.Errorf("expected %s to exist", rel)
		}
	}

	expected := len(templates.LiteratureScaffolding())
	if created != expected {
		t.Errorf("created %d files, expected %d", created, expected)
	}
}

func TestInstallLiteratureSetup_Idempotent(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()

	if _, _, err := InstallLiteratureSetup(dir); err != nil {
		t.Fatalf("first call: %v", err)
	}

	created, updated, err := InstallLiteratureSetup(dir)
	if err != nil {
		t.Fatalf("second call: %v", err)
	}
	if created != 0 {
		t.Errorf("expected 0 created, got %d", created)
	}
	if updated != 0 {
		t.Errorf("expected 0 updated, got %d", updated)
	}
}

func TestInstallDocsStructure(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()

	created, updated, err := InstallDocsStructure(dir)
	if err != nil {
		t.Fatalf("InstallDocsStructure: %v", err)
	}
	if created == 0 {
		t.Error("expected files to be created")
	}
	if updated != 0 {
		t.Errorf("expected 0 updated on first run, got %d", updated)
	}

	for _, rel := range []string{
		"docs/decisions/0000-template.md",
		"docs/researcher_notes/.gitkeep",
		"docs/agent_notes/.gitkeep",
	} {
		path := filepath.Join(dir, rel)
		if _, err := os.Stat(path); os.IsNotExist(err) {
			t.Errorf("expected %s to exist", rel)
		}
	}

	expected := len(templates.DocsScaffolding())
	if created != expected {
		t.Errorf("created %d files, expected %d", created, expected)
	}
}

func TestInstallDocsStructure_Idempotent(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()

	if _, _, err := InstallDocsStructure(dir); err != nil {
		t.Fatalf("first call: %v", err)
	}

	created, updated, err := InstallDocsStructure(dir)
	if err != nil {
		t.Fatalf("second call: %v", err)
	}
	if created != 0 {
		t.Errorf("expected 0 created, got %d", created)
	}
	if updated != 0 {
		t.Errorf("expected 0 updated, got %d", updated)
	}
}

func TestInstallTestsScaffolding(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()

	created, updated, err := InstallTestsScaffolding(dir)
	if err != nil {
		t.Fatalf("InstallTestsScaffolding: %v", err)
	}
	if created == 0 {
		t.Error("expected files to be created")
	}
	if updated != 0 {
		t.Errorf("expected 0 updated on first run, got %d", updated)
	}

	for _, rel := range []string{
		"tests/__init__.py",
		"tests/conftest.py",
		"tests/test_config.py",
	} {
		path := filepath.Join(dir, rel)
		if _, err := os.Stat(path); os.IsNotExist(err) {
			t.Errorf("expected %s to exist", rel)
		}
	}

	expected := len(templates.TestsScaffolding())
	if created != expected {
		t.Errorf("created %d files, expected %d", created, expected)
	}
}

func TestInstallTestsScaffolding_Idempotent(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()

	if _, _, err := InstallTestsScaffolding(dir); err != nil {
		t.Fatalf("first call: %v", err)
	}

	created, updated, err := InstallTestsScaffolding(dir)
	if err != nil {
		t.Fatalf("second call: %v", err)
	}
	if created != 0 {
		t.Errorf("expected 0 created, got %d", created)
	}
	if updated != 0 {
		t.Errorf("expected 0 updated, got %d", updated)
	}
}

func TestScaffolding_PreservesUserEdits(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()

	// Install paper scaffolding
	if _, _, err := InstallPaperScaffolding(dir); err != nil {
		t.Fatalf("first install: %v", err)
	}

	// Modify a file (simulates user editing the scaffolded file)
	mainTex := filepath.Join(dir, "paper", "main.tex")
	userContent := "user modified content"
	if err := os.WriteFile(mainTex, []byte(userContent), 0644); err != nil {
		t.Fatalf("modify file: %v", err)
	}

	created, updated, err := InstallPaperScaffolding(dir)
	if err != nil {
		t.Fatalf("second install: %v", err)
	}
	if created != 0 {
		t.Errorf("expected 0 created on re-run, got %d", created)
	}
	if updated != 0 {
		t.Errorf("expected 0 updated (user edits preserved), got %d", updated)
	}

	// Verify the user's content was not overwritten
	got, err := os.ReadFile(mainTex)
	if err != nil {
		t.Fatalf("read modified file: %v", err)
	}
	if string(got) != userContent {
		t.Errorf("user edit was overwritten: got %q, want %q", string(got), userContent)
	}
}

func TestScaffolding_CompileShExecutable(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()

	if _, _, err := InstallPaperScaffolding(dir); err != nil {
		t.Fatalf("InstallPaperScaffolding: %v", err)
	}

	info, err := os.Stat(filepath.Join(dir, "paper", "compile.sh"))
	if err != nil {
		t.Fatalf("stat compile.sh: %v", err)
	}

	perm := info.Mode().Perm()
	if perm&0111 == 0 {
		t.Errorf("compile.sh should be executable, got %v", perm)
	}
}

func TestScaffoldingTemplates_NonEmpty(t *testing.T) {
	t.Parallel()

	checks := []struct {
		name string
		fn   func() map[string]string
		min  int
	}{
		{"PaperScaffolding", templates.PaperScaffolding, 10},
		{"SrcScaffolding", templates.SrcScaffolding, 12},
		{"LiteratureScaffolding", templates.LiteratureScaffolding, 2},
		{"DocsScaffolding", templates.DocsScaffolding, 3},
		{"TestsScaffolding", templates.TestsScaffolding, 2},
	}

	for _, tc := range checks {
		m := tc.fn()
		if len(m) < tc.min {
			t.Errorf("%s returned %d files, expected at least %d", tc.name, len(m), tc.min)
		}
	}
}

func TestInitRepo_CreatesScaffolding(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()

	result, err := InitRepo(dir, InitOptions{SkipHooks: true})
	if err != nil {
		t.Fatalf("InitRepo: %v", err)
	}
	if !result.Success {
		t.Error("expected success")
	}

	// Verify scaffolding counts are populated
	if result.PaperInstalled == 0 {
		t.Error("expected PaperInstalled > 0")
	}
	if result.SrcInstalled == 0 {
		t.Error("expected SrcInstalled > 0")
	}
	if result.LiteratureInstalled == 0 {
		t.Error("expected LiteratureInstalled > 0")
	}
	if result.DocsScaffInstalled == 0 {
		t.Error("expected DocsScaffInstalled > 0")
	}
	if result.TestsInstalled == 0 {
		t.Error("expected TestsInstalled > 0")
	}

	// Verify key scaffolding files exist on disk
	for _, rel := range []string{
		"paper/main.tex",
		"src/config.py",
		"literature/pdfs/.gitkeep",
		"docs/decisions/0000-template.md",
		"tests/conftest.py",
	} {
		path := filepath.Join(dir, rel)
		if _, err := os.Stat(path); os.IsNotExist(err) {
			t.Errorf("InitRepo should create %s", rel)
		}
	}
}
