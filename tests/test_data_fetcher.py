#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
Unit tests for Pocket Export Tool data fetcher module.
Tests the PocketDataFetcher class and related functionality.
"""

import unittest
from unittest.mock import patch, MagicMock

from data_fetcher import PocketDataFetcher, create_data_fetcher, ExportProgress


class TestPocketDataFetcher(unittest.TestCase):
    """Test cases for PocketDataFetcher class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_session = MagicMock()
        self.consumer_key = "test-consumer-key"
        self.access_token = "test-access-token"
        self.fetcher = PocketDataFetcher(
            session=self.mock_session,
            consumer_key=self.consumer_key,
            access_token=self.access_token,
        )

    def test_init(self):
        """Test fetcher initialization."""
        self.assertEqual(self.fetcher.consumer_key, self.consumer_key)
        self.assertEqual(self.fetcher.access_token, self.access_token)
        self.assertEqual(self.fetcher.session, self.mock_session)
        self.assertEqual(self.fetcher.base_url, "https://getpocket.com/v3/get")
        self.assertEqual(self.fetcher.rate_limit_delay, 1.5)

    @patch("data_fetcher.time.sleep")
    @patch("data_fetcher.logger")
    def test_fetch_batch_success(self, mock_logger, mock_sleep):
        """Test successful batch fetching."""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "list": {
                "123": {"item_id": "123", "title": "Test Article 1"},
                "456": {"item_id": "456", "title": "Test Article 2"},
            },
            "complete": 0,
        }
        self.mock_session.post.return_value = mock_response

        result = self.fetcher._fetch_batch(
            detail_type="complete", state="all", count=2, offset=0
        )

        self.assertIsNotNone(result)
        self.assertEqual(len(result["list"]), 2)

        # Verify API call parameters
        call_args = self.mock_session.post.call_args
        self.assertEqual(call_args[0][0], "https://getpocket.com/v3/get")

        # Check payload
        payload = call_args[1]["json"]
        self.assertEqual(payload["consumer_key"], self.consumer_key)
        self.assertEqual(payload["access_token"], self.access_token)
        self.assertEqual(payload["detailType"], "complete")
        self.assertEqual(payload["state"], "all")
        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["offset"], 0)

    @patch("data_fetcher.time.sleep")
    @patch("data_fetcher.logger")
    def test_fetch_batch_rate_limit(self, mock_logger, mock_sleep):
        """Test rate limit handling."""
        # Mock rate limit response, then success
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "list": {"123": {"item_id": "123"}},
            "complete": 1,
        }

        self.mock_session.post.side_effect = [mock_response_429, mock_response_success]

        result = self.fetcher._fetch_batch(
            detail_type="complete", state="all", count=1, offset=0
        )

        # Should retry after rate limit
        self.assertEqual(self.mock_session.post.call_count, 2)
        self.assertIsNotNone(result)
        mock_sleep.assert_called_with(5)  # Rate limit delay

    @patch("data_fetcher.logger")
    def test_fetch_batch_authentication_error(self, mock_logger):
        """Test authentication error handling."""
        # Mock 401 response
        mock_response = MagicMock()
        mock_response.status_code = 401
        self.mock_session.post.return_value = mock_response

        result = self.fetcher._fetch_batch(
            detail_type="complete", state="all", count=1, offset=0
        )

        self.assertIsNone(result)
        mock_logger.error.assert_called()

    @patch("data_fetcher.time.sleep")
    @patch("data_fetcher.logger")
    def test_fetch_batch_timeout(self, mock_logger, mock_sleep):
        """Test timeout handling."""
        # Mock timeout exception, then success
        from requests.exceptions import Timeout

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "list": {"123": {"item_id": "123"}},
            "complete": 1,
        }

        self.mock_session.post.side_effect = [
            Timeout("Request timeout"),
            mock_response_success,
        ]

        result = self.fetcher._fetch_batch(
            detail_type="complete", state="all", count=1, offset=0
        )

        # Should retry after timeout
        self.assertEqual(self.mock_session.post.call_count, 2)
        self.assertIsNotNone(result)
        mock_sleep.assert_called_with(2)  # Timeout delay

    @patch("data_fetcher.time.sleep")
    @patch("data_fetcher.logger")
    def test_fetch_articles_generator(self, mock_logger, mock_sleep):
        """Test article fetching generator."""
        # Mock two batches of responses
        mock_response_1 = MagicMock()
        mock_response_1.status_code = 200
        mock_response_1.json.return_value = {
            "list": {
                "123": {"item_id": "123", "title": "Article 1"},
                "456": {"item_id": "456", "title": "Article 2"},
            },
            "complete": 0,
        }

        mock_response_2 = MagicMock()
        mock_response_2.status_code = 200
        mock_response_2.json.return_value = {
            "list": {"789": {"item_id": "789", "title": "Article 3"}},
            "complete": 1,
        }

        self.mock_session.post.side_effect = [mock_response_1, mock_response_2]

        # Test generator
        articles = list(
            self.fetcher.fetch_articles(
                detail_type="complete", state="all", count=2, max_articles=None
            )
        )

        self.assertEqual(len(articles), 3)
        self.assertEqual(articles[0]["item_id"], "123")
        self.assertEqual(articles[1]["item_id"], "456")
        self.assertEqual(articles[2]["item_id"], "789")

    @patch("data_fetcher.time.sleep")
    @patch("data_fetcher.logger")
    def test_fetch_articles_with_limit(self, mock_logger, mock_sleep):
        """Test article fetching with maximum limit."""
        # Mock response with more articles than limit
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "list": {
                "123": {"item_id": "123", "title": "Article 1"},
                "456": {"item_id": "456", "title": "Article 2"},
                "789": {"item_id": "789", "title": "Article 3"},
            },
            "complete": 0,
        }

        self.mock_session.post.return_value = mock_response

        # Test with limit of 2
        articles = list(
            self.fetcher.fetch_articles(
                detail_type="complete", state="all", count=3, max_articles=2
            )
        )

        self.assertEqual(len(articles), 2)
        self.assertEqual(articles[0]["item_id"], "123")
        self.assertEqual(articles[1]["item_id"], "456")

    @patch("data_fetcher.time.sleep")
    @patch("data_fetcher.logger")
    def test_fetch_all_articles_with_batching(self, mock_logger, mock_sleep):
        """Test the new full export with batch processing method."""
        # Mock the fetch_articles method to return test data
        test_articles = [
            {"item_id": "1", "resolved_title": "Test Article 1"},
            {"item_id": "2", "resolved_title": "Test Article 2"},
            {"item_id": "3", "resolved_title": "Test Article 3"},
        ]

        with patch.object(self.fetcher, "fetch_articles") as mock_fetch:
            mock_fetch.return_value = iter(test_articles)

            # Test the new method
            articles = list(self.fetcher.fetch_all_articles_with_batching())

            # Verify the method was called with correct parameters
            mock_fetch.assert_called_once_with(
                detail_type="complete",
                state="all",
                count=272,  # Should use max_batch_size
                max_articles=None,
            )

            # Verify we got all articles
            self.assertEqual(len(articles), 3)
            self.assertEqual(articles[0]["item_id"], "1")
            self.assertEqual(articles[1]["item_id"], "2")
            self.assertEqual(articles[2]["item_id"], "3")

    def test_max_batch_size_limit(self):
        """Test that the max_batch_size limit is enforced."""
        # Test that count is limited to max_batch_size
        with patch.object(self.fetcher, "_fetch_batch") as mock_fetch_batch:
            mock_fetch_batch.return_value = {"list": {}, "complete": 1}

            # Try to fetch with count > max_batch_size
            list(self.fetcher.fetch_articles(count=500))

            # Should be called with max_batch_size (272) instead of 500
            mock_fetch_batch.assert_called()
            call_args = mock_fetch_batch.call_args
            self.assertEqual(call_args[1]["count"], 272)

    @patch("data_fetcher.logger")
    def test_get_article_count(self, mock_logger):
        """Test getting article count."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "list": {"123": {"item_id": "123"}, "456": {"item_id": "456"}}
        }

        self.mock_session.post.return_value = mock_response

        count = self.fetcher.get_article_count()
        self.assertEqual(count, 2)

    @patch("data_fetcher.logger")
    def test_fetch_all_articles(self, mock_logger):
        """Test fetching all articles."""
        # Mock the fetch_articles generator method
        mock_articles = [
            {"item_id": "123", "title": "Article 1"},
            {"item_id": "456", "title": "Article 2"},
        ]
        
        with patch.object(self.fetcher, 'fetch_articles') as mock_fetch_articles:
            mock_fetch_articles.return_value = iter(mock_articles)
            
            articles = self.fetcher.fetch_all_articles(detail_type="complete")
            self.assertEqual(len(articles), 2)
            self.assertEqual(articles[0]["item_id"], "123")
            self.assertEqual(articles[1]["item_id"], "456")


class TestCreateDataFetcher(unittest.TestCase):
    """Test cases for create_data_fetcher function."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_authenticator = MagicMock()
        self.mock_authenticator.consumer_key = "test-consumer-key"
        self.mock_authenticator.access_token = "test-access-token"
        self.mock_session = MagicMock()
        self.mock_authenticator.get_session.return_value = self.mock_session

    @patch("data_fetcher.logger")
    def test_create_data_fetcher_success(self, mock_logger):
        """Test successful data fetcher creation."""
        fetcher = create_data_fetcher(self.mock_authenticator)

        self.assertIsNotNone(fetcher)
        self.assertIsInstance(fetcher, PocketDataFetcher)
        self.assertEqual(fetcher.consumer_key, "test-consumer-key")
        self.assertEqual(fetcher.access_token, "test-access-token")

    @patch("data_fetcher.logger")
    def test_create_data_fetcher_no_session(self, mock_logger):
        """Test data fetcher creation with no session."""
        self.mock_authenticator.get_session.return_value = None

        fetcher = create_data_fetcher(self.mock_authenticator)

        self.assertIsNone(fetcher)
        mock_logger.error.assert_called()

    @patch("data_fetcher.logger")
    def test_create_data_fetcher_exception(self, mock_logger):
        """Test data fetcher creation with exception."""
        self.mock_authenticator.get_session.side_effect = Exception("Test error")

        fetcher = create_data_fetcher(self.mock_authenticator)

        self.assertIsNone(fetcher)
        mock_logger.error.assert_called()


class TestExportProgress(unittest.TestCase):
    """Test cases for ExportProgress class."""

    def setUp(self):
        """Set up test fixtures."""
        self.progress = ExportProgress(total_articles=1000, verbose=False)

    def test_init(self):
        """Test progress tracker initialization."""
        self.assertEqual(self.progress.processed_articles, 0)
        self.assertEqual(self.progress.current_batch, 0)
        self.assertEqual(self.progress.total_articles, 1000)
        self.assertTrue(self.progress.start_time > 0)

    def test_update(self):
        """Test progress update."""
        batch_articles = [{"id": "1"}, {"id": "2"}, {"id": "3"}]

        self.progress.update(batch_articles, 1)

        self.assertEqual(self.progress.processed_articles, 3)
        self.assertEqual(self.progress.current_batch, 1)

    def test_update_multiple_batches(self):
        """Test progress update across multiple batches."""
        batch1 = [{"id": "1"}, {"id": "2"}]
        batch2 = [{"id": "3"}, {"id": "4"}, {"id": "5"}]

        self.progress.update(batch1, 1)
        self.progress.update(batch2, 2)

        self.assertEqual(self.progress.processed_articles, 5)
        self.assertEqual(self.progress.current_batch, 2)

    def test_format_time_seconds(self):
        """Test time formatting for seconds."""
        result = self.progress._format_time(45.5)
        self.assertEqual(result, "46s")

    def test_format_time_minutes(self):
        """Test time formatting for minutes."""
        result = self.progress._format_time(125.0)
        self.assertEqual(result, "2m")

    def test_format_time_hours(self):
        """Test time formatting for hours."""
        result = self.progress._format_time(7320.0)  # 2 hours 2 minutes
        self.assertEqual(result, "2.0h")

    @patch("builtins.print")
    def test_display_status_with_total(self, mock_print):
        """Test status display with known total."""
        self.progress.processed_articles = 500
        self.progress.current_batch = 10

        self.progress._display_status()

        # Verify print was called (status display)
        mock_print.assert_called()

    @patch("builtins.print")
    def test_display_status_without_total(self, mock_print):
        """Test status display without known total."""
        progress = ExportProgress(verbose=False)  # No total articles
        progress.processed_articles = 500
        progress.current_batch = 10

        progress._display_status()

        # Verify print was called (status display)
        mock_print.assert_called()

    @patch("builtins.print")
    def test_finish(self, mock_print):
        """Test completion status display."""
        # Create progress with verbose=True to enable printing
        progress = ExportProgress(total_articles=1000, verbose=True)
        progress.processed_articles = 1000

        progress.finish()

        # Verify completion message was printed
        mock_print.assert_called()

    def test_finish_with_rate_calculation(self):
        """Test completion with rate calculation."""
        # Simulate some processing time
        import time

        time.sleep(0.1)  # Small delay to ensure time difference

        self.progress.processed_articles = 100

        # Should not raise any exceptions
        self.progress.finish()

    def test_verbose_mode(self):
        """Test verbose mode initialization."""
        progress_verbose = ExportProgress(verbose=True)
        self.assertTrue(progress_verbose.verbose)

        progress_quiet = ExportProgress(verbose=False)
        self.assertFalse(progress_quiet.verbose)


if __name__ == "__main__":
    unittest.main()
