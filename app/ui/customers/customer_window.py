from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from app.database.connection import SessionLocal
from app.services.customer_service import CustomerService


class CustomerDialog(QDialog):
    def __init__(
        self,
        parent=None,
        customer=None,
    ):
        super().__init__(parent)

        self.customer = customer

        self.setWindowTitle(
            "Edit Customer"
            if customer
            else "New Customer"
        )

        self.setMinimumWidth(500)

        self.build_ui()

        if customer:
            self.load_customer()

    def build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel(
            "EDIT CUSTOMER"
            if self.customer
            else "NEW CUSTOMER"
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 22px;
                font-weight: bold;
                padding-bottom: 10px;
            }
            """
        )

        layout.addWidget(title)

        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(
            "Customer full name"
        )

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText(
            "Phone number"
        )

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText(
            "Email address"
        )

        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText(
            "Customer address"
        )

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText(
            "Optional notes"
        )

        form.addRow(
            "Name *:",
            self.name_input,
        )

        form.addRow(
            "Phone:",
            self.phone_input,
        )

        form.addRow(
            "Email:",
            self.email_input,
        )

        form.addRow(
            "Address:",
            self.address_input,
        )

        form.addRow(
            "Notes:",
            self.notes_input,
        )

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(
            self.validate_and_accept
        )

        buttons.rejected.connect(
            self.reject
        )

        layout.addWidget(buttons)

    def load_customer(self):
        self.name_input.setText(
            self.customer.name or ""
        )

        self.phone_input.setText(
            self.customer.phone or ""
        )

        self.email_input.setText(
            self.customer.email or ""
        )

        self.address_input.setText(
            self.customer.address or ""
        )

        self.notes_input.setText(
            self.customer.notes or ""
        )

    def validate_and_accept(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(
                self,
                "Validation Error",
                "Customer name is required.",
            )
            return

        self.accept()

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "email": self.email_input.text().strip(),
            "address": self.address_input.text().strip(),
            "notes": self.notes_input.text().strip(),
        }


class CustomerWindow(QWidget):
    def __init__(self, user):
        super().__init__()

        self.user = user

        self.setWindowTitle(
            "Customer Management"
        )

        self.setMinimumSize(
            1000,
            650,
        )

        self.build_ui()
        self.load_customers()

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

        main_layout.setSpacing(15)

        # ======================================================
        # HEADER
        # ======================================================

        header_layout = QHBoxLayout()

        title = QLabel(
            "CUSTOMER MANAGEMENT"
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 26px;
                font-weight: bold;
            }
            """
        )

        header_layout.addWidget(title)
        header_layout.addStretch()

        new_button = QPushButton(
            "+ NEW CUSTOMER"
        )

        new_button.setMinimumHeight(40)

        new_button.setStyleSheet(
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

        new_button.clicked.connect(
            self.create_customer
        )

        header_layout.addWidget(
            new_button
        )

        main_layout.addLayout(
            header_layout
        )

        # ======================================================
        # SEARCH
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
            "Search by name, phone or email..."
        )

        self.search_input.textChanged.connect(
            self.search_customers
        )

        refresh_button = QPushButton(
            "REFRESH"
        )

        refresh_button.setMinimumHeight(35)

        refresh_button.clicked.connect(
            self.load_customers
        )

        search_layout.addWidget(
            search_label
        )

        search_layout.addWidget(
            self.search_input
        )

        search_layout.addWidget(
            refresh_button
        )

        main_layout.addWidget(
            search_frame
        )

        # ======================================================
        # TABLE
        # ======================================================

        self.customer_table = QTableWidget(
            0,
            6,
        )

        self.customer_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Name",
                "Phone",
                "Email",
                "Address",
                "Status",
            ]
        )

        self.customer_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.customer_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        self.customer_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.customer_table.doubleClicked.connect(
            self.edit_customer
        )

        header = (
            self.customer_table.horizontalHeader()
        )

        header.setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        main_layout.addWidget(
            self.customer_table
        )

        # ======================================================
        # ACTION BUTTONS
        # ======================================================

        actions_layout = QHBoxLayout()

        self.edit_button = QPushButton(
            "EDIT CUSTOMER"
        )

        self.deactivate_button = QPushButton(
            "DEACTIVATE CUSTOMER"
        )

        self.edit_button.setMinimumHeight(40)
        self.deactivate_button.setMinimumHeight(40)

        self.edit_button.clicked.connect(
            self.edit_customer
        )

        self.deactivate_button.clicked.connect(
            self.deactivate_customer
        )

        actions_layout.addWidget(
            self.edit_button
        )

        actions_layout.addWidget(
            self.deactivate_button
        )

        actions_layout.addStretch()

        main_layout.addLayout(
            actions_layout
        )

    # ==========================================================
    # LOAD CUSTOMERS
    # ==========================================================

    def load_customers(self):
        self.search_input.clear()

        with SessionLocal() as session:
            service = CustomerService(
                session
            )

            customers = service.list_customers()

            self.populate_table(
                customers
            )

    # ==========================================================
    # SEARCH
    # ==========================================================

    def search_customers(self):
        query = self.search_input.text()

        with SessionLocal() as session:
            service = CustomerService(
                session
            )

            customers = service.search_customers(
                query
            )

            self.populate_table(
                customers
            )

    # ==========================================================
    # TABLE
    # ==========================================================

    def populate_table(
        self,
        customers,
    ):
        self.customer_table.setRowCount(0)

        for customer in customers:

            row = (
                self.customer_table.rowCount()
            )

            self.customer_table.insertRow(
                row
            )

            values = [
                str(customer.id),
                customer.name or "",
                customer.phone or "",
                customer.email or "",
                customer.address or "",
                "Active"
                if customer.is_active
                else "Inactive",
            ]

            for column, value in enumerate(
                values
            ):
                item = QTableWidgetItem(
                    value
                )

                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

                self.customer_table.setItem(
                    row,
                    column,
                    item,
                )

    # ==========================================================
    # SELECTED CUSTOMER
    # ==========================================================

    def get_selected_customer_id(self):
        selected_rows = (
            self.customer_table.selectionModel()
            .selectedRows()
        )

        if not selected_rows:
            return None

        row = selected_rows[0].row()

        item = self.customer_table.item(
            row,
            0,
        )

        if item is None:
            return None

        return int(
            item.text()
        )

    # ==========================================================
    # CREATE
    # ==========================================================

    def create_customer(self):
        dialog = CustomerDialog(
            self
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()

        try:
            with SessionLocal() as session:

                service = CustomerService(
                    session
                )

                service.create_customer(
                    name=data["name"],
                    phone=data["phone"],
                    email=data["email"],
                    address=data["address"],
                    notes=data["notes"],
                )

                session.commit()

            QMessageBox.information(
                self,
                "Success",
                "Customer created successfully.",
            )

            self.load_customers()

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Error",
                str(exc),
            )

    # ==========================================================
    # EDIT
    # ==========================================================

    def edit_customer(self):
        customer_id = (
            self.get_selected_customer_id()
        )

        if customer_id is None:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a customer first.",
            )
            return

        try:
            with SessionLocal() as session:

                service = CustomerService(
                    session
                )

                customer = service.get_customer(
                    customer_id
                )

                if customer is None:
                    raise ValueError(
                        "Customer not found."
                    )

                dialog = CustomerDialog(
                    self,
                    customer,
                )

                if (
                    dialog.exec()
                    != QDialog.DialogCode.Accepted
                ):
                    return

                data = dialog.get_data()

                service.update_customer(
                    customer_id=customer_id,
                    name=data["name"],
                    phone=data["phone"],
                    email=data["email"],
                    address=data["address"],
                    notes=data["notes"],
                )

                session.commit()

            QMessageBox.information(
                self,
                "Success",
                "Customer updated successfully.",
            )

            self.load_customers()

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Error",
                str(exc),
            )

    # ==========================================================
    # DEACTIVATE
    # ==========================================================

    def deactivate_customer(self):
        customer_id = (
            self.get_selected_customer_id()
        )

        if customer_id is None:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a customer first.",
            )
            return

        confirmation = QMessageBox.question(
            self,
            "Confirm Deactivation",
            "Are you sure you want to deactivate this customer?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )

        if (
            confirmation
            != QMessageBox.StandardButton.Yes
        ):
            return

        try:
            with SessionLocal() as session:

                service = CustomerService(
                    session
                )

                service.deactivate_customer(
                    customer_id
                )

                session.commit()

            QMessageBox.information(
                self,
                "Success",
                "Customer deactivated successfully.",
            )

            self.load_customers()

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Error",
                str(exc),
            )