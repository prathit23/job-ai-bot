# Maintenance

## Normal User Flow

Run:

```text
Job Assistant Menu.bat
```

Choose option `1` for the live pipeline.

## Quality Gates

Before pushing changes:

```powershell
$py = "C:\Users\prath\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py -m unittest discover -s tests
```

On GitHub, CI runs the same test suite on every push and pull request.

## When A Job Source Breaks

Look at:

- `daily_queue/*_summary.json`
- `data/ingest_logs/*.json`
- the `Pipeline Summary` at the end of the latest Markdown queue

Common failures:

- `404`: wrong ATS token or company moved ATS.
- `403`: blocked or private endpoint.
- timeout/throttle: source is slow or rate-limiting.

Fix source keys in:

```text
config/targets.json
```

## When Scoring Looks Wrong

Add a regression test first. Good places:

- `tests/test_scoring.py`
- `tests/test_review_queue.py`
- `tests/test_ingest_normalization.py`

Then update:

- `config/scoring.json` for keyword/phrase changes.
- `jobbot/scoring.py` for scoring behavior.
- `jobbot/review_queue.py` for output/export behavior.

## Release Hygiene

Do not commit:

- candidate private resume files
- generated queues
- SQLite databases
- logs
- desktop shortcuts
- secrets
