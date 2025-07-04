#!/usr/bin/env python3
"""
Test script for incremental export functionality.
"""

import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import json

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from incremental_export import incremental_export, setup_authentication


def test_authentication():
    """Test authentication setup."""
    print("🔍 Testing authentication...")
    
    # Test with no environment variables
    with patch.dict(os.environ, {}, clear=True):
        auth = setup_authentication()
        assert auth is None, "Should return None when no credentials"
    
    # Test with valid environment variables
    with patch.dict(os.environ, {
        'POCKET_CONSUMER_KEY': 'test_consumer_key',
        'POCKET_ACCESS_TOKEN': 'test_access_token'
    }):
        auth = setup_authentication()
        assert auth is not None, "Should return authenticator with valid credentials"
        assert auth.consumer_key == 'test_consumer_key'
        assert auth.access_token == 'test_access_token'
    
    print("✅ Authentication tests passed")


def test_incremental_export_structure():
    """Test that the incremental export function has the right structure."""
    print("🔍 Testing incremental export structure...")
    
    # Check that the function exists and is callable
    assert callable(incremental_export), "incremental_export should be callable"
    
    # Check that it accepts the expected parameters
    import inspect
    sig = inspect.signature(incremental_export)
    params = list(sig.parameters.keys())
    
    expected_params = ['state', 'verbose']
    for param in expected_params:
        assert param in params, f"incremental_export should accept '{param}' parameter"
    
    print("✅ Incremental export structure tests passed")


def test_file_operations():
    """Test file operations used by incremental export."""
    print("🔍 Testing file operations...")
    
    # Test directory creation
    test_dir = "test_output"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    os.makedirs(test_dir, exist_ok=True)
    assert os.path.exists(test_dir), "Directory should be created"
    
    # Test file writing
    test_file = os.path.join(test_dir, "test.json")
    test_data = [{"test": "data"}]
    
    with open(test_file, 'w') as f:
        json.dump(test_data, f)
    
    assert os.path.exists(test_file), "File should be written"
    
    # Clean up
    shutil.rmtree(test_dir)
    
    print("✅ File operations tests passed")


def test_mock_export():
    """Test incremental export with mocked data fetcher."""
    print("🔍 Testing mock incremental export...")
    
    # Create a mock data fetcher that returns test data
    class MockDataFetcher:
        def fetch_all_articles_with_batching(self, detail_type, state, progress_callback):
            # Simulate 3 batches of 5 articles each
            test_articles = []
            for i in range(15):
                test_articles.append({
                    "item_id": f"test_{i}",
                    "resolved_title": f"Test Article {i}",
                    "resolved_url": f"https://example.com/article_{i}",
                    "excerpt": f"Test excerpt {i}",
                    "time_added": "1234567890",
                    "time_read": "1234567890" if i < 10 else None,
                    "status": "0" if i < 10 else "1"
                })
            
            # Split into batches and call callback
            batch_size = 5
            for batch_num in range(3):
                start_idx = batch_num * batch_size
                end_idx = start_idx + batch_size
                batch = test_articles[start_idx:end_idx]
                
                # Call the progress callback
                progress_callback(batch, batch_num + 1)
                
                # Yield each article in the batch
                for article in batch:
                    yield article
    
    # Mock the create_data_fetcher function
    with patch('incremental_export.create_data_fetcher') as mock_create_fetcher:
        mock_create_fetcher.return_value = MockDataFetcher()
        
        # Mock the setup_authentication
        with patch('incremental_export.setup_authentication') as mock_auth:
            mock_auth.return_value = MagicMock()
            
            # Create temporary directories for testing
            with tempfile.TemporaryDirectory() as temp_dir:
                # Change to temp directory
                original_cwd = os.getcwd()
                os.chdir(temp_dir)
                
                try:
                    # Run the incremental export
                    incremental_export(state="all", verbose=False)
                    
                    # Check that files were created
                    assert os.path.exists("raw_data/pocket_export_raw.json"), "Raw data file should exist"
                    assert os.path.exists("parsed_data/articles.jsonl"), "Parsed data file should exist"
                    
                    # Check file contents
                    with open("raw_data/pocket_export_raw.json", 'r') as f:
                        raw_data = json.load(f)
                        assert len(raw_data) == 15, f"Should have 15 articles, got {len(raw_data)}"
                    
                    with open("parsed_data/articles.jsonl", 'r') as f:
                        lines = f.readlines()
                        assert len(lines) == 15, f"Should have 15 lines, got {len(lines)}"
                    
                    print("✅ Mock incremental export test passed")
                    
                finally:
                    # Restore original directory
                    os.chdir(original_cwd)
    
    print("✅ Mock export tests passed")


def run_all_tests():
    """Run all tests."""
    print("🧪 Running incremental export tests...")
    print("=" * 50)
    
    try:
        test_authentication()
        test_incremental_export_structure()
        test_file_operations()
        test_mock_export()
        
        print("=" * 50)
        print("🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 