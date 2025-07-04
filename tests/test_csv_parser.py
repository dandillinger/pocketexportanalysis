#!/usr/bin/env python3
"""
Unit tests for CSV Parser Module
"""

import pytest
import tempfile
import os
from csv_parser import PocketCSVParser, parse_pocket_csv


class TestPocketCSVParser:
    """Test cases for PocketCSVParser class."""

    def test_valid_csv_structure(self):
        """Test parsing of valid CSV structure."""
        csv_content = """URL,Title,Excerpt,Author,Tags,Time Added,Time Updated,Time Read,Time Favorited,Status
https://example.com/article1,Test Article 1,This is a test excerpt,Test Author,tech;programming,1640995200,1640995200,,,0
https://example.com/article2,Test Article 2,Another test excerpt,Another Author,news;tech,1640995200,1640995200,1640995200,,1"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_file = f.name

        try:
            parser = PocketCSVParser(temp_file)
            articles = parser.parse_csv()

            assert len(articles) == 2
            assert articles[0]["resolved_url"] == "https://example.com/article1"
            assert articles[0]["resolved_title"] == "Test Article 1"
            assert articles[0]["excerpt"] == "This is a test excerpt"
            assert articles[0]["status"] == "0"
            assert len(articles[0]["tags"]) == 2
            assert "tech" in [tag["tag"] for tag in articles[0]["tags"].values()]

        finally:
            os.unlink(temp_file)

    def test_missing_essential_columns(self):
        """Test handling of CSV with missing essential columns."""
        csv_content = """Title,Excerpt,Author
Test Article,This is a test,Test Author"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_file = f.name

        try:
            parser = PocketCSVParser(temp_file)
            with pytest.raises(ValueError, match="Invalid CSV structure"):
                parser.parse_csv()
        finally:
            os.unlink(temp_file)

    def test_empty_csv(self):
        """Test handling of empty CSV file."""
        csv_content = """URL,Title,Excerpt,Author,Tags,Time Added,Time Updated,Time Read,Time Favorited,Status"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_file = f.name

        try:
            parser = PocketCSVParser(temp_file)
            articles = parser.parse_csv()
            assert len(articles) == 0
        finally:
            os.unlink(temp_file)

    def test_malformed_rows(self):
        """Test handling of malformed rows."""
        csv_content = """URL,Title,Excerpt,Author,Tags,Time Added,Time Updated,Time Read,Time Favorited,Status
https://example.com/article1,Test Article 1,This is a test excerpt,Test Author,tech;programming,1640995200,1640995200,,,0
,Invalid Article,,,,
https://example.com/article2,Test Article 2,Another test excerpt,Another Author,news;tech,1640995200,1640995200,1640995200,,1"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_file = f.name

        try:
            parser = PocketCSVParser(temp_file)
            articles = parser.parse_csv()

            # Should only parse valid rows
            assert len(articles) == 2
            assert articles[0]["resolved_url"] == "https://example.com/article1"
            assert articles[1]["resolved_url"] == "https://example.com/article2"
        finally:
            os.unlink(temp_file)

    def test_tag_parsing(self):
        """Test parsing of different tag formats."""
        csv_content = """URL,Title,Excerpt,Author,Tags,Time Added,Time Updated,Time Read,Time Favorited,Status
https://example.com/article1,Test Article 1,This is a test excerpt,Test Author,"tech,programming",1640995200,1640995200,,,0
https://example.com/article2,Test Article 2,Another test excerpt,Another Author,"news;tech",1640995200,1640995200,,,0
https://example.com/article3,Test Article 3,Another test excerpt,Another Author,"tech|programming|python",1640995200,1640995200,,,0"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_file = f.name

        try:
            parser = PocketCSVParser(temp_file)
            articles = parser.parse_csv()

            assert len(articles) == 3
            # Check tag parsing
            assert len(articles[0]["tags"]) == 2  # tech,programming
            assert len(articles[1]["tags"]) == 2  # news;tech
            assert len(articles[2]["tags"]) == 3  # tech|programming|python
        finally:
            os.unlink(temp_file)

    def test_timestamp_parsing(self):
        """Test parsing of different timestamp formats."""
        csv_content = """URL,Title,Excerpt,Author,Tags,Time Added,Time Updated,Time Read,Time Favorited,Status
https://example.com/article1,Test Article 1,This is a test excerpt,Test Author,tech,1640995200,1640995200,,,0
https://example.com/article2,Test Article 2,Another test excerpt,Another Author,news,2022-01-01 12:00:00,2022-01-01 12:00:00,,,0
https://example.com/article3,Test Article 3,Another test excerpt,Another Author,tech,2022-01-01,2022-01-01,,,0"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_file = f.name

        try:
            parser = PocketCSVParser(temp_file)
            articles = parser.parse_csv()

            assert len(articles) == 3
            # Check that timestamps are parsed
            assert articles[0]["time_added"] is not None
            assert articles[1]["time_added"] is not None
            assert articles[2]["time_added"] is not None
        finally:
            os.unlink(temp_file)

    def test_convenience_function(self):
        """Test the convenience function parse_pocket_csv."""
        csv_content = """URL,Title,Excerpt,Author,Tags,Time Added,Time Updated,Time Read,Time Favorited,Status
https://example.com/article1,Test Article 1,This is a test excerpt,Test Author,tech,1640995200,1640995200,,,0"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_file = f.name

        try:
            articles = parse_pocket_csv(temp_file)
            assert len(articles) == 1
            assert articles[0]["resolved_url"] == "https://example.com/article1"
        finally:
            os.unlink(temp_file)


class TestCSVParserEdgeCases:
    """Test edge cases and error handling."""

    def test_file_not_found(self):
        """Test handling of non-existent file."""
        parser = PocketCSVParser("nonexistent_file.csv")
        with pytest.raises(FileNotFoundError):
            parser.parse_csv()

    def test_unicode_content(self):
        """Test handling of Unicode content."""
        csv_content = """URL,Title,Excerpt,Author,Tags,Time Added,Time Updated,Time Read,Time Favorited,Status
https://example.com/article1,Test Article with émojis 🚀,This is a test with unicode: café,Test Author,tech,1640995200,1640995200,,,0"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            temp_file = f.name

        try:
            parser = PocketCSVParser(temp_file)
            articles = parser.parse_csv()

            assert len(articles) == 1
            assert "émojis" in articles[0]["resolved_title"]
            assert "café" in articles[0]["excerpt"]
        finally:
            os.unlink(temp_file)

    def test_word_count_extraction(self):
        """Test word count extraction from excerpt."""
        csv_content = """URL,Title,Excerpt,Author,Tags,Time Added,Time Updated,Time Read,Time Favorited,Status
https://example.com/article1,Test Article,This is a test excerpt with five words,Test Author,tech,1640995200,1640995200,,,0"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_file = f.name

        try:
            parser = PocketCSVParser(temp_file)
            articles = parser.parse_csv()

            assert len(articles) == 1
            assert (
                articles[0]["word_count"] == 8
            )  # "This is a test excerpt with five words" (8 words)
        finally:
            os.unlink(temp_file)
