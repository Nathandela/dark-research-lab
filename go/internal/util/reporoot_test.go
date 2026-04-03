package util

import (
	"os"
	"testing"
)

func TestGetRepoRoot_DRLRoot(t *testing.T) {
	t.Setenv("DRL_ROOT", "/custom/root")
	t.Setenv("COMPOUND_AGENT_ROOT", "")
	got := GetRepoRoot()
	if got != "/custom/root" {
		t.Errorf("got %q, want /custom/root", got)
	}
}

func TestGetRepoRoot_FallbackToCompoundAgentRoot(t *testing.T) {
	t.Setenv("DRL_ROOT", "")
	t.Setenv("COMPOUND_AGENT_ROOT", "/legacy/root")
	got := GetRepoRoot()
	if got != "/legacy/root" {
		t.Errorf("got %q, want /legacy/root", got)
	}
}

func TestGetRepoRoot_DRLRootTakesPrecedence(t *testing.T) {
	t.Setenv("DRL_ROOT", "/new/root")
	t.Setenv("COMPOUND_AGENT_ROOT", "/old/root")
	got := GetRepoRoot()
	if got != "/new/root" {
		t.Errorf("got %q, want /new/root", got)
	}
}

func TestGetRepoRoot_FallbackToCwd(t *testing.T) {
	t.Setenv("DRL_ROOT", "")
	t.Setenv("COMPOUND_AGENT_ROOT", "")
	got := GetRepoRoot()
	cwd, _ := os.Getwd()
	if got != cwd {
		t.Errorf("got %q, want %q", got, cwd)
	}
}
