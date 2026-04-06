package literature

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"github.com/nathandelacretaz/dark-research-lab/internal/knowledge"
	"github.com/nathandelacretaz/dark-research-lab/internal/setup"
	"github.com/nathandelacretaz/dark-research-lab/internal/storage"
)

const pdfExtractTimeout = 60 * time.Second

// IndexOptions controls literature indexing behavior.
type IndexOptions struct {
	Force bool // Re-index even if hash unchanged
}

// IndexResult holds statistics about a literature indexing operation.
type IndexResult struct {
	PDFsProcessed  int
	PDFsSkipped    int
	PDFsErrored    int
	ChunksCreated  int
	NotesGenerated int
	DurationMs     int64
	Errors         []string
}

// IndexLiterature walks literature/pdfs/, extracts text via Python, and indexes
// chunks into the knowledge database.
func IndexLiterature(repoRoot string, kdb *storage.KnowledgeDB, opts *IndexOptions) (*IndexResult, error) {
	start := time.Now()
	result := &IndexResult{}

	pdfsDir := filepath.Join(repoRoot, "literature", "pdfs")
	notesDir := filepath.Join(repoRoot, "literature", "notes")

	pdfs, err := FindPDFs(pdfsDir)
	if err != nil {
		return result, fmt.Errorf("find PDFs: %w", err)
	}

	if len(pdfs) == 0 {
		result.DurationMs = time.Since(start).Milliseconds()
		return result, nil
	}

	force := false
	if opts != nil {
		force = opts.Force
	}

	for _, pdfPath := range pdfs {
		extracted, err := extractPDF(repoRoot, pdfPath)
		if err != nil {
			result.PDFsErrored++
			result.Errors = append(result.Errors, fmt.Sprintf("%s: %v", filepath.Base(pdfPath), err))
			continue
		}

		relPath := relativeLiteraturePath(repoRoot, pdfPath)

		// Check if content unchanged
		hash := knowledge.ChunkContentHash(extracted.Text)
		if !force && kdb.GetFileHash(relPath) == hash {
			result.PDFsSkipped++
			continue
		}

		// Chunk the extracted text
		chunks := knowledge.ChunkFile(relPath, extracted.Text, nil)
		kChunks := toKnowledgeChunks(relPath, chunks)

		// Replace old chunks atomically
		if err := replaceChunks(kdb, relPath, kChunks, hash); err != nil {
			result.PDFsErrored++
			result.Errors = append(result.Errors, fmt.Sprintf("%s: %v", filepath.Base(pdfPath), err))
			continue
		}

		result.PDFsProcessed++
		result.ChunksCreated += len(kChunks)

		// Generate summary note
		if _, err := WriteSummaryNote(notesDir, extracted.Metadata, extracted.Text); err != nil {
			result.Errors = append(result.Errors, fmt.Sprintf("%s: write summary: %v", filepath.Base(pdfPath), err))
		} else {
			result.NotesGenerated++
		}
	}

	result.DurationMs = time.Since(start).Milliseconds()
	return result, nil
}

// replaceChunks atomically deletes old chunks and upserts new ones within a single transaction.
func replaceChunks(kdb *storage.KnowledgeDB, relPath string, chunks []storage.KnowledgeChunk, hash string) error {
	return kdb.ReplaceChunksAtomic(relPath, chunks, hash)
}

// pythonPath returns the venv python if available, otherwise falls back to python3.
func pythonPath(repoRoot string) string {
	venvPython := setup.VenvPythonPath(repoRoot)
	if _, err := os.Stat(venvPython); err == nil {
		return venvPython
	}
	return "python3"
}

// extractPDF calls the Python extraction script and returns parsed results.
func extractPDF(repoRoot, pdfPath string) (*ExtractedPDF, error) {
	ctx, cancel := context.WithTimeout(context.Background(), pdfExtractTimeout)
	defer cancel()

	pyPath := pythonPath(repoRoot)
	cmd := exec.CommandContext(ctx, pyPath, "-m", "src.literature.extract", "--json", pdfPath)
	cmd.Dir = repoRoot

	output, err := cmd.Output()
	if err != nil {
		if ctx.Err() == context.DeadlineExceeded {
			return nil, fmt.Errorf("PDF extraction timed out after %s (file may be too large)", pdfExtractTimeout)
		}
		if exitErr, ok := err.(*exec.ExitError); ok {
			return nil, classifyPythonError(string(exitErr.Stderr))
		}
		if strings.Contains(err.Error(), "executable file not found") {
			return nil, fmt.Errorf("Python not found. Run 'drl setup' to create the project venv")
		}
		return nil, fmt.Errorf("run python: %w", err)
	}

	return ParseExtractedJSON(output)
}

// classifyPythonError extracts a clear message from Python stderr.
func classifyPythonError(stderr string) error {
	stderr = strings.TrimSpace(stderr)
	if stderr == "" {
		return fmt.Errorf("python extraction failed (no error output)")
	}

	lines := strings.Split(stderr, "\n")
	lastLine := ""
	for i := len(lines) - 1; i >= 0; i-- {
		if strings.TrimSpace(lines[i]) != "" {
			lastLine = strings.TrimSpace(lines[i])
			break
		}
	}
	if lastLine == "" {
		lastLine = stderr
	}

	// Strip Python exception class prefix (e.g. "ModuleNotFoundError: No module named 'fitz'" -> "No module named 'fitz'")
	detail := lastLine
	if idx := strings.Index(detail, ": "); idx != -1 {
		detail = detail[idx+2:]
	}

	switch {
	case strings.Contains(stderr, "ModuleNotFoundError"):
		return fmt.Errorf("missing Python dependency: %s\n  Fix: run 'drl setup' to install dependencies into .venv/", detail)
	case strings.Contains(stderr, "ImportError"):
		return fmt.Errorf("Python import error: %s\n  Fix: run 'drl setup' to reinstall dependencies", detail)
	case strings.Contains(stderr, "No module named 'src"):
		return fmt.Errorf("Python module path error: src/ package not found.\n  Fix: run 'drl setup' to regenerate the project structure")
	case strings.Contains(stderr, "FileNotFoundError"):
		return fmt.Errorf("PDF file not found or unreadable: %s", detail)
	case strings.Contains(stderr, "PermissionError"):
		return fmt.Errorf("permission denied reading PDF: %s", detail)
	default:
		return fmt.Errorf("python extraction failed: %s\n  Run 'drl doctor' to check your Python environment", lastLine)
	}
}

// relativeLiteraturePath returns the relative path from repo root for a literature file.
func relativeLiteraturePath(repoRoot, absPath string) string {
	rel, err := filepath.Rel(repoRoot, absPath)
	if err != nil {
		return absPath
	}
	return rel
}

func toKnowledgeChunks(relPath string, chunks []knowledge.Chunk) []storage.KnowledgeChunk {
	now := time.Now().UTC().Format(time.RFC3339)
	kChunks := make([]storage.KnowledgeChunk, len(chunks))
	for i, c := range chunks {
		kChunks[i] = storage.KnowledgeChunk{
			ID:          c.ID,
			FilePath:    c.FilePath,
			StartLine:   c.StartLine,
			EndLine:     c.EndLine,
			ContentHash: c.ContentHash,
			Text:        c.Text,
			UpdatedAt:   now,
		}
	}
	return kChunks
}
