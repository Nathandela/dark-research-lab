package setup

import (
	"encoding/json"
	"os"
	"path/filepath"
)

const hintsMarkerFile = ".drl-hints-shown"

// ReadHintsEnabled reads .claude/dark-research-lab.json and returns whether
// "hints": true is configured.
func ReadHintsEnabled(repoRoot string) bool {
	data, err := os.ReadFile(filepath.Join(repoRoot, ".claude", "dark-research-lab.json"))
	if err != nil {
		return false
	}
	var config map[string]any
	if err := json.Unmarshal(data, &config); err != nil {
		return false
	}
	hints, ok := config["hints"].(bool)
	return ok && hints
}

// ShouldShowHint returns true if hints are enabled and the hint has not
// yet been shown in this repo (marker file absent).
func ShouldShowHint(repoRoot string) bool {
	if !ReadHintsEnabled(repoRoot) {
		return false
	}
	markerPath := filepath.Join(repoRoot, ".claude", hintsMarkerFile)
	_, err := os.Stat(markerPath)
	return os.IsNotExist(err)
}

// MarkHintShown creates the marker file so the hint is not shown again.
func MarkHintShown(repoRoot string) error {
	markerPath := filepath.Join(repoRoot, ".claude", hintsMarkerFile)
	return os.WriteFile(markerPath, []byte{}, 0644)
}

// WorkflowHint returns the one-time onboarding hint text.
func WorkflowHint() string {
	return `Tip: dark-research-lab tracks lessons across sessions. Start with:
  drl learn "<insight>" --trigger "<what happened>"
  drl search "<topic>"
  drl info
`
}
