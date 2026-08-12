from contextlib import nullcontext
from threading import RLock

from sqlalchemy.orm import Session


_SQLITE_SECTION_TRANSACTION_MUTEX = RLock()


def section_transaction_guard(db: Session):
    """Serialize section-sensitive transactions in local SQLite.

    PostgreSQL callers rely on their ``FOR UPDATE`` section-row locks. SQLite
    ignores that syntax, so every repository that follows the shared
    section-first lock order uses one re-entrant in-process mutex instead.
    """

    if db.get_bind().dialect.name == "sqlite":
        return _SQLITE_SECTION_TRANSACTION_MUTEX

    return nullcontext()
