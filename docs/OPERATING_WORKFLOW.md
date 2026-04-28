# Operating Workflow

## Daily Job Production

Run the local pipeline:

```powershell
& "C:\Users\prath\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m jobbot ingest
& "C:\Users\prath\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m jobbot write-queue
```

For offline testing:

```powershell
& "C:\Users\prath\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m jobbot seed-sample
& "C:\Users\prath\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m jobbot write-queue
```

The pipeline writes:

- `daily_queue/YYYY-MM-DD.md`
- `daily_queue/YYYY-MM-DD.csv`

## Human Review

Open the Markdown queue first. It is the canonical review surface for this phase.

Review buckets in this order:

1. `Apply`
2. `Maybe`
3. `Manual Review`
4. `Skip`

Each job includes:

- Title and company.
- Location.
- Score.
- Sponsorship signal.
- Apply link.
- Reasons for the score.

## Claude Handoff Later

Claude should not review the full job universe. After a human selects jobs from the daily queue, a later Phase 3 task can create a small Claude packet for each selected job:

- Job title, company, apply URL, and full JD.
- Score and score reasons.
- Candidate truth bank.
- Base PM or BA resume.
- Non-fabrication instructions.

For this slice, the handoff is documented only. Resume generation automation is intentionally not implemented.

## Local Dashboard

The dashboard is secondary. Start it with:

```powershell
& "C:\Users\prath\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m jobbot serve
```

Then open:

```text
http://127.0.0.1:8765
```
