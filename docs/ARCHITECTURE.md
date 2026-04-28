# Architecture

## Pipeline

```text
Configured ATS targets
-> ingest normalizers
-> SQLite jobs table
-> deterministic scoring
-> daily Markdown/CSV review queue
-> human review
```

## Main Modules

- `jobbot/ingest.py`: fetches and normalizes Greenhouse, Lever, and Ashby postings.
- `jobbot/db.py`: owns SQLite initialization, upserts, query helpers, and rescoring.
- `jobbot/scoring.py`: deterministic title/location/sponsorship/seniority scoring.
- `jobbot/review_queue.py`: writes Markdown, CSV, and JSON summary artifacts.
- `jobbot/server.py`: lightweight local dashboard/API.
- `jobbot/__main__.py`: CLI entry point.

## Data Contracts

Generated runtime files are local-only and ignored by git:

- `data/jobs.sqlite3`
- `data/ingest_logs/*.json`
- `daily_queue/*.md`
- `daily_queue/*.csv`
- `daily_queue/*_summary.json`

Config files are tracked:

- `config/targets.json`
- `config/scoring.json`
- `config/profile.json` placeholder

## Resume Tailoring Future

Phase 3 should consume selected jobs from SQLite or CSV and produce Claude packets:

```text
selected job + truth bank + base resume + scoring reasons
-> Claude packet
-> tailored resume draft
-> human review
```

Do not make resume tailoring depend on Excel formatting. Use structured JSON packets.
