import hashlib
import unittest

from argon2 import PasswordHasher

from app.security import (
    hash_password,
    verify_and_update_password,
    verify_password,
)


class PasswordSecurityTestCase(unittest.TestCase):
    def test_new_hashes_use_argon2id_with_unique_salts(self):
        first = hash_password("SecurePass123!")
        second = hash_password("SecurePass123!")

        self.assertTrue(first.startswith("$argon2id$"))
        self.assertTrue(second.startswith("$argon2id$"))
        self.assertNotEqual(first, second)
        self.assertTrue(verify_password("SecurePass123!", first))
        self.assertTrue(verify_password("SecurePass123!", second))
        self.assertFalse(verify_password("WrongPass123!", first))

    def test_long_unicode_passwords_are_not_truncated(self):
        password = "শ" * 40 + "A"
        stored_hash = hash_password(password)

        self.assertGreater(len(password.encode("utf-8")), 72)
        self.assertTrue(verify_password(password, stored_hash))
        self.assertFalse(verify_password("শ" * 40 + "B", stored_hash))

    def test_legacy_passwords_remain_verifiable(self):
        password = "LegacyPass123!"
        legacy_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

        self.assertTrue(verify_password(password, legacy_hash))
        self.assertFalse(verify_password("WrongPass123!", legacy_hash))

    def test_successful_legacy_verification_returns_argon2_upgrade(self):
        password = "LegacyPass123!"
        legacy_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

        valid, replacement = verify_and_update_password(password, legacy_hash)

        self.assertTrue(valid)
        self.assertTrue(replacement.startswith("$argon2id$"))
        self.assertTrue(verify_password(password, replacement))

    def test_wrong_legacy_password_never_returns_a_replacement(self):
        legacy_hash = hashlib.sha256(b"LegacyPass123!").hexdigest()

        self.assertEqual(
            verify_and_update_password("WrongPass123!", legacy_hash),
            (False, None),
        )

    def test_current_argon2_hash_does_not_need_an_update(self):
        stored_hash = hash_password("SecurePass123!")

        self.assertEqual(
            verify_and_update_password("SecurePass123!", stored_hash),
            (True, None),
        )
        self.assertEqual(
            verify_and_update_password("WrongPass123!", stored_hash),
            (False, None),
        )

    def test_old_argon2_parameters_are_upgraded_after_verification(self):
        password = "SecurePass123!"
        old_hash = PasswordHasher(
            time_cost=1, memory_cost=8192, parallelism=1,
        ).hash(password)

        valid, replacement = verify_and_update_password(password, old_hash)

        self.assertTrue(valid)
        self.assertNotEqual(replacement, old_hash)
        self.assertTrue(verify_password(password, replacement))

    def test_malformed_or_unknown_hashes_are_safe_authentication_failures(self):
        password = "LegacyPass123!"
        legacy_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
        for malformed in (
            "",
            "not-a-password-hash",
            legacy_hash.upper(),
            legacy_hash[:-1],
            legacy_hash + "\n",
            "$argon2id$broken",
            "$argon2id$v=19$m=65536,t=3,p=4$invalid$invalid",
        ):
            with self.subTest(stored_hash=malformed):
                self.assertFalse(verify_password(password, malformed))
                self.assertEqual(
                    verify_and_update_password(password, malformed),
                    (False, None),
                )


if __name__ == "__main__":
    unittest.main()
