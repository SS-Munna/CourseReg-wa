from collections.abc import Mapping

from sqlalchemy import Engine, text


POSTGRESQL_ADVISORY_LOCK_ID = 1_129_334_356
POSTGRESQL_INTEGER_TYPES = {"smallint", "integer", "bigint"}


def _postgresql_user_columns(connection) -> Mapping[str, str]:
    rows = connection.execute(
        text(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'users'
            """
        )
    ).all()
    return dict(rows)


def _migrate_legacy_postgresql_users(connection) -> None:
    columns = _postgresql_user_columns(connection)

    if not columns:
        return

    user_id_type = columns.get("id")

    if user_id_type in POSTGRESQL_INTEGER_TYPES:
        connection.execute(
            text(
                """
                ALTER TABLE users
                ALTER COLUMN id DROP DEFAULT
                """
            )
        )
        connection.execute(
            text(
                """
                ALTER TABLE users
                ALTER COLUMN id TYPE UUID
                USING (
                    LPAD(TO_HEX(id::bigint), 32, '0')::uuid
                )
                """
            )
        )
    elif user_id_type != "uuid":
        raise RuntimeError(
            "Unsupported users.id database type: "
            f"{user_id_type or 'missing'}"
        )

    if "full_name" not in columns:
        if "name" not in columns:
            raise RuntimeError(
                "The users table has neither name nor full_name."
            )
        connection.execute(
            text(
                """
                ALTER TABLE users
                RENAME COLUMN name TO full_name
                """
            )
        )

    connection.execute(
        text(
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS account_status VARCHAR(50)
            """
        )
    )
    connection.execute(
        text(
            """
            UPDATE users
            SET account_status = 'active'
            WHERE account_status IS NULL
            """
        )
    )
    connection.execute(
        text(
            """
            ALTER TABLE users
            ALTER COLUMN account_status SET NOT NULL
            """
        )
    )
    connection.execute(
        text(
            """
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS created_at
                TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
            ADD COLUMN IF NOT EXISTS updated_at
                TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
            """
        )
    )


def run_startup_schema_migrations(database_engine: Engine) -> None:
    if database_engine.dialect.name != "postgresql":
        return

    with database_engine.begin() as connection:
        connection.execute(
            text(
                "SELECT pg_advisory_xact_lock(:migration_lock_id)"
            ),
            {"migration_lock_id": POSTGRESQL_ADVISORY_LOCK_ID},
        )
        _migrate_legacy_postgresql_users(connection)
