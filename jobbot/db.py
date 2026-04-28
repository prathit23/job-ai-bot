from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .paths import DB_PATH
from .scoring import score_job
from .utils import clean_text, now_iso, stable_hash


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    return db


def init_db(db_path: Path = DB_PATH) -> None:
    with connect(db_path) as db:
        db.executescript(
            """
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
            """
        )


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["score_reasons"] = json.loads(item.get("score_reasons") or "[]")
    return item


def upsert_job(db: sqlite3.Connection, job: dict[str, Any]) -> str:
    scored = score_job(job)
    job_hash = stable_hash(job.get("company", ""), job.get("title", ""), job.get("location", ""), job.get("apply_url", ""))
    existing = db.execute("SELECT id FROM jobs WHERE job_hash = ?", (job_hash,)).fetchone()
    values = {
        "job_hash": job_hash,
        "source": job.get("source", "unknown"),
        "source_company_key": job.get("source_company_key", ""),
        "company": clean_text(job.get("company")),
        "title": clean_text(job.get("title")),
        "location": clean_text(job.get("location")),
        "remote_flag": scored["remote_flag"],
        "apply_url": job.get("apply_url", ""),
        "description": clean_text(job.get("description")),
        "posted_at": job.get("posted_at", ""),
        "updated_at": now_iso(),
        **scored,
        "score_reasons": json.dumps(scored["score_reasons"]),
    }
    if existing:
        db.execute(
            """
            UPDATE jobs
            SET source = :source, source_company_key = :source_company_key, company = :company,
                title = :title, location = :location, remote_flag = :remote_flag,
                apply_url = :apply_url, description = :description, posted_at = :posted_at,
                updated_at = :updated_at, bucket = :bucket, role_score = :role_score,
                location_score = :location_score, sponsorship_score = :sponsorship_score,
                seniority_score = :seniority_score, effort_score = :effort_score,
                total_score = :total_score, sponsorship_signal = :sponsorship_signal,
                score_reasons = :score_reasons
            WHERE job_hash = :job_hash
            """,
            values,
        )
        return "updated"

    values["discovered_at"] = now_iso()
    db.execute(
        """
        INSERT INTO jobs (
            job_hash, source, source_company_key, company, title, location, remote_flag,
            apply_url, description, posted_at, discovered_at, updated_at, bucket,
            role_score, location_score, sponsorship_score, seniority_score, effort_score,
            total_score, sponsorship_signal, score_reasons
        ) VALUES (
            :job_hash, :source, :source_company_key, :company, :title, :location, :remote_flag,
            :apply_url, :description, :posted_at, :discovered_at, :updated_at, :bucket,
            :role_score, :location_score, :sponsorship_score, :seniority_score, :effort_score,
            :total_score, :sponsorship_signal, :score_reasons
        )
        """,
        values,
    )
    return "inserted"


def list_jobs(params: dict[str, list[str]] | None = None, db_path: Path = DB_PATH) -> list[dict[str, Any]]:
    params = params or {}
    clauses = []
    values: list[Any] = []
    for field in ["status", "bucket", "sponsorship_signal"]:
        if params.get(field) and params[field][0]:
            clauses.append(f"{field} = ?")
            values.append(params[field][0])
    if params.get("q") and params["q"][0]:
        clauses.append("(title LIKE ? OR company LIKE ? OR description LIKE ?)")
        q = f"%{params['q'][0]}%"
        values.extend([q, q, q])
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    with connect(db_path) as db:
        rows = db.execute(
            f"SELECT * FROM jobs {where} ORDER BY total_score DESC, discovered_at DESC LIMIT 500",
            values,
        ).fetchall()
    return [row_to_dict(r) for r in rows]


def get_job(job_id: int, db_path: Path = DB_PATH) -> dict[str, Any] | None:
    with connect(db_path) as db:
        row = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return row_to_dict(row) if row else None


def update_job(job_id: int, payload: dict[str, Any], db_path: Path = DB_PATH) -> dict[str, Any]:
    allowed = {"status", "bucket", "notes"}
    fields = [key for key in payload.keys() if key in allowed]
    if not fields:
        return get_job(job_id, db_path) or {}
    assignments = ", ".join([f"{field} = ?" for field in fields])
    values = [payload[field] for field in fields] + [now_iso(), job_id]
    with connect(db_path) as db:
        db.execute(f"UPDATE jobs SET {assignments}, updated_at = ? WHERE id = ?", values)
    return get_job(job_id, db_path) or {}


def get_stats(db_path: Path = DB_PATH) -> dict[str, Any]:
    with connect(db_path) as db:
        rows = db.execute("SELECT bucket, COUNT(*) count FROM jobs GROUP BY bucket").fetchall()
        statuses = db.execute("SELECT status, COUNT(*) count FROM jobs GROUP BY status").fetchall()
        latest = db.execute("SELECT * FROM ingest_runs ORDER BY id DESC LIMIT 1").fetchone()
    return {
        "buckets": {r["bucket"]: r["count"] for r in rows},
        "statuses": {r["status"]: r["count"] for r in statuses},
        "latest_ingest": dict(latest) if latest else None,
    }


def rescore_all_jobs(db_path: Path = DB_PATH) -> dict[str, int]:
    init_db(db_path)
    counts = {"rescored": 0}
    with connect(db_path) as db:
        rows = db.execute("SELECT * FROM jobs").fetchall()
        for row in rows:
            job = row_to_dict(row)
            scored = score_job(job)
            db.execute(
                """
                UPDATE jobs
                SET remote_flag = ?, bucket = ?, role_score = ?, location_score = ?,
                    sponsorship_score = ?, seniority_score = ?, effort_score = ?,
                    total_score = ?, sponsorship_signal = ?, score_reasons = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    scored["remote_flag"],
                    scored["bucket"],
                    scored["role_score"],
                    scored["location_score"],
                    scored["sponsorship_score"],
                    scored["seniority_score"],
                    scored["effort_score"],
                    scored["total_score"],
                    scored["sponsorship_signal"],
                    json.dumps(scored["score_reasons"]),
                    now_iso(),
                    row["id"],
                ),
            )
            counts["rescored"] += 1
    return counts
