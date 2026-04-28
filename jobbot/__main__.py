from __future__ import annotations

import argparse
import json

from .db import init_db, rescore_all_jobs
from .ingest import ingest_sample, ingest_targets
from .review_queue import write_daily_queue
from .server import serve


def main() -> None:
    parser = argparse.ArgumentParser(description="Local AI Job Application Assistant")
    subcommands = parser.add_subparsers(dest="command")
    subcommands.add_parser("seed-sample", help="Load sample jobs into SQLite")
    subcommands.add_parser("ingest", help="Fetch configured ATS targets into SQLite")
    subcommands.add_parser("write-queue", help="Write daily Markdown and CSV review queues")
    subcommands.add_parser("rescore", help="Recompute scores for existing jobs")
    subcommands.add_parser("serve", help="Start the local dashboard")

    parser.add_argument("--seed-sample", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--ingest", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    init_db()
    command = args.command
    if args.seed_sample:
        command = "seed-sample"
    if args.ingest:
        command = "ingest"
    if command is None:
        command = "serve"

    if command == "seed-sample":
        print(json.dumps(ingest_sample(), indent=2))
    elif command == "ingest":
        print(json.dumps(ingest_targets(), indent=2))
    elif command == "write-queue":
        print(json.dumps(write_daily_queue(), indent=2))
    elif command == "rescore":
        print(json.dumps(rescore_all_jobs(), indent=2))
    elif command == "serve":
        serve()
    else:
        raise SystemExit(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
