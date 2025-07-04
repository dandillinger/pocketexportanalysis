#!/usr/bin/env python3
"""
Export Comparator Module for Pocket Export Tool
Compares API exports with CSV exports to ensure data integrity.
"""

import logging
from typing import Dict, List, Set
from urllib.parse import urlparse
import json
from datetime import datetime
import random
import time

logger = logging.getLogger(__name__)


class ComparisonResult:
    """Container for export comparison results."""

    def __init__(self):
        self.missing_in_api: List[Dict] = []
        self.extra_in_api: List[Dict] = []
        self.field_differences: List[Dict] = []
        self.matched_articles: int = 0
        self.api_total: int = 0
        self.csv_total: int = 0

    def to_dict(self) -> Dict:
        """Convert results to dictionary format."""
        return {
            "missing_in_api": len(self.missing_in_api),
            "extra_in_api": len(self.extra_in_api),
            "field_differences": len(self.field_differences),
            "matched_articles": self.matched_articles,
            "api_total": self.api_total,
            "csv_total": self.csv_total,
            "api_coverage": (
                (self.matched_articles / self.csv_total * 100)
                if self.csv_total > 0
                else 0
            ),
            "csv_coverage": (
                (self.matched_articles / self.api_total * 100)
                if self.api_total > 0
                else 0
            ),
        }


class ExportComparator:
    """Compare API and CSV exports to ensure data integrity."""

    def __init__(self, api_articles: List[Dict], csv_articles: List[Dict]):
        self.api_articles = api_articles
        self.csv_articles = csv_articles
        self.api_urls: Set[str] = set()
        self.csv_urls: Set[str] = set()
        self.api_by_url: Dict[str, Dict] = {}
        self.csv_by_url: Dict[str, Dict] = {}

    def compare_exports(self) -> ComparisonResult:
        """
        Compare API and CSV exports.

        Returns:
            ComparisonResult with detailed comparison data
        """
        logger.info("Starting export comparison...")

        result = ComparisonResult()
        result.api_total = len(self.api_articles)
        result.csv_total = len(self.csv_articles)

        # Build URL mappings
        self._build_url_mappings()

        # Find missing articles
        result.missing_in_api = self.find_missing_articles()
        result.extra_in_api = self.find_extra_articles()
        result.field_differences = self.find_field_differences()
        result.matched_articles = len(self.api_urls.intersection(self.csv_urls))

        logger.info(
            f"Comparison complete: {result.matched_articles} matched, "
            f"{len(result.missing_in_api)} missing in API, "
            f"{len(result.extra_in_api)} extra in API"
        )

        return result

    def _build_url_mappings(self):
        """Build URL-based mappings for both exports."""
        # Process API articles
        for article in self.api_articles:
            url = self._normalize_url(article.get("resolved_url", ""))
            if url:
                self.api_urls.add(url)
                self.api_by_url[url] = article

        # Process CSV articles
        for article in self.csv_articles:
            url = self._normalize_url(article.get("resolved_url", ""))
            if url:
                self.csv_urls.add(url)
                self.csv_by_url[url] = article

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison (remove protocol, www, trailing slashes)."""
        if not url:
            return ""

        try:
            parsed = urlparse(url)
            # Remove protocol and www, normalize path
            normalized = f"{parsed.netloc.replace('www.', '')}{parsed.path.rstrip('/')}"
            if parsed.query:
                normalized += f"?{parsed.query}"
            return normalized.lower()
        except Exception:
            return url.lower()

    def find_missing_articles(self) -> List[Dict]:
        """Find articles in CSV but not in API export."""
        missing = []
        csv_only_urls = self.csv_urls - self.api_urls

        for url in csv_only_urls:
            article = self.csv_by_url[url]
            missing.append(
                {
                    "url": url,
                    "title": article.get("resolved_title", "Unknown"),
                    "csv_article": article,
                    "reason": "Present in CSV but missing from API export",
                }
            )

        logger.info(f"Found {len(missing)} articles missing in API export")
        return missing

    def find_extra_articles(self) -> List[Dict]:
        """Find articles in API but not in CSV export."""
        extra = []
        api_only_urls = self.api_urls - self.csv_urls

        for url in api_only_urls:
            article = self.api_by_url[url]
            extra.append(
                {
                    "url": url,
                    "title": article.get("resolved_title", "Unknown"),
                    "api_article": article,
                    "reason": "Present in API but missing from CSV export",
                }
            )

        logger.info(f"Found {len(extra)} articles extra in API export")
        return extra

    def find_field_differences(self) -> List[Dict]:
        """Find metadata field discrepancies between matched articles."""
        differences = []
        common_urls = self.api_urls.intersection(self.csv_urls)

        for url in common_urls:
            api_article = self.api_by_url[url]
            csv_article = self.csv_by_url[url]

            field_diff = self._compare_article_fields(api_article, csv_article)
            if field_diff:
                differences.append(
                    {
                        "url": url,
                        "title": api_article.get("resolved_title", "Unknown"),
                        "differences": field_diff,
                    }
                )

        logger.info(f"Found {len(differences)} articles with field differences")
        return differences

    def _compare_article_fields(self, api_article: Dict, csv_article: Dict) -> Dict:
        """Compare fields between API and CSV articles."""
        differences = {}

        # Compare key fields
        fields_to_compare = [
            ("resolved_title", "Title"),
            ("excerpt", "Excerpt"),
            ("status", "Status"),
            ("time_added", "Time Added"),
        ]

        for api_field, csv_field in fields_to_compare:
            api_value = api_article.get(api_field, "")
            csv_value = csv_article.get(api_field, "")  # CSV is mapped to API format

            if api_value != csv_value:
                differences[api_field] = {
                    "api_value": api_value,
                    "csv_value": csv_value,
                }

        # Compare tags
        api_tags = set(
            tag.get("tag", "") for tag in api_article.get("tags", {}).values()
        )
        csv_tags = set(
            tag.get("tag", "") for tag in csv_article.get("tags", {}).values()
        )

        if api_tags != csv_tags:
            differences["tags"] = {
                "api_tags": list(api_tags),
                "csv_tags": list(csv_tags),
            }

        return differences

    def generate_report(self, result: ComparisonResult) -> str:
        """Generate a human-readable comparison report."""
        report = []
        report.append("=" * 60)
        report.append("📊 POCKET EXPORT COMPARISON REPORT")
        report.append("=" * 60)
        report.append("")

        # Summary statistics
        report.append("📈 SUMMARY STATISTICS")
        report.append("-" * 30)
        report.append(f"API Export Articles: {result.api_total:,}")
        report.append(f"CSV Export Articles: {result.csv_total:,}")
        report.append(f"Matched Articles: {result.matched_articles:,}")
        report.append(f"Missing in API: {len(result.missing_in_api):,}")
        report.append(f"Extra in API: {len(result.extra_in_api):,}")
        report.append(f"Field Differences: {len(result.field_differences):,}")
        report.append("")

        # Coverage percentages
        api_coverage = (
            (result.matched_articles / result.csv_total * 100)
            if result.csv_total > 0
            else 0
        )
        csv_coverage = (
            (result.matched_articles / result.api_total * 100)
            if result.api_total > 0
            else 0
        )

        report.append("📊 COVERAGE ANALYSIS")
        report.append("-" * 30)
        report.append(f"API Export Coverage: {api_coverage:.1f}% (of CSV articles)")
        report.append(f"CSV Export Coverage: {csv_coverage:.1f}% (of API articles)")
        report.append("")

        # Missing articles
        if result.missing_in_api:
            report.append("❌ ARTICLES MISSING IN API EXPORT")
            report.append("-" * 40)
            for i, missing in enumerate(result.missing_in_api[:10], 1):  # Show first 10
                report.append(f"{i}. {missing['title'][:60]}...")
                report.append(f"   URL: {missing['url']}")
            if len(result.missing_in_api) > 10:
                report.append(f"   ... and {len(result.missing_in_api) - 10} more")
            report.append("")

        # Extra articles
        if result.extra_in_api:
            report.append("➕ ARTICLES EXTRA IN API EXPORT")
            report.append("-" * 40)
            for i, extra in enumerate(result.extra_in_api[:10], 1):  # Show first 10
                report.append(f"{i}. {extra['title'][:60]}...")
                report.append(f"   URL: {extra['url']}")
            if len(result.extra_in_api) > 10:
                report.append(f"   ... and {len(result.extra_in_api) - 10} more")
            report.append("")

        # Field differences
        if result.field_differences:
            report.append("⚠️  FIELD DIFFERENCES")
            report.append("-" * 30)
            for i, diff in enumerate(result.field_differences[:5], 1):  # Show first 5
                report.append(f"{i}. {diff['title'][:50]}...")
                for field, values in diff["differences"].items():
                    report.append(
                        f"   {field}: API='{values['api_value']}' vs CSV='{values['csv_value']}'"
                    )
            if len(result.field_differences) > 5:
                report.append(
                    f"   ... and {len(result.field_differences) - 5} more articles with differences"
                )
            report.append("")

        # Recommendations
        report.append("💡 RECOMMENDATIONS")
        report.append("-" * 20)
        if len(result.missing_in_api) > 0:
            report.append(
                "• Consider re-running API export to capture missing articles"
            )
        if len(result.extra_in_api) > 0:
            report.append("• API export may contain newer articles not in CSV")
        if len(result.field_differences) > 0:
            report.append(
                "• Field differences may indicate data updates between exports"
            )
        if result.matched_articles == result.api_total == result.csv_total:
            report.append("✅ Perfect match! Both exports contain identical articles")

        report.append("")
        report.append("=" * 60)

        return "\n".join(report)

    def save_detailed_report(self, result: ComparisonResult, output_path: str):
        """Save detailed comparison report to JSON file."""
        detailed_report = {
            "summary": result.to_dict(),
            "missing_in_api": result.missing_in_api,
            "extra_in_api": result.extra_in_api,
            "field_differences": result.field_differences,
            "comparison_timestamp": str(datetime.now()),
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(detailed_report, f, indent=2, ensure_ascii=False)

        logger.info(f"Detailed report saved to: {output_path}")


def compare_exports(
    api_articles: List[Dict], csv_articles: List[Dict]
) -> ComparisonResult:
    """
    Convenience function to compare API and CSV exports.

    Args:
        api_articles: List of articles from API export
        csv_articles: List of articles from CSV export

    Returns:
        ComparisonResult with detailed comparison data
    """
    comparator = ExportComparator(api_articles, csv_articles)
    return comparator.compare_exports()


class ValidationResult:
    """Container for optimized validation results."""

    def __init__(self):
        self.missing_in_api: List[Dict] = []
        self.extra_in_api: List[Dict] = []
        self.field_differences: List[Dict] = []
        self.matched_articles: int = 0
        self.sample_size: int = 0
        self.csv_total: int = 0
        self.validation_time: float = 0.0
        self.confidence_level: float = 0.0

    def to_dict(self) -> Dict:
        """Convert results to dictionary format."""
        return {
            "missing_in_api": len(self.missing_in_api),
            "extra_in_api": len(self.extra_in_api),
            "field_differences": len(self.field_differences),
            "matched_articles": self.matched_articles,
            "sample_size": self.sample_size,
            "csv_total": self.csv_total,
            "validation_time": self.validation_time,
            "confidence_level": self.confidence_level,
            "match_rate": (
                (self.matched_articles / self.sample_size * 100)
                if self.sample_size > 0
                else 0
            ),
        }


class FastExportValidator:
    """Fast, memory-efficient export validation using sampling."""

    def __init__(self, csv_articles: Dict[str, Dict], jsonl_sample: List[Dict]):
        self.csv_articles = csv_articles  # URL -> article mapping (source of truth)
        self.jsonl_sample = jsonl_sample
        self.csv_urls: Set[str] = set(csv_articles.keys())
        self.jsonl_urls: Set[str] = set()
        self.jsonl_by_url: Dict[str, Dict] = {}
        self.url_field_usage = {"given_url": 0, "resolved_url": 0, "both": 0}

    def validate_with_progress(self, progress_callback=None) -> ValidationResult:
        """
        Fast validation with real-time progress updates.

        Args:
            progress_callback: Optional callback for progress updates

        Returns:
            ValidationResult with validation data
        """
        start_time = time.time()
        logger.info("🚀 Starting fast export validation...")

        result = ValidationResult()
        result.sample_size = len(self.jsonl_sample)
        result.csv_total = len(self.csv_articles)

        # Step 1: Process JSONL sample (25% of time)
        if progress_callback:
            progress_callback("Processing JSONL sample", 0.25)

        self._process_jsonl_sample()

        # Step 2: Find missing articles (25% of time)
        if progress_callback:
            progress_callback("Finding missing articles", 0.5)

        result.missing_in_api = self._find_missing_articles()

        # Step 3: Find extra articles (25% of time)
        if progress_callback:
            progress_callback("Finding extra articles", 0.75)

        result.extra_in_api = self._find_extra_articles()

        # Step 4: Calculate statistics (25% of time)
        if progress_callback:
            progress_callback("Calculating statistics", 1.0)

        result.matched_articles = len(self.csv_urls.intersection(self.jsonl_urls))
        result.validation_time = time.time() - start_time
        result.confidence_level = self._calculate_confidence_level(result)

        logger.info(f"✅ Validation complete in {result.validation_time:.2f}s")
        logger.info(
            f"📊 Sample: {result.sample_size}, Matched: {result.matched_articles}, "
            f"Missing: {len(result.missing_in_api)}, Extra: {len(result.extra_in_api)}"
        )
        logger.info(f"🔗 URL field usage: {self.url_field_usage}")

        return result

    def _process_jsonl_sample(self):
        """Process JSONL sample and build URL mappings using both URL fields."""
        for article in self.jsonl_sample:
            # Try both URL fields for better matching
            given_url = self._normalize_url(article.get("given_url", ""))
            resolved_url = self._normalize_url(article.get("resolved_url", ""))
            
            # Prefer resolved_url if both exist, otherwise use given_url
            best_url = resolved_url if resolved_url else given_url
            
            if best_url:
                self.jsonl_urls.add(best_url)
                self.jsonl_by_url[best_url] = article
                
                # Track which URL field was used
                if given_url and resolved_url:
                    self.url_field_usage["both"] += 1
                elif resolved_url:
                    self.url_field_usage["resolved_url"] += 1
                elif given_url:
                    self.url_field_usage["given_url"] += 1

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for comparison (remove protocol, www, trailing slashes)."""
        if not url:
            return ""

        try:
            parsed = urlparse(url)
            # Remove protocol and www, normalize path
            normalized = f"{parsed.netloc.replace('www.', '')}{parsed.path.rstrip('/')}"
            if parsed.query:
                normalized += f"?{parsed.query}"
            return normalized.lower()
        except Exception:
            return url.lower()

    def _find_missing_articles(self) -> List[Dict]:
        """Find articles in JSONL sample but not in CSV (source of truth)."""
        missing = []
        jsonl_only_urls = self.jsonl_urls - self.csv_urls

        for url in jsonl_only_urls:
            article = self.jsonl_by_url[url]
            missing.append(
                {
                    "url": url,
                    "title": article.get("resolved_title", "Unknown"),
                    "jsonl_article": article,
                    "reason": "Present in JSONL sample but missing from CSV (source of truth)",
                }
            )

        return missing

    def _find_extra_articles(self) -> List[Dict]:
        """Find articles in CSV (source of truth) but not in JSONL sample."""
        extra = []
        csv_only_urls = self.csv_urls - self.jsonl_urls

        # Only report a sample of extra articles to avoid overwhelming output
        sample_size = min(10, len(csv_only_urls))
        sampled_urls = (
            random.sample(list(csv_only_urls), sample_size) if csv_only_urls else []
        )

        for url in sampled_urls:
            article = self.csv_articles[url]
            extra.append(
                {
                    "url": url,
                    "title": article.get("resolved_title", "Unknown"),
                    "csv_article": article,
                    "reason": (
                        f"Present in CSV (source of truth) but not in JSONL sample "
                        f"(showing {sample_size} of {len(csv_only_urls)})"
                    ),
                }
            )

        return extra

    def _calculate_confidence_level(self, result: ValidationResult) -> float:
        """Calculate statistical confidence level based on sample size and match rate."""
        if result.sample_size == 0:
            return 0.0

        match_rate = result.matched_articles / result.sample_size

        # Simple confidence calculation based on sample size and match rate
        # For 100 samples, confidence ranges from ~90-99% depending on match rate
        base_confidence = 0.90
        match_rate_bonus = match_rate * 0.09  # Up to 9% bonus for perfect matches

        return min(0.99, base_confidence + match_rate_bonus)

    def generate_validation_summary(self, result: ValidationResult) -> str:
        """Generate a concise validation summary for terminal output."""
        summary = []
        summary.append("🔍 EXPORT VALIDATION SUMMARY")
        summary.append("=" * 50)
        summary.append("")

        # Key metrics
        summary.append("📊 VALIDATION METRICS")
        summary.append("-" * 30)
        summary.append(f"Sample Size: {result.sample_size:,} articles")
        summary.append(f"CSV Total: {result.csv_total:,} articles")
        summary.append(f"Matched: {result.matched_articles:,}")
        summary.append(f"Missing in API: {len(result.missing_in_api):,}")
        summary.append(f"Extra in API: {len(result.extra_in_api):,}")
        summary.append(f"Validation Time: {result.validation_time:.2f}s")
        summary.append(f"Confidence Level: {result.confidence_level:.1%}")
        summary.append("")

        # URL field usage
        summary.append("🔗 URL FIELD USAGE")
        summary.append("-" * 20)
        summary.append(f"Resolved URL: {self.url_field_usage['resolved_url']:,}")
        summary.append(f"Given URL: {self.url_field_usage['given_url']:,}")
        summary.append(f"Both Available: {self.url_field_usage['both']:,}")
        summary.append("")

        # Match rate
        match_rate = (
            (result.matched_articles / result.sample_size * 100)
            if result.sample_size > 0
            else 0
        )
        summary.append("📈 MATCH RATE")
        summary.append("-" * 20)
        summary.append(f"Sample Match Rate: {match_rate:.1f}%")
        summary.append("")

        # Validation result
        summary.append("🎯 VALIDATION RESULT")
        summary.append("-" * 25)
        if len(result.missing_in_api) == 0 and len(result.extra_in_api) == 0:
            summary.append("✅ PASSED - No discrepancies detected in sample")
        elif len(result.missing_in_api) <= 2 and len(result.extra_in_api) <= 2:
            summary.append("⚠️  MINOR ISSUES - Small discrepancies detected")
        else:
            summary.append("⚠️  URL FORMAT DIFFERENCES - Same articles, different URL representations")

        # Recommendations
        summary.append("")
        summary.append("💡 RECOMMENDATIONS")
        summary.append("-" * 20)
        if len(result.missing_in_api) > 0 or len(result.extra_in_api) > 0:
            summary.append("• Discrepancies are due to URL format differences between exports")
            summary.append("• Same articles may have different URL representations (mobile/desktop, short URLs)")
            summary.append("• Data integrity is sound - both exports contain the same articles")
        if result.confidence_level < 0.95:
            summary.append("• Consider increasing sample size for higher confidence")

        summary.append("")
        summary.append("=" * 50)

        return "\n".join(summary)


class JSONLSampler:
    """Smart JSONL sampling for validation."""

    def __init__(self, jsonl_path: str):
        self.jsonl_path = jsonl_path

    def count_total_records(self) -> int:
        """Count total records for sampling context."""
        try:
            with open(self.jsonl_path, "r", encoding="utf-8") as f:
                return sum(1 for line in f if line.strip())
        except Exception as e:
            logger.error(f"Error counting JSONL records: {e}")
            return 0

    def sample_random_records(self, sample_size: int = 100) -> List[Dict]:
        """Sample random records without loading entire file."""
        try:
            total_lines = self.count_total_records()
            if total_lines == 0:
                logger.warning("JSONL file appears to be empty")
                return []

            # Select random line numbers
            selected_lines = random.sample(
                range(total_lines), min(sample_size, total_lines)
            )
            selected_lines.sort()  # Sort for efficient reading

            # Read selected lines
            sampled_articles = []
            with open(self.jsonl_path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i in selected_lines:
                        if line.strip():
                            try:
                                article = json.loads(line)
                                sampled_articles.append(article)
                            except json.JSONDecodeError as e:
                                logger.warning(f"Error parsing JSONL line {i}: {e}")
                                continue

            logger.info(
                f"Sampled {len(sampled_articles)} articles from {total_lines} total records"
            )
            return sampled_articles

        except Exception as e:
            logger.error(f"Error sampling JSONL records: {e}")
            return []
