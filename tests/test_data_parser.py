import unittest
from data_parser import parse_pocket_article

from datetime import datetime


class TestParsePocketArticle(unittest.TestCase):
    def test_extracts_required_fields(self):
        raw = {
            "item_id": "123",
            "resolved_url": "https://example.com",
            "resolved_title": "Example Title",
            "excerpt": "Summary",
            "tags": {"tag1": {}, "tag2": {}},
            "status": "0",
            "time_added": "1625097600",  # 2021-07-01T00:00:00Z
            "word_count": "500",
        }
        article = parse_pocket_article(raw)
        self.assertEqual(article.item_id, "123")
        self.assertEqual(article.resolved_url, "https://example.com")
        self.assertEqual(article.resolved_title, "Example Title")
        self.assertEqual(article.excerpt, "Summary")
        self.assertEqual(article.tags, {"tag1": {}, "tag2": {}})
        self.assertEqual(article.status, "0")
        self.assertEqual(article.time_added, "2021-07-01T00:00:00Z")
        self.assertEqual(article.word_count, 500)
        self.assertEqual(article.original["item_id"], "123")

    def test_handles_missing_fields(self):
        raw = {"item_id": "456"}
        article = parse_pocket_article(raw)
        self.assertEqual(article.item_id, "456")
        self.assertIsNone(article.resolved_url)
        self.assertIsNone(article.resolved_title)
        self.assertIsNone(article.excerpt)
        self.assertEqual(article.tags, {})
        self.assertIsNone(article.status)
        self.assertIsNone(article.time_added)
        self.assertIsNone(article.word_count)

    def test_handles_null_fields(self):
        raw = {
            "item_id": None,
            "resolved_url": None,
            "resolved_title": None,
            "excerpt": None,
            "tags": None,
            "status": None,
            "time_added": None,
            "word_count": None,
        }
        article = parse_pocket_article(raw)
        self.assertIsNone(article.item_id)
        self.assertIsNone(article.resolved_url)
        self.assertIsNone(article.resolved_title)
        self.assertIsNone(article.excerpt)
        self.assertEqual(article.tags, {})
        self.assertIsNone(article.status)
        self.assertIsNone(article.time_added)
        self.assertIsNone(article.word_count)

    def test_normalizes_timestamp(self):
        raw = {"item_id": "789", "time_added": "1700000000"}
        article = parse_pocket_article(raw)
        dt = datetime.utcfromtimestamp(1700000000).isoformat() + "Z"
        self.assertEqual(article.time_added, dt)

    def test_handles_invalid_timestamp(self):
        raw = {"item_id": "101", "time_added": "not_a_timestamp"}
        article = parse_pocket_article(raw)
        self.assertIsNone(article.time_added)

    def test_handles_non_dict_tags(self):
        raw = {"item_id": "102", "tags": "not_a_dict"}
        article = parse_pocket_article(raw)
        self.assertEqual(article.tags, {})

    def test_handles_word_count_as_int(self):
        raw = {"item_id": "103", "word_count": 42}
        article = parse_pocket_article(raw)
        self.assertEqual(article.word_count, 42)

    def test_handles_word_count_invalid(self):
        raw = {"item_id": "104", "word_count": "not_a_number"}
        article = parse_pocket_article(raw)
        self.assertIsNone(article.word_count)


if __name__ == "__main__":
    unittest.main()
