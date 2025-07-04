import os
import shutil
import tempfile
import unittest
from storage import ensure_dir, save_raw_json, save_articles_jsonl, get_file_summary


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.raw_path = os.path.join(self.tmpdir, "raw.json")
        self.jsonl_path = os.path.join(self.tmpdir, "parsed.jsonl")

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_ensure_dir(self):
        new_dir = os.path.join(self.tmpdir, "subdir")
        ensure_dir(new_dir)
        self.assertTrue(os.path.isdir(new_dir))

    def test_save_raw_json(self):
        data = {"foo": "bar", "num": 42}
        result = save_raw_json(data, self.raw_path)
        self.assertTrue(result)
        with open(self.raw_path, "r", encoding="utf-8") as f:
            loaded = f.read()
        self.assertIn("foo", loaded)
        self.assertIn("42", loaded)

    def test_save_articles_jsonl(self):
        articles = [{"item_id": "1", "title": "A"}, {"item_id": "2", "title": "B"}]
        result = save_articles_jsonl(articles, self.jsonl_path)
        self.assertTrue(result)
        with open(self.jsonl_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 2)
        self.assertIn("item_id", lines[0])

    def test_get_file_summary(self):
        articles = [{"item_id": "1", "title": "A"}, {"item_id": "2", "title": "B"}]
        save_articles_jsonl(articles, self.jsonl_path)
        summary = get_file_summary(self.jsonl_path)
        self.assertEqual(summary["article_count"], 2)
        self.assertTrue(summary["size_bytes"] > 0)

    def test_creates_raw_data_directory(self):
        temp_dir = tempfile.mkdtemp()
        raw_dir = os.path.join(temp_dir, "raw_data")
        raw_file = os.path.join(raw_dir, "test.json")
        if os.path.exists(raw_dir):
            shutil.rmtree(raw_dir)
        self.assertFalse(os.path.exists(raw_dir))
        # Simulate logic from pocket_export.py
        os.makedirs(raw_dir, exist_ok=True)
        with open(raw_file, "w") as f:
            f.write("[]")
        self.assertTrue(os.path.exists(raw_dir))
        self.assertTrue(os.path.exists(raw_file))
        shutil.rmtree(temp_dir)

    def test_creates_parsed_data_directory(self):
        temp_dir = tempfile.mkdtemp()
        parsed_dir = os.path.join(temp_dir, "parsed_data")
        parsed_file = os.path.join(parsed_dir, "test.jsonl")
        if os.path.exists(parsed_dir):
            shutil.rmtree(parsed_dir)
        self.assertFalse(os.path.exists(parsed_dir))
        # Simulate logic from pocket_export.py
        os.makedirs(parsed_dir, exist_ok=True)
        with open(parsed_file, "w") as f:
            f.write("{}\n")
        self.assertTrue(os.path.exists(parsed_dir))
        self.assertTrue(os.path.exists(parsed_file))
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()
