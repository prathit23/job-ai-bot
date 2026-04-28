from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .paths import SCORING_PATH
from .utils import clean_text, load_json


DEFAULT_CONFIG = {
    "valid_title_patterns": [
        "product manager",
        "product owner",
        "technical product manager",
        "associate product manager",
        "senior product manager",
        "lead product manager",
        "group product manager",
        "product analyst",
        "senior product analyst",
        "business analyst",
        "business systems analyst",
        "business process analyst",
        "systems analyst",
        "product operations",
        "product operations manager",
        "program manager",
        "technical program manager",
        "strategic program manager",
        "business program manager",
        "digital product",
        "platform product",
        "data product",
        "scrum product owner",
        "solutions product",
        "product strategy",
        "strategy and operations",
        "business operations manager",
        "go-to-market program manager",
    ],
    "excluded_title_patterns": [
        "software engineer",
        "data scientist",
        "machine learning engineer",
        "ml engineer",
        "frontend engineer",
        "backend engineer",
        "full stack engineer",
        "solutions engineer",
        "account executive",
        "sales manager",
        "marketing manager",
        "customer success manager",
        "customer activation manager",
        "designer",
        "recruiter",
        "counsel",
        "attorney",
        "finance manager",
        "data engineer",
    ],
    "positive_sponsorship_phrases": [
        "h-1b",
        "h1b",
        "visa sponsorship",
        "sponsor visas",
        "immigration sponsorship",
        "work visa",
        "employment sponsorship",
    ],
    "negative_sponsorship_phrases": [
        "no sponsorship",
        "without sponsorship",
        "will not sponsor",
        "unable to sponsor",
        "cannot sponsor",
        "do not sponsor",
        "must be authorized to work in the united states without",
        "must be authorized to work in the us without",
        "us citizen",
        "u.s. citizen",
        "citizenship required",
        "green card required",
    ],
    "target_location_terms": [
        "remote",
        "remote-us",
        "remote us",
        "remote - us",
        "remote, us",
        "remote united states",
        "hybrid",
        "boston",
        "cambridge",
        "new york",
        "nyc",
        "manhattan",
        "brooklyn",
    ],
    "us_location_terms": [
        "united states",
        " usa",
        " us ",
        "u.s.",
        "remote-us",
        "remote us",
        "remote - us",
        "remote, us",
        "remote united states",
        "boston",
        "cambridge",
        "new york",
        "nyc",
        "manhattan",
        "brooklyn",
        "chicago",
        "atlanta",
        "san francisco",
        "seattle",
        "los angeles",
        "austin",
        "washington",
        "new jersey",
        "california",
        "massachusetts",
        "illinois",
        "georgia",
    ],
    "non_us_location_terms": [
        "china",
        "canada",
        "toronto",
        "mexico",
        "bengaluru",
        "india",
        "singapore",
        "dublin",
        "ireland",
        "london",
        "paris",
        "sydney",
        "australia",
        "japan",
        "tokyo",
        "bucharest",
        "barcelona",
        "europe",
        "emea",
    ],
    "seniority_penalty_terms": [
        "director",
        "vp",
        "vice president",
        "head of",
        "principal",
        "staff product",
    ],
    "bucket_thresholds": {
        "apply": 78,
        "maybe": 60,
    },
}


def load_scoring_config(path: Path = SCORING_PATH) -> dict[str, Any]:
    config = load_json(path, DEFAULT_CONFIG)
    merged = dict(DEFAULT_CONFIG)
    for key, value in config.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            nested = dict(merged[key])
            nested.update(value)
            merged[key] = nested
        else:
            merged[key] = value
    return merged


def classify_sponsorship(text: str, config: dict[str, Any] | None = None) -> tuple[int, str, list[str]]:
    config = config or load_scoring_config()
    body = text.lower()
    reasons: list[str] = []
    if any(term.lower() in body for term in config["negative_sponsorship_phrases"]):
        reasons.append("Posting appears to rule out sponsorship.")
        return 0, "negative", reasons
    if any(term.lower() in body for term in config["positive_sponsorship_phrases"]):
        reasons.append("Posting includes a positive visa/sponsorship signal.")
        return 100, "positive", reasons
    reasons.append("No clear sponsorship language found.")
    return 55, "unknown", reasons


def score_job(job: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
    config = config or load_scoring_config()
    title = clean_text(job.get("title"))
    location = clean_text(job.get("location"))
    description = clean_text(job.get("description"))
    combined = f"{title} {location} {description}".lower()
    reasons: list[str] = []

    excluded_matches = [kw for kw in config["excluded_title_patterns"] if kw.lower() in title.lower()]
    role_matches = [kw for kw in config["valid_title_patterns"] if kw.lower() in title.lower()]
    if excluded_matches:
        role_score = 0
        reasons.append(f"Excluded title match: {', '.join(excluded_matches[:2])}.")
    elif role_matches:
        role_score = min(100, 50 + len(role_matches) * 20)
    else:
        role_score = 10

    if role_matches:
        reasons.append(f"Title role match: {', '.join(role_matches[:3])}.")
    elif not excluded_matches:
        reasons.append("No strong PM/PO/BA title match.")

    loc_lower = location.lower()
    has_us_location = any(term.lower() in f" {loc_lower} " for term in config["us_location_terms"])
    has_non_us_location = any(term.lower() in loc_lower for term in config["non_us_location_terms"])
    has_target_location = any(term.lower() in loc_lower for term in config["target_location_terms"])

    if has_non_us_location and not has_us_location:
        location_score = 0
        reasons.append("Location appears outside the US target market.")
    elif has_target_location and has_us_location:
        location_score = 100
        reasons.append("Location matches remote/hybrid/Boston/NYC target.")
    elif has_us_location:
        location_score = 75
        reasons.append("US location found, but remote/Boston/NYC is unclear.")
    else:
        location_score = 20
        reasons.append("Location is outside or unclear for target market.")

    sponsorship_score, sponsorship_signal, sponsor_reasons = classify_sponsorship(combined, config)
    reasons.extend(sponsor_reasons)

    seniority_score = 100
    title_lower = title.lower()
    if any(term.lower() in title_lower for term in config["seniority_penalty_terms"]):
        seniority_score = 45
        reasons.append("Seniority may be too high.")
    elif re.search(r"\b(senior|sr\.?|lead)\b", title_lower):
        seniority_score = 80
        reasons.append("Senior/lead role; keep if experience aligns.")

    desc_len = len(description)
    if desc_len > 6000:
        effort_score = 65
        reasons.append("Long application/JD; likely higher review effort.")
    elif desc_len < 400:
        effort_score = 55
        reasons.append("Sparse JD; manual review recommended.")
    else:
        effort_score = 80

    total = round(
        role_score * 0.35
        + location_score * 0.2
        + sponsorship_score * 0.2
        + seniority_score * 0.15
        + effort_score * 0.1
    )

    thresholds = config["bucket_thresholds"]
    if has_non_us_location and not has_us_location:
        bucket = "skip"
    elif excluded_matches:
        bucket = "skip"
    elif sponsorship_signal == "negative":
        bucket = "skip"
    elif total >= thresholds["apply"] and role_score >= 60:
        bucket = "apply"
    elif total >= thresholds["maybe"]:
        bucket = "maybe"
    else:
        bucket = "manual_review"

    return {
        "role_score": role_score,
        "location_score": location_score,
        "sponsorship_score": sponsorship_score,
        "seniority_score": seniority_score,
        "effort_score": effort_score,
        "total_score": total,
        "sponsorship_signal": sponsorship_signal,
        "bucket": bucket,
        "score_reasons": reasons,
        "remote_flag": 1 if location_score == 100 and "remote" in combined else 0,
    }
