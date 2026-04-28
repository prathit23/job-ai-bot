from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from .db import get_stats, list_jobs
from .paths import DAILY_QUEUE_DIR, DB_PATH
from .utils import clean_text, timestamp_slug


BUCKET_ORDER = ["apply", "maybe", "manual_review"]
MAX_JOBS_PER_BUCKET = 25

ROLE_HEADINGS = [
    "About the Role",
    "The Role",
    "Job Description",
    "What you'll do",
    "What you will do",
    "What you'll achieve",
    "What you will achieve",
    "Responsibilities",
    "In this role",
]

RESPONSIBILITY_HEADINGS = [
    "Responsibilities:",
    "Responsibilities",
    "What you'll do",
    "What you will do",
    "What you'll achieve",
    "What you will achieve",
]

QUALIFICATION_HEADINGS = [
    "You May Be a Good Fit If You Have:",
    "You May Be a Good Fit If You Have",
    "You may be a good fit if you have:",
    "You may be a good fit if you have",
    "You may be a good fit if you:",
    "You may be a good fit if you",
    "Who you are",
    "We're looking for someone who",
    "We are looking for someone who",
    "You may be a fit",
    "Minimum requirements",
    "Qualifications",
    "Skills you'll need",
    "We're excited about you because",
]

PREFERRED_QUALIFICATION_HEADINGS = [
    "Strong Candidates May Also Have:",
    "Strong Candidates May Also Have",
    "Preferred qualifications:",
    "Preferred qualifications",
    "Nice to have:",
    "Nice to have",
]

COMPENSATION_HEADINGS = [
    "Annual Salary:",
    "Annual Salary",
    "Compensation:",
    "Compensation",
    "Salary range:",
    "Salary range",
]

LOGISTICS_HEADINGS = [
    "Logistics",
    "Location-based hybrid policy:",
    "Location-based hybrid policy",
    "Minimum education:",
    "Minimum education",
]

VISA_HEADINGS = [
    "Visa sponsorship:",
    "Visa sponsorship",
]

DEADLINE_HEADINGS = [
    "Deadline to Apply:",
    "Deadline to Apply",
]

COMPANY_HEADINGS = [
    "Who we are",
    "About Us",
    "About Stripe",
    "About Airbnb",
    "About Ramp",
    "About the Company",
]

NON_US_LOCATION_TERMS = [
    "canada",
    "toronto",
    "montreal",
    "united kingdom",
    "uk",
    "london",
    "europe",
    "emea",
    "india",
    "bengaluru",
    "singapore",
    "dublin",
    "ireland",
    "paris",
    "australia",
    "sydney",
    "japan",
    "tokyo",
]

US_LOCATION_TERMS = [
    "united states",
    "remote-us",
    "us-remote",
    "us-national",
    "remote in the us",
    "new york",
    "nyc",
    "san francisco",
    "seattle",
    "boston",
    "cambridge",
    "chicago",
    "atlanta",
    "los angeles",
    "austin",
    "washington",
    "california",
    "ma",
    "ny",
    "ca",
    "wa",
    "il",
    "ga",
    "tx",
]

SECTION_STOP_HEADINGS = sorted(
    set(
        ["Responsibilities:", "Responsibilities", "What you'll do", "What you will do", "What you'll achieve", "What you will achieve"]
        + QUALIFICATION_HEADINGS
        + PREFERRED_QUALIFICATION_HEADINGS
        + COMPENSATION_HEADINGS
        + LOGISTICS_HEADINGS
        + VISA_HEADINGS
        + DEADLINE_HEADINGS
        + COMPANY_HEADINGS
    )
    | {
        "About the Team",
        "Benefits",
        "The annual compensation range",
        "Equal Opportunity",
        "Our Commitment",
        "Apply for this job",
    },
    key=len,
    reverse=True,
)


def write_daily_queue(
    jobs: list[dict[str, Any]] | None = None,
    output_dir: Path = DAILY_QUEUE_DIR,
    db_path: Path = DB_PATH,
    date_slug: str | None = None,
) -> dict[str, str]:
    jobs = jobs if jobs is not None else list_jobs(db_path=db_path)
    queue_jobs = limit_jobs_for_queue(jobs)
    date_slug = date_slug or timestamp_slug()
    output_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_dir / f"{date_slug}.md"
    csv_path = output_dir / f"{date_slug}.csv"
    summary_path = output_dir / f"{date_slug}_summary.json"
    md_path.write_text(render_markdown(queue_jobs, date_slug), encoding="utf-8")
    write_csv(queue_jobs, csv_path)
    summary_path.write_text(json.dumps(build_pipeline_summary(queue_jobs), indent=2), encoding="utf-8")
    return {"markdown": str(md_path), "csv": str(csv_path), "summary": str(summary_path)}


def limit_jobs_for_queue(jobs: list[dict[str, Any]], per_bucket: int = MAX_JOBS_PER_BUCKET) -> list[dict[str, Any]]:
    limited: list[dict[str, Any]] = []
    for bucket in BUCKET_ORDER:
        items = [job for job in jobs if job.get("bucket", "manual_review") == bucket]
        limited.extend(sorted(items, key=lambda item: item.get("total_score", 0), reverse=True)[:per_bucket])
    return limited


def render_markdown(jobs: list[dict[str, Any]], date_slug: str) -> str:
    lines = [f"# Daily Job Queue - {date_slug}", ""]
    grouped = {bucket: [] for bucket in BUCKET_ORDER}
    for job in jobs:
        grouped.setdefault(job.get("bucket", "manual_review"), []).append(job)
    for bucket in BUCKET_ORDER:
        items = sorted(grouped.get(bucket, []), key=lambda item: item.get("total_score", 0), reverse=True)
        lines.extend([f"## {bucket.replace('_', ' ').title()}", ""])
        if not items:
            lines.extend(["No jobs in this bucket.", ""])
            continue
        for index, job in enumerate(items, 1):
            reasons = job.get("score_reasons", [])
            sections = extract_role_sections(job)
            lines.extend(
                [
                    f"### {index}. {job['title']} - {job['company']}",
                    "- [ ] Review / apply",
                    f"- Location: {display_location(job)}",
                    f"- Score: {job.get('total_score', 0)}/100",
                    f"- Sponsorship: {job.get('sponsorship_signal', 'unknown')}",
                    f"- Apply: {job.get('apply_url') or 'No apply URL'}",
                    f"- Overview: {markdown_summary(sections['role_overview'])}",
                    f"- Key responsibilities: {markdown_summary(sections['key_responsibilities'])}",
                    f"- Reasons: {'; '.join(reasons) if reasons else 'No reasons recorded.'}",
                    "",
                ]
            )
    lines.extend(render_pipeline_summary(build_pipeline_summary(jobs)))
    return "\n".join(lines)


def write_csv(jobs: list[dict[str, Any]], path: Path) -> None:
    fields = [
        "bucket",
        "total_score",
        "sponsorship_signal",
        "company",
        "title",
        "location",
        "apply_url",
        "role_overview",
        "key_responsibilities",
        "qualifications",
        "preferred_qualifications",
        "compensation",
        "logistics",
        "visa_sponsorship",
        "application_deadline",
        "company_overview",
        "status",
        "score_reasons",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for job in jobs:
            sections = extract_role_sections(job)
            writer.writerow(
                {
                    "bucket": _csv_value(job.get("bucket")),
                    "total_score": _csv_value(job.get("total_score")),
                    "sponsorship_signal": _csv_value(job.get("sponsorship_signal")),
                    "company": _csv_value(job.get("company")),
                    "title": _csv_value(job.get("title")),
                    "location": display_location(job),
                    "apply_url": _csv_value(job.get("apply_url")),
                    "role_overview": sections["role_overview"],
                    "key_responsibilities": sections["key_responsibilities"],
                    "qualifications": sections["qualifications"],
                    "preferred_qualifications": sections["preferred_qualifications"],
                    "compensation": sections["compensation"],
                    "logistics": sections["logistics"],
                    "visa_sponsorship": sections["visa_sponsorship"],
                    "application_deadline": sections["application_deadline"],
                    "company_overview": sections["company_overview"],
                    "status": _csv_value(job.get("status")),
                    "score_reasons": _csv_value(job.get("score_reasons")),
                }
            )


def job_overview(job: dict[str, Any], limit: int = 360) -> str:
    return markdown_summary(extract_role_sections(job)["role_overview"])


def responsibility_summary(job: dict[str, Any], limit: int = 360) -> str:
    return markdown_summary(extract_role_sections(job)["key_responsibilities"])


def display_location(job: dict[str, Any]) -> str:
    raw = clean_text(job.get("location"))
    if not raw:
        return "Unknown"
    parts = [p.strip() for p in re.split(r"[;|]", raw) if p.strip()]
    expanded_parts = []
    for part in parts:
        if "," in part and any(term in part.lower() for term in NON_US_LOCATION_TERMS):
            expanded_parts.extend([p.strip() for p in part.split(",") if p.strip()])
        else:
            expanded_parts.append(part)
    us_parts = []
    for part in expanded_parts:
        lower = f" {part.lower()} "
        is_non_us = any(term in lower for term in NON_US_LOCATION_TERMS)
        is_us = any(term in lower for term in US_LOCATION_TERMS)
        if is_us and not is_non_us:
            us_parts.append(part)
        elif is_us and is_non_us:
            cleaned = _remove_non_us_terms(part)
            if cleaned:
                us_parts.append(cleaned)
    deduped = []
    for part in us_parts:
        if part not in deduped:
            deduped.append(part)
    return "; ".join(deduped) if deduped else "US location unclear"


def extract_role_sections(job: dict[str, Any]) -> dict[str, str]:
    description = _normalize_apostrophes(clean_text(job.get("description")))
    if not description:
        return {
            "role_overview": "No role overview available.",
            "key_responsibilities": "No responsibilities available.",
            "qualifications": "No qualifications section found.",
            "preferred_qualifications": "No preferred qualifications section found.",
            "compensation": "No compensation section found.",
            "logistics": "No logistics section found.",
            "visa_sponsorship": "No visa sponsorship section found.",
            "application_deadline": "No application deadline section found.",
            "company_overview": "No company overview available.",
        }

    sentences = _sentences(description)
    role_text = _section_after_heading(description, ROLE_HEADINGS)
    responsibility_text = _section_after_heading(description, RESPONSIBILITY_HEADINGS)
    qualification_text = _section_after_heading(description, QUALIFICATION_HEADINGS)
    preferred_qualification_text = _section_after_heading(description, PREFERRED_QUALIFICATION_HEADINGS)
    compensation_text = _section_after_heading(description, COMPENSATION_HEADINGS, prefer_earliest=False)
    logistics_text = _section_after_heading(description, LOGISTICS_HEADINGS)
    visa_text = _section_after_heading(description, VISA_HEADINGS, prefer_earliest=False)
    deadline_text = _section_after_heading(description, DEADLINE_HEADINGS, prefer_earliest=False)
    company_text = _section_after_heading(description, COMPANY_HEADINGS)

    return {
        "role_overview": role_text or _fallback_role_text(sentences),
        "key_responsibilities": responsibility_text or _responsibility_from_sentences(sentences),
        "qualifications": qualification_text or "No qualifications section found.",
        "preferred_qualifications": preferred_qualification_text or "No preferred qualifications section found.",
        "compensation": compensation_text or _inline_value_after_heading(description, COMPENSATION_HEADINGS) or "No compensation section found.",
        "logistics": logistics_text or "No logistics section found.",
        "visa_sponsorship": visa_text or _inline_value_after_heading(description, VISA_HEADINGS) or "No visa sponsorship section found.",
        "application_deadline": deadline_text or _inline_value_after_heading(description, DEADLINE_HEADINGS) or "No application deadline section found.",
        "company_overview": company_text or _fallback_company_text(sentences),
    }


def _section_after_heading(text: str, headings: list[str], prefer_earliest: bool = True) -> str:
    normalized = _normalize_apostrophes(text)
    starts = []
    lower = normalized.lower()
    for heading in headings:
        index = _find_heading(lower, heading.lower())
        if index >= 0:
            starts.append((index, heading))
    if not starts:
        return ""
    if prefer_earliest:
        start, heading = min(starts, key=lambda item: item[0])
    else:
        start, heading = starts[0]
    content_start = start + len(heading)
    stop = _next_heading_index(normalized, content_start)
    section = normalized[content_start:stop].strip(" :-\n\t")
    return _clean_section(section)


def _next_heading_index(text: str, start: int) -> int:
    lower = text.lower()
    indexes = []
    for heading in SECTION_STOP_HEADINGS:
        index = _find_heading(lower[start + 20 :], heading.lower())
        if index >= 0:
            indexes.append(start + 20 + index)
    return min(indexes) if indexes else len(text)


def _find_heading(lower_text: str, lower_heading: str) -> int:
    index = lower_text.find(lower_heading)
    while index >= 0:
        before = lower_text[index - 1] if index > 0 else " "
        after_index = index + len(lower_heading)
        after = lower_text[after_index] if after_index < len(lower_text) else " "
        before_ok = not before.isalnum()
        after_ok = not after.isalnum()
        if before_ok and after_ok:
            return index
        index = lower_text.find(lower_heading, index + 1)
    return -1


def _responsibility_from_sentences(sentences: list[str]) -> str:
    responsibility_terms = [
        "responsible",
        "own",
        "lead",
        "partner",
        "manage",
        "define",
        "drive",
        "build",
        "coordinate",
        "collaborate",
        "analyze",
        "translate",
        "requirements",
        "roadmap",
        "stakeholder",
    ]
    picked = [s for s in sentences if any(term in s.lower() for term in responsibility_terms)]
    return " ".join(picked[:4] or sentences[:3]) or "No responsibilities available."


def _fallback_role_text(sentences: list[str]) -> str:
    skip_terms = ["about stripe", "about airbnb", "about us", "who we are", "equal opportunity"]
    useful = [s for s in sentences if not any(term in s.lower() for term in skip_terms)]
    return " ".join(useful[:4] or sentences[:3]) or "No role overview available."


def _fallback_company_text(sentences: list[str]) -> str:
    return " ".join(sentences[:2]) if sentences else "No company overview available."


def _sentences(text: str) -> list[str]:
    compact = " ".join(_normalize_apostrophes(text).split())
    parts = []
    for part in compact.replace("!", ".").replace("?", ".").split("."):
        cleaned = part.strip()
        if len(cleaned) >= 30:
            parts.append(cleaned + ".")
    return parts


def _clean_section(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^(overview|application)\b", "", text, flags=re.IGNORECASE).strip(" :-")
    return text


def _inline_value_after_heading(text: str, headings: list[str], max_chars: int = 600) -> str:
    normalized = _normalize_apostrophes(text)
    lower = normalized.lower()
    for heading in headings:
        index = lower.find(heading.lower())
        if index < 0:
            continue
        start = index + len(heading)
        stop_candidates = [normalized.find(marker, start + 1) for marker in [". ", "\n"]]
        stop_candidates = [candidate for candidate in stop_candidates if candidate >= 0]
        stop = min(stop_candidates) if stop_candidates else min(len(normalized), start + max_chars)
        value = normalized[start:stop].strip(" :-\n\t")
        if value:
            return value
    return ""


def sentence_summary(text: str, max_sentences: int = 2) -> str:
    sentences = _sentences(text)
    if sentences:
        return " ".join(sentences[:max_sentences])
    return text


def markdown_summary(text: str, max_words: int = 45) -> str:
    sentence_text = sentence_summary(text, max_sentences=3)
    words = sentence_text.split()
    if len(words) <= max_words:
        return sentence_text
    return " ".join(words[:max_words]) + " [full text in CSV]"


def build_pipeline_summary(jobs: list[dict[str, Any]]) -> dict[str, Any]:
    stats = get_stats()
    latest = stats.get("latest_ingest") or {}
    errors = latest.get("errors") or "[]"
    if isinstance(errors, str):
        try:
            errors = json.loads(errors)
        except json.JSONDecodeError:
            errors = [errors]
    return {
        "job_count_in_queue": len(jobs),
        "bucket_counts": stats.get("buckets", {}),
        "latest_ingest": {
            "started_at": latest.get("started_at"),
            "finished_at": latest.get("finished_at"),
            "source_count": latest.get("source_count", 0),
            "fetched_count": latest.get("fetched_count", 0),
            "inserted_count": latest.get("inserted_count", 0),
            "updated_count": latest.get("updated_count", 0),
            "error_count": latest.get("error_count", 0),
            "errors": errors,
        },
    }


def render_pipeline_summary(summary: dict[str, Any]) -> list[str]:
    latest = summary["latest_ingest"]
    lines = [
        "## Pipeline Summary",
        "",
        f"- Jobs in this queue: {summary['job_count_in_queue']}",
        f"- Latest ingest fetched: {latest['fetched_count']}",
        f"- Latest ingest inserted: {latest['inserted_count']}",
        f"- Latest ingest updated: {latest['updated_count']}",
        f"- Latest ingest errors: {latest['error_count']}",
        f"- Skipped jobs omitted from queue: {summary['bucket_counts'].get('skip', 0)}",
    ]
    if latest["errors"]:
        lines.append("- What did not work:")
        for error in latest["errors"]:
            lines.append(f"  - {error}")
    else:
        lines.append("- What did not work: no ingest errors recorded.")
    lines.append("")
    return lines


def _normalize_apostrophes(text: str) -> str:
    return (
        text.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2014", " - ")
        .replace("\u2013", "-")
    )


def _remove_non_us_terms(text: str) -> str:
    parts = [p.strip() for p in text.split(",") if p.strip()]
    kept = []
    for part in parts:
        lower = f" {part.lower()} "
        if any(term in lower for term in NON_US_LOCATION_TERMS):
            continue
        kept.append(part)
    return ", ".join(kept)


def _csv_value(value: Any) -> str:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    return "" if value is None else str(value)
