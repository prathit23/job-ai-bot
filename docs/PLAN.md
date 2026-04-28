# AI Job Application Assistant Plan

This repository is implementing the local/private job assistant in tight review slices. The current implementation scope is Phase 1-2 only: job discovery, deterministic scoring, and daily review output.

## Phase 1: Job Discovery MVP

Goal: collect jobs relevant to Product Manager, Product Owner, Business Analyst, and adjacent roles from safe ATS-style feeds, normalize them, dedupe them, and store them locally.

Implemented sources:

- Sample fixture data for offline testing.
- Greenhouse public job board API.
- Lever public postings API.
- Ashby public job posting API.

Stored fields:

- Company, title, location, source, source company key.
- Apply URL, description, posted date, discovered date.
- Stable job hash based on company, title, location, and apply URL.

Definition of Done:

- Sample ingest creates SQLite rows.
- Live ingest can attempt configured ATS targets.
- Duplicate jobs update existing rows instead of creating duplicates.
- Job list is queryable through the local API and CLI commands.

## Phase 2: Scoring and Prioritization

Goal: rank jobs with deterministic rules before any LLM is used.

Scores:

- Role fit.
- Location fit.
- H-1B sponsorship signal.
- Seniority fit.
- Application effort.
- Weighted total score.

Buckets:

- `apply`
- `maybe`
- `manual_review`
- `skip`

Sponsorship policy:

- Explicit negative sponsorship language forces `skip`.
- Explicit positive sponsorship language boosts the score.
- Missing sponsorship language is `unknown`, not rejected.

Definition of Done:

- Fixtures cover positive, negative, and unknown sponsorship language.
- Jobs are grouped into expected buckets.
- Daily Markdown and CSV queues are generated.
- Unit tests pass with the bundled Python runtime.

## Out Of Scope For This Slice

- Automated Claude resume generation.
- DOCX/PDF export.
- Custom autofill development.
- Auto-submit.
- Cloud hosting.

Those later phases should consume the Phase 1-2 outputs instead of changing their contract.
