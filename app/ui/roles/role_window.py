from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.database.connection import SessionLocal
from app.services.permission_service import user_has_permission
from app.services.role_service import RoleService


class RoleDialog(QDialog):
    def __init__(
        self,
        parent=None,
        role=None,
    ):
        super().__init__(parent)

        self.role = role

        self.setWindowTitle(
            "Edit Role"
            if role
            else "Create Role"
        )

        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.name_input = QLineEdit()

        self.name_input.setPlaceholderText(
            "Role name"
        )

        form.addRow(
            "Role Name:",
            self.name_input,
        )

        self.description_input = QTextEdit()

        self.description_input.setPlaceholderText(
            "Role description"
        )

        self.description_input.setMaximumHeight(
            120
        )

        form.addRow(
            "Description:",
            self.description_input,
        )

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(
            self.accept
        )

        buttons.rejected.connect(
            self.reject
        )

        layout.addWidget(buttons)

        if role:
            self.name_input.setText(
                role.name
            )

            self.description_input.setPlainText(
                role.description or ""
            )

    def get_values(self):
        return (
            self.name_input.text().strip(),
            self.description_input.toPlainText().strip(),
        )


class RoleWindow(QWidget):
    def __init__(self, user):
        super().__init__()

        self.user = user
        self.selected_role_id = None

        self.setWindowTitle(
            "Role Management"
        )

        self.setMinimumSize(
            1000,
            650,
        )

        self.build_ui()
        self.load_roles()

    # ==========================================================
    # PERMISSION CHECK
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
        main_layout = QVBoxLayout(self)

        title = QLabel(
            "Role Management"
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                font-weight: bold;
            }
            """
        )

        main_layout.addWidget(title)

        description = QLabel(
            "Create roles and control which permissions each role has."
        )

        description.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
            }
            """
        )

        main_layout.addWidget(
            description
        )

        content_layout = QHBoxLayout()

        # ======================================================
        # ROLE LIST
        # ======================================================

        role_panel = QGroupBox(
            "Roles"
        )

        role_layout = QVBoxLayout(
            role_panel
        )

        self.role_list = QListWidget()

        self.role_list.currentItemChanged.connect(
            self.role_selected
        )

        role_layout.addWidget(
            self.role_list
        )

        role_buttons = QHBoxLayout()

        self.create_button = QPushButton(
            "CREATE"
        )

        self.create_button.clicked.connect(
            self.create_role
        )

        role_buttons.addWidget(
            self.create_button
        )

        self.edit_button = QPushButton(
            "EDIT"
        )

        self.edit_button.clicked.connect(
            self.edit_role
        )

        role_buttons.addWidget(
            self.edit_button
        )

        self.delete_button = QPushButton(
            "DELETE"
        )

        self.delete_button.clicked.connect(
            self.delete_role
        )

        role_buttons.addWidget(
            self.delete_button
        )

        role_layout.addLayout(
            role_buttons
        )

        content_layout.addWidget(
            role_panel,
            1,
        )

        # ======================================================
        # PERMISSIONS
        # ======================================================

        permission_panel = QGroupBox(
            "Permissions"
        )

        permission_layout = QVBoxLayout(
            permission_panel
        )

        self.selected_role_label = QLabel(
            "Select a role."
        )

        self.selected_role_label.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                font-weight: bold;
            }
            """
        )

        permission_layout.addWidget(
            self.selected_role_label
        )

        self.permission_list = QListWidget()

        permission_layout.addWidget(
            self.permission_list
        )

        self.save_permissions_button = QPushButton(
            "SAVE PERMISSIONS"
        )

        self.save_permissions_button.setMinimumHeight(
            40
        )

        self.save_permissions_button.clicked.connect(
            self.save_permissions
        )

        permission_layout.addWidget(
            self.save_permissions_button
        )

        content_layout.addWidget(
            permission_panel,
            2,
        )

        main_layout.addLayout(
            content_layout
        )

        self.update_button_state()

    # ==========================================================
    # LOAD ROLES
    # ==========================================================

    def load_roles(self):
        self.role_list.blockSignals(True)

        self.role_list.clear()

        with SessionLocal() as session:
            service = RoleService(session)

            roles = service.list_roles()

            for role in roles:
                item = QListWidgetItem(
                    role.name
                )

                item.setData(
                    Qt.ItemDataRole.UserRole,
                    role.id,
                )

                item.setToolTip(
                    role.description or ""
                )

                self.role_list.addItem(
                    item
                )

        self.role_list.blockSignals(False)

        if self.role_list.count() > 0:
            self.role_list.setCurrentRow(0)

        else:
            self.clear_permissions()

    # ==========================================================
    # ROLE SELECTED
    # ==========================================================

    def role_selected(
        self,
        current,
        previous,
    ):
        if current is None:
            self.selected_role_id = None
            self.clear_permissions()
            self.update_button_state()
            return

        role_id = current.data(
            Qt.ItemDataRole.UserRole
        )

        self.selected_role_id = role_id

        self.load_permissions(
            role_id
        )

        self.update_button_state()

    # ==========================================================
    # LOAD PERMISSIONS
    # ==========================================================

    def load_permissions(
        self,
        role_id: int,
    ):
        self.permission_list.clear()

        with SessionLocal() as session:
            service = RoleService(session)

            role = service.get_by_id(
                role_id
            )

            if role is None:
                return

            permissions = service.list_permissions()

            selected_ids = {
                permission.id
                for permission in role.permissions
            }

            self.selected_role_label.setText(
                f"Permissions for: {role.name}"
            )

            for permission in permissions:
                item = QListWidgetItem()

                checkbox = QCheckBox(
                    f"{permission.name} — "
                    f"{permission.description or ''}"
                )

                checkbox.setProperty(
                    "permission_id",
                    permission.id,
                )

                checkbox.setChecked(
                    permission.id
                    in selected_ids
                )

                self.permission_list.addItem(
                    item
                )

                self.permission_list.setItemWidget(
                    item,
                    checkbox,
                )

    # ==========================================================
    # CLEAR PERMISSIONS
    # ==========================================================

    def clear_permissions(self):
        self.selected_role_label.setText(
            "Select a role."
        )

        self.permission_list.clear()

    # ==========================================================
    # CREATE ROLE
    # ==========================================================

    def create_role(self):
        if not self.has_permission(
            "roles.manage"
        ):
            QMessageBox.warning(
                self,
                "Access Denied",
                "You do not have permission to manage roles.",
            )
            return

        dialog = RoleDialog(
            self
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        name, description = (
            dialog.get_values()
        )

        try:
            with SessionLocal() as session:
                service = RoleService(
                    session
                )

                service.create_role(
                    name=name,
                    description=description,
                )

                session.commit()

            self.load_roles()

            QMessageBox.information(
                self,
                "Success",
                "Role created successfully.",
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Error",
                str(exc),
            )

    # ==========================================================
    # EDIT ROLE
    # ==========================================================

    def edit_role(self):
        if not self.has_permission(
            "roles.manage"
        ):
            QMessageBox.warning(
                self,
                "Access Denied",
                "You do not have permission to manage roles.",
            )
            return

        if self.selected_role_id is None:
            return

        with SessionLocal() as session:
            service = RoleService(
                session
            )

            role = service.get_by_id(
                self.selected_role_id
            )

            if role is None:
                return

            dialog = RoleDialog(
                self,
                role,
            )

            if (
                dialog.exec()
                != QDialog.DialogCode.Accepted
            ):
                return

            name, description = (
                dialog.get_values()
            )

            try:
                service.update_role(
                    role_id=role.id,
                    name=name,
                    description=description,
                )

                session.commit()

            except Exception as exc:
                session.rollback()

                QMessageBox.critical(
                    self,
                    "Error",
                    str(exc),
                )

                return

        self.load_roles()

        QMessageBox.information(
            self,
            "Success",
            "Role updated successfully.",
        )

    # ==========================================================
    # DELETE ROLE
    # ==========================================================

    def delete_role(self):
        if not self.has_permission(
            "roles.manage"
        ):
            QMessageBox.warning(
                self,
                "Access Denied",
                "You do not have permission to manage roles.",
            )
            return

        if self.selected_role_id is None:
            return

        with SessionLocal() as session:
            service = RoleService(
                session
            )

            role = service.get_by_id(
                self.selected_role_id
            )

            if role is None:
                return

            answer = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Delete role '{role.name}'?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
            )

            if (
                answer
                != QMessageBox.StandardButton.Yes
            ):
                return

            try:
                service.delete_role(
                    role.id
                )

                session.commit()

            except Exception as exc:
                session.rollback()

                QMessageBox.critical(
                    self,
                    "Error",
                    str(exc),
                )

                return

        self.selected_role_id = None

        self.load_roles()

        QMessageBox.information(
            self,
            "Success",
            "Role deleted successfully.",
        )

    # ==========================================================
    # SAVE PERMISSIONS
    # ==========================================================

    def save_permissions(self):
        if not self.has_permission(
            "roles.manage"
        ):
            QMessageBox.warning(
                self,
                "Access Denied",
                "You do not have permission to manage roles.",
            )
            return

        if self.selected_role_id is None:
            return

        permission_ids = []

        for index in range(
            self.permission_list.count()
        ):
            item = self.permission_list.item(
                index
            )

            checkbox = (
                self.permission_list.itemWidget(
                    item
                )
            )

            if checkbox is not None:
                if checkbox.isChecked():
                    permission_ids.append(
                        checkbox.property(
                            "permission_id"
                        )
                    )

        try:
            with SessionLocal() as session:
                service = RoleService(
                    session
                )

                service.set_permissions(
                    role_id=self.selected_role_id,
                    permission_ids=permission_ids,
                )

                session.commit()

            QMessageBox.information(
                self,
                "Success",
                "Permissions updated successfully.",
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Error",
                str(exc),
            )

    # ==========================================================
    # BUTTON STATES
    # ==========================================================

    def update_button_state(self):
        has_role = (
            self.selected_role_id
            is not None
        )

        can_manage = self.has_permission(
            "roles.manage"
        )

        self.create_button.setEnabled(
            can_manage
        )

        self.edit_button.setEnabled(
            can_manage and has_role
        )

        self.delete_button.setEnabled(
            can_manage and has_role
        )

        self.save_permissions_button.setEnabled(
            can_manage and has_role
        )