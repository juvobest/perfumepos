from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User


class UserService:
    def __init__(self, session: Session):
        self.session = session

    def list_users(self) -> list[User]:
        statement = (
            select(User)
            .order_by(User.id)
        )

        return list(
            self.session.scalars(statement).all()
        )

    def get_by_id(
        self,
        user_id: int,
    ) -> User | None:
        return self.session.get(
            User,
            user_id,
        )

    def get_by_username(
        self,
        username: str,
    ) -> User | None:
        statement = select(User).where(
            User.username == username
        )

        return self.session.scalar(statement)

    def create_user(
        self,
        username: str,
        full_name: str,
        password: str,
        role_name: str,
    ) -> User:
        username = username.strip()
        full_name = full_name.strip()

        if not username:
            raise ValueError(
                "Username is required."
            )

        if not full_name:
            raise ValueError(
                "Full name is required."
            )

        if not password:
            raise ValueError(
                "Password is required."
            )

        if len(password) < 8:
            raise ValueError(
                "Password must be at least 8 characters."
            )

        existing_user = self.get_by_username(
            username
        )

        if existing_user is not None:
            raise ValueError(
                "Username already exists."
            )

        role = self.session.scalar(
            select(Role).where(
                Role.name == role_name
            )
        )

        if role is None:
            raise ValueError(
                "Role not found."
            )

        user = User(
            username=username,
            full_name=full_name,
            password_hash=hash_password(
                password
            ),
            is_active=True,
        )

        user.roles.append(role)

        self.session.add(user)
        self.session.flush()

        return user

    def update_user(
        self,
        user_id: int,
        full_name: str | None = None,
        role_name: str | None = None,
        password: str | None = None,
    ) -> User:
        user = self.get_by_id(user_id)

        if user is None:
            raise ValueError(
                "User not found."
            )

        if full_name is not None:
            full_name = full_name.strip()

            if not full_name:
                raise ValueError(
                    "Full name is required."
                )

            user.full_name = full_name

        if role_name is not None:
            role = self.session.scalar(
                select(Role).where(
                    Role.name == role_name
                )
            )

            if role is None:
                raise ValueError(
                    "Role not found."
                )

            user.roles = [role]

        if password is not None:
            if len(password) < 8:
                raise ValueError(
                    "Password must be at least 8 characters."
                )

            user.password_hash = hash_password(
                password
            )

        self.session.flush()

        return user

    def deactivate_user(
        self,
        user_id: int,
    ) -> User:
        user = self.get_by_id(user_id)

        if user is None:
            raise ValueError(
                "User not found."
            )

        user.is_active = False

        self.session.flush()

        return user

    def activate_user(
        self,
        user_id: int,
    ) -> User:
        user = self.get_by_id(user_id)

        if user is None:
            raise ValueError(
                "User not found."
            )

        user.is_active = True

        self.session.flush()

        return user

    def list_roles(self) -> list[Role]:
        statement = (
            select(Role)
            .order_by(Role.id)
        )

        return list(
            self.session.scalars(statement).all()
        )