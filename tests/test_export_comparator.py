#!/usr/bin/env python3
"""
Unit tests for Export Comparator Module
"""


import tempfile
import os
from export_comparator import ExportComparator, ComparisonResult, compare_exports


class TestExportComparator:
    """Test cases for ExportComparator class."""

    def test_perfect_match(self):
        """Test comparison when exports are identical."""
        api_articles = [
            {
                "item_id": "123",
                "resolved_url": "https://example.com/article1",
                "resolved_title": "Test Article 1",
                "excerpt": "Test excerpt",
                "tags": {"0": {"tag": "tech", "item_id": "tag1"}},
                "status": "0",
                "time_added": "2022-01-01T00:00:00Z",
            }
        ]

        csv_articles = [
            {
                "item_id": "123",
                "resolved_url": "https://example.com/article1",
                "resolved_title": "Test Article 1",
                "excerpt": "Test excerpt",
                "tags": {"0": {"tag": "tech", "item_id": "tag1"}},
                "status": "0",
                "time_added": "2022-01-01T00:00:00Z",
            }
        ]

        comparator = ExportComparator(api_articles, csv_articles)
        result = comparator.compare_exports()

        assert result.api_total == 1
        assert result.csv_total == 1
        assert result.matched_articles == 1
        assert len(result.missing_in_api) == 0
        assert len(result.extra_in_api) == 0
        assert len(result.field_differences) == 0

    def test_missing_in_api(self):
        """Test detection of articles missing in API export."""
        api_articles = [
            {
                "item_id": "123",
                "resolved_url": "https://example.com/article1",
                "resolved_title": "Test Article 1",
                "excerpt": "Test excerpt",
                "tags": {},
                "status": "0",
                "time_added": "2022-01-01T00:00:00Z",
            }
        ]

        csv_articles = [
            {
                "item_id": "123",
                "resolved_url": "https://example.com/article1",
                "resolved_title": "Test Article 1",
                "excerpt": "Test excerpt",
                "tags": {},
                "status": "0",
                "time_added": "2022-01-01T00:00:00Z",
            },
            {
                "item_id": "456",
                "resolved_url": "https://example.com/article2",
                "resolved_title": "Test Article 2",
                "excerpt": "Test excerpt 2",
                "tags": {},
                "status": "0",
                "time_added": "2022-01-01T00:00:00Z",
            },
        ]

        comparator = ExportComparator(api_articles, csv_articles)
        result = comparator.compare_exports()

        assert result.api_total == 1
        assert result.csv_total == 2
        assert result.matched_articles == 1
        assert len(result.missing_in_api) == 1
        assert len(result.extra_in_api) == 0
        assert result.missing_in_api[0]["url"] == "example.com/article2"

    def test_extra_in_api(self):
        """Test detection of articles extra in API export."""
        api_articles = [
            {
                "item_id": "123",
                "resolved_url": "https://example.com/article1",
                "resolved_title": "Test Article 1",
                "excerpt": "Test excerpt",
                "tags": {},
                "status": "0",
                "time_added": "2022-01-01T00:00:00Z",
            },
            {
                "item_id": "456",
                "resolved_url": "https://example.com/article2",
                "resolved_title": "Test Article 2",
                "excerpt": "Test excerpt 2",
                "tags": {},
                "status": "0",
                "time_added": "2022-01-01T00:00:00Z",
            },
        ]

        csv_articles = [
            {
                "item_id": "123",
                "resolved_url": "https://example.com/article1",
                "resolved_title": "Test Article 1",
                "excerpt": "Test excerpt",
                "tags": {},
                "status": "0",
                "time_added": "2022-01-01T00:00:00Z",
            }
        ]

        comparator = ExportComparator(api_articles, csv_articles)
        result = comparator.compare_exports()

        assert result.api_total == 2
        assert result.csv_total == 1
        assert result.matched_articles == 1
        assert len(result.missing_in_api) == 0
        assert len(result.extra_in_api) == 1
        assert result.extra_in_api[0]["url"] == "example.com/article2"

    def test_field_differences(self):
        """Test detection of field differences between matched articles."""
        api_articles = [
            {
                "item_id": "123",
                "resolved_url": "https://example.com/article1",
                "resolved_title": "Test Article 1",
                "excerpt": "Test excerpt",
                "tags": {"0": {"tag": "tech", "item_id": "tag1"}},
                "status": "0",
                "time_added": "2022-01-01T00:00:00Z",
            }
        ]

        csv_articles = [
            {
                "item_id": "123",
                "resolved_url": "https://example.com/article1",
                "resolved_title": "Test Article 1 Modified",
                "excerpt": "Test excerpt modified",
                "tags": {"0": {"tag": "news", "item_id": "tag1"}},
                "status": "1",
                "time_added": "2022-01-01T00:00:00Z",
            }
        ]

        comparator = ExportComparator(api_articles, csv_articles)
        result = comparator.compare_exports()

        assert result.matched_articles == 1
        assert len(result.field_differences) == 1
        assert "resolved_title" in result.field_differences[0]["differences"]
        assert "excerpt" in result.field_differences[0]["differences"]
        assert "tags" in result.field_differences[0]["differences"]
        assert "status" in result.field_differences[0]["differences"]

    def test_url_normalization(self):
        """Test URL normalization for comparison."""
        api_articles = [
            {
                "item_id": "123",
                "resolved_url": "https://www.example.com/article1",
                "resolved_title": "Test Article 1",
                "excerpt": "Test excerpt",
                "tags": {},
                "status": "0",
                "time_added": "2022-01-01T00:00:00Z",
            }
        ]

        csv_articles = [
            {
                "item_id": "123",
                "resolved_url": "http://example.com/article1/",
                "resolved_title": "Test Article 1",
                "excerpt": "Test excerpt",
                "tags": {},
                "status": "0",
                "time_added": "2022-01-01T00:00:00Z",
            }
        ]

        comparator = ExportComparator(api_articles, csv_articles)
        result = comparator.compare_exports()

        # Should match despite different protocols and www
        assert result.matched_articles == 1
        assert len(result.missing_in_api) == 0
        assert len(result.extra_in_api) == 0

    def test_convenience_function(self):
        """Test the convenience function compare_exports."""
        api_articles = [
            {
                "item_id": "123",
                "resolved_url": "https://example.com/article1",
                "resolved_title": "Test Article 1",
                "excerpt": "Test excerpt",
                "tags": {},
                "status": "0",
                "time_added": "2022-01-01T00:00:00Z",
            }
        ]

        csv_articles = [
            {
                "item_id": "123",
                "resolved_url": "https://example.com/article1",
                "resolved_title": "Test Article 1",
                "excerpt": "Test excerpt",
                "tags": {},
                "status": "0",
                "time_added": "2022-01-01T00:00:00Z",
            }
        ]

        result = compare_exports(api_articles, csv_articles)

        assert result.api_total == 1
        assert result.csv_total == 1
        assert result.matched_articles == 1

    def test_report_generation(self):
        """Test report generation functionality."""
        api_articles = [
            {
                "item_id": "123",
                "resolved_url": "https://example.com/article1",
                "resolved_title": "Test Article 1",
                "excerpt": "Test excerpt",
                "tags": {},
                "status": "0",
                "time_added": "2022-01-01T00:00:00Z",
            }
        ]

        csv_articles = [
            {
                "item_id": "123",
                "resolved_url": "https://example.com/article1",
                "resolved_title": "Test Article 1",
                "excerpt": "Test excerpt",
                "tags": {},
                "status": "0",
                "time_added": "2022-01-01T00:00:00Z",
            }
        ]

        comparator = ExportComparator(api_articles, csv_articles)
        result = comparator.compare_exports()
        report = comparator.generate_report(result)

        assert "POCKET EXPORT COMPARISON REPORT" in report
        assert "SUMMARY STATISTICS" in report
        assert "API Export Articles: 1" in report
        assert "CSV Export Articles: 1" in report
        assert "Matched Articles: 1" in report

    def test_detailed_report_saving(self):
        """Test saving detailed report to JSON file."""
        api_articles = [
            {
                "item_id": "123",
                "resolved_url": "https://example.com/article1",
                "resolved_title": "Test Article 1",
                "excerpt": "Test excerpt",
                "tags": {},
                "status": "0",
                "time_added": "2022-01-01T00:00:00Z",
            }
        ]

        csv_articles = [
            {
                "item_id": "123",
                "resolved_url": "https://example.com/article1",
                "resolved_title": "Test Article 1",
                "excerpt": "Test excerpt",
                "tags": {},
                "status": "0",
                "time_added": "2022-01-01T00:00:00Z",
            }
        ]

        comparator = ExportComparator(api_articles, csv_articles)
        result = comparator.compare_exports()

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            comparator.save_detailed_report(result, temp_file)

            # Verify file was created and contains expected data
            assert os.path.exists(temp_file)
            with open(temp_file, "r") as f:
                import json

                data = json.load(f)
                assert "summary" in data
                assert "missing_in_api" in data
                assert "extra_in_api" in data
                assert "field_differences" in data
                assert data["summary"]["api_total"] == 1
                assert data["summary"]["csv_total"] == 1
        finally:
            os.unlink(temp_file)


class TestComparisonResult:
    """Test cases for ComparisonResult class."""

    def test_to_dict_conversion(self):
        """Test conversion to dictionary format."""
        result = ComparisonResult()
        result.missing_in_api = [{"url": "test1"}, {"url": "test2"}]
        result.extra_in_api = [{"url": "test3"}]
        result.field_differences = [{"url": "test4"}]
        result.matched_articles = 5
        result.api_total = 10
        result.csv_total = 8

        data = result.to_dict()

        assert data["missing_in_api"] == 2
        assert data["extra_in_api"] == 1
        assert data["field_differences"] == 1
        assert data["matched_articles"] == 5
        assert data["api_total"] == 10
        assert data["csv_total"] == 8
        assert data["api_coverage"] == 62.5  # 5/8 * 100
        assert data["csv_coverage"] == 50.0  # 5/10 * 100

    def test_coverage_calculation_edge_cases(self):
        """Test coverage calculation with edge cases."""
        result = ComparisonResult()
        result.matched_articles = 0
        result.api_total = 0
        result.csv_total = 0

        data = result.to_dict()

        assert data["api_coverage"] == 0
        assert data["csv_coverage"] == 0
