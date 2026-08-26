from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.services.backup_service import (
    BackupError,
    create_timestamped_backup,
    restore_backup,
)


class BackupWindow(QWidget):
    def __init__(self, user):
        super().__init__()

        self.user = user

        self.setWindowTitle(
            "StockFlow POS - Backup & Restore"
        )

        self.setMinimumSize(
            650,
            450,
        )

        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            40,
            35,
            40,
            35,
        )

        layout.setSpacing(20)

        title = QLabel(
            "Database Backup & Restore"
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                font-weight: bold;
            }
            """
        )

        description = QLabel(
            "Protect your StockFlow POS data by creating "
            "regular database backups. You can also restore "
            "the application from a previous backup."
        )

        description.setWordWrap(True)

        description.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
            }
            """
        )

        layout.addWidget(title)
        layout.addWidget(description)

        layout.addSpacing(15)

        # --------------------------------------------------
        # BACKUP
        # --------------------------------------------------

        backup_frame = QFrame()

        backup_frame.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        backup_layout = QVBoxLayout(
            backup_frame
        )

        backup_title = QLabel(
            "Create Database Backup"
        )

        backup_title.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
            }
            """
        )

        backup_text = QLabel(
            "Save a complete copy of the current database "
            "to a location of your choice."
        )

        backup_text.setWordWrap(True)

        backup_button = QPushButton(
            "CREATE BACKUP"
        )

        backup_button.setMinimumHeight(
            45
        )

        backup_button.clicked.connect(
            self.create_backup
        )

        backup_layout.addWidget(
            backup_title
        )

        backup_layout.addWidget(
            backup_text
        )

        backup_layout.addSpacing(
            10
        )

        backup_layout.addWidget(
            backup_button
        )

        layout.addWidget(
            backup_frame
        )

        # --------------------------------------------------
        # RESTORE
        # --------------------------------------------------

        restore_frame = QFrame()

        restore_frame.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        restore_layout = QVBoxLayout(
            restore_frame
        )

        restore_title = QLabel(
            "Restore Database"
        )

        restore_title.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
            }
            """
        )

        restore_text = QLabel(
            "Restore StockFlow POS from a previous database "
            "backup. The current database will automatically "
            "be backed up before restoration."
        )

        restore_text.setWordWrap(True)

        restore_button = QPushButton(
            "RESTORE BACKUP"
        )

        restore_button.setMinimumHeight(
            45
        )

        restore_button.clicked.connect(
            self.restore_backup
        )

        restore_layout.addWidget(
            restore_title
        )

        restore_layout.addWidget(
            restore_text
        )

        restore_layout.addSpacing(
            10
        )

        restore_layout.addWidget(
            restore_button
        )

        layout.addWidget(
            restore_frame
        )

        layout.addStretch()

        note = QLabel(
            "Important: Restoring a backup replaces the "
            "current database. A safety copy is created "
            "automatically before restoration."
        )

        note.setWordWrap(True)

        note.setStyleSheet(
            """
            QLabel {
                color: #8a4b08;
                font-weight: bold;
            }
            """
        )

        layout.addWidget(
            note
        )

    def create_backup(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Backup Folder",
        )

        if not directory:
            return

        try:
            backup_path = (
                create_timestamped_backup(
                    directory
                )
            )

        except BackupError as exc:
            QMessageBox.critical(
                self,
                "Backup Failed",
                str(exc),
            )
            return

        QMessageBox.information(
            self,
            "Backup Successful",
            "Database backup created successfully.\n\n"
            f"{backup_path}",
        )

    def restore_backup(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Database Backup",
            "",
            "Database Files (*.db);;All Files (*)",
        )

        if not file_path:
            return

        answer = QMessageBox.warning(
            self,
            "Confirm Database Restore",
            "Restoring this backup will replace the "
            "current database.\n\n"
            "The current database will first be saved "
            "as a safety backup.\n\n"
            "Do you want to continue?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            safety_backup = restore_backup(
                file_path
            )

        except BackupError as exc:
            QMessageBox.critical(
                self,
                "Restore Failed",
                str(exc),
            )
            return

        QMessageBox.information(
            self,
            "Restore Successful",
            "The database was restored successfully.\n\n"
            "StockFlow POS must now be restarted.\n\n"
            f"Safety backup:\n{safety_backup}",
        )