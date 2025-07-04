from typing import Dict, Any
from datetime import datetime
from models import PocketArticle


def parse_pocket_article(raw: Dict[str, Any]) -> PocketArticle:
    """
    Parse a raw Pocket API article dict into a PocketArticle dataclass.
    Handles missing/null fields, type validation, and timestamp normalization.
    """

    def get_str(field):
        val = raw.get(field)
        return str(val) if val is not None else None

    def get_int(field):
        val = raw.get(field)
        try:
            return int(val) if val is not None else None
        except (ValueError, TypeError):
            return None

    def normalize_time(ts):
        if not ts:
            return None
        try:
            # Pocket time_added is a Unix timestamp string
            dt = datetime.utcfromtimestamp(int(ts))
            return dt.isoformat() + "Z"
        except Exception:
            return None

    # Extract fields
    item_id = get_str("item_id")
    resolved_url = get_str("resolved_url")
    resolved_title = get_str("resolved_title")
    excerpt = get_str("excerpt")
    tags = raw.get("tags") if isinstance(raw.get("tags"), dict) else {}
    status = get_str("status")
    time_added = normalize_time(raw.get("time_added"))
    word_count = get_int("word_count")

    # Build PocketArticle
    return PocketArticle(
        item_id=item_id,
        resolved_url=resolved_url,
        resolved_title=resolved_title,
        excerpt=excerpt,
        tags=tags,
        status=status,
        time_added=time_added,
        word_count=word_count,
        original=raw.copy(),
    )
