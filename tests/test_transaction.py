from sqlalchemy import text

import pytest

from app.database.connection import SessionLocal
from app.database.transaction import transaction


def test_transaction_commits_successfully():
    with SessionLocal() as session:
        with transaction(session):
            result = session.execute(
                text("SELECT 1")
            )

            assert result.scalar() == 1


def test_transaction_rolls_back_on_error():
    with SessionLocal() as session:
        with pytest.raises(
            ValueError,
            match="Test transaction failure.",
        ):
            with transaction(session):
                raise ValueError(
                    "Test transaction failure."
                )