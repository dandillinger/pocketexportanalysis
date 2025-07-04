#!/usr/bin/env python3
"""
Script to save current export data that's been collected in memory.
This will attempt to save whatever data has been fetched so far.
"""

import json
import os
import sys
from datetime import datetime

def save_current_data():
    """Save whatever data has been collected so far."""
    
    # Check if the export process is still running
    import subprocess
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    if 'pocket_export.py --full-export' in result.stdout:
        print("⚠️  Export process is still running. Data may be incomplete.")
    
    # Check current file sizes
    raw_file = "raw_data/pocket_export_raw.json"
    parsed_file = "parsed_data/articles.jsonl"
    
    print("📊 Current file status:")
    
    if os.path.exists(raw_file):
        size = os.path.getsize(raw_file)
        print(f"   Raw data: {size:,} bytes ({size/1024:.1f} KB)")
        
        # Try to count articles in raw file
        try:
            with open(raw_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    print(f"   Articles in raw file: {len(data)}")
                elif isinstance(data, dict) and 'list' in data:
                    print(f"   Articles in raw file: {len(data['list'])}")
        except Exception as e:
            print(f"   Error reading raw file: {e}")
    
    if os.path.exists(parsed_file):
        size = os.path.getsize(parsed_file)
        print(f"   Parsed data: {size:,} bytes ({size/1024:.1f} KB)")
        
        # Count lines in parsed file
        try:
            with open(parsed_file, 'r') as f:
                lines = f.readlines()
                print(f"   Articles in parsed file: {len(lines)}")
        except Exception as e:
            print(f"   Error reading parsed file: {e}")
    
    # Create backup of current data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if os.path.exists(raw_file):
        backup_raw = f"raw_data/pocket_export_raw_backup_{timestamp}.json"
        try:
            import shutil
            shutil.copy2(raw_file, backup_raw)
            print(f"✅ Backed up raw data to: {backup_raw}")
        except Exception as e:
            print(f"❌ Failed to backup raw data: {e}")
    
    if os.path.exists(parsed_file):
        backup_parsed = f"parsed_data/articles_backup_{timestamp}.jsonl"
        try:
            import shutil
            shutil.copy2(parsed_file, backup_parsed)
            print(f"✅ Backed up parsed data to: {backup_parsed}")
        except Exception as e:
            print(f"❌ Failed to backup parsed data: {e}")
    
    print("\n💡 To save current data:")
    print("   1. The export process is still running and collecting data")
    print("   2. Current files have been backed up with timestamp")
    print("   3. You can wait for completion or interrupt the process")
    print("   4. Files will be updated when the export completes")

if __name__ == "__main__":
    save_current_data() 