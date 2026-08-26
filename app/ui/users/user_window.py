from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.database.connection import SessionLocal
from app.services.permission_service import user_has_permission
from app.services.user_service import UserService


class UserDialog(QDialog):
    def __init__(
        self,
        roles,
        user=None,
        parent=None,
    ):
        super().__init__(parent)

        self.user = user

        if user is None:
            self.setWindowTitle("Create User")
        else:
            self.setWindowTitle("Edit User")

        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.username_input = QLineEdit()

        self.full_name_input = QLineEdit()

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.role_combo = QComboBox()

        for role in roles:
            self.role_combo.addItem(
                role.name
            )

        if user is not None:
            self.username_input.setText(
                user.username
            )

            self.username_input.setReadOnly(
                True
            )

            self.full_name_input.setText(
                user.full_name
            )

            if user.roles:
                current_role = user.roles[0].name

                index = self.role_combo.findText(
                    current_role
                )

                if index >= 0:
                    self.role_combo.setCurrentIndex(
                        index
                    )

        form.addRow(
            "Username:",
            self.username_input,
        )

        form.addRow(
            "Full Name:",
            self.full_name_input,
        )

        form.addRow(
            "Password:",
            self.password_input,
        )

        if user is not None:
            password_note = QLabel(
                "Leave password blank to keep the current password."
            )

            password_note.setStyleSheet(
                "color: #666;"
            )

            form.addRow(
                "",
                password_note,
            )

        form.addRow(
            "Role:",
            self.role_combo,
        )

        layout.addLayout(form)

        buttons = QHBoxLayout()

        save_button = QPushButton(
            "SAVE"
        )

        cancel_button = QPushButton(
            "CANCEL"
        )

        save_button.clicked.connect(
            self.accept
        )

        cancel_button.clicked.connect(
            self.reject
        )

        buttons.addWidget(
            save_button
        )

        buttons.addWidget(
            cancel_button
        )

        layout.addSpacing(15)

        layout.addLayout(
            buttons
        )

    def get_data(self):
        return {
            "username": (
                self.username_input
                .text()
                .strip()
            ),
            "full_name": (
                self.full_name_input
                .text()
                .strip()
            ),
            "password": (
                self.password_input
                .text()
            ),
            "role_name": (
                self.role_combo
                .currentText()
            ),
        }


class UserWindow(QWidget):
    def __init__(self, user):
        super().__init__()

        self.user = user

        self.setWindowTitle(
            "User Management"
        )

        self.setMinimumSize(
            900,
            600,
        )

        self.build_ui()

        self.load_users()

    # ==========================================================
    # PERMISSIONS
    # ==========================================================

    def has_permission(
        self,
        permission_name: str,
    ) -> bool:
        with SessionLocal() as session:
            return user_has_permission(
                session,
                self.user,
                permission_name,
            )

    # ==========================================================
    # UI
    # ==========================================================

    def build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel(
            "User Management"
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                font-weight: bold;
            }
            """
        )

        layout.addWidget(
            title
        )

        description = QLabel(
            "Create, edit and manage system users and their roles."
        )

        description.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
                color: #666;
            }
            """
        )

        layout.addWidget(
            description
        )

        layout.addSpacing(15)

        button_layout = QHBoxLayout()

        self.create_button = QPushButton(
            "CREATE USER"
        )

        self.edit_button = QPushButton(
            "EDIT USER"
        )

        self.activate_button = QPushButton(
            "ACTIVATE"
        )

        self.deactivate_button = QPushButton(
            "DEACTIVATE"
        )

        self.refresh_button = QPushButton(
            "REFRESH"
        )

        button_layout.addWidget(
            self.create_button
        )

        button_layout.addWidget(
            self.edit_button
        )

        button_layout.addWidget(
            self.activate_button
        )

        button_layout.addWidget(
            self.deactivate_button
        )

        button_layout.addStretch()

        button_layout.addWidget(
            self.refresh_button
        )

        layout.addLayout(
            button_layout
        )

        self.table = QTableWidget()

        self.table.setColumnCount(
            5
        )

        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Username",
                "Full Name",
                "Role",
                "Status",
            ]
        )

        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.table.horizontalHeader().setStretchLastSection(
            True
        )

        layout.addWidget(
            self.table
        )

        self.create_button.clicked.connect(
            self.create_user
        )

        self.edit_button.clicked.connect(
            self.edit_user
        )

        self.activate_button.clicked.connect(
            self.activate_user
        )

        self.deactivate_button.clicked.connect(
            self.deactivate_user
        )

        self.refresh_button.clicked.connect(
            self.load_users
        )

        self.apply_permissions()

    # ==========================================================
    # BUTTON PERMISSIONS
    # ==========================================================

    def apply_permissions(self):
        self.create_button.setEnabled(
            self.has_permission(
                "users.create"
            )
        )

        self.edit_button.setEnabled(
            self.has_permission(
                "users.edit"
            )
        )

        self.activate_button.setEnabled(
            self.has_permission(
                "users.edit"
            )
        )

        self.deactivate_button.setEnabled(
            self.has_permission(
                "users.deactivate"
            )
        )

    # ==========================================================
    # LOAD USERS
    # ==========================================================

    def load_users(self):
        if not self.has_permission(
            "users.view"
        ):
            QMessageBox.warning(
                self,
                "Access Denied",
                "You do not have permission to view users.",
            )

            return

        with SessionLocal() as session:
            service = UserService(
                session
            )

            users = service.list_users()

            self.table.setRowCount(
                len(users)
            )

            for row, user in enumerate(users):
                self.table.setItem(
                    row,
                    0,
                    QTableWidgetItem(
                        str(user.id)
                    ),
                )

                self.table.setItem(
                    row,
                    1,
                    QTableWidgetItem(
                        user.username
                    ),
                )

                self.table.setItem(
                    row,
                    2,
                    QTableWidgetItem(
                        user.full_name
                    ),
                )

                role_name = (
                    user.roles[0].name
                    if user.roles
                    else "No Role"
                )

                self.table.setItem(
                    row,
                    3,
                    QTableWidgetItem(
                        role_name
                    ),
                )

                status = (
                    "ACTIVE"
                    if user.is_active
                    else "INACTIVE"
                )

                self.table.setItem(
                    row,
                    4,
                    QTableWidgetItem(
                        status
                    ),
                )

            self.table.resizeColumnsToContents()

    # ==========================================================
    # SELECTED USER
    # ==========================================================

    def get_selected_user_id(self):
        selected = (
            self.table.selectedItems()
        )

        if not selected:
            QMessageBox.warning(
                self,
                "No User Selected",
                "Please select a user first.",
            )

            return None

        row = selected[0].row()

        item = self.table.item(
            row,
            0,
        )

        if item is None:
            return None

        return int(
            item.text()
        )

    # ==========================================================
    # CREATE USER
    # ==========================================================

    def create_user(self):
        if not self.has_permission(
            "users.create"
        ):
            QMessageBox.warning(
                self,
                "Access Denied",
                "You do not have permission to create users.",
            )

            return

        with SessionLocal() as session:
            service = UserService(
                session
            )

            roles = service.list_roles()

            dialog = UserDialog(
                roles,
                parent=self,
            )

            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            data = dialog.get_data()

            try:
                service.create_user(
                    username=data["username"],
                    full_name=data["full_name"],
                    password=data["password"],
                    role_name=data["role_name"],
                )

                session.commit()

            except ValueError as error:
                session.rollback()

                QMessageBox.warning(
                    self,
                    "Unable to Create User",
                    str(error),
                )

                return

        QMessageBox.information(
            self,
            "Success",
            "User created successfully.",
        )

        self.load_users()

    # ==========================================================
    # EDIT USER
    # ==========================================================

    def edit_user(self):
        if not self.has_permission(
            "users.edit"
        ):
            QMessageBox.warning(
                self,
                "Access Denied",
                "You do not have permission to edit users.",
            )

            return

        user_id = self.get_selected_user_id()

        if user_id is None:
            return

        with SessionLocal() as session:
            service = UserService(
                session
            )

            user = service.get_by_id(
                user_id
            )

            if user is None:
                QMessageBox.warning(
                    self,
                    "Error",
                    "User not found.",
                )

                return

            roles = service.list_roles()

            dialog = UserDialog(
                roles,
                user=user,
                parent=self,
            )

            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            data = dialog.get_data()

            try:
                service.update_user(
                    user_id=user_id,
                    full_name=data["full_name"],
                    role_name=data["role_name"],
                    password=(
                        data["password"]
                        if data["password"]
                        else None
                    ),
                )

                session.commit()

            except ValueError as error:
                session.rollback()

                QMessageBox.warning(
                    self,
                    "Unable to Update User",
                    str(error),
                )

                return

        QMessageBox.information(
            self,
            "Success",
            "User updated successfully.",
        )

        self.load_users()

    # ==========================================================
    # DEACTIVATE USER
    # ==========================================================

    def deactivate_user(self):
        if not self.has_permission(
            "users.deactivate"
        ):
            QMessageBox.warning(
                self,
                "Access Denied",
                "You do not have permission to deactivate users.",
            )

            return

        user_id = self.get_selected_user_id()

        if user_id is None:
            return

        if user_id == self.user.id:
            QMessageBox.warning(
                self,
                "Action Not Allowed",
                "You cannot deactivate your own account.",
            )

            return

        answer = QMessageBox.question(
            self,
            "Confirm Deactivation",
            "Are you sure you want to deactivate this user?",
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        with SessionLocal() as session:
            service = UserService(
                session
            )

            try:
                service.deactivate_user(
                    user_id
                )

                session.commit()

            except ValueError as error:
                session.rollback()

                QMessageBox.warning(
                    self,
                    "Unable to Deactivate",
                    str(error),
                )

                return

        QMessageBox.information(
            self,
            "Success",
            "User deactivated successfully.",
        )

        self.load_users()

    # ==========================================================
    # ACTIVATE USER
    # ==========================================================

    def activate_user(self):
        if not self.has_permission(
            "users.edit"
        ):
            QMessageBox.warning(
                self,
                "Access Denied",
                "You do not have permission to activate users.",
            )

            return

        user_id = self.get_selected_user_id()

        if user_id is None:
            return

        with SessionLocal() as session:
            service = UserService(
                session
            )

            try:
                service.activate_user(
                    user_id
                )

                session.commit()

            except ValueError as error:
                session.rollback()

                QMessageBox.warning(
                    self,
                    "Unable to Activate",
                    str(error),
                )

                return

        QMessageBox.information(
            self,
            "Success",
            "User activated successfully.",
        )

        self.load_users()