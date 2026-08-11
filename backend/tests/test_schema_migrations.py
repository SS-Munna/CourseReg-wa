import unittest
from unittest.mock import MagicMock, patch

from app import database
from app.schema_migrations import (
    POSTGRESQL_ADVISORY_LOCK_ID,
    _migrate_legacy_postgresql_users,
    run_startup_schema_migrations,
)


def normalized_sql(statement) -> str:
    return " ".join(str(statement).split())


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class LegacyUserMigrationTestCase(unittest.TestCase):
    def make_connection(self, columns):
        connection = MagicMock()
        connection.execute.side_effect = [
            FakeResult(columns),
            *[MagicMock() for _ in range(7)],
        ]
        return connection

    def test_integer_user_schema_is_upgraded_without_deleting_rows(self):
        connection = self.make_connection(
            [
                ("id", "integer"),
                ("name", "character varying"),
                ("email", "character varying"),
            ]
        )

        _migrate_legacy_postgresql_users(connection)

        statements = [
            normalized_sql(call.args[0])
            for call in connection.execute.call_args_list
        ]
        combined_sql = "\n".join(statements)

        self.assertIn("ALTER COLUMN id DROP DEFAULT", combined_sql)
        self.assertIn("ALTER COLUMN id TYPE UUID", combined_sql)
        self.assertIn(
            "LPAD(TO_HEX(id::bigint), 32, '0')::uuid",
            combined_sql,
        )
        self.assertIn("RENAME COLUMN name TO full_name", combined_sql)
        self.assertIn(
            "ADD COLUMN IF NOT EXISTS account_status",
            combined_sql,
        )
        self.assertIn("SET account_status = 'active'", combined_sql)
        self.assertIn(
            "ALTER COLUMN account_status SET NOT NULL",
            combined_sql,
        )
        self.assertIn(
            "ADD COLUMN IF NOT EXISTS created_at",
            combined_sql,
        )
        self.assertNotIn("DELETE FROM users", combined_sql)
        self.assertNotIn("DROP TABLE users", combined_sql)

    def test_current_uuid_user_schema_does_not_rewrite_identifiers(self):
        connection = self.make_connection(
            [
                ("id", "uuid"),
                ("full_name", "character varying"),
                ("account_status", "character varying"),
                ("created_at", "timestamp with time zone"),
                ("updated_at", "timestamp with time zone"),
            ]
        )

        _migrate_legacy_postgresql_users(connection)

        combined_sql = "\n".join(
            normalized_sql(call.args[0])
            for call in connection.execute.call_args_list
        )
        self.assertNotIn("ALTER COLUMN id TYPE UUID", combined_sql)
        self.assertNotIn("RENAME COLUMN", combined_sql)

    def test_fresh_database_without_users_table_is_unchanged(self):
        connection = MagicMock()
        connection.execute.return_value = FakeResult([])

        _migrate_legacy_postgresql_users(connection)

        self.assertEqual(connection.execute.call_count, 1)

    def test_unexpected_user_identifier_type_fails_safely(self):
        connection = MagicMock()
        connection.execute.return_value = FakeResult(
            [
                ("id", "text"),
                ("full_name", "character varying"),
            ]
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "Unsupported users.id database type: text",
        ):
            _migrate_legacy_postgresql_users(connection)

    def test_non_postgresql_database_skips_startup_migration(self):
        sqlite_engine = MagicMock()
        sqlite_engine.dialect.name = "sqlite"

        run_startup_schema_migrations(sqlite_engine)

        sqlite_engine.begin.assert_not_called()

    def test_postgresql_migration_uses_transaction_and_advisory_lock(self):
        connection = MagicMock()
        connection.execute.side_effect = [MagicMock(), FakeResult([])]
        context_manager = MagicMock()
        context_manager.__enter__.return_value = connection
        postgresql_engine = MagicMock()
        postgresql_engine.dialect.name = "postgresql"
        postgresql_engine.begin.return_value = context_manager

        run_startup_schema_migrations(postgresql_engine)

        postgresql_engine.begin.assert_called_once_with()
        first_call = connection.execute.call_args_list[0]
        self.assertIn(
            "SELECT pg_advisory_xact_lock(:migration_lock_id)",
            normalized_sql(first_call.args[0]),
        )
        self.assertEqual(
            first_call.args[1],
            {"migration_lock_id": POSTGRESQL_ADVISORY_LOCK_ID},
        )

    def test_database_initialization_migrates_before_create_all(self):
        calls = []

        with (
            patch.object(
                database,
                "run_startup_schema_migrations",
                side_effect=lambda engine: calls.append("migrate"),
            ),
            patch.object(
                database.Base.metadata,
                "create_all",
                side_effect=lambda **kwargs: calls.append("create"),
            ),
        ):
            database.init_database()

        self.assertEqual(calls, ["migrate", "create"])


if __name__ == "__main__":
    unittest.main()
