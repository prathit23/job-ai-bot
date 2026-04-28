# Agent Guide

This repo is designed so Codex and Claude can collaborate without stepping on each other.

## Current Scope

Implemented:

- ATS job ingestion from Greenhouse, Lever, and Ashby.
- Deterministic scoring for PM/PO/BA-adjacent roles.
- Local SQLite storage.
- Daily Markdown/CSV review queues.
- Pipeline summaries and ingest error logs.

Out of scope until Phase 3:

- Resume rewriting.
- DOCX/PDF generation.
- Auto-submit.
- Browser automation beyond optional manual launchers.

## Ownership Split

Codex should own:

- Python code.
- Tests.
- CLI/dashboard plumbing.
- Data normalization.
- Scoring implementation.

Claude should own:

- Resume truth-bank extraction.
- Resume tailoring prompts.
- Cover letter prompts.
- Human-facing review copy.
- Evaluating selected jobs against the truth bank.

## Rules For Future Agents

- Keep generated data out of git: `data/`, `daily_queue/`, logs, SQLite files.
- Add tests for every scoring or export bug before fixing it.
- Prefer deterministic rules before LLM calls.
- Do not scrape LinkedIn or Indeed.
- Do not add auto-submit behavior without explicit approval.
- Keep H-1B logic configurable and avoid hardcoding legal conclusions.
