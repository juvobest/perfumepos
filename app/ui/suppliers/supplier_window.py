from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.database.connection import SessionLocal
from app.services.supplier_service import SupplierService


class SupplierFormDialog(QDialog):
    """
    Dialog used for creating and editing suppliers.
    """

    def __init__(
        self,
        parent=None,
        supplier=None,
    ):
        super().__init__(parent)

        self.supplier = supplier

        if supplier is None:
            self.setWindowTitle(
                "Add Supplier"
            )
        else:
            self.setWindowTitle(
                "Edit Supplier"
            )

        self.setMinimumWidth(500)

        self.build_ui()

        if supplier is not None:
            self.load_supplier()

    # ==========================================================
    # UI
    # ==========================================================

    def build_ui(self):
        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        layout.setSpacing(15)

        title = QLabel(
            "Supplier Information"
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 20px;
                font-weight: bold;
            }
            """
        )

        layout.addWidget(title)

        form_layout = QFormLayout()

        form_layout.setSpacing(10)

        # ------------------------------------------------------
        # NAME
        # ------------------------------------------------------

        self.name_input = QLineEdit()

        self.name_input.setPlaceholderText(
            "Supplier name"
        )

        form_layout.addRow(
            "Name *:",
            self.name_input,
        )

        # ------------------------------------------------------
        # CONTACT PERSON
        # ------------------------------------------------------

        self.contact_person_input = QLineEdit()

        self.contact_person_input.setPlaceholderText(
            "Contact person's name"
        )

        form_layout.addRow(
            "Contact Person:",
            self.contact_person_input,
        )

        # ------------------------------------------------------
        # PHONE
        # ------------------------------------------------------

        self.phone_input = QLineEdit()

        self.phone_input.setPlaceholderText(
            "Phone number"
        )

        form_layout.addRow(
            "Phone:",
            self.phone_input,
        )

        # ------------------------------------------------------
        # EMAIL
        # ------------------------------------------------------

        self.email_input = QLineEdit()

        self.email_input.setPlaceholderText(
            "Email address"
        )

        form_layout.addRow(
            "Email:",
            self.email_input,
        )

        # ------------------------------------------------------
        # ADDRESS
        # ------------------------------------------------------

        self.address_input = QTextEdit()

        self.address_input.setPlaceholderText(
            "Supplier address"
        )

        self.address_input.setFixedHeight(
            75
        )

        form_layout.addRow(
            "Address:",
            self.address_input,
        )

        # ------------------------------------------------------
        # NOTES
        # ------------------------------------------------------

        self.notes_input = QTextEdit()

        self.notes_input.setPlaceholderText(
            "Additional notes"
        )

        self.notes_input.setFixedHeight(
            90
        )

        form_layout.addRow(
            "Notes:",
            self.notes_input,
        )

        layout.addLayout(
            form_layout
        )

        # ------------------------------------------------------
        # BUTTONS
        # ------------------------------------------------------

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        button_box.accepted.connect(
            self.validate_and_accept
        )

        button_box.rejected.connect(
            self.reject
        )

        layout.addWidget(
            button_box
        )

    # ==========================================================
    # LOAD EXISTING SUPPLIER
    # ==========================================================

    def load_supplier(self):
        self.name_input.setText(
            self.supplier.name or ""
        )

        self.contact_person_input.setText(
            self.supplier.contact_person or ""
        )

        self.phone_input.setText(
            self.supplier.phone or ""
        )

        self.email_input.setText(
            self.supplier.email or ""
        )

        self.address_input.setPlainText(
            self.supplier.address or ""
        )

        self.notes_input.setPlainText(
            self.supplier.notes or ""
        )

    # ==========================================================
    # VALIDATION
    # ==========================================================

    def validate_and_accept(self):
        name = self.name_input.text().strip()

        if not name:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Supplier name cannot be empty.",
            )

            self.name_input.setFocus()

            return

        self.accept()

    # ==========================================================
    # VALUES
    # ==========================================================

    def get_values(self):
        return {
            "name": self.name_input.text().strip(),
            "contact_person": (
                self.contact_person_input
                .text()
                .strip()
                or None
            ),
            "phone": (
                self.phone_input
                .text()
                .strip()
                or None
            ),
            "email": (
                self.email_input
                .text()
                .strip()
                or None
            ),
            "address": (
                self.address_input
                .toPlainText()
                .strip()
                or None
            ),
            "notes": (
                self.notes_input
                .toPlainText()
                .strip()
                or None
            ),
        }


class SupplierWindow(QWidget):
    """
    Supplier management window.

    Supports:
        - Search
        - Add
        - Edit
        - Deactivate
        - Activate
        - View inactive suppliers
    """

    def __init__(self, user):
        super().__init__()

        self.user = user

        self.setWindowTitle(
            "Supplier Management"
        )

        self.setMinimumSize(
            1000,
            650,
        )

        self.build_ui()

        self.load_suppliers()

    # ==========================================================
    # UI
    # ==========================================================

    def build_ui(self):
        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            25,
            25,
            25,
            25,
        )

        main_layout.setSpacing(
            15
        )

        # ======================================================
        # HEADER
        # ======================================================

        header_layout = QHBoxLayout()

        title = QLabel(
            "SUPPLIER MANAGEMENT"
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 26px;
                font-weight: bold;
            }
            """
        )

        header_layout.addWidget(
            title
        )

        header_layout.addStretch()

        user_label = QLabel(
            f"User: {self.user.full_name}"
        )

        user_label.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
            }
            """
        )

        header_layout.addWidget(
            user_label
        )

        main_layout.addLayout(
            header_layout
        )

        # ======================================================
        # SEARCH AREA
        # ======================================================

        search_frame = QFrame()

        search_frame.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        search_layout = QHBoxLayout(
            search_frame
        )

        search_label = QLabel(
            "Search:"
        )

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Search suppliers by name, contact person, phone or email..."
        )

        self.search_input.textChanged.connect(
            self.handle_search
        )

        self.show_inactive_checkbox = QCheckBox(
            "Show inactive"
        )

        self.show_inactive_checkbox.stateChanged.connect(
            self.handle_show_inactive_changed
        )

        self.refresh_button = QPushButton(
            "REFRESH"
        )

        self.refresh_button.clicked.connect(
            self.load_suppliers
        )

        search_layout.addWidget(
            search_label
        )

        search_layout.addWidget(
            self.search_input,
            1,
        )

        search_layout.addWidget(
            self.show_inactive_checkbox
        )

        search_layout.addWidget(
            self.refresh_button
        )

        main_layout.addWidget(
            search_frame
        )

        # ======================================================
        # ACTION BUTTONS
        # ======================================================

        action_layout = QHBoxLayout()

        self.add_button = QPushButton(
            "ADD SUPPLIER"
        )

        self.add_button.setMinimumHeight(
            40
        )

        self.add_button.setStyleSheet(
            """
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 18px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #2ecc71;
            }
            """
        )

        self.add_button.clicked.connect(
            self.add_supplier
        )

        self.edit_button = QPushButton(
            "EDIT SELECTED"
        )

        self.edit_button.setMinimumHeight(
            40
        )

        self.edit_button.clicked.connect(
            self.edit_supplier
        )

        self.deactivate_button = QPushButton(
            "DEACTIVATE"
        )

        self.deactivate_button.setMinimumHeight(
            40
        )

        self.deactivate_button.setStyleSheet(
            """
            QPushButton {
                background-color: #c0392b;
                color: white;
                border: none;
                padding: 10px 18px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #e74c3c;
            }
            """
        )

        self.deactivate_button.clicked.connect(
            self.deactivate_supplier
        )

        self.activate_button = QPushButton(
            "ACTIVATE"
        )

        self.activate_button.setMinimumHeight(
            40
        )

        self.activate_button.setStyleSheet(
            """
            QPushButton {
                background-color: #2980b9;
                color: white;
                border: none;
                padding: 10px 18px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #3498db;
            }
            """
        )

        self.activate_button.clicked.connect(
            self.activate_supplier
        )

        action_layout.addWidget(
            self.add_button
        )

        action_layout.addWidget(
            self.edit_button
        )

        action_layout.addWidget(
            self.deactivate_button
        )

        action_layout.addWidget(
            self.activate_button
        )

        action_layout.addStretch()

        main_layout.addLayout(
            action_layout
        )

        # ======================================================
        # SUPPLIER TABLE
        # ======================================================

        self.supplier_table = QTableWidget(
            0,
            8,
        )

        self.supplier_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Supplier",
                "Contact Person",
                "Phone",
                "Email",
                "Address",
                "Status",
                "Notes",
            ]
        )

        self.supplier_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.supplier_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        self.supplier_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.supplier_table.setAlternatingRowColors(
            True
        )

        self.supplier_table.horizontalHeader().setStretchLastSection(
            True
        )

        self.supplier_table.doubleClicked.connect(
            self.edit_supplier
        )

        main_layout.addWidget(
            self.supplier_table
        )

        # ======================================================
        # STATUS
        # ======================================================

        self.status_label = QLabel(
            "0 suppliers"
        )

        self.status_label.setStyleSheet(
            """
            QLabel {
                font-size: 13px;
                color: #555555;
            }
            """
        )

        main_layout.addWidget(
            self.status_label
        )

    # ==========================================================
    # LOAD SUPPLIERS
    # ==========================================================

    def load_suppliers(self):
        try:
            with SessionLocal() as session:

                service = SupplierService(
                    session
                )

                suppliers = service.list_suppliers(
                    include_inactive=self.show_inactive_checkbox.isChecked()
                    if hasattr(
                        self,
                        "show_inactive_checkbox",
                    )
                    else False
                )

                self.populate_table(
                    suppliers
                )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Database Error",
                f"Unable to load suppliers:\n\n{exc}",
            )

    # ==========================================================
    # POPULATE TABLE
    # ==========================================================

    def populate_table(
        self,
        suppliers,
    ):
        self.supplier_table.setRowCount(
            0
        )

        for supplier in suppliers:

            row = self.supplier_table.rowCount()

            self.supplier_table.insertRow(
                row
            )

            values = [
                supplier.id,
                supplier.name,
                supplier.contact_person or "",
                supplier.phone or "",
                supplier.email or "",
                supplier.address or "",
                (
                    "Active"
                    if supplier.is_active
                    else "Inactive"
                ),
                supplier.notes or "",
            ]

            for column, value in enumerate(
                values
            ):
                item = QTableWidgetItem(
                    str(value)
                )

                item.setData(
                    Qt.ItemDataRole.UserRole,
                    supplier.id,
                )

                self.supplier_table.setItem(
                    row,
                    column,
                    item,
                )

        self.supplier_table.resizeColumnsToContents()

        self.status_label.setText(
            f"{len(suppliers)} supplier"
            f"{'' if len(suppliers) == 1 else 's'}"
        )

    # ==========================================================
    # SEARCH
    # ==========================================================

    def handle_search(
        self,
        text: str,
    ):
        search_text = text.strip().lower()

        try:
            with SessionLocal() as session:

                service = SupplierService(
                    session
                )

                suppliers = service.list_suppliers(
                    include_inactive=self.show_inactive_checkbox.isChecked()
                )

                if search_text:

                    suppliers = [
                        supplier
                        for supplier in suppliers
                        if (
                            search_text
                            in supplier.name.lower()
                            or search_text
                            in (
                                supplier.contact_person
                                or ""
                            ).lower()
                            or search_text
                            in (
                                supplier.phone
                                or ""
                            ).lower()
                            or search_text
                            in (
                                supplier.email
                                or ""
                            ).lower()
                        )
                    ]

                self.populate_table(
                    suppliers
                )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Search Error",
                f"Unable to search suppliers:\n\n{exc}",
            )

    # ==========================================================
    # SHOW INACTIVE
    # ==========================================================

    def handle_show_inactive_changed(
        self,
        state,
    ):
        self.handle_search(
            self.search_input.text()
        )

    # ==========================================================
    # GET SELECTED SUPPLIER
    # ==========================================================

    def get_selected_supplier_id(self):
        selected_rows = (
            self.supplier_table
            .selectionModel()
            .selectedRows()
        )

        if not selected_rows:
            return None

        row = selected_rows[0].row()

        item = self.supplier_table.item(
            row,
            0,
        )

        if item is None:
            return None

        try:
            return int(
                item.text()
            )
        except ValueError:
            return None

    # ==========================================================
    # ADD SUPPLIER
    # ==========================================================

    def add_supplier(self):
        dialog = SupplierFormDialog(
            self
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        values = dialog.get_values()

        try:
            with SessionLocal() as session:

                service = SupplierService(
                    session
                )

                service.create_supplier(
                    **values
                )

                session.commit()

            QMessageBox.information(
                self,
                "Supplier Added",
                "Supplier was added successfully.",
            )

            self.search_input.clear()

            self.load_suppliers()

        except ValueError as exc:

            QMessageBox.warning(
                self,
                "Unable to Add Supplier",
                str(exc),
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Database Error",
                f"Unable to add supplier:\n\n{exc}",
            )

    # ==========================================================
    # EDIT SUPPLIER
    # ==========================================================

    def edit_supplier(self):
        supplier_id = (
            self.get_selected_supplier_id()
        )

        if supplier_id is None:
            QMessageBox.warning(
                self,
                "No Supplier Selected",
                "Please select a supplier to edit.",
            )

            return

        try:
            with SessionLocal() as session:

                service = SupplierService(
                    session
                )

                supplier = service.get_by_id(
                    supplier_id
                )

                if supplier is None:
                    QMessageBox.warning(
                        self,
                        "Supplier Not Found",
                        "The selected supplier no longer exists.",
                    )

                    return

                dialog = SupplierFormDialog(
                    self,
                    supplier,
                )

                if (
                    dialog.exec()
                    != QDialog.DialogCode.Accepted
                ):
                    return

                values = dialog.get_values()

                service.update_supplier(
                    supplier_id,
                    **values,
                )

                session.commit()

            QMessageBox.information(
                self,
                "Supplier Updated",
                "Supplier was updated successfully.",
            )

            self.load_suppliers()

        except ValueError as exc:

            QMessageBox.warning(
                self,
                "Unable to Update Supplier",
                str(exc),
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Database Error",
                f"Unable to update supplier:\n\n{exc}",
            )

    # ==========================================================
    # DEACTIVATE SUPPLIER
    # ==========================================================

    def deactivate_supplier(self):
        supplier_id = (
            self.get_selected_supplier_id()
        )

        if supplier_id is None:
            QMessageBox.warning(
                self,
                "No Supplier Selected",
                "Please select a supplier.",
            )

            return

        try:
            with SessionLocal() as session:

                service = SupplierService(
                    session
                )

                supplier = service.get_by_id(
                    supplier_id
                )

                if supplier is None:
                    QMessageBox.warning(
                        self,
                        "Supplier Not Found",
                        "Supplier not found.",
                    )

                    return

                if not supplier.is_active:
                    QMessageBox.information(
                        self,
                        "Already Inactive",
                        "This supplier is already inactive.",
                    )

                    return

                confirmation = QMessageBox.question(
                    self,
                    "Deactivate Supplier",
                    (
                        f"Are you sure you want to "
                        f"deactivate '{supplier.name}'?"
                    ),
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No,
                )

                if (
                    confirmation
                    != QMessageBox.StandardButton.Yes
                ):
                    return

                service.deactivate_supplier(
                    supplier_id
                )

                session.commit()

            QMessageBox.information(
                self,
                "Supplier Deactivated",
                "Supplier was deactivated successfully.",
            )

            self.load_suppliers()

        except ValueError as exc:

            QMessageBox.warning(
                self,
                "Unable to Deactivate Supplier",
                str(exc),
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Database Error",
                f"Unable to deactivate supplier:\n\n{exc}",
            )

    # ==========================================================
    # ACTIVATE SUPPLIER
    # ==========================================================

    def activate_supplier(self):
        supplier_id = (
            self.get_selected_supplier_id()
        )

        if supplier_id is None:
            QMessageBox.warning(
                self,
                "No Supplier Selected",
                "Please select a supplier.",
            )

            return

        try:
            with SessionLocal() as session:

                service = SupplierService(
                    session
                )

                supplier = service.get_by_id(
                    supplier_id
                )

                if supplier is None:
                    QMessageBox.warning(
                        self,
                        "Supplier Not Found",
                        "Supplier not found.",
                    )

                    return

                if supplier.is_active:
                    QMessageBox.information(
                        self,
                        "Already Active",
                        "This supplier is already active.",
                    )

                    return

                service.activate_supplier(
                    supplier_id
                )

                session.commit()

            QMessageBox.information(
                self,
                "Supplier Activated",
                "Supplier was activated successfully.",
            )

            self.load_suppliers()

        except ValueError as exc:

            QMessageBox.warning(
                self,
                "Unable to Activate Supplier",
                str(exc),
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Database Error",
                f"Unable to activate supplier:\n\n{exc}",
            )