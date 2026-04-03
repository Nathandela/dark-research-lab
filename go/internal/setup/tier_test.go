package setup

import (
	"os"
	"path/filepath"
	"testing"
)

func TestTierSetup_EmptyRepo(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()
	os.MkdirAll(filepath.Join(dir, ".git"), 0755)

	// No .claude/ dir exists -> should install all tiers
	result, err := InitRepo(dir, InitOptions{SkipHooks: true})
	if err != nil {
		t.Fatalf("InitRepo failed: %v", err)
	}

	// Infrastructure tier
	if !result.AgentsMdUpdated {
		t.Error("expected AGENTS.md updated (infrastructure)")
	}
	if !result.ClaudeMdUpdated {
		t.Error("expected CLAUDE.md updated (infrastructure)")
	}
	if result.CommandsInstalled == 0 {
		t.Error("expected commands installed (infrastructure)")
	}
	if result.DocsInstalled == 0 {
		t.Error("expected docs installed (infrastructure)")
	}

	// Core tier (skills + agents)
	if result.SkillsInstalled == 0 {
		t.Error("expected phase skills installed (core)")
	}
	if result.AgentsInstalled == 0 {
		t.Error("expected agent templates installed (core)")
	}

	// Style tier (agent role skills)
	if result.RoleSkillsInstalled == 0 {
		t.Error("expected agent role skills installed (style)")
	}
}

func TestTierSetup_ExistingRepo(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()
	os.MkdirAll(filepath.Join(dir, ".git"), 0755)

	// Pre-create .claude/ to simulate existing repo
	os.MkdirAll(filepath.Join(dir, ".claude"), 0755)

	// Existing .claude/ + no flags -> infrastructure only
	result, err := InitRepo(dir, InitOptions{SkipHooks: true})
	if err != nil {
		t.Fatalf("InitRepo failed: %v", err)
	}

	// Infrastructure should be installed
	if result.CommandsInstalled == 0 {
		t.Error("expected commands installed (infrastructure)")
	}
	if result.DocsInstalled == 0 {
		t.Error("expected docs installed (infrastructure)")
	}
	if result.ResearchInstalled == 0 {
		t.Error("expected research docs installed (infrastructure)")
	}

	// Core tier should be SKIPPED
	if result.SkillsInstalled != 0 {
		t.Errorf("expected 0 phase skills installed, got %d", result.SkillsInstalled)
	}
	if result.AgentsInstalled != 0 {
		t.Errorf("expected 0 agents installed, got %d", result.AgentsInstalled)
	}

	// Style tier should be SKIPPED
	if result.RoleSkillsInstalled != 0 {
		t.Errorf("expected 0 role skills installed, got %d", result.RoleSkillsInstalled)
	}
}

func TestTierSetup_CoreSkillFlag(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()
	os.MkdirAll(filepath.Join(dir, ".git"), 0755)

	// Pre-create .claude/ to simulate existing repo
	os.MkdirAll(filepath.Join(dir, ".claude"), 0755)

	// --core-skill -> infrastructure + core (skills + agents)
	result, err := InitRepo(dir, InitOptions{
		SkipHooks: true,
		CoreSkill: true,
	})
	if err != nil {
		t.Fatalf("InitRepo failed: %v", err)
	}

	// Infrastructure
	if result.CommandsInstalled == 0 {
		t.Error("expected commands installed (infrastructure)")
	}
	if result.DocsInstalled == 0 {
		t.Error("expected docs installed (infrastructure)")
	}

	// Core tier should be installed
	if result.SkillsInstalled == 0 {
		t.Error("expected phase skills installed (core)")
	}
	if result.AgentsInstalled == 0 {
		t.Error("expected agents installed (core)")
	}

	// Style tier should be SKIPPED
	if result.RoleSkillsInstalled != 0 {
		t.Errorf("expected 0 role skills installed, got %d", result.RoleSkillsInstalled)
	}
}

func TestTierSetup_AllSkillFlag(t *testing.T) {
	t.Parallel()
	dir := t.TempDir()
	os.MkdirAll(filepath.Join(dir, ".git"), 0755)

	// Pre-create .claude/ to simulate existing repo
	os.MkdirAll(filepath.Join(dir, ".claude"), 0755)

	// --all-skill -> everything including style
	result, err := InitRepo(dir, InitOptions{
		SkipHooks: true,
		AllSkill:  true,
	})
	if err != nil {
		t.Fatalf("InitRepo failed: %v", err)
	}

	// Infrastructure
	if result.CommandsInstalled == 0 {
		t.Error("expected commands installed (infrastructure)")
	}
	if result.DocsInstalled == 0 {
		t.Error("expected docs installed (infrastructure)")
	}

	// Core tier
	if result.SkillsInstalled == 0 {
		t.Error("expected phase skills installed (core)")
	}
	if result.AgentsInstalled == 0 {
		t.Error("expected agents installed (core)")
	}

	// Style tier
	if result.RoleSkillsInstalled == 0 {
		t.Error("expected agent role skills installed (style)")
	}
}
