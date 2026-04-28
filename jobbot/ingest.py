from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .db import connect, init_db, upsert_job
from .paths import DB_PATH, INGEST_LOG_DIR, SAMPLE_JOBS_PATH, TARGETS_PATH
from .utils import clean_text, load_json, now_iso


def http_json(url: str, timeout: int = 20) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "LocalJobAssistant/0.2"})
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return json.loads(res.read().decode("utf-8"))


def normalize_location(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        names = []
        for item in value:
            if isinstance(item, dict):
                names.append(item.get("name") or item.get("location") or "")
            else:
                names.append(str(item))
        return ", ".join([n for n in names if n])
    if isinstance(value, dict):
        return value.get("name") or value.get("location") or ""
    return ""


def normalize_greenhouse_job(item: dict[str, Any], company: dict[str, Any]) -> dict[str, Any]:
    token = company["key"]
    return {
        "source": "greenhouse",
        "source_company_key": token,
        "company": company.get("company", token),
        "title": clean_text(item.get("title", "")),
        "location": clean_text(normalize_location(item.get("location"))),
        "apply_url": item.get("absolute_url", ""),
        "description": clean_text(item.get("content", "")),
        "posted_at": item.get("updated_at", ""),
    }


def normalize_lever_job(item: dict[str, Any], company: dict[str, Any]) -> dict[str, Any]:
    key = company["key"]
    lists = item.get("lists", [])
    description = " ".join([str(item.get("description", ""))] + [str(v.get("content", "")) for v in lists])
    return {
        "source": "lever",
        "source_company_key": key,
        "company": company.get("company", key),
        "title": clean_text(item.get("text", "")),
        "location": clean_text(normalize_location(item.get("categories", {}).get("location", ""))),
        "apply_url": item.get("hostedUrl") or item.get("applyUrl", ""),
        "description": clean_text(description),
        "posted_at": str(item.get("createdAt", "")),
    }


def normalize_ashby_job(item: dict[str, Any], company: dict[str, Any]) -> dict[str, Any]:
    key = company["key"]
    secondary = normalize_location(item.get("secondaryLocations", []))
    loc = item.get("location", "") or secondary
    if secondary and secondary not in loc:
        loc = f"{loc}, {secondary}"
    return {
        "source": "ashby",
        "source_company_key": key,
        "company": company.get("company", key),
        "title": clean_text(item.get("title", "")),
        "location": clean_text(loc),
        "apply_url": item.get("jobUrl") or item.get("applyUrl", ""),
        "description": clean_text(item.get("descriptionPlain") or item.get("descriptionHtml", "")),
        "posted_at": item.get("publishedDate", ""),
    }


def fetch_greenhouse(company: dict[str, Any]) -> list[dict[str, Any]]:
    token = company["key"]
    url = f"https://boards-api.greenhouse.io/v1/boards/{urllib.parse.quote(token)}/jobs?content=true"
    payload = http_json(url)
    return [normalize_greenhouse_job(item, company) for item in payload.get("jobs", [])]


def fetch_lever(company: dict[str, Any]) -> list[dict[str, Any]]:
    key = company["key"]
    url = f"https://api.lever.co/v0/postings/{urllib.parse.quote(key)}?mode=json"
    payload = http_json(url)
    return [normalize_lever_job(item, company) for item in payload if isinstance(payload, list)]


def fetch_ashby(company: dict[str, Any]) -> list[dict[str, Any]]:
    key = company["key"]
    url = f"https://api.ashbyhq.com/posting-api/job-board/{urllib.parse.quote(key)}?includeCompensation=true"
    payload = http_json(url)
    return [normalize_ashby_job(item, company) for item in payload.get("jobs", [])]


FETCHERS = {"greenhouse": fetch_greenhouse, "lever": fetch_lever, "ashby": fetch_ashby}


def ingest_jobs(jobs: list[dict[str, Any]], db_path: Path = DB_PATH) -> dict[str, Any]:
    init_db(db_path)
    result = {
        "started_at": now_iso(),
        "source_count": 1,
        "fetched_count": 0,
        "inserted_count": 0,
        "updated_count": 0,
        "error_count": 0,
        "errors": [],
    }
    with connect(db_path) as db:
        cursor = db.execute("INSERT INTO ingest_runs (started_at, source_count) VALUES (?, ?)", (result["started_at"], 1))
        run_id = cursor.lastrowid
        for job in jobs:
            action = upsert_job(db, job)
            result[f"{action}_count"] += 1
            result["fetched_count"] += 1
        result["finished_at"] = now_iso()
        db.execute(
            """
            UPDATE ingest_runs
            SET finished_at = ?, fetched_count = ?, inserted_count = ?, updated_count = ?,
                error_count = ?, errors = ?
            WHERE id = ?
            """,
            (
                result["finished_at"],
                result["fetched_count"],
                result["inserted_count"],
                result["updated_count"],
                result["error_count"],
                json.dumps(result["errors"]),
                run_id,
            ),
        )
    result["log_path"] = write_ingest_log(result)
    return result


def ingest_sample(sample_path: Path = SAMPLE_JOBS_PATH, db_path: Path = DB_PATH) -> dict[str, Any]:
    sample_jobs = load_json(sample_path, [])
    return ingest_jobs(sample_jobs, db_path)


def ingest_targets(targets_path: Path = TARGETS_PATH, db_path: Path = DB_PATH) -> dict[str, Any]:
    init_db(db_path)
    targets = load_json(targets_path, {"companies": []})
    companies = [c for c in targets.get("companies", []) if c.get("enabled", True)]
    result = {
        "started_at": now_iso(),
        "source_count": len(companies),
        "fetched_count": 0,
        "inserted_count": 0,
        "updated_count": 0,
        "error_count": 0,
        "errors": [],
    }
    with connect(db_path) as db:
        cursor = db.execute(
            "INSERT INTO ingest_runs (started_at, source_count) VALUES (?, ?)",
            (result["started_at"], result["source_count"]),
        )
        run_id = cursor.lastrowid
        for company in companies:
            source = company.get("source")
            fetcher = FETCHERS.get(source)
            if not fetcher:
                result["error_count"] += 1
                result["errors"].append(f"Unsupported source {source} for {company.get('company')}")
                continue
            try:
                for job in fetcher(company):
                    action = upsert_job(db, job)
                    result[f"{action}_count"] += 1
                    result["fetched_count"] += 1
            except Exception as exc:
                result["error_count"] += 1
                result["errors"].append(f"{company.get('company', company.get('key'))}: {exc}")
            time.sleep(0.2)
        result["finished_at"] = now_iso()
        db.execute(
            """
            UPDATE ingest_runs
            SET finished_at = ?, fetched_count = ?, inserted_count = ?, updated_count = ?,
                error_count = ?, errors = ?
            WHERE id = ?
            """,
            (
                result["finished_at"],
                result["fetched_count"],
                result["inserted_count"],
                result["updated_count"],
                result["error_count"],
                json.dumps(result["errors"]),
                run_id,
            ),
        )
    result["log_path"] = write_ingest_log(result)
    return result


def write_ingest_log(result: dict[str, Any]) -> str:
    INGEST_LOG_DIR.mkdir(parents=True, exist_ok=True)
    safe_started = result["started_at"].replace(":", "").replace("+", "_").replace(".", "_")
    path = INGEST_LOG_DIR / f"{safe_started}.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return str(path)
