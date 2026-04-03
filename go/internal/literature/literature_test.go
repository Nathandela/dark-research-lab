package literature

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestMakeSlug(t *testing.T) {
	tests := []struct {
		input string
		want  string
	}{
		{"My Research Paper.pdf", "my-research-paper"},
		{"Paper (2024) - Final!.pdf", "paper-2024-final"},
		{"a---b___c.pdf", "a-b-c"},
		{"UPPERCASE.PDF", "uppercase"},
		{"simple.pdf", "simple"},
	}
	for _, tt := range tests {
		got := MakeSlug(tt.input)
		if got != tt.want {
			t.Errorf("MakeSlug(%q) = %q, want %q", tt.input, got, tt.want)
		}
	}
}

func TestFindPDFs(t *testing.T) {
	dir := t.TempDir()

	// Create test files
	for _, name := range []string{"paper1.pdf", "paper2.pdf", "readme.txt", "notes.md"} {
		if err := os.WriteFile(filepath.Join(dir, name), []byte("test"), 0o644); err != nil {
			t.Fatal(err)
		}
	}

	pdfs, err := FindPDFs(dir)
	if err != nil {
		t.Fatal(err)
	}
	if len(pdfs) != 2 {
		t.Fatalf("expected 2 PDFs, got %d: %v", len(pdfs), pdfs)
	}
	for _, p := range pdfs {
		if !strings.HasSuffix(p, ".pdf") {
			t.Errorf("non-PDF in results: %s", p)
		}
	}
}

func TestFindPDFs_EmptyDir(t *testing.T) {
	dir := t.TempDir()
	pdfs, err := FindPDFs(dir)
	if err != nil {
		t.Fatal(err)
	}
	if len(pdfs) != 0 {
		t.Fatalf("expected 0 PDFs, got %d", len(pdfs))
	}
}

func TestFindPDFs_MissingDir(t *testing.T) {
	pdfs, err := FindPDFs("/nonexistent/path/to/pdfs")
	if err != nil {
		t.Fatal("should not error on missing dir")
	}
	if len(pdfs) != 0 {
		t.Fatalf("expected 0 PDFs, got %d", len(pdfs))
	}
}

func TestParseExtractedJSON(t *testing.T) {
	jsonStr := `{"text":"Hello world from PDF","metadata":{"title":"Test","author":"Author","page_count":3,"filename":"test.pdf","creation_date":""}}`

	result, err := ParseExtractedJSON([]byte(jsonStr))
	if err != nil {
		t.Fatal(err)
	}
	if result.Text != "Hello world from PDF" {
		t.Errorf("unexpected text: %q", result.Text)
	}
	if result.Metadata.Title != "Test" {
		t.Errorf("unexpected title: %q", result.Metadata.Title)
	}
	if result.Metadata.PageCount != 3 {
		t.Errorf("unexpected page_count: %d", result.Metadata.PageCount)
	}
}

func TestParseExtractedJSON_Invalid(t *testing.T) {
	_, err := ParseExtractedJSON([]byte("not json"))
	if err == nil {
		t.Fatal("expected error for invalid JSON")
	}
}

func TestWriteSummaryNote(t *testing.T) {
	dir := t.TempDir()
	meta := PDFMetadata{
		Title:    "Test Paper Title",
		Author:   "Jane Doe",
		PageCount: 5,
		Filename: "test_paper.pdf",
	}
	text := "This is the abstract and content of the paper about economics."

	path, err := WriteSummaryNote(dir, meta, text)
	if err != nil {
		t.Fatal(err)
	}

	content, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}

	s := string(content)
	if !strings.Contains(s, "# Test Paper Title") {
		t.Error("missing title in summary")
	}
	if !strings.Contains(s, "Jane Doe") {
		t.Error("missing author in summary")
	}
	if !strings.Contains(s, "test_paper.pdf") {
		t.Error("missing source filename in summary")
	}
}

func TestWriteSummaryNote_Truncation(t *testing.T) {
	dir := t.TempDir()
	meta := PDFMetadata{Title: "Long Paper", Filename: "long.pdf", PageCount: 1}

	// Create text longer than MaxExcerptChars (500)
	longText := strings.Repeat("Economics research. ", 50) // 1000 chars
	path, err := WriteSummaryNote(dir, meta, longText)
	if err != nil {
		t.Fatal(err)
	}

	content, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}

	s := string(content)
	if !strings.Contains(s, "...") {
		t.Error("expected truncation marker '...' for long text")
	}
}
