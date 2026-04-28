from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def today_slug() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def timestamp_slug() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")


def load_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    no_tags = re.sub(r"<[^>]+>", " ", str(value))
    decoded = html.unescape(no_tags)
    return re.sub(r"\s+", " ", decoded).strip()


def stable_hash(*parts: str) -> str:
    joined = "\n".join(str(p).strip().lower() for p in parts if p)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-")
    return cleaned.lower() or "item"
