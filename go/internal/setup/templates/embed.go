// Package templates provides embedded template files for dark-research-lab setup.
// Templates are embedded at compile time using //go:embed directives.
package templates

import (
	"embed"
	"fmt"
	"io/fs"
	"path"
	"strings"
)

//go:embed agents/*.md
var agentsFS embed.FS

//go:embed commands/*.md
var commandsFS embed.FS

//go:embed skills
var skillsFS embed.FS

//go:embed agent-role-skills
var agentRoleSkillsFS embed.FS

//go:embed docs/*.md
var docsFS embed.FS

//go:embed docs/research
var researchFS embed.FS

//go:embed all:scaffolding
var scaffoldingFS embed.FS

//go:embed agents-md.md
var agentsMdTemplate string

//go:embed claude-md-reference.md
var claudeMdReference string

//go:embed plugin.json
var pluginJSON string

// Markers for idempotent section detection.
const (
	CompoundAgentSectionHeader = "## Dark Research Lab Integration"
	ClaudeRefStartMarker       = "<!-- dark-research-lab:claude-ref:start -->"
	ClaudeRefEndMarker         = "<!-- dark-research-lab:claude-ref:end -->"
	AgentsSectionStartMarker   = "<!-- dark-research-lab:start -->"
	AgentsSectionEndMarker     = "<!-- dark-research-lab:end -->"
)

// AgentsMdTemplate returns the AGENTS.md section template.
func AgentsMdTemplate() string {
	return agentsMdTemplate
}

// ClaudeMdReference returns the CLAUDE.md reference snippet.
func ClaudeMdReference() string {
	return claudeMdReference
}

// PluginJSON returns the plugin.json template with {{VERSION}} placeholder.
func PluginJSON() string {
	return pluginJSON
}

// AgentTemplates returns a map of filename -> content for agent .md files.
func AgentTemplates() map[string]string {
	return readEmbedDir(agentsFS, "agents")
}

// CommandTemplates returns a map of filename -> content for command .md files.
func CommandTemplates() map[string]string {
	return readEmbedDir(commandsFS, "commands")
}

// PhaseSkills returns a map of phase-name -> SKILL.md content.
func PhaseSkills() map[string]string {
	result := make(map[string]string)
	_ = fs.WalkDir(skillsFS, "skills", func(p string, d fs.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return err
		}
		if path.Base(p) == "SKILL.md" {
			// Extract phase name: "skills/<phase>/SKILL.md" -> "<phase>"
			parts := strings.Split(p, "/")
			if len(parts) >= 3 {
				phase := parts[1]
				data, readErr := fs.ReadFile(skillsFS, p)
				if readErr == nil {
					result[phase] = string(data)
				}
			}
		}
		return nil
	})
	return result
}

// PhaseSkillReferences returns a map of "phase/relative-path" -> content
// for reference files alongside phase skills.
func PhaseSkillReferences() map[string]string {
	result := make(map[string]string)
	_ = fs.WalkDir(skillsFS, "skills", func(p string, d fs.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return err
		}
		if path.Base(p) == "SKILL.md" {
			return nil // Skip SKILL.md itself
		}
		// Path: "skills/<phase>/references/<file>.md"
		// Key: "<phase>/references/<file>.md"
		parts := strings.Split(p, "/")
		if len(parts) >= 2 {
			relPath := strings.Join(parts[1:], "/") // strip "skills/" prefix
			data, readErr := fs.ReadFile(skillsFS, p)
			if readErr == nil {
				result[relPath] = string(data)
			}
		}
		return nil
	})
	return result
}

// AgentRoleSkills returns a map of role-name -> SKILL.md content.
func AgentRoleSkills() map[string]string {
	result := make(map[string]string)
	_ = fs.WalkDir(agentRoleSkillsFS, "agent-role-skills", func(p string, d fs.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return err
		}
		if path.Base(p) == "SKILL.md" {
			// Extract role name: "agent-role-skills/<role>/SKILL.md" -> "<role>"
			parts := strings.Split(p, "/")
			if len(parts) >= 3 {
				role := parts[1]
				data, readErr := fs.ReadFile(agentRoleSkillsFS, p)
				if readErr == nil {
					result[role] = string(data)
				}
			}
		}
		return nil
	})
	return result
}

// AgentRoleSkillReferences returns a map of "role/relative-path" -> content
// for reference files alongside agent role skills.
func AgentRoleSkillReferences() map[string]string {
	result := make(map[string]string)
	_ = fs.WalkDir(agentRoleSkillsFS, "agent-role-skills", func(p string, d fs.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return err
		}
		if path.Base(p) == "SKILL.md" {
			return nil // Skip SKILL.md itself
		}
		// Path: "agent-role-skills/<role>/references/<file>.md"
		// Key: "<role>/references/<file>.md"
		parts := strings.Split(p, "/")
		if len(parts) >= 2 {
			relPath := strings.Join(parts[1:], "/") // strip "agent-role-skills/" prefix
			data, readErr := fs.ReadFile(agentRoleSkillsFS, p)
			if readErr == nil {
				result[relPath] = string(data)
			}
		}
		return nil
	})
	return result
}

// DocTemplates returns a map of filename -> content for documentation .md files.
// Content includes {{VERSION}} and {{DATE}} placeholders for substitution.
func DocTemplates() map[string]string {
	return readEmbedDir(docsFS, "docs")
}

// ResearchDocs returns a map of relative-path -> content for research documentation.
// Paths are relative to the research root (e.g., "security/overview.md", "index.md").
func ResearchDocs() map[string]string {
	const root = "docs/research"
	result := make(map[string]string)
	_ = fs.WalkDir(researchFS, root, func(p string, d fs.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return err
		}
		// Strip "docs/research/" prefix to get relative path
		rel := strings.TrimPrefix(p, root+"/")
		data, readErr := fs.ReadFile(researchFS, p)
		if readErr == nil {
			result[rel] = string(data)
		}
		return nil
	})
	return result
}

// PaperScaffolding returns a map of relative-path -> content for paper templates.
func PaperScaffolding() map[string]string {
	return readEmbedTree(scaffoldingFS, "scaffolding/paper")
}

// SrcScaffolding returns a map of relative-path -> content for Python source templates.
func SrcScaffolding() map[string]string {
	return readEmbedTree(scaffoldingFS, "scaffolding/src")
}

// LiteratureScaffolding returns a map of relative-path -> content for literature templates.
func LiteratureScaffolding() map[string]string {
	return readEmbedTree(scaffoldingFS, "scaffolding/literature")
}

// DocsScaffolding returns a map of relative-path -> content for docs templates.
func DocsScaffolding() map[string]string {
	return readEmbedTree(scaffoldingFS, "scaffolding/docs")
}

// TestsScaffolding returns a map of relative-path -> content for test templates.
func TestsScaffolding() map[string]string {
	return readEmbedTree(scaffoldingFS, "scaffolding/tests")
}

// DataScaffolding returns a map of relative-path -> content for data directory templates.
func DataScaffolding() map[string]string {
	return readEmbedTree(scaffoldingFS, "scaffolding/data")
}

// readEmbedTree walks an embedded FS directory tree and returns a map
// of relative-path -> content. Relative paths use slash separators.
// Panics on errors since embedded FS failures indicate a broken binary.
func readEmbedTree(fsys embed.FS, root string) map[string]string {
	result := make(map[string]string)
	err := fs.WalkDir(fsys, root, func(p string, d fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if d.IsDir() {
			return nil
		}
		rel := strings.TrimPrefix(p, root+"/")
		data, readErr := fs.ReadFile(fsys, p)
		if readErr != nil {
			return fmt.Errorf("read embedded %s: %w", p, readErr)
		}
		result[rel] = string(data)
		return nil
	})
	if err != nil {
		panic(fmt.Sprintf("walk embedded FS %q: %v", root, err))
	}
	return result
}

// readEmbedDir reads all files from an embedded FS directory into a map.
// Panics on errors since embedded FS failures indicate a broken binary.
func readEmbedDir(fsys embed.FS, dir string) map[string]string {
	result := make(map[string]string)
	entries, err := fs.ReadDir(fsys, dir)
	if err != nil {
		panic(fmt.Sprintf("read embedded dir %q: %v", dir, err))
	}
	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		data, readErr := fs.ReadFile(fsys, path.Join(dir, entry.Name()))
		if readErr != nil {
			panic(fmt.Sprintf("read embedded %s/%s: %v", dir, entry.Name(), readErr))
		}
		result[entry.Name()] = string(data)
	}
	return result
}
