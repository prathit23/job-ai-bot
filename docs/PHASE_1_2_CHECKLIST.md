# Phase 1-2 Checklist

## Planning Docs

- [x] Add `docs/PLAN.md`.
- [x] Add `docs/OPERATING_WORKFLOW.md`.
- [x] Add `docs/PHASE_1_2_CHECKLIST.md`.

## Phase 1: Discovery

- [x] Move database helpers into `jobbot/db.py`.
- [x] Move ATS normalization and ingestion into `jobbot/ingest.py`.
- [x] Add sample ingest command.
- [x] Add live ingest command.
- [x] Dedupe by stable job hash.

## Phase 2: Scoring

- [x] Move deterministic scoring into `jobbot/scoring.py`.
- [x] Add configurable role, location, sponsorship, seniority, and bucket settings.
- [x] Force explicit negative sponsorship language to `skip`.
- [x] Keep unknown sponsorship jobs reviewable.

## Review Queue

- [x] Add Markdown queue writer.
- [x] Add CSV queue writer.
- [x] Add CLI command for queue generation.

## Tests

- [x] Add scoring tests.
- [x] Add ATS normalization tests.
- [x] Add dedupe tests.
- [x] Add review queue tests.

## Definition Of Done

- [x] Unit tests pass.
- [x] Sample ingest creates rows.
- [x] Daily queue writes Markdown and CSV.
- [x] Local server responds on `/api/jobs` and `/api/stats`.
- [x] README matches Phase 1-2 commands.
