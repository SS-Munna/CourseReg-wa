import unittest

from app.database import get_database_status


class DatabaseStatusTestCase(unittest.TestCase):
    def test_status_response_does_not_expose_credentials(self):
        response = get_database_status()

        self.assertEqual(response["status"], "connected")
        self.assertEqual(
            response["database"],
            "SQLAlchemy relational database",
        )
        self.assertNotIn("database_url", response)
        self.assertNotIn("postgresql://", str(response).lower())
        self.assertNotIn("password", str(response).lower())


if __name__ == "__main__":
    unittest.main()
