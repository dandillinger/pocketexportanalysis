#!/usr/bin/env python3
"""
Performance tests for Pocket Export Tool.
Benchmarks key functions to ensure they meet performance requirements.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest
import json

from data_parser import parse_pocket_article
from storage import save_raw_json, save_articles_jsonl, get_file_summary


class TestPerformanceBenchmarks(unittest.TestCase):
    """Performance benchmarks for key functions."""

    def setUp(self):
        """Set up test data for benchmarking."""
        # Create sample article data
        self.sample_article = {
            "item_id": "123456789",
            "resolved_title": "Sample Article Title",
            "resolved_url": "https://example.com/article",
            "excerpt": "This is a sample excerpt of the article content.",
            "time_added": "1700000000",
            "time_updated": "1700000001",
            "time_read": "1700000002",
            "time_favorited": "1700000003",
            "word_count": "500",
            "authors": {"1": {"name": "John Doe", "url": "https://example.com/author"}},
            "images": {
                "1": {"src": "https://example.com/image.jpg", "alt": "Sample image"}
            },
            "tags": {"tech": {"tag": "tech"}, "python": {"tag": "python"}},
            "is_article": "1",
            "is_index": "0",
            "has_video": "0",
            "has_image": "1",
            "lang": "en",
            "domain_metadata": {
                "name": "Example Domain",
                "logo": "https://example.com/logo.png",
            },
            "listen_duration_estimate": "300",
        }

        # Create multiple articles for batch testing
        self.multiple_articles = [self.sample_article.copy() for _ in range(100)]
        for i, article in enumerate(self.multiple_articles):
            article["item_id"] = str(i + 1)
            article["resolved_title"] = f"Article {i + 1}"

    def test_parse_pocket_article_performance(self, benchmark):
        """Benchmark article parsing performance."""

        def parse_single_article():
            return parse_pocket_article(self.sample_article)

        result = benchmark(parse_single_article)
        self.assertIsNotNone(result)
        self.assertEqual(result["item_id"], "123456789")

    def test_parse_multiple_articles_performance(self, benchmark):
        """Benchmark parsing multiple articles."""

        def parse_multiple_articles():
            return [parse_pocket_article(article) for article in self.multiple_articles]

        result = benchmark(parse_multiple_articles)
        self.assertEqual(len(result), 100)
        self.assertEqual(result[0]["item_id"], "1")

    def test_save_raw_json_performance(self, benchmark):
        """Benchmark raw JSON saving performance."""
        import tempfile
        import os

        def save_raw_json_benchmark():
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                temp_path = f.name

            try:
                result = save_raw_json(self.multiple_articles, temp_path)
                return result
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        result = benchmark(save_raw_json_benchmark)
        self.assertTrue(result)

    def test_save_articles_jsonl_performance(self, benchmark):
        """Benchmark JSONL saving performance."""
        import tempfile
        import os

        def save_jsonl_benchmark():
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".jsonl", delete=False
            ) as f:
                temp_path = f.name

            try:
                parsed_articles = [
                    parse_pocket_article(article) for article in self.multiple_articles
                ]
                result = save_articles_jsonl(parsed_articles, temp_path)
                return result
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        result = benchmark(save_jsonl_benchmark)
        self.assertTrue(result)

    def test_get_file_summary_performance(self, benchmark):
        """Benchmark file summary generation performance."""
        import tempfile
        import os

        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name
            json.dump(self.multiple_articles, f)

        try:

            def get_summary_benchmark():
                return get_file_summary(temp_path)

            result = benchmark(get_summary_benchmark)
            self.assertIsNotNone(result)
            self.assertEqual(result["article_count"], 100)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_memory_usage_benchmark(self, benchmark):
        """Benchmark memory usage for large datasets."""
        import gc

        def memory_usage_test():
            # Create a large dataset
            large_dataset = []
            for i in range(1000):
                article = self.sample_article.copy()
                article["item_id"] = str(i)
                article["excerpt"] = "A" * 1000  # Large excerpt
                large_dataset.append(article)

            # Parse all articles
            parsed_articles = [
                parse_pocket_article(article) for article in large_dataset
            ]

            # Force garbage collection
            gc.collect()

            return len(parsed_articles)

        result = benchmark(memory_usage_test)
        self.assertEqual(result, 1000)

    def test_api_response_parsing_performance(self, benchmark):
        """Benchmark API response parsing performance."""
        # Simulate API response format
        api_response = {
            "list": {str(i): self.sample_article.copy() for i in range(100)},
            "complete": 1,
        }

        def parse_api_response():
            articles = []
            for item_id, article_data in api_response["list"].items():
                article_data["item_id"] = item_id
                parsed = parse_pocket_article(article_data)
                articles.append(parsed)
            return articles

        result = benchmark(parse_api_response)
        self.assertEqual(len(result), 100)


if __name__ == "__main__":
    unittest.main()
