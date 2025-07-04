#!/usr/bin/env python3
"""
CSV Parser Module for Pocket Export Tool
Handles parsing Pocket's manual CSV export format and mapping to API structure.
"""

import csv
import logging
from typing import Dict, List, Optional, Iterator
from datetime import datetime
import re
import glob
import os
import tempfile

logger = logging.getLogger(__name__)


class PocketCSVParser:
    """Parse Pocket's manual CSV export format and map to API structure."""

    def __init__(self, csv_file_path: str):
        self.csv_file_path = csv_file_path
        # Support both Pocket's manual export format and the actual CSV format
        self.expected_columns_variants = [
            # Actual CSV format from Pocket
            ["title", "url", "time_added", "tags", "status"],
            # Original expected format (for backward compatibility)
            [
                "URL",
                "Title",
                "Excerpt",
                "Author",
                "Tags",
                "Time Added",
                "Time Updated",
                "Time Read",
                "Time Favorited",
                "Status",
            ],
        ]

    def parse_csv(self) -> List[Dict]:
        """
        Parse Pocket's CSV export format.

        Returns:
            List of article dictionaries in API-compatible format
        """
        articles = []

        try:
            with open(self.csv_file_path, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                # Validate CSV structure
                if not self._validate_csv_structure(reader.fieldnames):
                    raise ValueError(
                        f"Invalid CSV structure. Expected one of: {self.expected_columns_variants}"
                    )

                for row_num, row in enumerate(
                    reader, start=2
                ):  # Start at 2 (header is row 1)
                    try:
                        article = self.map_to_api_format(row)
                        if article:
                            articles.append(article)
                    except Exception as e:
                        logger.warning(f"Error parsing row {row_num}: {e}")
                        continue

                logger.info(f"Successfully parsed {len(articles)} articles from CSV")
                return articles

        except FileNotFoundError:
            logger.error(f"CSV file not found: {self.csv_file_path}")
            raise
        except Exception as e:
            logger.error(f"Error parsing CSV file: {e}")
            raise

    def stream_csv(self) -> Iterator[Dict]:
        """
        Stream CSV parsing for memory efficiency.

        Yields:
            Article dictionaries in API-compatible format
        """
        try:
            with open(self.csv_file_path, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                # Validate CSV structure
                if not self._validate_csv_structure(reader.fieldnames):
                    raise ValueError(
                        f"Invalid CSV structure. Expected one of: {self.expected_columns_variants}"
                    )

                for row_num, row in enumerate(
                    reader, start=2
                ):  # Start at 2 (header is row 1)
                    try:
                        article = self.map_to_api_format(row)
                        if article:
                            yield article
                    except Exception as e:
                        logger.warning(f"Error parsing row {row_num}: {e}")
                        continue

        except FileNotFoundError:
            logger.error(f"CSV file not found: {self.csv_file_path}")
            raise
        except Exception as e:
            logger.error(f"Error parsing CSV file: {e}")
            raise

    def load_csv_as_source_of_truth(self) -> Dict[str, Dict]:
        """
        Load CSV as authoritative reference, return URL -> article mapping.
        Optimized for validation where CSV is the source of truth.

        Returns:
            Dictionary mapping normalized URLs to article data
        """
        url_mapping = {}

        try:
            with open(self.csv_file_path, "r", encoding="utf-8") as file:
                reader = csv.DictReader(file)

                # Validate CSV structure
                if not self._validate_csv_structure(reader.fieldnames):
                    raise ValueError(
                        f"Invalid CSV structure. Expected one of: {self.expected_columns_variants}"
                    )

                for row_num, row in enumerate(reader, start=2):
                    try:
                        article = self.map_to_api_format(row)
                        if article and article.get("resolved_url"):
                            # Normalize URL for comparison
                            normalized_url = self._normalize_url(
                                article["resolved_url"]
                            )
                            if normalized_url:
                                url_mapping[normalized_url] = article
                    except Exception as e:
                        logger.warning(f"Error parsing row {row_num}: {e}")
                        continue

                logger.info(f"Loaded {len(url_mapping)} articles as source of truth")
                return url_mapping

        except FileNotFoundError:
            logger.error(f"CSV file not found: {self.csv_file_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading CSV as source of truth: {e}")
            raise

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison (remove protocol, www, trailing slashes)."""
        if not url:
            return ""

        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            # Remove protocol and www, normalize path
            normalized = f"{parsed.netloc.replace('www.', '')}{parsed.path.rstrip('/')}"
            if parsed.query:
                normalized += f"?{parsed.query}"
            return normalized.lower()
        except Exception:
            return url.lower()

    def _validate_csv_structure(self, fieldnames: Optional[List[str]]) -> bool:
        """Validate that CSV has expected Pocket export columns."""
        if not fieldnames:
            return False

        # Check if fieldnames match any of our expected variants
        for expected_columns in self.expected_columns_variants:
            if all(col in fieldnames for col in expected_columns):
                return True

        # Also check for essential columns in case of partial matches
        essential_columns_variants = [
            ["URL", "Title"],  # Original format
            ["url", "title"],  # Actual format
        ]

        for essential_columns in essential_columns_variants:
            if all(col in fieldnames for col in essential_columns):
                return True

        return False

    def map_to_api_format(self, csv_row: Dict) -> Optional[Dict]:
        """
        Map CSV row to API export structure.

        Args:
            csv_row: Dictionary representing a CSV row

        Returns:
            Article dictionary in API-compatible format or None if invalid
        """
        try:
            # Handle both CSV formats - check which one we have
            if "url" in csv_row and "title" in csv_row:
                # Actual CSV format: title,url,time_added,tags,status
                url = csv_row.get("url", "").strip()
                title = csv_row.get("title", "").strip()
                time_added = self._parse_timestamp(csv_row.get("time_added", ""))
                tags_str = csv_row.get("tags", "").strip()
                status_raw = csv_row.get("status", "unread")

                # Convert status to API format
                status = "0" if status_raw == "unread" else "1"

                # Create API-compatible structure
                article = {
                    "item_id": self._generate_item_id(url, title),
                    "resolved_url": url,
                    "resolved_title": title,
                    "excerpt": "",  # Not available in this format
                    "tags": self._parse_tags(tags_str),
                    "status": status,
                    "time_added": time_added,
                    "time_updated": time_added,  # Use time_added as fallback
                    "time_read": None,
                    "time_favorited": None,
                    "word_count": 0,  # Not available in this format
                    "original": {"csv_row": csv_row, "source": "manual_csv_export"},
                }

            else:
                # Original expected format: URL,Title,Excerpt,Author,Tags,Time Added,...
                url = csv_row.get("URL", "").strip()
                title = csv_row.get("Title", "").strip()

                # Skip rows without essential data
                if not url or not title:
                    return None

                # Parse tags
                tags_str = csv_row.get("Tags", "").strip()
                tags = self._parse_tags(tags_str)

                # Parse timestamps
                time_added = self._parse_timestamp(csv_row.get("Time Added", ""))
                time_updated = self._parse_timestamp(csv_row.get("Time Updated", ""))
                time_read = self._parse_timestamp(csv_row.get("Time Read", ""))
                time_favorited = self._parse_timestamp(
                    csv_row.get("Time Favorited", "")
                )

                # Parse status
                status = csv_row.get("Status", "0")

                # Create API-compatible structure
                article = {
                    "item_id": self._generate_item_id(url, title),
                    "resolved_url": url,
                    "resolved_title": title,
                    "excerpt": csv_row.get("Excerpt", "").strip(),
                    "tags": tags,
                    "status": status,
                    "time_added": time_added,
                    "time_updated": time_updated,
                    "time_read": time_read,
                    "time_favorited": time_favorited,
                    "word_count": self._extract_word_count(csv_row.get("Excerpt", "")),
                    "original": {"csv_row": csv_row, "source": "manual_csv_export"},
                }

            return article

        except Exception as e:
            logger.warning(f"Error mapping CSV row to API format: {e}")
            return None

    def _parse_tags(self, tags_str: str) -> Dict:
        """Parse tags string into dictionary format."""
        if not tags_str:
            return {}

        tags = {}
        # Split by common delimiters and clean
        tag_list = re.split(r"[,;|]", tags_str)

        for i, tag in enumerate(tag_list):
            tag = tag.strip()
            if tag:
                tags[str(i)] = {"tag": tag, "item_id": f"csv_tag_{i}"}

        return tags

    def _parse_timestamp(self, timestamp_str: str) -> Optional[str]:
        """Parse timestamp string to ISO 8601 format."""
        if not timestamp_str or timestamp_str.strip() == "":
            return None

        try:
            # Handle different timestamp formats
            timestamp_str = timestamp_str.strip()

            # Try parsing as Unix timestamp
            if timestamp_str.isdigit():
                timestamp = int(timestamp_str)
                return datetime.fromtimestamp(timestamp).isoformat() + "Z"

            # Try parsing as ISO format
            if "T" in timestamp_str:
                dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                return dt.isoformat() + "Z"

            # Try parsing as date format
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y %H:%M:%S"]:
                try:
                    dt = datetime.strptime(timestamp_str, fmt)
                    return dt.isoformat() + "Z"
                except ValueError:
                    continue

            logger.warning(f"Could not parse timestamp: {timestamp_str}")
            return None

        except Exception as e:
            logger.warning(f"Error parsing timestamp '{timestamp_str}': {e}")
            return None

    def _generate_item_id(self, url: str, title: str) -> str:
        """Generate a unique item ID for CSV articles."""
        import hashlib

        content = f"{url}{title}".encode("utf-8")
        return hashlib.md5(content, usedforsecurity=False).hexdigest()[:12]

    def _extract_word_count(self, text: str) -> int:
        """Extract word count from text."""
        if not text:
            return 0
        return len(text.split())


def parse_pocket_csv(csv_file_path: str) -> List[Dict]:
    """
    Convenience function to parse Pocket CSV export.

    Args:
        csv_file_path: Path to the CSV file

    Returns:
        List of article dictionaries in API-compatible format
    """
    parser = PocketCSVParser(csv_file_path)
    return parser.parse_csv()


def parse_all_pocket_csvs_in_dir(csv_dir: str) -> List[Dict]:
    """
    Parse and merge all CSV files in a directory, removing duplicate headers.
    Args:
        csv_dir: Directory containing CSV files
    Returns:
        List of article dictionaries in API-compatible format
    """
    all_articles = []
    csv_files = sorted(glob.glob(os.path.join(csv_dir, "*.csv")))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in directory: {csv_dir}")
    header = None
    for idx, csv_file in enumerate(csv_files):
        with open(csv_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if not lines:
            continue
        if idx == 0:
            header = lines[0]
            data_lines = lines[1:]
        else:
            # Only skip first line if it matches the header
            if lines[0].strip() == header.strip():
                data_lines = lines[1:]
            else:
                data_lines = lines
        # Write to a temp file for parsing
        with tempfile.NamedTemporaryFile(
            mode="w+", suffix=".csv", delete=False, encoding="utf-8"
        ) as tf:
            tf.write(header)
            tf.writelines(data_lines)
            tf.flush()
            tf.seek(0)
            temp_path = tf.name
        # DEBUG: Print header and first few lines
        with open(temp_path, "r", encoding="utf-8") as debug_f:
            debug_lines = debug_f.readlines()
            print(f"DEBUG: Temp file {temp_path} header: {debug_lines[0].strip()}")
            print(f"DEBUG: Temp file {temp_path} first 3 lines: {debug_lines[:3]}")
        # Parse this chunk
        parser = PocketCSVParser(temp_path)
        articles = parser.parse_csv()
        all_articles.extend(articles)
        os.unlink(temp_path)
    return all_articles
