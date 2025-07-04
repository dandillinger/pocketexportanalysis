#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
Unit tests for authentication and environment variable handling.
"""
import unittest
from unittest.mock import patch, MagicMock
import json

from pocket_export import setup_authentication, PocketAuthenticator


class TestPocketAuthenticator(unittest.TestCase):
    """Test cases for PocketAuthenticator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.authenticator = PocketAuthenticator()
        self.test_consumer_key = "test-consumer-key-12345"
        self.test_access_token = "test-access-token-67890"

    def test_init(self):
        """Test authenticator initialization."""
        self.assertIsNone(self.authenticator.consumer_key)
        self.assertIsNone(self.authenticator.access_token)
        # Session should be None until load_credentials is called
        self.assertIsNone(self.authenticator.session)

    def test_get_session_with_credentials(self):
        """Test getting session when credentials are loaded."""
        self.authenticator.consumer_key = self.test_consumer_key
        self.authenticator.access_token = self.test_access_token
        self.authenticator.load_credentials()  # Ensure session is set
        session = self.authenticator.get_session()
        self.assertIsNotNone(session)
        self.assertEqual(session, self.authenticator.session)

    def test_get_session_without_credentials(self):
        """Test getting session when credentials are not loaded."""
        session = self.authenticator.get_session()
        self.assertIsNone(session)

    def test_load_credentials_success(self):
        """Test successful credential loading."""
        # Set environment variables directly
        with patch.dict(
            os.environ,
            {
                "POCKET_CONSUMER_KEY": "test-consumer-key",
                "POCKET_ACCESS_TOKEN": "test-access-token",
            },
        ):
            result = self.authenticator.load_credentials()

            self.assertTrue(result)
            self.assertEqual(self.authenticator.consumer_key, "test-consumer-key")
            self.assertEqual(self.authenticator.access_token, "test-access-token")

    def test_load_credentials_missing_consumer_key(self):
        """Test credential loading with missing consumer key."""
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            result = self.authenticator.load_credentials()

            self.assertFalse(result)
            self.assertIsNone(self.authenticator.consumer_key)
            self.assertIsNone(self.authenticator.access_token)

    def test_load_credentials_missing_access_token(self):
        """Test credential loading with missing access token."""
        # Set only consumer key and ensure access token is not present
        with patch.dict(os.environ, {"POCKET_CONSUMER_KEY": "test-consumer-key"}, clear=True):
            if "POCKET_ACCESS_TOKEN" in os.environ:
                del os.environ["POCKET_ACCESS_TOKEN"]
            authenticator = PocketAuthenticator()  # Use a fresh instance
            result = authenticator.load_credentials()
            self.assertFalse(result)  # Should fail without access token
            self.assertEqual(authenticator.consumer_key, "test-consumer-key")
            self.assertIsNone(authenticator.access_token)

    def test_load_credentials_exception(self):
        """Test credential loading with exception."""
        # This test is not needed since we don't use load_dotenv in pocket_export
        # The authenticator only reads from os.environ directly
        with patch.dict(os.environ, {}, clear=True):
            result = self.authenticator.load_credentials()
            self.assertFalse(result)


class TestSetupAuthentication(unittest.TestCase):
    """Test cases for setup_authentication function."""

    @patch("pocket_export.PocketAuthenticator")
    def test_setup_authentication_success(self, mock_authenticator_class):
        """Test successful authentication setup."""
        # Mock the authenticator instance
        mock_authenticator = MagicMock()
        mock_authenticator.load_credentials.return_value = True
        mock_authenticator_class.return_value = mock_authenticator

        result = setup_authentication()

        self.assertIsNotNone(result)
        mock_authenticator.load_credentials.assert_called_once()

    @patch("pocket_export.PocketAuthenticator")
    def test_setup_authentication_load_failure(self, mock_authenticator_class):
        """Test authentication setup with load failure."""
        # Mock the authenticator instance
        mock_authenticator = MagicMock()
        mock_authenticator.load_credentials.return_value = False
        mock_authenticator_class.return_value = mock_authenticator

        result = setup_authentication()

        self.assertIsNone(result)
        mock_authenticator.load_credentials.assert_called_once()


class TestEnvironmentVariableHandling(unittest.TestCase):
    """Test cases for environment variable handling."""

    def test_environment_variable_loading(self):
        """Test loading environment variables."""
        with patch.dict(
            os.environ,
            {
                "POCKET_CONSUMER_KEY": "env-consumer-key",
                "POCKET_ACCESS_TOKEN": "env-access-token",
            },
        ):
            authenticator = PocketAuthenticator()
            result = authenticator.load_credentials()

            self.assertTrue(result)
            self.assertEqual(authenticator.consumer_key, "env-consumer-key")
            self.assertEqual(authenticator.access_token, "env-access-token")

    def test_environment_variable_whitespace_handling(self):
        """Test handling of environment variables with whitespace."""
        with patch.dict(
            os.environ,
            {
                "POCKET_CONSUMER_KEY": "   test-key   ",  # With whitespace
                "POCKET_ACCESS_TOKEN": "   test-token   ",
            },
        ):
            authenticator = PocketAuthenticator()
            result = authenticator.load_credentials()

            self.assertTrue(result)
            self.assertEqual(authenticator.consumer_key, "   test-key   ")
            self.assertEqual(authenticator.access_token, "   test-token   ")


if __name__ == "__main__":
    unittest.main()
