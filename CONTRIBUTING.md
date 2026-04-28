# Contributing

This is currently a personal local tool, but changes should still be reviewable.

## Before Making Changes

1. Read `AGENTS.md`.
2. Read `docs/ARCHITECTURE.md`.
3. Confirm the change belongs to the current phase.

## Development Rules

- Add or update tests before changing scoring/export behavior.
- Keep generated data out of git.
- Keep the command-line and `.bat` flows simple.
- Prefer deterministic logic over LLM calls.

## Test

```powershell
$py = "C:\Users\prath\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py -m unittest discover -s tests
```
