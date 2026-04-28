import unittest

from jobbot.scoring import score_job


class ScoringTests(unittest.TestCase):
    def test_product_owner_remote_h1b_positive_scores_apply(self):
        result = score_job(
            {
                "title": "Product Owner, Customer Platforms",
                "location": "Remote - United States / Boston, MA",
                "description": "Product Owner role with requirements, user stories, UAT, launch readiness, and H-1B visa sponsorship.",
            }
        )
        self.assertEqual(result["bucket"], "apply")
        self.assertEqual(result["sponsorship_signal"], "positive")

    def test_business_analyst_without_sponsorship_scores_skip(self):
        result = score_job(
            {
                "title": "Business Systems Analyst",
                "location": "Hybrid - New York, NY",
                "description": "Must be authorized to work in the US without sponsorship.",
            }
        )
        self.assertEqual(result["bucket"], "skip")
        self.assertEqual(result["sponsorship_signal"], "negative")

    def test_unclear_sponsorship_is_not_rejected(self):
        result = score_job(
            {
                "title": "Associate Product Manager",
                "location": "Boston, MA / Hybrid",
                "description": "Work with customer research, analytics, agile engineering teams, and roadmap planning.",
            }
        )
        self.assertIn(result["bucket"], {"apply", "maybe"})
        self.assertEqual(result["sponsorship_signal"], "unknown")

    def test_director_roles_are_penalized(self):
        result = score_job(
            {
                "title": "Director of Product Management",
                "location": "Remote - United States",
                "description": "Product management leadership role with H-1B sponsorship.",
            }
        )
        self.assertLess(result["seniority_score"], 60)

    def test_engineering_title_is_excluded_even_with_product_keywords(self):
        result = score_job(
            {
                "title": "Senior Software Engineer, Customer Activation",
                "location": "Remote - United States",
                "description": "Work closely with product managers on roadmap, customer activation, and product strategy.",
            }
        )
        self.assertEqual(result["bucket"], "skip")
        self.assertEqual(result["role_score"], 0)

    def test_data_scientist_title_is_excluded(self):
        result = score_job(
            {
                "title": "Senior Data Scientist, Product Analytics",
                "location": "New York, NY",
                "description": "Partner with product managers and business analysts on experimentation.",
            }
        )
        self.assertEqual(result["bucket"], "skip")
        self.assertEqual(result["role_score"], 0)

    def test_non_us_location_is_skipped(self):
        result = score_job(
            {
                "title": "Product Manager",
                "location": "China",
                "description": "Product Manager role with H-1B sponsorship and remote collaboration.",
            }
        )
        self.assertEqual(result["bucket"], "skip")
        self.assertEqual(result["location_score"], 0)

    def test_role_title_uses_single_longest_match(self):
        result = score_job(
            {
                "title": "Technical Program Manager, Product Security",
                "location": "Remote - United States",
                "description": "Responsible for roadmap, stakeholders, and H-1B visa sponsorship.",
            }
        )
        self.assertEqual(result["role_score"], 85)
        self.assertIn("technical program manager", " ".join(result["score_reasons"]).lower())

    def test_eeo_us_citizen_language_does_not_force_skip(self):
        result = score_job(
            {
                "title": "Product Manager",
                "location": "Remote - United States",
                "description": "We welcome U.S. citizens, permanent residents, visa holders, and applicants from all backgrounds.",
            }
        )
        self.assertNotEqual(result["sponsorship_signal"], "negative")
        self.assertNotEqual(result["bucket"], "skip")

    def test_required_us_citizenship_still_skips(self):
        result = score_job(
            {
                "title": "Product Manager",
                "location": "Remote - United States",
                "description": "Applicants must be U.S. citizens due to contract requirements.",
            }
        )
        self.assertEqual(result["sponsorship_signal"], "negative")
        self.assertEqual(result["bucket"], "skip")


if __name__ == "__main__":
    unittest.main()
