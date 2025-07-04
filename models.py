from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class PocketArticle:
    item_id: str
    resolved_url: Optional[str] = None
    resolved_title: Optional[str] = None
    excerpt: Optional[str] = None
    tags: Optional[Dict[str, Any]] = field(default_factory=dict)
    status: Optional[str] = None
    time_added: Optional[str] = None  # ISO 8601 string
    word_count: Optional[int] = None
    original: Dict[str, Any] = field(
        default_factory=dict
    )  # Preserve all original fields for auditing
