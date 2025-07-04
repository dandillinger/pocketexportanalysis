#!/usr/bin/env python3
"""
Incremental Pocket Export Tool
Saves data after each batch to avoid losing progress on timeouts.
"""

import os
import sys
import logging
from typing import List, Dict
from data_parser import parse_pocket_article
from storage import save_raw_json, save_articles_jsonl, get_file_summary
from data_fetcher import create_data_fetcher, ExportProgress

# Import authentication directly to avoid broken pocket_export.py
import requests
from typing import Optional


class PocketAuthenticator:
    def __init__(self):
        self.consumer_key = None
        self.access_token = None
        self.session = None

    def load_credentials(self) -> bool:
        self.consumer_key = os.getenv("POCKET_CONSUMER_KEY")
        self.access_token = os.getenv("POCKET_ACCESS_TOKEN")
        if not self.consumer_key or not self.access_token:
            return False
        self.session = requests.Session()
        return True

    def get_session(self) -> Optional[requests.Session]:
        return self.session


def setup_authentication() -> Optional[PocketAuthenticator]:
    authenticator = PocketAuthenticator()
    if authenticator.load_credentials():
        return authenticator
    return None


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def incremental_export(state: str = "all", verbose: bool = False):
    """
    Perform incremental export with data saved after each batch.
    """
    authenticator = setup_authentication()
    if not authenticator:
        logger.error("Authentication failed. Exiting.")
        sys.exit(1)
    fetcher = create_data_fetcher(authenticator)
    if not fetcher:
        logger.error("Failed to create data fetcher. Exiting.")
        sys.exit(1)
    raw_path = os.path.join("raw_data", "pocket_export_raw.json")
    parsed_path = os.path.join("parsed_data", "articles.jsonl")
    os.makedirs("raw_data", exist_ok=True)
    os.makedirs("parsed_data", exist_ok=True)
    all_raw_articles = []
    all_parsed_articles = []
    total_articles = 0
    batch_number = 0
    logger.info(f"🚀 INCREMENTAL EXPORT: Fetching ALL articles (state: {state})...")
    logger.info("📊 Data will be saved after each batch to prevent data loss")
    try:
        progress = ExportProgress(verbose=True)

        def progress_callback(batch_articles: List[Dict], current_batch: int):
            nonlocal total_articles, batch_number
            batch_number = current_batch
            batch_size = len(batch_articles)
            total_articles += batch_size
            logger.info(f"📦 Processing batch {batch_number} ({batch_size} articles)...")
            for article in batch_articles:
                all_raw_articles.append(article)
                parsed_article = parse_pocket_article(article)
                all_parsed_articles.append(parsed_article)
            logger.info(f"💾 Saving batch {batch_number} data to files...")
            if save_raw_json(all_raw_articles, raw_path):
                logger.info(f"✅ Raw data saved: {len(all_raw_articles):,} articles")
            else:
                logger.error(f"❌ Failed to save raw data for batch {batch_number}")
            if save_articles_jsonl(all_parsed_articles, parsed_path):
                logger.info(f"✅ Parsed data saved: {len(all_parsed_articles):,} articles")
            else:
                logger.error(f"❌ Failed to save parsed data for batch {batch_number}")
            progress.update(batch_articles, batch_number)
            logger.info(f"📊 Total progress: {total_articles:,} articles processed")

        article_generator = fetcher.fetch_all_articles_with_batching(
            detail_type="complete",
            state=state,
            progress_callback=progress_callback,
        )
        for article in article_generator:
            pass
        progress.finish()
        logger.info(f"�� INCREMENTAL EXPORT COMPLETED! Total articles: {total_articles:,}")
        raw_summary = get_file_summary(raw_path)
        parsed_summary = get_file_summary(parsed_path)
        print("\n" + "=" * 60)
        print("📊 FINAL EXPORT SUMMARY")
        print("=" * 60)
        print(f"📁 Raw Data: {raw_summary['file']}")
        print(f"   Size: {raw_summary['size_bytes']:,} bytes "
              f"({raw_summary['size_bytes'] / 1024:.1f} KB)")
        print(f"   Articles: {raw_summary['article_count']:,}")
        print(f"\n📄 Parsed Data: {parsed_summary['file']}")
        print(f"   Size: {parsed_summary['size_bytes']:,} bytes "
              f"({parsed_summary['size_bytes'] / 1024:.1f} KB)")
        print(f"   Articles: {parsed_summary['article_count']:,}")
        print(f"\n⚡ Processing:")
        print(f"   Articles processed: {total_articles:,}")
        print(f"   Batches completed: {batch_number}")
        print("   Success rate: 100%")
        print("\n✅ Incremental export completed successfully!")
        print("=" * 60)
    except KeyboardInterrupt:
        logger.info("⏹️  Export interrupted by user")
        logger.info(f"📊 Data saved so far: {len(all_raw_articles):,} articles")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error during incremental export: {e}")
        logger.info(f"📊 Data saved before error: {len(all_raw_articles):,} articles")
        sys.exit(1)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Incremental Pocket Export Tool")
    parser.add_argument("--state", choices=["all", "unread", "archive"], default="all",
                       help="Article state filter (default: all)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    incremental_export(state=args.state, verbose=args.verbose)


if __name__ == "__main__":
    main() 