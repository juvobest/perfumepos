import sys

from PySide6.QtWidgets import QApplication
from sqlalchemy import select

from app.database.init_db import init_database
from app.database.connection import SessionLocal
from app.database.seed import seed_permissions, seed_roles
from app.models.business_settings import BusinessSettings
from app.ui.login.login_window import LoginWindow
from app.ui.setup.setup_window import SetupWindow


def setup_required() -> bool:
    """
    Return True when SHOPFAVE has not been configured yet.
    """

    with SessionLocal() as session:
        settings = session.scalar(
            select(BusinessSettings)
        )

        return settings is None


def main():
    # Create all database tables.
    init_database()

    # Make sure permissions and roles exist.
    # This is especially important for a fresh installation.
    seed_permissions()
    seed_roles()

    app = QApplication(sys.argv)

    if setup_required():
        window = SetupWindow()
    else:
        window = LoginWindow()

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()