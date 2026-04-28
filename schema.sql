CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_hash TEXT NOT NULL UNIQUE,
    source TEXT NOT NULL,
    source_company_key TEXT NOT NULL,
    company TEXT NOT NULL,
    title TEXT NOT NULL,
    location TEXT,
    remote_flag INTEGER DEFAULT 0,
    apply_url TEXT,
    description TEXT,
    posted_at TEXT,
    discovered_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'found',
    bucket TEXT NOT NULL DEFAULT 'manual_review',
    role_score INTEGER NOT NULL DEFAULT 0,
    location_score INTEGER NOT NULL DEFAULT 0,
    sponsorship_score INTEGER NOT NULL DEFAULT 0,
    seniority_score INTEGER NOT NULL DEFAULT 0,
    effort_score INTEGER NOT NULL DEFAULT 0,
    total_score INTEGER NOT NULL DEFAULT 0,
    sponsorship_signal TEXT NOT NULL DEFAULT 'unknown',
    score_reasons TEXT NOT NULL DEFAULT '[]',
    notes TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS ingest_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    source_count INTEGER NOT NULL DEFAULT 0,
    fetched_count INTEGER NOT NULL DEFAULT 0,
    inserted_count INTEGER NOT NULL DEFAULT 0,
    updated_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    errors TEXT NOT NULL DEFAULT '[]'
);
