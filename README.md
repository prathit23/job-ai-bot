<<<<<<< HEAD
# job-ai-bot
Repo to create AI Job Bot
=======
# AI Job Application Assistant

Local job-search helper for Product Manager, Product Owner, Business Analyst, and adjacent roles.

It fetches jobs from configured ATS sources, scores them for role/location/H-1B fit, and writes a simple daily review queue.

## Use It

Double-click:

```text
Job Assistant Menu.bat
```

That menu lets you:

1. Run live job pipeline.
2. Run sample pipeline.
3. Start dashboard.
4. Open the daily queue folder.

For normal use, choose:

```text
1. Run live job pipeline
```

When it finishes, review the newest files in:

```text
daily_queue/
```

Start with the `.md` file. The `.csv` is there if you want spreadsheet-style review.

Each run writes timestamped files, so it will not fail if yesterday's queue is still open in Excel.

## What The Pipeline Does

```text
Fetch jobs -> dedupe -> rescore -> bucket -> write daily queue
```

Buckets:

- `apply`
- `maybe`
- `manual_review`
- `skip`

Negative sponsorship language goes to `skip`. Missing sponsorship language stays reviewable.

## Configure Sources

Edit:

```text
config/targets.json
```

Supported sources:

- Greenhouse
- Lever
- Ashby

## Optional Command Line

If you prefer one command instead of the menu:

```powershell
.\Run Pipeline.bat
```

To test without internet:

```powershell
.\Run Sample Pipeline.bat
```

## Developer Notes

Planning docs:

- `docs/PLAN.md`
- `docs/OPERATING_WORKFLOW.md`
- `docs/PHASE_1_2_CHECKLIST.md`

Tests:

```powershell
$py = "C:\Users\prath\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py -m unittest discover -s tests
```

Direct app commands, if needed:

```powershell
& $py -m jobbot ingest
& $py -m jobbot rescore
& $py -m jobbot write-queue
& $py -m jobbot serve
```
>>>>>>> dd1fffc (Initial job assistant)
