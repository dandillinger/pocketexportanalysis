import os
import json
from pathlib import Path
from typing import List, Dict, Any


def ensure_dir(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)


def save_raw_json(data: Any, out_path: str) -> bool:
    try:
        ensure_dir(os.path.dirname(out_path))
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving raw JSON: {e}")
        return False


def save_articles_jsonl(articles: List[Any], out_path: str) -> bool:
    try:
        ensure_dir(os.path.dirname(out_path))
        with open(out_path, "w", encoding="utf-8") as f:
            for article in articles:
                # If dataclass, convert to dict
                if hasattr(article, "__dataclass_fields__"):
                    article = article.__dict__
                json.dump(article, f, ensure_ascii=False)
                f.write("\n")
        return True
    except Exception as e:
        print(f"Error saving articles JSONL: {e}")
        return False


def get_file_summary(path: str) -> Dict[str, Any]:
    try:
        size = os.path.getsize(path)
        with open(path, "r", encoding="utf-8") as f:
            count = sum(1 for _ in f)
        return {"file": path, "size_bytes": size, "article_count": count}
    except Exception as e:
        return {"file": path, "error": str(e)}
