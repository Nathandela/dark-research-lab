---
title: "Reproducibility manifest with checksums and instructions"
status: accepted
date: 2026-04-03
deciders: ["Nathan Delacrétaz"]
---

# Reproducibility Manifest with Checksums and Instructions

## Context

The initial reproducibility manifest (`repro_manifest.json`) captured only 5 fields: Python version, dependencies reference, data file paths, run command, and environment. This is insufficient for independent replication: data files lacked integrity verification, analysis scripts were not inventoried, and there were no human-readable reproduction instructions.

## Decision

Expand the manifest to include:
- Analysis script inventory with SHA-256 checksums (all `.py` files under `src/`)
- Data file entries as objects with path and SHA-256 checksum (instead of bare path strings)
- Dependencies as an object with file reference and checksum (instead of a bare string)
- Full environment spec with Python version inside the environment block
- Step-by-step reproduction instructions as an ordered list

## Rationale

SHA-256 checksums enable verifying that scripts and data have not been modified since the manifest was generated. Structured reproduction steps lower the barrier for independent replication. These are standard expectations in computational social science reproducibility packages.

## Consequences

### Positive
- Independent researchers can verify file integrity before replication
- Reproduction instructions are machine-readable and human-readable
- Manifest is self-contained: no external documentation needed to replicate

### Negative
- Manifest generation is slower due to hashing (negligible for typical project sizes)
- Breaking change: `data_files` is now a list of dicts, not strings; `dependencies` is now a dict, not a string

## Alternatives Considered

### Keep flat manifest, add checksums in a separate file
- Pros: Backward compatible
- Cons: Two files to maintain, easy to forget updating one
- Why rejected: Single manifest is simpler and more reliable
