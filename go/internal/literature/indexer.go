package literature

import (
	"fmt"
	"os/exec"
	"path/filepath"
	"time"

	"github.com/nathandelacretaz/dark-research-lab/internal/knowledge"
	"github.com/nathandelacretaz/dark-research-lab/internal/storage"
)

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

// replaceChunks atomically deletes old chunks and upserts new ones within a transaction.
func replaceChunks(kdb *storage.KnowledgeDB, relPath string, chunks []storage.KnowledgeChunk, hash string) error {
	tx, err := kdb.DB().Begin()
	if err != nil {
		return fmt.Errorf("begin transaction: %w", err)
	}
	defer tx.Rollback()

	if err := kdb.DeleteChunksByFilePath([]string{relPath}); err != nil {
		return fmt.Errorf("delete old chunks: %w", err)
	}
	if len(chunks) > 0 {
		if err := kdb.UpsertChunks(chunks); err != nil {
			return fmt.Errorf("upsert chunks: %w", err)
		}
	}
	if err := kdb.SetFileHash(relPath, hash); err != nil {
		return fmt.Errorf("set file hash: %w", err)
	}

	return tx.Commit()
}

// extractPDF calls the Python extraction script and returns parsed results.
func extractPDF(repoRoot, pdfPath string) (*ExtractedPDF, error) {
	cmd := exec.Command("python3", "-m", "src.literature.extract", "--json", pdfPath)
	cmd.Dir = repoRoot

	output, err := cmd.Output()
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			return nil, fmt.Errorf("python extraction failed: %s", string(exitErr.Stderr))
		}
		return nil, fmt.Errorf("run python: %w", err)
	}

	return ParseExtractedJSON(output)
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
