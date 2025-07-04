#!/usr/bin/env python3
"""
Test script for enhanced incremental export functionality.
"""

import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import json

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_incremental_export import enhanced_incremental_export, setup_authentication


def test_enhanced_export_structure():
    """Test that the enhanced export function has the right structure."""
    print("🔍 Testing enhanced export structure...")
    
    # Check that the function exists and is callable
    assert callable(enhanced_incremental_export), "enhanced_incremental_export should be callable"
    
    # Check that it accepts the expected parameters
    import inspect
    sig = inspect.signature(enhanced_incremental_export)
    params = list(sig.parameters.keys())
    
    expected_params = ['state', 'verbose']
    for param in expected_params:
        assert param in params, f"enhanced_incremental_export should accept '{param}' parameter"
    
    print("✅ Enhanced export structure tests passed")


def test_progressive_delay_calculation():
    """Test the progressive delay calculation in data_fetcher."""
    print("🔍 Testing progressive delay calculation...")
    
    from data_fetcher import PocketDataFetcher
    
    # Create a mock fetcher to test delay calculation
    mock_session = MagicMock()
    fetcher = PocketDataFetcher(
        session=mock_session,
        consumer_key="test_key",
        access_token="test_token"
    )
    
    # Test progressive delays
    delays = []
    for batch in range(0, 50, 10):  # Test every 10th batch
        delay = fetcher._calculate_progressive_delay(batch)
        delays.append(delay)
        print(f"   Batch {batch}: {delay:.2f}s")
    
    # Verify delays increase over time
    for i in range(1, len(delays)):
        assert delays[i] >= delays[i-1], f"Delay should increase: {delays[i-1]} -> {delays[i]}"
    
    print("✅ Progressive delay calculation tests passed")


def test_mock_enhanced_export():
    """Test enhanced incremental export with mocked data fetcher."""
    print("🔍 Testing mock enhanced incremental export...")
    
    # Create a mock data fetcher that returns test data
    class MockDataFetcher:
        def __init__(self):
            self.base_rate_limit_delay = 1.5
            self.progressive_delay_factor = 0.1
            self.rate_limit_backoff = 2.0
        
        def _calculate_progressive_delay(self, batch_number):
            delay_multiplier = 1.0 + (batch_number // 10) * self.progressive_delay_factor
            import random
            jitter = random.uniform(0.8, 1.2)
            return self.base_rate_limit_delay * delay_multiplier * jitter
        
        def fetch_all_articles_with_batching(self, detail_type, state, progress_callback):
            # Simulate 5 batches of 10 articles each
            test_articles = []
            for i in range(50):
                test_articles.append({
                    "item_id": f"test_{i}",
                    "resolved_title": f"Test Article {i}",
                    "resolved_url": f"https://example.com/article_{i}",
                    "excerpt": f"Test excerpt {i}",
                    "time_added": "1234567890",
                    "time_read": "1234567890" if i < 30 else None,
                    "status": "0" if i < 30 else "1"
                })
            
            # Split into batches and call callback
            batch_size = 10
            for batch_num in range(5):
                start_idx = batch_num * batch_size
                end_idx = start_idx + batch_size
                batch = test_articles[start_idx:end_idx]
                
                # Simulate progressive delay
                delay = self._calculate_progressive_delay(batch_num)
                print(f"   Batch {batch_num + 1}: {len(batch)} articles, delay: {delay:.2f}s")
                
                # Call the progress callback
                progress_callback(batch, batch_num + 1)
                
                # Yield each article in the batch
                for article in batch:
                    yield article
    
    # Mock the create_data_fetcher function
    with patch('enhanced_incremental_export.create_data_fetcher') as mock_create_fetcher:
        mock_create_fetcher.return_value = MockDataFetcher()
        
        # Mock the setup_authentication
        with patch('enhanced_incremental_export.setup_authentication') as mock_auth:
            mock_auth.return_value = MagicMock()
            
            # Create temporary directories for testing
            with tempfile.TemporaryDirectory() as temp_dir:
                # Change to temp directory
                original_cwd = os.getcwd()
                os.chdir(temp_dir)
                
                try:
                    # Run the enhanced incremental export
                    enhanced_incremental_export(state="all", verbose=False)
                    
                    # Check that files were created
                    assert os.path.exists("raw_data/pocket_export_raw.json"), "Raw data file should exist"
                    assert os.path.exists("parsed_data/articles.jsonl"), "Parsed data file should exist"
                    
                    # Check file contents
                    with open("raw_data/pocket_export_raw.json", 'r') as f:
                        raw_data = json.load(f)
                        assert len(raw_data) == 50, f"Should have 50 articles, got {len(raw_data)}"
                    
                    with open("parsed_data/articles.jsonl", 'r') as f:
                        lines = f.readlines()
                        assert len(lines) == 50, f"Should have 50 lines, got {len(lines)}"
                    
                    print("✅ Mock enhanced incremental export test passed")
                    
                finally:
                    # Restore original directory
                    os.chdir(original_cwd)
    
    print("✅ Mock enhanced export tests passed")


def test_rate_limit_handling():
    """Test rate limit handling strategies."""
    print("🔍 Testing rate limit handling...")
    
    from data_fetcher import PocketDataFetcher
    
    # Create a mock fetcher
    mock_session = MagicMock()
    fetcher = PocketDataFetcher(
        session=mock_session,
        consumer_key="test_key",
        access_token="test_token"
    )
    
    # Test exponential backoff
    original_backoff = fetcher.rate_limit_backoff
    assert original_backoff == 2.0, f"Initial backoff should be 2.0, got {original_backoff}"
    
    # Simulate rate limit retry
    retry_delay = 5 * fetcher.rate_limit_backoff
    assert retry_delay == 10.0, f"Retry delay should be 10.0s, got {retry_delay}"
    
    # Simulate backoff increase
    fetcher.rate_limit_backoff = min(fetcher.rate_limit_backoff * 1.5, 10.0)
    assert fetcher.rate_limit_backoff == 3.0, f"Backoff should increase to 3.0, got {fetcher.rate_limit_backoff}"
    
    print("✅ Rate limit handling tests passed")


def run_all_tests():
    """Run all tests."""
    print("🧪 Running enhanced incremental export tests...")
    print("=" * 50)
    
    try:
        test_enhanced_export_structure()
        test_progressive_delay_calculation()
        test_rate_limit_handling()
        test_mock_enhanced_export()
        
        print("=" * 50)
        print("🎉 All enhanced export tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 