import unittest
from pathlib import Path

from jobbot.db import connect, init_db, list_jobs, upsert_job
from tests.helpers import cleanup_workspace_tmp, workspace_tmp_dir


class DedupeTests(unittest.TestCase):
    def test_same_hash_updates_existing_row(self):
        tmp = workspace_tmp_dir()
        try:
            db_path = tmp / "jobs.sqlite3"
            init_db(db_path)
            job = {
                "source": "sample",
                "source_company_key": "sample",
                "company": "Example",
                "title": "Product Manager",
                "location": "Remote",
                "apply_url": "https://example.com/job",
                "description": "Product Manager role with H-1B sponsorship.",
            }
            with connect(db_path) as db:
                self.assertEqual(upsert_job(db, job), "inserted")
                updated = dict(job)
                updated["description"] = "Updated Product Manager role with H-1B sponsorship."
                self.assertEqual(upsert_job(db, updated), "updated")
            self.assertEqual(len(list_jobs(db_path=db_path)), 1)
        finally:
            cleanup_workspace_tmp(tmp)

    def test_different_apply_url_creates_new_row(self):
        tmp = workspace_tmp_dir()
        try:
            db_path = tmp / "jobs.sqlite3"
            init_db(db_path)
            job = {
                "source": "sample",
                "source_company_key": "sample",
                "company": "Example",
                "title": "Product Manager",
                "location": "Remote",
                "apply_url": "https://example.com/job-1",
                "description": "Product Manager role.",
            }
            with connect(db_path) as db:
                self.assertEqual(upsert_job(db, job), "inserted")
                second = dict(job)
                second["apply_url"] = "https://example.com/job-2"
                self.assertEqual(upsert_job(db, second), "inserted")
            self.assertEqual(len(list_jobs(db_path=db_path)), 2)
        finally:
            cleanup_workspace_tmp(tmp)


if __name__ == "__main__":
    unittest.main()
