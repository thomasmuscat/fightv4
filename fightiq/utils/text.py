from __future__ import annotations
import re
import uuid
from datetime import datetime
from typing import Any

def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    if text in ["", "--", "nan", "None"]:
        return None
    return text

def slugify(value: str | None) -> str:
    value = clean_text(value) or ""
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-")

def stable_uuid(prefix: str, slug: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"fightiq:{prefix}:{slug}"))

def to_int(value: Any, default: int = 0) -> int:
    value = clean_text(value)
    if not value:
        return default
    m = re.search(r"-?\d+", value)
    return int(m.group(0)) if m else default

def to_float(value: Any) -> float | None:
    value = clean_text(value)
    if not value:
        return None
    value = value.replace("%", "").replace('"', "")
    m = re.search(r"-?\d+(\.\d+)?", value)
    return float(m.group(0)) if m else None

def height_to_cm(value: Any) -> float | None:
    value = clean_text(value)
    if not value:
        return None
    m = re.search(r"(\d+)'\s*(\d+)", value)
    if not m:
        return None
    return round((int(m.group(1))*12 + int(m.group(2))) * 2.54, 1)

def reach_to_cm(value: Any) -> float | None:
    n = to_float(value)
    if n is None:
        return None
    return round(n * 2.54, 1) if n < 100 else round(n, 1)

def parse_date(value: Any) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    for fmt in ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None

def parse_fraction(value: Any) -> tuple[int | None, int | None]:
    text = clean_text(value)
    if not text:
        return None, None
    if "of" in text:
        a, b = text.split("of", 1)
    elif "/" in text:
        a, b = text.split("/", 1)
    else:
        return None, None
    try:
        return int(a.strip()), int(b.strip())
    except Exception:
        return None, None
