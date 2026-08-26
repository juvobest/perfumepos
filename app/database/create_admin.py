import getpass

from sqlalchemy import select

from app.core.security import hash_password
from app.database.connection import SessionLocal
from app.models.role import Role
from app.models.user import User


def create_admin() -> None:
    username = input("Admin username: ").strip()
    full_name = input("Admin full name: ").strip()
    password = getpass.getpass("Admin password: ")
    confirm_password = getpass.getpass("Confirm password: ")

    if not username:
        print("Username cannot be empty.")
        return

    if not full_name:
        print("Full name cannot be empty.")
        return

    if not password:
        print("Password cannot be empty.")
        return

    if password != confirm_password:
        print("Passwords do not match.")
        return

    with SessionLocal() as session:
        existing_user = session.scalar(
            select(User).where(User.username == username)
        )

        if existing_user is not None:
            print(f"User '{username}' already exists.")
            return

        admin_role = session.scalar(
            select(Role).where(Role.name == "Admin")
        )

        if admin_role is None:
            print("Admin role does not exist. Run the seed script first.")
            return

        admin_user = User(
            username=username,
            full_name=full_name,
            password_hash=hash_password(password),
            is_active=True,
        )

        admin_user.roles.append(admin_role)

        session.add(admin_user)
        session.commit()

        print(f"Admin user '{username}' created successfully.")


if __name__ == "__main__":
    create_admin()