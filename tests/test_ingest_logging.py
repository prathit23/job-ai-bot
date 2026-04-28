import unittest

from jobbot.ingest import write_ingest_log


class IngestLoggingTests(unittest.TestCase):
    def test_write_ingest_log_returns_json_path(self):
        result = {
            "started_at": "2026-04-28T03:14:46.703974+00:00",
            "finished_at": "2026-04-28T03:15:00.137765+00:00",
            "source_count": 1,
            "fetched_count": 0,
            "inserted_count": 0,
            "updated_count": 0,
            "error_count": 1,
            "errors": ["Example: HTTP Error 404: Not Found"],
        }
        path = write_ingest_log(result)
        self.assertTrue(path.endswith(".json"))


if __name__ == "__main__":
    unittest.main()
