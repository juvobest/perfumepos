from datetime import datetime
from pathlib import Path
import shutil

from app.database.connection import DATABASE_PATH, engine


class BackupError(Exception):
    """Raised when a database backup or restore fails."""


def _validate_database_file(
    database_path: str | Path,
) -> None:
    database_path = Path(database_path)

    if not database_path.exists():
        raise BackupError(
            "The database file does not exist."
        )

    if database_path.stat().st_size <= 0:
        raise BackupError(
            "The database file is empty."
        )


def create_backup(
    destination: str | Path,
) -> Path:
    """
    Create a complete backup of the active SQLite database.
    """

    source = Path(DATABASE_PATH)
    destination = Path(destination)

    _validate_database_file(source)

    if source.resolve() == destination.resolve():
        raise BackupError(
            "The backup destination cannot be the active database."
        )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        # Release SQLAlchemy connections before copying.
        engine.dispose()

        # Copy directly to a temporary file first.
        temp_destination = destination.with_suffix(
            destination.suffix + ".tmp"
        )

        if temp_destination.exists():
            temp_destination.unlink()

        shutil.copyfile(
            source,
            temp_destination,
        )

        # Verify the temporary copy.
        if (
            not temp_destination.exists()
            or temp_destination.stat().st_size
            != source.stat().st_size
        ):
            raise BackupError(
                "The backup copy was incomplete."
            )

        # Replace the destination only after the copy
        # has completed successfully.
        if destination.exists():
            destination.unlink()

        temp_destination.replace(
            destination
        )

    except BackupError:
        raise

    except Exception as exc:
        raise BackupError(
            f"Backup failed: {exc}"
        ) from exc

    # Final verification.
    if (
        not destination.exists()
        or destination.stat().st_size <= 0
    ):
        raise BackupError(
            "The backup file was not created correctly."
        )

    return destination


def create_timestamped_backup(
    backup_directory: str | Path,
) -> Path:
    """
    Create a timestamped database backup.
    """

    backup_directory = Path(
        backup_directory
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    destination = (
        backup_directory
        / f"stockflow_backup_{timestamp}.db"
    )

    return create_backup(
        destination
    )


def restore_backup(
    backup_file: str | Path,
) -> Path:
    """
    Restore a database backup.

    A safety backup of the current database is created
    before the selected backup replaces it.
    """

    backup_file = Path(
        backup_file
    )

    database_file = Path(
        DATABASE_PATH
    )

    _validate_database_file(
        backup_file
    )

    if (
        backup_file.resolve()
        == database_file.resolve()
    ):
        raise BackupError(
            "The selected file is already the active database."
        )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    safety_backup = database_file.with_name(
        f"{database_file.stem}_before_restore_"
        f"{timestamp}.db"
    )

    try:
        engine.dispose()

        # Back up the current database first.
        shutil.copyfile(
            database_file,
            safety_backup,
        )

        # Verify safety backup.
        if (
            safety_backup.stat().st_size
            != database_file.stat().st_size
        ):
            raise BackupError(
                "The safety backup could not be created."
            )

        # Restore through a temporary file first.
        temp_database = database_file.with_suffix(
            database_file.suffix + ".restore"
        )

        if temp_database.exists():
            temp_database.unlink()

        shutil.copyfile(
            backup_file,
            temp_database,
        )

        if (
            temp_database.stat().st_size
            != backup_file.stat().st_size
        ):
            raise BackupError(
                "The restore copy was incomplete."
            )

        if database_file.exists():
            database_file.unlink()

        temp_database.replace(
            database_file
        )

    except BackupError:
        raise

    except Exception as exc:
        raise BackupError(
            f"Restore failed: {exc}"
        ) from exc

    return safety_backup