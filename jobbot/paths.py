from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"
DAILY_QUEUE_DIR = ROOT / "daily_queue"
INGEST_LOG_DIR = DATA_DIR / "ingest_logs"
SAMPLE_DATA_DIR = ROOT / "sample_data"
STATIC_DIR = ROOT / "static"

DB_PATH = DATA_DIR / "jobs.sqlite3"
TARGETS_PATH = CONFIG_DIR / "targets.json"
SCORING_PATH = CONFIG_DIR / "scoring.json"
SAMPLE_JOBS_PATH = SAMPLE_DATA_DIR / "sample_jobs.json"

HOST = "127.0.0.1"
PORT = int(os.environ.get("JOB_ASSISTANT_PORT", "8765"))
