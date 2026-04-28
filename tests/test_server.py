import unittest

from jobbot.server import autofill_profile


class ServerTests(unittest.TestCase):
    def test_autofill_profile_returns_extension_field_names(self):
        profile = autofill_profile()
        self.assertIn("fullName", profile)
        self.assertIn("workAuthorization", profile)
        self.assertIn("salaryExpectation", profile)
        self.assertIn("commonAnswers", profile)
        self.assertIn("sponsorship", profile["commonAnswers"])


if __name__ == "__main__":
    unittest.main()
