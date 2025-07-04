#!/usr/bin/env python3
"""
Quick validation script for Pocket export.
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from export_comparator import FastExportValidator, JSONLSampler
from csv_parser import PocketCSVParser

def validate_sample_size(sample_size: str) -> int:
    """Validate sample size is between 9 and 999."""
    try:
        size = int(sample_size)
    except ValueError:
        raise argparse.ArgumentTypeError("Sample size must be an integer")
    
    if size < 9:
        raise argparse.ArgumentTypeError("Sample size must be at least 9")
    if size > 999:
        raise argparse.ArgumentTypeError("Sample size must be at most 999")
    return size

def main():
    """Validate the current export against CSV data."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Validate Pocket export data")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run validation (default action)"
    )
    parser.add_argument(
        "--csv-dir",
        default="csv_exports",
        help="Directory containing CSV files (default: csv_exports)"
    )
    parser.add_argument(
        "--sample-size",
        type=validate_sample_size,
        default=200,
        help="Number of JSONL records to sample for validation (9-999, default: 200)"
    )
    parser.add_argument(
        "--show-mismatches",
        type=int,
        default=0,
        help="Show detailed mismatch examples (0-50, default: 0)"
    )
    
    args = parser.parse_args()
    
    load_dotenv()
    
    # Check if files exist
    jsonl_path = "parsed_data/articles.jsonl"
    csv_dir = args.csv_dir
    
    if not os.path.exists(jsonl_path):
        print("❌ JSONL file not found:", jsonl_path)
        sys.exit(1)
        
    if not os.path.exists(csv_dir):
        print("❌ CSV directory not found:", csv_dir)
        sys.exit(1)
    
    print("🔍 Starting export validation...")
    print(f"📊 Sample size: {args.sample_size:,} articles")
    
    # Load CSV as source of truth
    print("📥 Loading CSV data as source of truth...")
    csv_articles = {}
    csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
    
    for csv_file in csv_files:
        csv_path = os.path.join(csv_dir, csv_file)
        parser = PocketCSVParser(csv_path)
        file_articles = parser.load_csv_as_source_of_truth()
        csv_articles.update(file_articles)
    
    print(f"✅ Loaded {len(csv_articles):,} articles from CSV")
    
    # Sample JSONL records
    print("📥 Sampling JSONL records...")
    sampler = JSONLSampler(jsonl_path)
    total_records = sampler.count_total_records()
    print(f"📊 Total JSONL records: {total_records:,}")
    
    # Sample records for validation
    sample_size = args.sample_size
    jsonl_sample = sampler.sample_random_records(sample_size)
    print(f"📊 Sampled {len(jsonl_sample):,} records for validation")
    
    # Run validation
    print("🔍 Running validation...")
    validator = FastExportValidator(csv_articles, jsonl_sample)
    
    def progress_callback(message, progress):
        print(f"🔄 {message} ({progress * 100:.0f}%)")
    
    result = validator.validate_with_progress(progress_callback)
    
    # Display results
    print("\n" + validator.generate_validation_summary(result))
    
    # Show detailed mismatches if requested
    if args.show_mismatches > 0:
        print("\n" + "=" * 60)
        print("🔍 DETAILED MISMATCH EXAMPLES")
        print("=" * 60)
        
        # Show missing articles (JSONL has but CSV doesn't)
        if result.missing_in_api:
            print(f"\n📤 MISSING IN CSV (JSONL has, CSV doesn't):")
            print("-" * 50)
            for i, mismatch in enumerate(result.missing_in_api[:args.show_mismatches]):
                article = mismatch.get("jsonl_article", {})
                print(f"{i+1}. {article.get('resolved_title', 'Unknown Title')}")
                print(f"   URL: {article.get('resolved_url', 'Unknown URL')}")
                print(f"   Added: {article.get('time_added', 'Unknown')}")
                print()
        
        # Show extra articles (CSV has but JSONL doesn't)
        if result.extra_in_api:
            print(f"\n📥 EXTRA IN CSV (CSV has, JSONL doesn't):")
            print("-" * 50)
            for i, mismatch in enumerate(result.extra_in_api[:args.show_mismatches]):
                article = mismatch.get("csv_article", {})
                print(f"{i+1}. {article.get('resolved_title', 'Unknown Title')}")
                print(f"   URL: {article.get('resolved_url', 'Unknown URL')}")
                print(f"   Added: {article.get('time_added', 'Unknown')}")
                print()
    
    # Additional analysis
    print("\n📊 ADDITIONAL ANALYSIS:")
    print(f"CSV Total: {len(csv_articles):,}")
    print(f"JSONL Total: {total_records:,}")
    print(f"Difference: {abs(len(csv_articles) - total_records):,}")
    
    if len(csv_articles) > total_records:
        print(f"⚠️  API export has {len(csv_articles) - total_records:,} fewer articles than CSV")
    elif total_records > len(csv_articles):
        print(f"⚠️  API export has {total_records - len(csv_articles):,} more articles than CSV")
    else:
        print("✅ Article counts match exactly!")
        print("💡 URL format differences are normal - same articles with different URL representations")

if __name__ == "__main__":
    main() 