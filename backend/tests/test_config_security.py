import os
import subprocess
import sys
import unittest
from pathlib import Path

from app.config import DEVELOPMENT_JWT_SECRET, EXAMPLE_JWT_SECRET, Settings


class ConfigSecurityTestCase(unittest.TestCase):
    def test_development_allows_the_local_fallback(self):
        config = Settings(
            environment="development", jwt_secret_key=DEVELOPMENT_JWT_SECRET
        )

        self.assertEqual(config.jwt_secret_key, DEVELOPMENT_JWT_SECRET)

    def test_non_development_rejects_empty_and_public_secrets(self):
        for environment in ("production", "staging", "test", "", " Production "):
            for secret in (
                "",
                "   ",
                DEVELOPMENT_JWT_SECRET,
                EXAMPLE_JWT_SECRET,
                f" {DEVELOPMENT_JWT_SECRET} ",
            ):
                with self.subTest(environment=environment, secret=secret):
                    with self.assertRaisesRegex(ValueError, "JWT_SECRET_KEY"):
                        Settings(environment=environment, jwt_secret_key=secret)

    def test_non_development_accepts_a_configured_private_secret(self):
        secret = "unit-test-configured-key-with-sufficient-randomness-6c4bd752"

        config = Settings(environment="production", jwt_secret_key=secret)

        self.assertEqual(config.jwt_secret_key, secret)

    def test_missing_production_secret_stops_configuration_import(self):
        environment = os.environ.copy()
        environment["ENVIRONMENT"] = "production"
        environment.pop("JWT_SECRET_KEY", None)
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from unittest.mock import patch; "
                "guard = patch('dotenv.load_dotenv'); "
                "guard.start(); import app.config",
            ],
            cwd=Path(__file__).resolve().parents[1],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("JWT_SECRET_KEY", result.stderr)


if __name__ == "__main__":
    unittest.main()
