---
title: "Use PyMuPDF for PDF text extraction"
status: accepted
date: 2026-04-03
deciders: ["Nathan"]
---

# Use PyMuPDF for PDF text extraction

## Context

The literature RAG pipeline needs to extract text from academic PDF papers for chunking, embedding, and search. The DRL project is Python-based for analysis work, and the Go CLI calls Python subprocesses for PDF processing.

## Decision

Use PyMuPDF (fitz) as the PDF text extraction library. The Go `drl index` command calls a Python subprocess that uses PyMuPDF to extract text, which is then passed back to Go for chunking and indexing via the existing knowledge infrastructure.

## Consequences

### Positive
- Fast C-based extraction (MuPDF engine)
- Good handling of academic paper layouts (columns, equations, tables)
- Metadata extraction (title, author, creation date) built-in
- Active maintenance and wide adoption

### Negative
- C dependency may complicate some deployment scenarios
- Large binary size from MuPDF engine

## Alternatives Considered

### pdfplumber
- Pros: Pure Python, good table extraction
- Cons: Slower than PyMuPDF for text-heavy documents, less robust with complex layouts
- Why rejected: Academic papers are text-heavy; speed and layout handling matter more than table precision
