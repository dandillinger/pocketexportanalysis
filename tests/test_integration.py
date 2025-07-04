#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
Integration tests for Pocket Export Tool.
Tests end-to-end workflows, API integration, and system behavior.
"""
import unittest
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from io import StringIO

from pocket_export import main
from data_fetcher import PocketDataFetcher
from data_parser import parse_pocket_article
from storage import save_raw_json, save_articles_jsonl


class TestIntegrationWorkflows(unittest.TestCase):
    """Integration tests for complete workflows."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("pocket_export.setup_authentication")
    @patch("pocket_export.create_data_fetcher")
    @patch("pocket_export.save_raw_json")
    @patch("pocket_export.save_articles_jsonl")
    @patch("pocket_export.get_file_summary")
    def test_full_export_integration(
        self,
        mock_get_summary,
        mock_save_parsed,
        mock_save_raw,
        mock_create_fetcher,
        mock_auth,
    ):
        """Test complete full export workflow integration."""
        # Mock authentication
        mock_auth_instance = MagicMock()
        mock_auth_instance.load_credentials.return_value = True
        mock_auth_instance.validate_credentials.return_value = True
        mock_auth.return_value = mock_auth_instance

        # Mock data fetcher
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_all_articles_with_batching.return_value = [
            {"item_id": "1", "resolved_title": "Test Article 1"},
            {"item_id": "2", "resolved_title": "Test Article 2"},
            {"item_id": "3", "resolved_title": "Test Article 3"},
        ]
        mock_create_fetcher.return_value = mock_fetcher

        # Mock storage functions
        mock_save_raw.return_value = True
        mock_save_parsed.return_value = True

        # Mock file summary
        mock_get_summary.return_value = {
            "file": "test.json",
            "size_bytes": 1024,
            "size_kb": 1.0,
            "article_count": 3,
        }

        # Test CLI arguments
        test_args = ["pocket_export.py", "--full-export", "--output-dir", self.test_dir]

        with patch("sys.argv", test_args):
            with patch("sys.stdout", StringIO()):
                main()

        # Verify the workflow was called correctly
        mock_auth.assert_called_once()
        mock_create_fetcher.assert_called_once_with(mock_auth_instance)
        mock_fetcher.fetch_all_articles_with_batching.assert_called_once_with(
            detail_type="complete", state="all"
        )
        mock_save_raw.assert_called_once()
        mock_save_parsed.assert_called_once()

    @patch("pocket_export.setup_authentication")
    @patch("pocket_export.create_data_fetcher")
    def test_batch_processing_integration(self, mock_create_fetcher, mock_auth):
        """Test batch processing integration with rate limiting."""
        # Mock authentication
        mock_auth_instance = MagicMock()
        mock_auth_instance.load_credentials.return_value = True
        mock_auth_instance.validate_credentials.return_value = True
        mock_auth.return_value = mock_auth_instance

        # Create real data fetcher with mocked session
        mock_session = MagicMock()
        fetcher = PocketDataFetcher(
            session=mock_session, consumer_key="test-key", access_token="test-token"
        )
        mock_create_fetcher.return_value = fetcher

        # Mock API responses for multiple batches
        mock_response_1 = MagicMock()
        mock_response_1.status_code = 200
        mock_response_1.json.return_value = {
            "list": {
                str(i): {"item_id": str(i), "title": f"Article {i}"}
                for i in range(1, 273)
            },
            "complete": 0,
        }

        mock_response_2 = MagicMock()
        mock_response_2.status_code = 200
        mock_response_2.json.return_value = {
            "list": {
                str(i): {"item_id": str(i), "title": f"Article {i}"}
                for i in range(273, 545)
            },
            "complete": 1,
        }

        mock_session.post.side_effect = [mock_response_1, mock_response_2]

        # Test batch processing
        articles = list(fetcher.fetch_all_articles_with_batching())

        # Verify batch processing
        self.assertEqual(len(articles), 544)  # 272 + 272
        self.assertEqual(mock_session.post.call_count, 2)  # Two API calls

        # Verify batch size compliance
        call_args = mock_session.post.call_args_list
        self.assertEqual(call_args[0][1]["json"]["count"], 272)
        self.assertEqual(call_args[1][1]["json"]["count"], 272)

    def test_rate_limiting_integration(self):
        """Test rate limiting compliance during batch processing."""
        mock_session = MagicMock()
        fetcher = PocketDataFetcher(
            session=mock_session, consumer_key="test-key", access_token="test-token"
        )

        # Mock rate limit response, then success
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "list": {"1": {"item_id": "1", "title": "Test Article"}},
            "complete": 1,
        }

        mock_session.post.side_effect = [mock_response_429, mock_response_success]

        # Test rate limiting handling
        with patch("time.sleep") as mock_sleep:
            result = fetcher._fetch_batch(
                detail_type="complete", state="all", count=272, offset=0
            )

            # Verify rate limiting was handled
            self.assertIsNotNone(result)
            self.assertEqual(mock_session.post.call_count, 2)
            mock_sleep.assert_called_with(5)  # Rate limit delay

    def test_memory_usage_integration(self):
        """Test memory usage for large exports."""
        mock_session = MagicMock()
        fetcher = PocketDataFetcher(
            session=mock_session, consumer_key="test-key", access_token="test-token"
        )

        # Mock large dataset response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "list": {
                str(i): {
                    "item_id": str(i),
                    "title": f"Article {i}",
                    "excerpt": "A" * 1000,  # Large excerpt to test memory
                    "authors": {"1": {"name": "Author " + str(i)}},
                    "images": {"1": {"src": "image.jpg"}},
                    "tags": {"tag1": {"tag": "tag1"}},
                }
                for i in range(1, 273)
            },
            "complete": 1,
        }
        mock_session.post.return_value = mock_response

        # Test memory usage with large dataset
        articles = list(fetcher.fetch_all_articles_with_batching())

        # Verify all articles were processed
        self.assertEqual(len(articles), 272)

        # Verify memory-efficient processing (no memory leaks)
        # This is a basic check - in a real scenario, you'd use memory profiling
        import gc

        gc.collect()

        # Test that we can still process more data
        articles2 = list(fetcher.fetch_all_articles_with_batching())
        self.assertEqual(len(articles2), 272)

    def test_error_recovery_integration(self):
        """Test error recovery during batch processing."""
        mock_session = MagicMock()
        fetcher = PocketDataFetcher(
            session=mock_session, consumer_key="test-key", access_token="test-token"
        )

        # Mock timeout error, then success (timeout errors are retried)
        from requests.exceptions import Timeout

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "list": {"1": {"item_id": "1", "title": "Test Article"}},
            "complete": 1,
        }

        mock_session.post.side_effect = [
            Timeout("Request timeout"),
            mock_response_success,
        ]

        # Test error recovery
        with patch("time.sleep") as mock_sleep:
            result = fetcher._fetch_batch(
                detail_type="complete", state="all", count=272, offset=0
            )

            # Verify error was handled and retry occurred
            self.assertIsNotNone(result)
            self.assertEqual(mock_session.post.call_count, 2)
            mock_sleep.assert_called_with(2)  # Error delay

    def test_file_system_integration(self):
        """Test file system operations during export."""
        # Test raw JSON saving
        test_data = [{"item_id": "1", "title": "Test Article"}]
        raw_path = os.path.join(self.test_dir, "test_raw.json")

        result = save_raw_json(test_data, raw_path)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(raw_path))

        # Verify file content
        with open(raw_path, "r") as f:
            saved_data = json.load(f)
        self.assertEqual(len(saved_data), 1)
        self.assertEqual(saved_data[0]["item_id"], "1")

        # Test parsed JSONL saving
        parsed_articles = [parse_pocket_article(article) for article in test_data]
        parsed_path = os.path.join(self.test_dir, "test_parsed.jsonl")

        result = save_articles_jsonl(parsed_articles, parsed_path)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(parsed_path))

        # Verify file content
        with open(parsed_path, "r") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        parsed_article = json.loads(lines[0])
        self.assertEqual(parsed_article["item_id"], "1")

    @patch("pocket_export.setup_authentication")
    @patch("pocket_export.create_data_fetcher")
    def test_cli_integration(self, mock_create_fetcher, mock_auth):
        """Test CLI integration with different arguments."""
        # Mock authentication
        mock_auth_instance = MagicMock()
        mock_auth_instance.load_credentials.return_value = True
        mock_auth_instance.validate_credentials.return_value = True
        mock_auth.return_value = mock_auth_instance

        # Mock data fetcher
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_all_articles_with_batching.return_value = [
            {"item_id": "1", "resolved_title": "Test Article 1"}
        ]
        mock_create_fetcher.return_value = mock_fetcher

        # Test different CLI argument combinations
        test_cases = [
            ["--full-export"],
            ["--full-export", "--state", "unread"],
            ["--full-export", "--state", "archive"],
            ["--full-export", "--output-dir", self.test_dir],
            ["--full-export", "--verbose"],
        ]

        for args in test_cases:
            with self.subTest(args=args):
                test_args = ["pocket_export.py"] + args

                with patch("sys.argv", test_args):
                    with patch("sys.stdout", StringIO()):
                        # Should not raise any exceptions
                        try:
                            main()
                        except SystemExit:
                            pass  # Expected for help/version commands

    def test_validation_integration(self):
        """Test fast validation workflow integration (Story 9)."""
        # Create test CSV file
        csv_content = """title,url,time_added,tags,status
Test Article 1,https://example.com/article1,1506217991,,unread
Test Article 2,https://example.com/article2,1544412255,work,unread
Test Article 3,https://example.com/article3,1499967219,,archive"""

        csv_file = os.path.join(self.test_dir, "test_export.csv")
        with open(csv_file, "w") as f:
            f.write(csv_content)

        # Create test JSONL file
        jsonl_content = [
            {
                "resolved_url": "https://example.com/article1",
                "resolved_title": "Test Article 1",
                "time_added": "2017-09-23T01:33:11Z",
                "tags": {},
                "status": "unread",
            },
            {
                "resolved_url": "https://example.com/article2",
                "resolved_title": "Test Article 2",
                "time_added": "2018-12-10T19:44:15Z",
                "tags": {"0": {"tag": "work", "item_id": "csv_tag_0"}},
                "status": "unread",
            },
            {
                "resolved_url": "https://example.com/article3",
                "resolved_title": "Test Article 3",
                "time_added": "2017-07-13T19:53:39Z",
                "tags": {},
                "status": "archive",
            },
            {
                "resolved_url": "https://example.com/article4",
                "resolved_title": "Test Article 4",
                "time_added": "2017-07-13T19:53:39Z",
                "tags": {},
                "status": "unread",
            },  # Extra article
        ]

        jsonl_file = os.path.join(self.test_dir, "articles.jsonl")
        with open(jsonl_file, "w") as f:
            for article in jsonl_content:
                f.write(json.dumps(article) + "\n")

        # Create parsed_data directory and copy JSONL
        parsed_dir = os.path.join(self.test_dir, "parsed_data")
        os.makedirs(parsed_dir, exist_ok=True)
        shutil.copy(jsonl_file, os.path.join(parsed_dir, "articles.jsonl"))

        # Test validation CLI
        test_args = [
            "pocket_export.py",
            "--validate",
            "--sample-size",
            "3",
            "--csv-dir",
            self.test_dir,
        ]

        with patch("sys.argv", test_args):
            with patch("sys.stdout", StringIO()) as mock_stdout:
                with patch("pocket_export.setup_authentication") as mock_auth:
                    # Mock authentication
                    mock_auth_instance = MagicMock()
                    mock_auth_instance.load_credentials.return_value = True
                    mock_auth_instance.validate_credentials.return_value = True
                    mock_auth.return_value = mock_auth_instance

                    # Change to test directory
                    original_cwd = os.getcwd()
                    os.chdir(self.test_dir)

                    try:
                        main()
                    finally:
                        os.chdir(original_cwd)

        # Verify validation output
        output = mock_stdout.getvalue()
        self.assertIn("EXPORT VALIDATION SUMMARY", output)
        self.assertIn("VALIDATION METRICS", output)
        self.assertIn("Sample Size: 3", output)
        self.assertIn("CSV Total: 3", output)

    def test_validation_performance_integration(self):
        """Test validation performance with larger datasets."""
        # Create larger test dataset
        csv_articles = []
        jsonl_articles = []

        for i in range(100):
            url = f"https://example.com/article{i}"
            title = f"Test Article {i}"

            # Add to CSV
            csv_articles.append(f"{title},{url},{1506217991 + i},,unread")

            # Add to JSONL (with some differences)
            if i < 95:  # 95% match rate
                jsonl_articles.append(
                    {
                        "resolved_url": url,
                        "resolved_title": title,
                        "time_added": "2017-09-23T01:33:11Z",
                        "tags": {},
                        "status": "unread",
                    }
                )

        # Create test files
        csv_file = os.path.join(self.test_dir, "large_export.csv")
        with open(csv_file, "w") as f:
            f.write("title,url,time_added,tags,status\n")
            f.write("\n".join(csv_articles))

        jsonl_file = os.path.join(self.test_dir, "large_articles.jsonl")
        with open(jsonl_file, "w") as f:
            for article in jsonl_articles:
                f.write(json.dumps(article) + "\n")

        # Create parsed_data directory
        parsed_dir = os.path.join(self.test_dir, "parsed_data")
        os.makedirs(parsed_dir, exist_ok=True)
        shutil.copy(jsonl_file, os.path.join(parsed_dir, "articles.jsonl"))

        # Test validation performance
        import time

        start_time = time.time()

        from export_comparator import JSONLSampler, FastExportValidator
        from csv_parser import PocketCSVParser

        # Load CSV as source of truth
        parser = PocketCSVParser(csv_file)
        csv_data = parser.load_csv_as_source_of_truth()

        # Sample JSONL
        sampler = JSONLSampler(jsonl_file)
        jsonl_sample = sampler.sample_random_records(20)

        # Validate
        validator = FastExportValidator(csv_data, jsonl_sample)
        result = validator.validate_with_progress()

        validation_time = time.time() - start_time

        # Verify performance
        self.assertLess(validation_time, 5.0)  # Should complete in under 5 seconds
        self.assertEqual(result.sample_size, 20)
        self.assertEqual(result.csv_total, 100)
        self.assertGreater(result.confidence_level, 0.90)


class TestPerformanceIntegration(unittest.TestCase):
    """Performance integration tests."""

    def test_large_dataset_performance(self):
        """Test performance with large datasets."""
        mock_session = MagicMock()
        fetcher = PocketDataFetcher(
            session=mock_session, consumer_key="test-key", access_token="test-token"
        )

        # Mock large dataset (10,000 articles)
        large_dataset = {
            "list": {
                str(i): {
                    "item_id": str(i),
                    "title": f"Article {i}",
                    "excerpt": f"Excerpt for article {i}",
                    "time_added": "1747875206",
                }
                for i in range(1, 10001)
            },
            "complete": 1,
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = large_dataset
        mock_session.post.return_value = mock_response

        # Test processing time
        import time

        start_time = time.time()

        articles = list(fetcher.fetch_all_articles_with_batching())

        processing_time = time.time() - start_time

        # Verify performance requirements
        self.assertEqual(len(articles), 10000)
        self.assertLess(
            processing_time, 10.0
        )  # Should process 10K articles in <10 seconds

        # Verify memory efficiency
        import sys

        memory_usage = sys.getsizeof(articles)
        self.assertLess(memory_usage, 100 * 1024 * 1024)  # Less than 100MB

    def test_api_rate_limit_compliance(self):
        """Test API rate limit compliance."""
        mock_session = MagicMock()
        fetcher = PocketDataFetcher(
            session=mock_session, consumer_key="test-key", access_token="test-token"
        )

        # Mock multiple API calls
        mock_responses = []
        for i in range(5):  # 5 batches
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "list": {
                    str(j): {"item_id": str(j), "title": f"Article {j}"}
                    for j in range(i * 272 + 1, (i + 1) * 272 + 1)
                },
                "complete": 0 if i < 4 else 1,
            }
            mock_responses.append(mock_response)

        mock_session.post.side_effect = mock_responses

        # Test rate limiting
        with patch("time.sleep") as mock_sleep:
            articles = list(fetcher.fetch_all_articles_with_batching())

            # Verify rate limiting delays were applied
            self.assertEqual(len(articles), 1360)  # 5 * 272
            self.assertEqual(mock_sleep.call_count, 4)  # 4 delays between 5 calls

            # Verify delay timing
            for call in mock_sleep.call_args_list:
                self.assertEqual(call[0][0], 1.5)  # 1.5 second delay


if __name__ == "__main__":
    unittest.main()
