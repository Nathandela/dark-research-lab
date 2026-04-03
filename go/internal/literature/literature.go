// Package literature provides PDF extraction, indexing, and summary generation
// for the literature RAG pipeline. PDF text extraction is delegated to a Python
// subprocess (PyMuPDF), while chunking, embedding, and search use the existing
// Go knowledge infrastructure.
package literature

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

// PDFMetadata holds metadata extracted from a PDF file.
type PDFMetadata struct {
	Title        string `json:"title"`
	Author       string `json:"author"`
	PageCount    int    `json:"page_count"`
	Filename     string `json:"filename"`
	CreationDate string `json:"creation_date"`
}

// ExtractedPDF holds the text and metadata from a Python extraction call.
type ExtractedPDF struct {
	Text     string      `json:"text"`
	Metadata PDFMetadata `json:"metadata"`
}

var slugRe = regexp.MustCompile(`[^a-z0-9]+`)

// MakeSlug converts a filename to a URL-safe slug.
func MakeSlug(filename string) string {
	stem := strings.TrimSuffix(filename, filepath.Ext(filename))
	slug := strings.ToLower(stem)
	slug = slugRe.ReplaceAllString(slug, "-")
	slug = strings.Trim(slug, "-")
	return slug
}

// FindPDFs returns absolute paths of all .pdf files in a directory.
// Returns nil (no error) if the directory does not exist.
func FindPDFs(dir string) ([]string, error) {
	if _, err := os.Stat(dir); os.IsNotExist(err) {
		return nil, nil
	}

	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil, fmt.Errorf("read dir %s: %w", dir, err)
	}

	var pdfs []string
	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		if strings.ToLower(filepath.Ext(e.Name())) == ".pdf" {
			pdfs = append(pdfs, filepath.Join(dir, e.Name()))
		}
	}
	return pdfs, nil
}

// ParseExtractedJSON parses the JSON output from the Python extraction script.
func ParseExtractedJSON(data []byte) (*ExtractedPDF, error) {
	var result ExtractedPDF
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("parse extraction JSON: %w", err)
	}
	return &result, nil
}

// MaxExcerptChars is the maximum characters of text to include in a summary.
const MaxExcerptChars = 500

// WriteSummaryNote writes a summary markdown file for a paper.
// Returns the path to the written file.
func WriteSummaryNote(notesDir string, meta PDFMetadata, text string) (string, error) {
	if err := os.MkdirAll(notesDir, 0o755); err != nil {
		return "", fmt.Errorf("create notes dir: %w", err)
	}

	slug := MakeSlug(meta.Filename)
	outPath := filepath.Join(notesDir, slug+".md")

	excerpt := strings.TrimSpace(text)
	runes := []rune(excerpt)
	if len(runes) > MaxExcerptChars {
		excerpt = string(runes[:MaxExcerptChars]) + "..."
	}

	var b strings.Builder
	fmt.Fprintf(&b, "# %s\n\n", meta.Title)
	fmt.Fprintf(&b, "- **Source:** `%s`\n", meta.Filename)
	if meta.Author != "" {
		fmt.Fprintf(&b, "- **Author:** %s\n", meta.Author)
	}
	fmt.Fprintf(&b, "- **Pages:** %d\n", meta.PageCount)
	fmt.Fprintf(&b, "\n## Excerpt\n\n%s\n", excerpt)

	if err := os.WriteFile(outPath, []byte(b.String()), 0o644); err != nil {
		return "", fmt.Errorf("write summary: %w", err)
	}
	return outPath, nil
}
