import os
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# ---------------------------------------------------------
# Database location
# ---------------------------------------------------------

# During normal development:
#     database lives in the project folder.
#
# When packaged with PyInstaller:
#     database lives in the user's Windows LocalAppData folder.
#
# This prevents the database from being stored inside the
# PyInstaller application files.

BASE_DIR = Path(__file__).resolve().parents[2]


def get_database_path() -> Path:
    # Explicit database override.
    # Useful during development/testing.
    database_file = os.getenv("PERFUME_POS_DATABASE")

    if database_file:
        path = Path(database_file)

        if not path.is_absolute():
            path = BASE_DIR / path

        return path

    # Packaged Windows application
    if getattr(sys, "frozen", False):
        app_data = (
            Path(os.environ.get("LOCALAPPDATA", Path.home()))
            / "SHOPFAVE"
        )

        app_data.mkdir(
            parents=True,
            exist_ok=True,
        )

        return app_data / "perfumepos.db"

    # Normal development
    return BASE_DIR / "perfumepos.db"


DATABASE_PATH = get_database_path()

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


# ---------------------------------------------------------
# SQLAlchemy engine
# ---------------------------------------------------------

engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
)


# ---------------------------------------------------------
# Session factory
# ---------------------------------------------------------

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)