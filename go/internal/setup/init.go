package setup

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/nathandelacretaz/dark-research-lab/internal/build"
)

// InitOptions controls what init creates.
type InitOptions struct {
	SkipHooks     bool
	SkipTemplates bool   // Skip installing agent/command/skill/doc templates.
	BinaryPath    string // Path to the Go binary for hook commands. Empty = npx fallback.
	CoreSkill     bool   // --core-skill: install infrastructure + core skills/agents
	AllSkill      bool   // --all-skill: install all tiers including style
}

// InitResult reports what init did.
type InitResult struct {
	Success             bool
	HooksInstalled      bool
	HooksUpgraded       bool
	DirsCreated         []string
	FilesCreated        []string
	AgentsInstalled     int
	AgentsUpdated       int
	CommandsInstalled   int
	CommandsUpdated     int
	SkillsInstalled     int
	SkillsUpdated       int
	RoleSkillsInstalled int
	RoleSkillsUpdated   int
	DocsInstalled       int
	DocsUpdated         int
	ResearchInstalled   int
	ResearchUpdated     int
	TemplatesPruned     int
	PaperInstalled      int
	PaperUpdated        int
	SrcInstalled        int
	SrcUpdated          int
	LiteratureInstalled int
	LiteratureUpdated   int
	DocsScaffInstalled  int
	DocsScaffUpdated    int
	TestsInstalled      int
	TestsUpdated        int
	DataInstalled       int
	DataUpdated         int
	AgentsMdUpdated     bool
	ClaudeMdUpdated     bool
	PluginCreated       bool
	PluginUpdated       bool
}

// initDirectories creates the .claude/ directory structure and index.jsonl.
func initDirectories(repoRoot string, result *InitResult) error {
	dirs := []string{
		filepath.Join(repoRoot, ".claude"),
		filepath.Join(repoRoot, ".claude", "lessons"),
		filepath.Join(repoRoot, ".claude", ".cache"),
		filepath.Join(repoRoot, ".claude", "agents", "drl"),
		filepath.Join(repoRoot, ".claude", "commands", "drl"),
		filepath.Join(repoRoot, ".claude", "skills", "drl"),
	}

	for _, dir := range dirs {
		_, statErr := os.Stat(dir)
		if err := os.MkdirAll(dir, 0755); err != nil {
			return fmt.Errorf("create directory %s: %w", dir, err)
		}
		if os.IsNotExist(statErr) {
			result.DirsCreated = append(result.DirsCreated, dir)
		}
	}

	indexPath := filepath.Join(repoRoot, ".claude", "lessons", "index.jsonl")
	if _, err := os.Stat(indexPath); os.IsNotExist(err) {
		if err := os.WriteFile(indexPath, []byte{}, 0644); err != nil {
			return fmt.Errorf("create index.jsonl: %w", err)
		}
		result.FilesCreated = append(result.FilesCreated, indexPath)
	}

	return EnsureGitignore(repoRoot)
}

// initHooks installs or upgrades Claude Code hooks in settings.json.
func initHooks(repoRoot string, binaryPath string, result *InitResult) error {
	settingsPath := filepath.Join(repoRoot, ".claude", "settings.json")
	settings, err := ReadClaudeSettings(settingsPath)
	if err != nil {
		return fmt.Errorf("read settings: %w", err)
	}

	needsInstall := !HasAllHooks(settings)
	needsUpgrade := HooksNeedUpgrade(settings, binaryPath)
	needsDedupe := HooksNeedDedupe(settings)

	if needsInstall || needsUpgrade || needsDedupe {
		AddAllHooks(settings, binaryPath)
		if err := WriteClaudeSettings(settingsPath, settings); err != nil {
			return fmt.Errorf("write settings: %w", err)
		}
		result.HooksUpgraded = needsUpgrade && !needsInstall
	}
	result.HooksInstalled = true
	return nil
}

// tierConfig controls which template groups are installed.
type tierConfig struct {
	installCore  bool // skills + agents
	installStyle bool // agent role skills
}

// resolveTier determines which tiers to install based on existing repo state and flags.
func resolveTier(existingRepo bool, opts InitOptions) tierConfig {
	if opts.AllSkill {
		return tierConfig{installCore: true, installStyle: true}
	}
	if opts.CoreSkill {
		return tierConfig{installCore: true, installStyle: false}
	}
	if !existingRepo {
		// Fresh repo: install everything
		return tierConfig{installCore: true, installStyle: true}
	}
	// Existing repo with no flags: infrastructure only
	return tierConfig{installCore: false, installStyle: false}
}

// installTemplates installs all template assets (agents, commands, skills, docs).
// Detects the project stack to substitute quality gate placeholders.
func installTemplates(repoRoot string, tier tierConfig, result *InitResult) error {
	version := build.Version

	updated, err := UpdateAgentsMd(repoRoot)
	if err != nil {
		return fmt.Errorf("update AGENTS.md: %w", err)
	}
	result.AgentsMdUpdated = updated

	updated, err = EnsureClaudeMdReference(repoRoot)
	if err != nil {
		return fmt.Errorf("ensure CLAUDE.md reference: %w", err)
	}
	result.ClaudeMdUpdated = updated

	created, pluginUpdated, err := CreatePluginManifest(repoRoot, version)
	if err != nil {
		return fmt.Errorf("create plugin.json: %w", err)
	}
	result.PluginCreated = created
	result.PluginUpdated = pluginUpdated

	stack := DetectStack(repoRoot)
	return installTemplateGroups(repoRoot, version, stack, tier, result)
}

// installTemplateGroups installs agent, command, skill, role skill, and doc templates.
// Stack info is used to substitute quality gate placeholders in skills and docs.
// The tier config controls which groups are installed.
func installTemplateGroups(repoRoot string, version string, stack StackInfo, tier tierConfig, result *InitResult) error {
	type installFunc struct {
		fn   func() (int, int, error)
		setN func(int)
		setU func(int)
		name string
	}

	// Infrastructure tier: always installed
	groups := []installFunc{
		{func() (int, int, error) { return InstallWorkflowCommands(repoRoot) },
			func(n int) { result.CommandsInstalled = n }, func(u int) { result.CommandsUpdated = u }, "workflow commands"},
		{func() (int, int, error) { return InstallDocTemplates(repoRoot, version, stack) },
			func(n int) { result.DocsInstalled = n }, func(u int) { result.DocsUpdated = u }, "doc templates"},
		{func() (int, int, error) { return InstallResearchDocs(repoRoot) },
			func(n int) { result.ResearchInstalled = n }, func(u int) { result.ResearchUpdated = u }, "research docs"},
		{func() (int, int, error) { return InstallPaperScaffolding(repoRoot) },
			func(n int) { result.PaperInstalled = n }, func(u int) { result.PaperUpdated = u }, "paper scaffolding"},
		{func() (int, int, error) { return InstallSrcScaffolding(repoRoot) },
			func(n int) { result.SrcInstalled = n }, func(u int) { result.SrcUpdated = u }, "src scaffolding"},
		{func() (int, int, error) { return InstallLiteratureSetup(repoRoot) },
			func(n int) { result.LiteratureInstalled = n }, func(u int) { result.LiteratureUpdated = u }, "literature setup"},
		{func() (int, int, error) { return InstallDocsStructure(repoRoot) },
			func(n int) { result.DocsScaffInstalled = n }, func(u int) { result.DocsScaffUpdated = u }, "docs structure"},
		{func() (int, int, error) { return InstallTestsScaffolding(repoRoot) },
			func(n int) { result.TestsInstalled = n }, func(u int) { result.TestsUpdated = u }, "tests scaffolding"},
		{func() (int, int, error) { return InstallDataScaffolding(repoRoot) },
			func(n int) { result.DataInstalled = n }, func(u int) { result.DataUpdated = u }, "data scaffolding"},
	}

	// Core tier: skills + agents
	if tier.installCore {
		groups = append(groups,
			installFunc{func() (int, int, error) { return InstallAgentTemplates(repoRoot) },
				func(n int) { result.AgentsInstalled = n }, func(u int) { result.AgentsUpdated = u }, "agent templates"},
			installFunc{func() (int, int, error) { return InstallPhaseSkills(repoRoot, stack) },
				func(n int) { result.SkillsInstalled = n }, func(u int) { result.SkillsUpdated = u }, "phase skills"},
		)
	}

	// Style tier: agent role skills
	if tier.installStyle {
		groups = append(groups,
			installFunc{func() (int, int, error) { return InstallAgentRoleSkills(repoRoot) },
				func(n int) { result.RoleSkillsInstalled = n }, func(u int) { result.RoleSkillsUpdated = u }, "agent role skills"},
		)
	}

	for _, g := range groups {
		n, u, err := g.fn()
		if err != nil {
			return fmt.Errorf("install %s: %w", g.name, err)
		}
		g.setN(n)
		g.setU(u)
	}

	pruned, err := PruneStaleTemplates(repoRoot)
	if err != nil {
		return fmt.Errorf("prune stale templates: %w", err)
	}
	result.TemplatesPruned = pruned

	if err := CompileSkillsIndex(repoRoot); err != nil {
		return fmt.Errorf("compile skills index: %w", err)
	}
	return nil
}

// InitRepo initializes dark-research-lab in a repository.
// Creates .claude/ structure, lessons index, and optionally installs hooks.
// Tier behavior:
//   - No .claude/ + no flags: install all tiers
//   - Has .claude/ + no flags: infrastructure only (skip skills, agents, role skills)
//   - --core-skill: infrastructure + core skills/agents
//   - --all-skill: everything including style
func InitRepo(repoRoot string, opts InitOptions) (*InitResult, error) {
	result := &InitResult{Success: true}

	// Detect existing repo BEFORE creating directories
	_, statErr := os.Stat(filepath.Join(repoRoot, ".claude"))
	existingRepo := statErr == nil

	tier := resolveTier(existingRepo, opts)

	if err := initDirectories(repoRoot, result); err != nil {
		return nil, err
	}

	if !opts.SkipHooks {
		if err := initHooks(repoRoot, opts.BinaryPath, result); err != nil {
			return nil, err
		}
	}

	if !opts.SkipTemplates {
		if err := installTemplates(repoRoot, tier, result); err != nil {
			return nil, err
		}
	}

	return result, nil
}

// EnsureGitignore creates or updates .claude/.gitignore with required patterns.
func EnsureGitignore(repoRoot string) error {
	gitignorePath := filepath.Join(repoRoot, ".claude", ".gitignore")

	// Ensure directory exists
	if err := os.MkdirAll(filepath.Dir(gitignorePath), 0755); err != nil {
		return err
	}

	marker := "# drl managed"
	patterns := marker + `
.cache/
*.sqlite
*.sqlite-shm
*.sqlite-wal
.drl-phase-state.json
.drl-failure-state.json
.drl-read-state.json
.drl-hints-shown
skills/drl/skills_index.json
`

	// If gitignore exists, check for our marker
	existing, err := os.ReadFile(gitignorePath)
	if err == nil {
		if strings.Contains(string(existing), marker) {
			return nil // Already has our patterns
		}
		// Append our patterns to existing content
		combined := strings.TrimRight(string(existing), "\n") + "\n" + patterns
		return os.WriteFile(gitignorePath, []byte(combined), 0644)
	}
	if !os.IsNotExist(err) {
		return fmt.Errorf("read .gitignore: %w", err)
	}

	return os.WriteFile(gitignorePath, []byte(patterns), 0644)
}
