from contextlib import contextmanager

from sqlalchemy.orm import Session


@contextmanager
def transaction(session: Session):
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise