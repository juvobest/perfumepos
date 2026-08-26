from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User


class AuthenticationError(Exception):
    """Raised when authentication fails."""


def authenticate_user(
    session: Session,
    username: str,
    password: str,
) -> User:
    """Authenticate a user and return the user record."""

    user = session.scalar(
        select(User).where(User.username == username)
    )

    if user is None:
        raise AuthenticationError("Invalid username or password.")

    if not user.is_active:
        raise AuthenticationError("This account is inactive.")

    if not verify_password(password, user.password_hash):
        raise AuthenticationError("Invalid username or password.")

    return user