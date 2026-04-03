package cli

import (
	"encoding/json"
	"fmt"
	"strings"

	"github.com/nathandelacretaz/dark-research-lab/internal/knowledge"
	"github.com/nathandelacretaz/dark-research-lab/internal/literature"
	"github.com/nathandelacretaz/dark-research-lab/internal/storage"
	"github.com/nathandelacretaz/dark-research-lab/internal/util"
	"github.com/spf13/cobra"
)

func indexCmd() *cobra.Command {
	var (
		force bool
		embed bool
	)
	cmd := &cobra.Command{
		Use:   "index",
		Short: "Index literature PDFs for knowledge search",
		Long:  "Extracts text from PDFs in literature/pdfs/, chunks and indexes them for search via 'drl knowledge'.",
		RunE: func(cmd *cobra.Command, args []string) error {
			repoRoot := util.GetRepoRoot()

			db, err := storage.OpenRepoKnowledgeDB(repoRoot)
			if err != nil {
				return fmt.Errorf("open knowledge db: %w", err)
			}
			defer db.Close()

			kdb := storage.NewKnowledgeDB(db)

			// Check embed daemon health if embedding requested
			if embed {
				embedder, closeEmbedder := getOrStartEmbedder(repoRoot)
				if embedder == nil {
					cmd.PrintErrln("[error] Embedding daemon is not running. Start it with 'drl setup' or run without --embed.")
					cmd.PrintErrln("[hint] The ca-embed daemon must be running for vector search. Keyword search (FTS5) works without it.")
					closeEmbedder()
					return fmt.Errorf("embed daemon not available")
				}
				closeEmbedder()
			}

			opts := &literature.IndexOptions{
				Force: force,
				Embed: embed,
			}

			result, err := literature.IndexLiterature(repoRoot, kdb, opts)
			if err != nil {
				return fmt.Errorf("index literature: %w", err)
			}

			cmd.Print(formatLiteratureIndexResult(result))

			// Embed if requested
			if embed && result.ChunksCreated > 0 {
				embedder, closeEmbedder := getOrStartEmbedder(repoRoot)
				defer closeEmbedder()
				if embedder != nil {
					embedResult, embedErr := knowledge.EmbedChunks(kdb, embedder, nil)
					if embedErr != nil {
						cmd.PrintErrln("[warn] embedding failed:", embedErr)
					} else {
						cmd.Printf("Embedded %d chunk(s).\n", embedResult.ChunksEmbedded)
					}
				}
			}

			for _, e := range result.Errors {
				cmd.PrintErrln("[warn]", e)
			}

			return nil
		},
	}
	cmd.Flags().BoolVarP(&force, "force", "f", false, "force re-index all PDFs")
	cmd.Flags().BoolVar(&embed, "embed", false, "embed chunks after indexing (requires ca-embed daemon)")
	return cmd
}

// registerLiteratureCommands adds literature-related commands to the root.
func registerLiteratureCommands(rootCmd *cobra.Command) {
	rootCmd.AddCommand(indexCmd())
}

func formatLiteratureIndexResult(result *literature.IndexResult) string {
	var b strings.Builder
	fmt.Fprintf(&b, "Indexed %d PDF(s), %d chunk(s) created", result.PDFsProcessed, result.ChunksCreated)
	if result.PDFsSkipped > 0 {
		fmt.Fprintf(&b, ", %d PDF(s) unchanged", result.PDFsSkipped)
	}
	if result.PDFsErrored > 0 {
		fmt.Fprintf(&b, ", %d PDF(s) errored", result.PDFsErrored)
	}
	if result.NotesGenerated > 0 {
		fmt.Fprintf(&b, ", %d note(s) generated", result.NotesGenerated)
	}
	fmt.Fprintf(&b, " (%.1fs)\n", float64(result.DurationMs)/1000.0)
	return b.String()
}

// --- JSON output for knowledge command ---

// KnowledgeResultJSON is the JSON output format for drl knowledge --json.
type KnowledgeResultJSON struct {
	File       string  `json:"file"`
	ChunkText  string  `json:"chunk_text"`
	Similarity float64 `json:"similarity"`
	StartLine  int     `json:"start_line"`
	EndLine    int     `json:"end_line"`
}

func formatKnowledgeResultsJSON(results []knowledge.ScoredChunkResult) (string, error) {
	items := make([]KnowledgeResultJSON, len(results))
	for i, r := range results {
		items[i] = KnowledgeResultJSON{
			File:       r.Chunk.FilePath,
			ChunkText:  r.Chunk.Text,
			Similarity: r.Score,
			StartLine:  r.Chunk.StartLine,
			EndLine:    r.Chunk.EndLine,
		}
	}
	out, err := json.Marshal(items)
	if err != nil {
		return "", fmt.Errorf("marshal knowledge results: %w", err)
	}
	return string(out), nil
}
