import unittest
from datetime import timedelta
from uuid import uuid4

from app.security import (
    AccessTokenError,
    create_access_token,
    decode_access_token,
    get_user_id_from_access_token,
)


class JwtSecurityTestCase(unittest.TestCase):
    def test_valid_access_token_contains_required_claims(self):
        user_id = uuid4()
        token = create_access_token(user_id)
        payload = decode_access_token(token)

        self.assertEqual(payload["sub"], str(user_id))
        self.assertIn("iat", payload)
        self.assertIn("exp", payload)
        self.assertEqual(
            get_user_id_from_access_token(token),
            user_id,
        )

    def test_expired_access_token_is_rejected(self):
        token = create_access_token(
            uuid4(),
            expires_delta=timedelta(seconds=-1),
        )

        with self.assertRaises(AccessTokenError):
            decode_access_token(token)

    def test_tampered_access_token_is_rejected(self):
        token_parts = create_access_token(uuid4()).split(".")
        signature = token_parts[2]
        replacement = "A" if signature[0] != "A" else "B"
        token_parts[2] = replacement + signature[1:]
        tampered_token = ".".join(token_parts)

        with self.assertRaises(AccessTokenError):
            decode_access_token(tampered_token)

    def test_malformed_access_token_is_rejected(self):
        with self.assertRaises(AccessTokenError):
            decode_access_token("not-a-valid-jwt")

    def test_old_demo_token_is_rejected(self):
        with self.assertRaises(AccessTokenError):
            decode_access_token("demo-token-7")

    def test_non_uuid_subject_is_rejected(self):
        token = create_access_token("7")  # type: ignore[arg-type]

        with self.assertRaises(AccessTokenError):
            get_user_id_from_access_token(token)


if __name__ == "__main__":
    unittest.main()
