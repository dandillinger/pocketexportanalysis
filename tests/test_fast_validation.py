#!/usr/bin/env python3
"""
Unit tests for Fast Export Validation
"""

import tempfile
import os
from export_comparator import FastExportValidator, ValidationResult, JSONLSampler


class TestFastExportValidator:
    """Test cases for FastExportValidator class."""

    def test_perfect_match_validation(self):
        """Test validation when CSV and JSONL sample are identical."""
        # Create test data
        csv_articles = {
            "example.com/article1": {
                "resolved_url": "https://example.com/article1",
                "resolved_title": "Test Article 1",
                "status": "0",
                "time_added": "2022-01-01T00:00:00Z",
            },
            "example.com/article2": {
                "resolved_url": "https://example.com/article2",
                "resolved_title": "Test Article 2",
                "status": "1",
                "time_added": "2022-01-02T00:00:00Z",
            },
        }

        jsonl_sample = [
            {
                "resolved_url": "https://example.com/article1",
                "resolved_title": "Test Article 1",
                "status": "0",
                "time_added": "2022-01-01T00:00:00Z",
            },
            {
                "resolved_url": "https://example.com/article2",
                "resolved_title": "Test Article 2",
                "status": "1",
                "time_added": "2022-01-02T00:00:00Z",
            },
        ]

        validator = FastExportValidator(csv_articles, jsonl_sample)
        result = validator.validate_with_progress()

        assert result.sample_size == 2
        assert result.csv_total == 2
        assert result.matched_articles == 2
        assert len(result.missing_in_api) == 0
        assert len(result.extra_in_api) == 0
        assert result.confidence_level > 0.95

    def test_missing_articles_validation(self):
        """Test detection of articles missing in JSONL sample."""
        csv_articles = {
            "example.com/article1": {
                "resolved_url": "https://example.com/article1",
                "resolved_title": "Test Article 1",
                "status": "0",
                "time_added": "2022-01-01T00:00:00Z",
            },
            "example.com/article2": {
                "resolved_url": "https://example.com/article2",
                "resolved_title": "Test Article 2",
                "status": "1",
                "time_added": "2022-01-02T00:00:00Z",
            },
        }

        # JSONL sample missing one article
        jsonl_sample = [
            {
                "resolved_url": "https://example.com/article1",
                "resolved_title": "Test Article 1",
                "status": "0",
                "time_added": "2022-01-01T00:00:00Z",
            }
        ]

        validator = FastExportValidator(csv_articles, jsonl_sample)
        result = validator.validate_with_progress()

        assert result.sample_size == 1
        assert result.csv_total == 2
        assert result.matched_articles == 1
        assert len(result.missing_in_api) == 0  # Article 1 is in both
        assert len(result.extra_in_api) == 1  # Article 2 is only in CSV

    def test_url_normalization(self):
        """Test URL normalization for comparison."""
        csv_articles = {
            "example.com/article1": {
                "resolved_url": "https://www.example.com/article1/",
                "resolved_title": "Test Article 1",
                "status": "0",
                "time_added": "2022-01-01T00:00:00Z",
            }
        }

        jsonl_sample = [
            {
                "resolved_url": "http://example.com/article1",
                "resolved_title": "Test Article 1",
                "status": "0",
                "time_added": "2022-01-01T00:00:00Z",
            }
        ]

        validator = FastExportValidator(csv_articles, jsonl_sample)
        result = validator.validate_with_progress()

        # Should match despite different protocols and www
        assert result.matched_articles == 1
        assert len(result.missing_in_api) == 0
        assert len(result.extra_in_api) == 0

    def test_validation_summary_generation(self):
        """Test validation summary generation."""
        csv_articles = {
            "example.com/article1": {
                "resolved_url": "https://example.com/article1",
                "resolved_title": "Test Article 1",
                "status": "0",
                "time_added": "2022-01-01T00:00:00Z",
            }
        }

        jsonl_sample = [
            {
                "resolved_url": "https://example.com/article1",
                "resolved_title": "Test Article 1",
                "status": "0",
                "time_added": "2022-01-01T00:00:00Z",
            }
        ]

        validator = FastExportValidator(csv_articles, jsonl_sample)
        result = validator.validate_with_progress()
        summary = validator.generate_validation_summary(result)

        assert "EXPORT VALIDATION SUMMARY" in summary
        assert "VALIDATION METRICS" in summary
        assert "Sample Size: 1" in summary
        assert "CSV Total: 1" in summary
        assert "Matched: 1" in summary
        assert "PASSED" in summary


class TestJSONLSampler:
    """Test cases for JSONLSampler class."""

    def test_count_total_records(self):
        """Test counting total records in JSONL file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"test": "data1"}\n')
            f.write('{"test": "data2"}\n')
            f.write('{"test": "data3"}\n')
            temp_file = f.name

        try:
            sampler = JSONLSampler(temp_file)
            count = sampler.count_total_records()
            assert count == 3
        finally:
            os.unlink(temp_file)

    def test_sample_random_records(self):
        """Test sampling random records from JSONL file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            for i in range(10):
                f.write(f'{{"id": {i}, "title": "Article {i}"}}\n')
            temp_file = f.name

        try:
            sampler = JSONLSampler(temp_file)
            sample = sampler.sample_random_records(5)

            assert len(sample) == 5
            assert all("id" in article for article in sample)
            assert all("title" in article for article in sample)
        finally:
            os.unlink(temp_file)

    def test_sample_size_larger_than_total(self):
        """Test sampling when sample size is larger than total records."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"test": "data1"}\n')
            f.write('{"test": "data2"}\n')
            temp_file = f.name

        try:
            sampler = JSONLSampler(temp_file)
            sample = sampler.sample_random_records(10)  # Larger than total

            assert len(sample) == 2  # Should return all available records
        finally:
            os.unlink(temp_file)


class TestValidationResult:
    """Test cases for ValidationResult class."""

    def test_to_dict_conversion(self):
        """Test conversion to dictionary format."""
        result = ValidationResult()
        result.missing_in_api = [{"url": "test1"}, {"url": "test2"}]
        result.extra_in_api = [{"url": "test3"}]
        result.field_differences = [{"url": "test4"}]
        result.matched_articles = 5
        result.sample_size = 10
        result.csv_total = 8
        result.validation_time = 1.5
        result.confidence_level = 0.95

        data = result.to_dict()

        assert data["missing_in_api"] == 2
        assert data["extra_in_api"] == 1
        assert data["field_differences"] == 1
        assert data["matched_articles"] == 5
        assert data["sample_size"] == 10
        assert data["csv_total"] == 8
        assert data["validation_time"] == 1.5
        assert data["confidence_level"] == 0.95
        assert data["match_rate"] == 50.0  # 5/10 * 100
