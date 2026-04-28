import unittest

from jobbot.ingest import normalize_ashby_job, normalize_greenhouse_job, normalize_lever_job


class IngestNormalizationTests(unittest.TestCase):
    def test_greenhouse_payload_normalizes(self):
        job = normalize_greenhouse_job(
            {
                "title": "Product Manager",
                "location": {"name": "Remote"},
                "absolute_url": "https://example.com/gh",
                "content": "<p>Own roadmap &amp; UAT.</p>",
                "updated_at": "2026-04-27",
            },
            {"company": "Example", "key": "example"},
        )
        self.assertEqual(job["source"], "greenhouse")
        self.assertEqual(job["location"], "Remote")
        self.assertEqual(job["description"], "Own roadmap & UAT.")

    def test_lever_payload_normalizes(self):
        job = normalize_lever_job(
            {
                "text": "Business Analyst",
                "categories": {"location": "New York, NY"},
                "hostedUrl": "https://example.com/lever",
                "description": "Gather requirements.",
                "lists": [{"content": "<b>Use Jira</b>"}],
                "createdAt": 123,
            },
            {"company": "Example", "key": "example"},
        )
        self.assertEqual(job["source"], "lever")
        self.assertEqual(job["title"], "Business Analyst")
        self.assertIn("Use Jira", job["description"])

    def test_ashby_payload_normalizes_missing_optional_fields(self):
        job = normalize_ashby_job(
            {
                "title": "Product Analyst",
                "descriptionHtml": "<p>Analyze product data.</p>",
            },
            {"company": "Example", "key": "example"},
        )
        self.assertEqual(job["source"], "ashby")
        self.assertEqual(job["location"], "")
        self.assertEqual(job["description"], "Analyze product data.")


if __name__ == "__main__":
    unittest.main()
