---
name: Flavor
description: Interactive interview that customizes DRL skill files for field-specific research conventions
---

# Flavor Customization System

## Overview

Customize the DRL skill files to match a researcher's field conventions, methodology preferences, journal requirements, and citation style. Flavor edits are version-controlled and reversible.

## Step 1: Safety Checkpoint (H2 Mitigation)

**Before editing any skill file, you MUST create a safety checkpoint.**

1. Stage all current changes: `git add .claude/skills/drl/`
2. Commit with a descriptive message: `git commit -m "checkpoint: pre-flavor skill state"`
3. This ensures all flavor changes are reversible via `git revert` or `git diff`

If the commit fails because there are no changes, that is fine -- proceed.

## Step 2: Interactive Interview

Use `AskUserQuestion` to gather field-specific configuration. Ask about each dimension:

### 2a. Research Field

- Primary field: economics, sociology, political science, psychology, public health, education, etc.
- Subfield or specialization (e.g., labor economics, organizational sociology)
- Interdisciplinary considerations

### 2b. Methodology Preferences

- Primary approach: quantitative, qualitative, mixed methods
- Preferred statistical methods: regression analysis, causal inference (IV, RDD, DiD), structural models, Bayesian methods
- Data analysis conventions: significance thresholds, effect size reporting, confidence intervals vs. p-values
- Robustness expectations: how many alternative specifications, which sensitivity analyses

### 2c. Journal Target

- Target journal name (if known)
- Journal formatting requirements (section structure, word limits, abstract format)
- Submission requirements (anonymous review, data availability statement, pre-registration)

### 2d. Citation Style

- Citation format: APA 7th, Chicago Author-Date, Chicago Notes, Harvard, journal-specific
- Bibliography conventions: full author lists vs. et al. threshold, DOI inclusion, URL formatting
- In-text citation style: (Author, Year) vs. Author (Year) vs. numbered

## Step 3: Web Search for Field Conventions

Search for the target journal and field conventions:

1. Search for journal-specific author guidelines and submission requirements
2. Search for field-specific statistical reporting standards (e.g., APA reporting standards for psychology)
3. Search for common robustness check expectations in the field
4. Note any field-specific vocabulary or terminology conventions

Record findings to inform skill file edits.

## Step 4: Skill File Editing

Read and edit the DRL skill files to incorporate field conventions.

### Atomic Write Protocol (H2 Mitigation)

For each skill file edit, use a write-then-rename sequence to prevent partial writes from corrupting skill files:

```bash
# 1. Read the current file
cat .claude/skills/drl/<skill>/SKILL.md

# 2. Write modified content to a temporary file
# (use Write tool or redirect to .tmp)
# Result: .claude/skills/drl/<skill>/SKILL.md.tmp

# 3. Atomically replace the original with the temp file
mv .claude/skills/drl/<skill>/SKILL.md.tmp .claude/skills/drl/<skill>/SKILL.md
```

If step 3 fails, the original file is untouched. If step 2 fails, there is no corruption -- only a leftover `.tmp` file to clean up.

### What Gets Customized

Edit the following skill files in `.claude/skills/drl/`:

1. **spec-dev/SKILL.md**: Adapt hypothesis format, literature gap framing, and methodology outline to field conventions
2. **plan/SKILL.md**: Adjust statistical method recommendations, variable naming conventions, and robustness battery to field norms
3. **work/SKILL.md** and sub-skills (**work-writing/SKILL.md**, **work-analysis/SKILL.md**): Set field-appropriate significance thresholds, effect size measures, and table/figure formatting
4. **review/SKILL.md**: Calibrate reviewer expectations for the field (e.g., IV validity checks for economics, effect size reporting for psychology)
5. **compound/SKILL.md**: Adjust paper structure to journal requirements, set abstract format, and configure citation style

Note: The procedural skills (lit-review, decision, compile, status) are intentionally excluded from flavor customization because their workflows are field-agnostic.

### Customization Targets Within Each Skill

For each skill file, look for and adapt:
- **Vocabulary**: Replace generic terms with field-specific terminology
- **Method defaults**: Set appropriate default statistical methods for the field
- **Quality thresholds**: Adjust what counts as a sufficient robustness battery
- **Output format**: Match table and figure conventions to the journal style
- **Review criteria**: Calibrate what reviewers check based on field expectations

## Step 5: Verify and Commit

1. Review all changes: `git diff .claude/skills/drl/`
2. Verify no skill file was corrupted (each still has valid YAML frontmatter and readable content)
3. Stage the changes: `git add .claude/skills/drl/`
4. Commit: `git commit -m "flavor: configure for <field> targeting <journal>"`

## Reverting Flavor Changes

If the researcher wants to undo flavor customization:
1. Find the pre-flavor checkpoint: `git log --oneline .claude/skills/drl/`
2. Revert to the checkpoint commit
3. Or selectively revert individual files: `git checkout <commit> -- .claude/skills/drl/<skill>/SKILL.md`

## Gate Criteria

Before concluding, verify:
- [ ] Safety checkpoint committed before any edits
- [ ] All four interview dimensions gathered (field, methodology, journal, citation)
- [ ] Web search performed for journal and field conventions
- [ ] Skill files edited via atomic write protocol
- [ ] Changes committed with descriptive message
- [ ] No skill file corrupted (YAML frontmatter intact)

## Quality Criteria

- [ ] Safety checkpoint committed before edits
- [ ] All four interview dimensions gathered (field, methodology, journal, citation)
- [ ] Web search performed for field conventions
- [ ] Atomic write protocol followed for each edit
- [ ] YAML frontmatter intact in all edited files
- [ ] Changes committed with descriptive message

## Common Pitfalls

- Editing skill files without creating a safety checkpoint first
- Applying changes that are too field-specific and break the general workflow
- Not searching for the actual journal requirements (guessing instead)
- Forgetting to update the citation style in the compound skill
- Making vocabulary changes that conflict with beads or DRL workflow terminology
