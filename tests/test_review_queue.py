import unittest
from pathlib import Path

from jobbot.review_queue import display_location, extract_role_sections, render_markdown, write_daily_queue
from tests.helpers import cleanup_workspace_tmp, workspace_tmp_dir


class ReviewQueueTests(unittest.TestCase):
    def test_markdown_groups_jobs_and_includes_reasons(self):
        jobs = [
            {
                "bucket": "apply",
                "title": "Product Owner",
                "company": "Example",
                "location": "Remote",
                "total_score": 88,
                "sponsorship_signal": "positive",
                "apply_url": "https://example.com/apply",
                "score_reasons": ["Role match: product owner.", "Posting includes a positive visa/sponsorship signal."],
            }
        ]
        markdown = render_markdown(jobs, "2026-04-28")
        self.assertIn("## Apply", markdown)
        self.assertIn("Product Owner - Example", markdown)
        self.assertIn("https://example.com/apply", markdown)
        self.assertIn("Overview:", markdown)
        self.assertIn("Key responsibilities:", markdown)
        self.assertIn("positive visa", markdown)

    def test_queue_writes_markdown_and_csv(self):
        jobs = [
            {
                "bucket": "maybe",
                "title": "Business Analyst",
                "company": "Example",
                "location": "New York, NY",
                "total_score": 70,
                "sponsorship_signal": "unknown",
                "apply_url": "https://example.com/ba",
                "status": "found",
                "score_reasons": ["No clear sponsorship language found."],
            }
        ]
        tmp = workspace_tmp_dir()
        try:
            result = write_daily_queue(jobs=jobs, output_dir=tmp, date_slug="2026-04-28")
            self.assertTrue(Path(result["markdown"]).exists())
            self.assertTrue(Path(result["csv"]).exists())
            self.assertTrue(Path(result["summary"]).exists())
            self.assertIn("Business Analyst", Path(result["markdown"]).read_text(encoding="utf-8"))
            csv_text = Path(result["csv"]).read_text(encoding="utf-8")
            self.assertIn("role_overview", csv_text)
            self.assertIn("key_responsibilities", csv_text)
            self.assertIn("full_description", csv_text)
            self.assertIn("Pipeline Summary", Path(result["markdown"]).read_text(encoding="utf-8"))
        finally:
            cleanup_workspace_tmp(tmp)

    def test_extract_role_sections_skips_company_boilerplate(self):
        sections = extract_role_sections(
            {
                "description": (
                    "Who we are About Stripe Stripe is a financial infrastructure platform for businesses. "
                    "About the Role We are seeking a Technical Program Manager to drive payments programs across product and engineering teams. "
                    "What you'll do Lead cross-functional planning, manage dependencies, and define delivery milestones. "
                    "Who you are You have program management experience and strong stakeholder skills."
                )
            }
        )
        self.assertIn("Technical Program Manager", sections["role_overview"])
        self.assertIn("Lead cross-functional", sections["key_responsibilities"])
        self.assertIn("program management experience", sections["qualifications"])
        self.assertNotIn("financial infrastructure platform", sections["role_overview"])

    def test_csv_role_fields_are_not_character_truncated(self):
        long_role = " ".join([f"Responsibility sentence {i} drives roadmap and stakeholder alignment." for i in range(80)])
        sections = extract_role_sections(
            {
                "description": (
                    "About Us Company boilerplate should not dominate. "
                    f"About the Role {long_role} "
                    "What you'll do Lead product discovery and coordinate delivery."
                )
            }
        )
        self.assertFalse(sections["role_overview"].endswith("..."))
        self.assertIn("Responsibility sentence 79", sections["role_overview"])

    def test_render_markdown_omits_skip_bucket_from_review_queue(self):
        markdown = render_markdown(
            [
                {
                    "bucket": "skip",
                    "title": "Product Manager",
                    "company": "Outside US",
                    "location": "London",
                    "total_score": 58,
                    "sponsorship_signal": "unknown",
                    "apply_url": "https://example.com/london",
                    "score_reasons": ["Location appears outside the US target market."],
                }
            ],
            "2026-04-28",
        )
        self.assertNotIn("## Skip", markdown)
        self.assertNotIn("Outside US", markdown)

    def test_display_location_removes_non_us_cities_from_mixed_location(self):
        location = display_location(
            {
                "location": "United States, United Kingdom, Canada, London, Toronto, New York, Montreal"
            }
        )
        self.assertIn("United States", location)
        self.assertIn("New York", location)
        self.assertNotIn("London", location)
        self.assertNotIn("Toronto", location)


if __name__ == "__main__":
    unittest.main()
