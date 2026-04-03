---
name: Compile
description: Compile the LaTeX paper, verify references resolve, and check output quality
---

# LaTeX Compilation Skill

## Overview

Compile the research paper from `paper/main.tex`, verify all references resolve correctly, and check that generated tables and figures are properly included. This skill serves as both a build tool and a quality gate for the final paper output.

## Step 1: Pre-Compilation Checks

Before compiling, verify the inputs are in order:

1. **Tool availability**: Verify that `pdflatex` and `bibtex` are installed:
   ```bash
   which pdflatex && which bibtex
   ```
   If either is missing, report an actionable error:
   - **macOS**: `brew install --cask mactex` or install BasicTeX
   - **Linux**: `apt install texlive-full` or `dnf install texlive-scheme-full`
   - **Existing TeX**: `tlmgr install <missing-package>`
   Do not attempt compilation without these tools.
2. **Main file exists**: Check that `paper/main.tex` exists and has content
3. **Section files**: Verify all `\input{}` or `\include{}` referenced files exist in `paper/sections/`
4. **Bibliography**: Confirm `paper/Ref.bib` exists and is non-empty
5. **Output files**: Check that referenced tables exist in `paper/outputs/tables/` and figures exist in `paper/outputs/figures/`
6. **Packages**: Scan `\usepackage{}` declarations for any non-standard packages that may need installation

List any missing files before attempting compilation.

## Step 2: LaTeX Compilation

Run the compilation sequence. If a `paper/compile.sh` script exists, use it:

```bash
bash paper/compile.sh
```

If no compile script exists, run the standard LaTeX build chain:

```bash
cd paper
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

The triple `pdflatex` pass is necessary to resolve cross-references, bibliography entries, and page numbers correctly.

## Step 3: Reference Resolution Verification

After compilation, check for unresolved references:

1. **Undefined references**: Search the log for "undefined reference" warnings
   ```bash
   grep -i "undefined reference" paper/main.log
   ```
2. **Missing citations**: Search for "Citation.*undefined" warnings
   ```bash
   grep -i "citation.*undefined" paper/main.log
   ```
3. **Missing figures**: Search for "File.*not found" errors
   ```bash
   grep -i "file.*not found" paper/main.log
   ```
4. **BibTeX warnings**: Check the BibTeX log for issues
   ```bash
   grep -i "warning" paper/main.blg
   ```

Report each unresolved reference with its location in the source files.

## Step 4: Output Verification

Check the quality of generated outputs:

1. **Tables**: For each file in `paper/outputs/tables/`:
   - Verify it is referenced in a paper section via `\input{}` or `\include{}`
   - Check formatting (column alignment, caption, label)
2. **Figures**: For each file in `paper/outputs/figures/`:
   - Verify it is referenced via `\includegraphics{}`
   - Check that the file format is supported (PDF, PNG, EPS)
3. **Orphan outputs**: Flag any tables or figures that exist but are not referenced in the paper
4. **Missing outputs**: Flag any `\input{}` or `\includegraphics{}` references that point to non-existent files

## Step 5: BibTeX Processing

Verify bibliography integrity:

1. Check that every `\cite{}` key in the paper has a matching entry in `paper/Ref.bib`
2. Check for orphan BibTeX entries (in the .bib file but never cited)
3. Verify BibTeX entry completeness:
   - Required fields present (author, title, year, journal/booktitle)
   - DOI included where available
   - No formatting errors in author names or titles
4. Check bibliography style matches the target journal requirements

## Step 6: Error Handling

Common LaTeX issues and their fixes:

1. **Missing package**: Install via `tlmgr install <package>` or add to the preamble
2. **Undefined control sequence**: Usually a missing package or typo in a command
3. **Overfull/underfull hbox**: Adjust text or table column widths
4. **Float placement issues**: Check `\begin{figure}[htbp]` placement specifiers
5. **Encoding issues**: Ensure UTF-8 encoding throughout
6. **Missing .aux file**: Run pdflatex twice to generate auxiliary files

For each error, report the file, line number, and suggested fix.

## Gate Criteria

The compilation gate passes when ALL of the following hold:
- [ ] `paper/main.pdf` is generated without fatal errors
- [ ] Zero "undefined reference" warnings in the log
- [ ] Zero "citation undefined" warnings in the log
- [ ] All tables and figures render correctly
- [ ] Bibliography compiles without BibTeX errors
- [ ] No orphan outputs (unreferenced tables or figures)
- [ ] No missing outputs (referenced but non-existent files)

## Quality Criteria

- [ ] Pre-compilation checks passed (all inputs exist)
- [ ] Full triple-pass compilation executed
- [ ] Zero undefined reference warnings
- [ ] Zero citation undefined warnings
- [ ] All tables and figures render correctly
- [ ] No orphan or missing outputs
- [ ] Bibliography compiles without errors

## Common Pitfalls

- Running pdflatex only once (references and citations need multiple passes)
- Not checking the .log file for warnings (only looking for errors)
- Assuming BibTeX keys match between .tex and .bib files without verifying
- Forgetting to re-run bibtex after adding new citations
- Using image formats not supported by the LaTeX engine (e.g., JPG with plain LaTeX)
- Not verifying that the compile script exists before calling it
