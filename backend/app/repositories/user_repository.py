from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User
from app.security import hash_password, verify_and_update_password, verify_password


def find_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email.lower()).first()


def find_user_by_id(db: Session, user_id: UUID) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, name: str, email: str, password: str) -> User:
    user = User(
        full_name=name.strip(),
        email=email.lower(),
        password_hash=hash_password(password),
        role="student",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def verify_user_credentials(db: Session, email: str, password: str) -> User | None:
    user = find_user_by_email(db, email)

    if user is None:
        return None

    # Inactive accounts keep their existing 403 response without changing data.
    if user.account_status != "active":
        return user if verify_password(password, user.password_hash) else None

    valid, updated_hash = verify_and_update_password(password, user.password_hash)
    if not valid:
        return None

    if updated_hash is not None:
        user.password_hash = updated_hash
        db.commit()
        db.refresh(user)

    return user
