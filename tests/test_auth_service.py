import pytest

from app.core.security import hash_password
from app.models.user import User
from app.services.auth_service import (
    AuthenticationError,
    authenticate_user,
)


class FakeSession:
    def __init__(self, user):
        self.user = user

    def scalar(self, statement):
        return self.user


def test_authenticate_user_success():
    password = "CorrectPassword123!"

    user = User(
        username="admin",
        full_name="Test Admin",
        password_hash=hash_password(password),
        is_active=True,
    )

    session = FakeSession(user)

    authenticated_user = authenticate_user(
        session,
        "admin",
        password,
    )

    assert authenticated_user.username == "admin"


def test_authenticate_user_wrong_password():
    password = "CorrectPassword123!"

    user = User(
        username="admin",
        full_name="Test Admin",
        password_hash=hash_password(password),
        is_active=True,
    )

    session = FakeSession(user)

    with pytest.raises(AuthenticationError):
        authenticate_user(
            session,
            "admin",
            "WrongPassword123!",
        )


def test_authenticate_inactive_user():
    password = "CorrectPassword123!"

    user = User(
        username="admin",
        full_name="Test Admin",
        password_hash=hash_password(password),
        is_active=False,
    )

    session = FakeSession(user)

    with pytest.raises(AuthenticationError):
        authenticate_user(
            session,
            "admin",
            password,
        )