#!/usr/bin/env python3
"""
Data Fetcher Module for Pocket Export Tool
Handles fetching articles from Pocket API with pagination and rate limiting.
"""

import json
import time
import logging
from typing import Dict, List, Optional, Generator, Callable
import requests
from requests import Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ExportProgress:
    """Track and display export progress in real-time."""

    def __init__(self, total_articles: Optional[int] = None, verbose: bool = True):
        self.start_time = time.time()
        self.processed_articles = 0
        self.current_batch = 0
        self.total_articles = total_articles
        self.last_update = time.time()
        self.verbose = verbose
        self.batch_start_time = time.time()

    def update(self, batch_articles: List[Dict], batch_number: int) -> None:
        """Update progress with new batch of articles."""
        self.current_batch = batch_number
        self.processed_articles += len(batch_articles)

        if self.verbose:
            self._display_status()

    def _display_status(self) -> None:
        """Display current export status."""
        current_time = time.time()
        elapsed_time = current_time - self.start_time

        # Calculate processing rate
        if elapsed_time > 0:
            rate = self.processed_articles / elapsed_time
        else:
            rate = 0

        # Display progress information
        print(
            f"\r🔄 Batch {self.current_batch} | "
            f"Articles: {self.processed_articles:,}",
            end="",
        )

        if self.total_articles:
            percentage = (self.processed_articles / self.total_articles) * 100
            print(f" / {self.total_articles:,} ({percentage:.1f}%)", end="")

        print(
            f" | Rate: {rate:.1f}/sec | " f"Elapsed: {self._format_time(elapsed_time)}",
            end="",
        )

        # Estimate remaining time if we have a total
        if self.total_articles and rate > 0:
            remaining_articles = self.total_articles - self.processed_articles
            estimated_remaining = remaining_articles / rate
            print(f" | ETA: {self._format_time(estimated_remaining)}", end="")

        print(" " * 10, end="\r")  # Clear any remaining characters

    def _format_time(self, seconds: float) -> str:
        """Format time in human-readable format."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.0f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

    def finish(self) -> None:
        """Display final completion status."""
        if self.verbose:
            total_time = time.time() - self.start_time
            print(
                f"\n✅ Export completed! "
                f"Processed {self.processed_articles:,} articles in {self._format_time(total_time)}"
            )

            if total_time > 0:
                avg_rate = self.processed_articles / total_time
                print(f"   Average rate: {avg_rate:.1f} articles/second")


class PocketDataFetcher:
    """Handles fetching data from Pocket API with pagination and rate limiting."""

    def __init__(self, session: Session, consumer_key: str, access_token: str):
        self.session = session
        self.consumer_key = consumer_key
        self.access_token = access_token
        self.base_url = "https://getpocket.com/v3/get"
        self.base_rate_limit_delay = 1.5  # Base delay in seconds
        self.max_batch_size = 272  # Discovered API limit
        self.progressive_delay_factor = 0.1  # Increase delay by 10% every 10 batches
        self.rate_limit_backoff = 2.0  # Multiplier for rate limit retries

    def fetch_articles(
        self,
        detail_type: str = "complete",
        state: str = "all",
        count: int = 272,
        max_articles: Optional[int] = None,
    ) -> Generator[Dict, None, None]:
        """
        Fetch articles from Pocket API with pagination.

        Args:
            detail_type: "complete" for full data, "simple" for basic
            state: "all", "unread", or "archive"
            count: Number of articles per request (max 272 - discovered limit)
            max_articles: Maximum total articles to fetch (None for all)

        Yields:
            Dictionary containing article data
        """
        offset = 0
        total_fetched = 0

        # Ensure count doesn't exceed the discovered API limit
        batch_count = min(count, self.max_batch_size)

        logger.info(
            f"Starting article fetch (detail_type: {detail_type}, state: {state})"
        )
        logger.info(f"Using batch size: {batch_count} (max: {self.max_batch_size})")

        while True:
            # Check if we've reached the maximum articles limit
            if max_articles and total_fetched >= max_articles:
                logger.info(f"Reached maximum articles limit: {max_articles}")
                break

            # Calculate how many articles to request in this batch
            current_batch_size = batch_count
            if max_articles:
                remaining = max_articles - total_fetched
                current_batch_size = min(batch_count, remaining)

            logger.info(f"Fetching batch: offset={offset}, count={current_batch_size}")

            # Fetch batch of articles
            response_data = self._fetch_batch(
                detail_type=detail_type,
                state=state,
                count=current_batch_size,
                offset=offset,
            )

            if not response_data:
                logger.warning("No response data received")
                break

            # Extract articles from response
            articles = response_data.get("list", {})
            if not articles:
                logger.info("No more articles to fetch")
                break

            # Yield each article
            for item_id, article_data in articles.items():
                yield article_data
                total_fetched += 1

                # Check if we've reached the limit
                if max_articles and total_fetched >= max_articles:
                    logger.info(f"Reached maximum articles limit: {max_articles}")
                    return

            # Check if we've received all articles
            # Note: Pocket API returns complete=1 for every batch, not just the final one
            # We should continue until we get an empty response or no more articles
            if len(articles) == 0:
                logger.info("No more articles to fetch (empty response)")
                break

            # Update offset for next batch
            offset += current_batch_size

            # Progressive rate limiting delay
            if len(articles) > 0:  # Only delay if we got articles
                current_delay = self._calculate_progressive_delay(offset // self.max_batch_size)
                logger.debug(f"Rate limiting delay: {current_delay:.1f}s (batch {offset // self.max_batch_size + 1})")
                time.sleep(current_delay)

        logger.info(f"Article fetch completed. Total articles: {total_fetched}")

    def _fetch_batch(
        self, detail_type: str, state: str, count: int, offset: int
    ) -> Optional[Dict]:
        """
        Fetch a single batch of articles from Pocket API.

        Args:
            detail_type: Level of detail for articles
            state: Article state filter
            count: Number of articles to fetch
            offset: Pagination offset

        Returns:
            Response data dictionary or None if failed
        """
        try:
            # Prepare request payload
            payload = {
                "consumer_key": self.consumer_key,
                "access_token": self.access_token,
                "detailType": detail_type,
                "state": state,
                "count": count,
                "offset": offset,
            }

            # Make API request
            response = self.session.post(
                self.base_url,
                json=payload,
                headers={
                    "Content-Type": "application/json; charset=UTF-8",
                    "X-Accept": "application/json",
                },
                timeout=30,
            )

            # Handle different response status codes
            if response.status_code == 200:
                data = response.json()
                logger.debug(
                    f"Successfully fetched batch: {len(data.get('list', {}))} articles"
                )
                return data

            elif response.status_code == 429:
                retry_delay = 5 * self.rate_limit_backoff
                logger.warning(f"Rate limit exceeded. Waiting {retry_delay} seconds...")
                time.sleep(retry_delay)
                # Increase backoff for next retry
                self.rate_limit_backoff = min(self.rate_limit_backoff * 1.5, 10.0)
                return self._fetch_batch(detail_type, state, count, offset)  # Retry

            elif response.status_code == 401:
                logger.error("Authentication failed. Check your credentials.")
                return None

            elif response.status_code == 403:
                logger.error("Access forbidden. Check your API permissions.")
                return None

            else:
                logger.error(
                    f"API request failed with status {response.status_code}: "
                    f"{response.text}"
                )
                return None

        except requests.exceptions.Timeout:
            logger.error("Request timeout. Retrying...")
            time.sleep(2)
            return self._fetch_batch(detail_type, state, count, offset)  # Retry

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during API request: {e}")
            return None

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {e}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error during API request: {e}")
            return None

    def fetch_all_articles_with_batching(
        self,
        detail_type: str = "complete",
        state: str = "all",
        progress_callback: Optional[Callable] = None,
        max_articles: Optional[int] = None,
    ) -> Generator[Dict, None, None]:
        """
        Fetch ALL articles using optimal batch processing with real-time progress updates.

        Args:
            detail_type: "complete" for full data, "simple" for basic
            state: "all", "unread", or "archive"
            progress_callback: Optional callback function for progress updates
            max_articles: Maximum number of articles to fetch (None for all)

        Yields:
            Dictionary containing article data
        """
        logger.info("🚀 Starting FULL EXPORT with batch processing")
        logger.info(f"📊 Batch size: {self.max_batch_size} articles per request")

        total_fetched = 0
        batch_number = 0
        current_batch_articles = []

        for article in self.fetch_articles(
            detail_type=detail_type,
            state=state,
            count=self.max_batch_size,
            max_articles=max_articles,  # Pass the limit
        ):
            total_fetched += 1
            current_batch_articles.append(article)

            # Check if we've completed a batch
            if len(current_batch_articles) == self.max_batch_size:
                batch_number += 1

                # Update progress if callback provided
                if progress_callback:
                    progress_callback(current_batch_articles, batch_number)

                # Reset batch articles
                current_batch_articles = []

            yield article

        # Handle any remaining articles in the final batch
        if current_batch_articles and progress_callback:
            batch_number += 1
            progress_callback(current_batch_articles, batch_number)

        logger.info(f"🎉 FULL EXPORT COMPLETE! Total articles: {total_fetched}")

    def _calculate_progressive_delay(self, batch_number: int) -> float:
        """
        Calculate progressive delay that increases over time to avoid rate limiting.
        
        Args:
            batch_number: Current batch number (0-based)
            
        Returns:
            Delay in seconds
        """
        # Increase delay by 10% every 10 batches
        delay_multiplier = 1.0 + (batch_number // 10) * self.progressive_delay_factor
        
        # Add some randomness to avoid predictable patterns
        import random
        jitter = random.uniform(0.8, 1.2)
        
        return self.base_rate_limit_delay * delay_multiplier * jitter

    def get_article_count(self) -> Optional[int]:
        """
        Get the total number of articles in the user's Pocket account.

        Returns:
            Total article count or None if failed
        """
        try:
            # Fetch a single article to get metadata
            response_data = self._fetch_batch(
                detail_type="simple", state="all", count=1, offset=0
            )

            if response_data and "list" in response_data:
                # The response might contain metadata about total count
                # For now, we'll estimate based on the first batch
                return len(response_data["list"])

            return None

        except Exception as e:
            logger.error(f"Error getting article count: {e}")
            return None

    def fetch_all_articles(self, detail_type: str = "complete") -> List[Dict]:
        """
        Fetch all articles from Pocket API.

        Args:
            detail_type: Level of detail for articles

        Returns:
            List of all article dictionaries
        """
        articles = []

        for article in self.fetch_articles(detail_type=detail_type):
            articles.append(article)

        logger.info(f"Fetched {len(articles)} total articles")
        return articles


def create_data_fetcher(authenticator) -> Optional[PocketDataFetcher]:
    """
    Create a data fetcher instance from an authenticator.

    Args:
        authenticator: PocketAuthenticator instance

    Returns:
        PocketDataFetcher instance or None if failed
    """
    try:
        session = authenticator.get_session()
        if not session:
            logger.error("No authenticated session available")
            return None

        return PocketDataFetcher(
            session=session,
            consumer_key=authenticator.consumer_key,
            access_token=authenticator.access_token,
        )

    except Exception as e:
        logger.error(f"Error creating data fetcher: {e}")
        return None
