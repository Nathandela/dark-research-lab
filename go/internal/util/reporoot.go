package util

import "os"

// GetRepoRoot returns the repository root directory.
// Uses DRL_ROOT env var if set, falls back to COMPOUND_AGENT_ROOT for
// backwards compatibility, otherwise uses cwd.
func GetRepoRoot() string {
	if root := os.Getenv("DRL_ROOT"); root != "" {
		return root
	}
	if root := os.Getenv("COMPOUND_AGENT_ROOT"); root != "" {
		return root
	}
	cwd, err := os.Getwd()
	if err != nil {
		return "."
	}
	return cwd
}
