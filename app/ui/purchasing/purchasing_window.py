from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.database.connection import SessionLocal
from app.services.product_service import ProductService
from app.services.purchase_service import PurchaseService
from app.services.supplier_service import SupplierService


class PurchasingWindow(QWidget):
    def __init__(self, user):
        super().__init__()

        self.user = user
        self.current_purchase = None

        self.setWindowTitle("Purchasing Management")
        self.setMinimumSize(1000, 650)

        self.build_ui()
        self.load_purchases()

    def build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Purchasing Management")
        title.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                font-weight: bold;
            }
            """
        )

        description = QLabel(
            "Create, manage and receive stock purchases."
        )

        description.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
                color: #555;
            }
            """
        )

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addSpacing(15)

        buttons_layout = QHBoxLayout()

        self.new_button = QPushButton("NEW PURCHASE")
        self.new_button.setMinimumHeight(40)

        self.view_button = QPushButton("VIEW PURCHASE")
        self.view_button.setMinimumHeight(40)

        self.receive_button = QPushButton("RECEIVE PURCHASE")
        self.receive_button.setMinimumHeight(40)

        self.cancel_button = QPushButton("CANCEL PURCHASE")
        self.cancel_button.setMinimumHeight(40)

        self.refresh_button = QPushButton("REFRESH")
        self.refresh_button.setMinimumHeight(40)

        buttons_layout.addWidget(self.new_button)
        buttons_layout.addWidget(self.view_button)
        buttons_layout.addWidget(self.receive_button)
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.refresh_button)

        layout.addLayout(buttons_layout)
        layout.addSpacing(15)

        self.purchase_table = QTableWidget()

        self.purchase_table.setColumnCount(9)

        self.purchase_table.setHorizontalHeaderLabels(
            [
                "Purchase No.",
                "Supplier",
                "Date",
                "Status",
                "Product",
                "Variant",
                "Qty",
                "Unit Cost",
                "Total",
            ]
        )

        self.purchase_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.purchase_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.purchase_table.horizontalHeader().setStretchLastSection(
            True
        )

        layout.addWidget(self.purchase_table)

        self.new_button.clicked.connect(
            self.create_new_purchase
        )

        self.view_button.clicked.connect(
            self.view_purchase
        )

        self.receive_button.clicked.connect(
            self.receive_purchase
        )

        self.cancel_button.clicked.connect(
            self.cancel_purchase
        )

        self.refresh_button.clicked.connect(
            self.load_purchases
        )

    def load_purchases(self):
        with SessionLocal() as session:
            service = PurchaseService(session)

            purchases = service.list_purchases()

            # Show one row for each purchase item so the receiver
            # can verify the exact product, variant, quantity,
            # unit cost and line total before receiving stock.
            rows = []

            for purchase in purchases:
                for item in purchase.items:
                    product = item.product_variant.product

                    variant_name = (
                        item.product_variant.variant_name
                        or ""
                    )

                    rows.append(
                        (
                            purchase,
                            product,
                            variant_name,
                            item,
                        )
                    )

            self.purchase_table.setRowCount(
                len(rows)
            )

            for row, (
                purchase,
                product,
                variant_name,
                item,
            ) in enumerate(rows):

                self.purchase_table.setItem(
                    row,
                    0,
                    QTableWidgetItem(
                        purchase.purchase_number
                    ),
                )

                self.purchase_table.setItem(
                    row,
                    1,
                    QTableWidgetItem(
                        purchase.supplier.name
                    ),
                )

                self.purchase_table.setItem(
                    row,
                    2,
                    QTableWidgetItem(
                        str(purchase.purchase_date)
                    ),
                )

                self.purchase_table.setItem(
                    row,
                    3,
                    QTableWidgetItem(
                        purchase.status
                    ),
                )

                self.purchase_table.setItem(
                    row,
                    4,
                    QTableWidgetItem(
                        product.name
                    ),
                )

                self.purchase_table.setItem(
                    row,
                    5,
                    QTableWidgetItem(
                        variant_name
                    ),
                )

                self.purchase_table.setItem(
                    row,
                    6,
                    QTableWidgetItem(
                        str(item.quantity)
                    ),
                )

                self.purchase_table.setItem(
                    row,
                    7,
                    QTableWidgetItem(
                        f"{item.unit_cost:,.2f}"
                    ),
                )

                self.purchase_table.setItem(
                    row,
                    8,
                    QTableWidgetItem(
                        f"{item.total_cost:,.2f}"
                    ),
                )

            self.purchase_table.resizeColumnsToContents()

            self.purchase_table.setColumnWidth(
                0, 120
            )
            self.purchase_table.setColumnWidth(
                1, 160
            )
            self.purchase_table.setColumnWidth(
                2, 100
            )
            self.purchase_table.setColumnWidth(
                3, 100
            )
            self.purchase_table.setColumnWidth(
                4, 220
            )
            self.purchase_table.setColumnWidth(
                5, 120
            )
            self.purchase_table.setColumnWidth(
                6, 70
            )
            self.purchase_table.setColumnWidth(
                7, 100
            )
            self.purchase_table.setColumnWidth(
                8, 120
            )

    def get_selected_purchase_id(self):
        row = self.purchase_table.currentRow()

        if row < 0:
            return None

        purchase_number = self.purchase_table.item(
            row,
            0,
        ).text()

        with SessionLocal() as session:
            service = PurchaseService(session)

            purchase = service.get_by_number(
                purchase_number
            )

            if purchase is None:
                return None

            return purchase.id

    def create_new_purchase(self):
        dialog = QDialog(self)

        dialog.setWindowTitle("Create Purchase")
        dialog.setMinimumWidth(500)

        layout = QVBoxLayout(dialog)

        form = QFormLayout()

        supplier_combo = QComboBox()

        notes_input = QTextEdit()
        notes_input.setMaximumHeight(100)

        with SessionLocal() as session:
            supplier_service = SupplierService(session)

            suppliers = supplier_service.list_suppliers()

            for supplier in suppliers:
                supplier_combo.addItem(
                    supplier.name,
                    supplier.id,
                )

        form.addRow(
            "Supplier:",
            supplier_combo,
        )

        form.addRow(
            "Notes:",
            notes_input,
        )

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        layout.addWidget(buttons)

        buttons.accepted.connect(
            dialog.accept
        )

        buttons.rejected.connect(
            dialog.reject
        )

        if supplier_combo.count() == 0:
            QMessageBox.warning(
                self,
                "No Suppliers",
                "Please create an active supplier before creating a purchase.",
            )

            return

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        supplier_id = supplier_combo.currentData()

        notes = notes_input.toPlainText().strip()

        with SessionLocal() as session:
            service = PurchaseService(session)

            try:
                purchase = service.create_purchase(
                    supplier_id=supplier_id,
                    purchase_date=date.today(),
                    created_by=self.user.id,
                    notes=notes or None,
                )

                session.commit()

                purchase_id = purchase.id
                purchase_number = purchase.purchase_number

            except ValueError as error:
                session.rollback()

                QMessageBox.warning(
                    self,
                    "Unable to Create Purchase",
                    str(error),
                )

                return

        self.load_purchases()

        self.open_purchase_items(
            purchase_id,
            purchase_number,
        )

    def open_purchase_items(
        self,
        purchase_id: int,
        purchase_number: str,
    ):
        dialog = PurchaseItemsDialog(
            self,
            purchase_id,
            purchase_number,
            self.user,
        )

        dialog.exec()

        self.load_purchases()

    def view_purchase(self):
        purchase_id = self.get_selected_purchase_id()

        if purchase_id is None:
            QMessageBox.information(
                self,
                "Select Purchase",
                "Please select a purchase first.",
            )

            return

        with SessionLocal() as session:
            service = PurchaseService(session)

            purchase = service.get_by_id(
                purchase_id
            )

            if purchase is None:
                return

            lines = [
                f"Purchase: {purchase.purchase_number}",
                f"Supplier: {purchase.supplier.name}",
                f"Date: {purchase.purchase_date}",
                f"Status: {purchase.status}",
                "",
                "Items:",
            ]

            for item in purchase.items:
                product = item.product_variant.product

                variant_name = (
                    item.product_variant.variant_name
                    or ""
                )

                label = product.name

                if variant_name:
                    label += f" - {variant_name}"

                lines.append(
                    f"{label} | "
                    f"Qty: {item.quantity} | "
                    f"Unit Cost: {item.unit_cost:,.2f} | "
                    f"Total: {item.total_cost:,.2f}"
                )

            lines.extend(
                [
                    "",
                    f"Total Amount: {purchase.total_amount:,.2f}",
                ]
            )

            QMessageBox.information(
                self,
                "Purchase Details",
                "\n".join(lines),
            )

    def receive_purchase(self):
        purchase_id = self.get_selected_purchase_id()

        if purchase_id is None:
            QMessageBox.information(
                self,
                "Select Purchase",
                "Please select a purchase first.",
            )

            return

        answer = QMessageBox.question(
            self,
            "Receive Purchase",
            "Are you sure you want to receive this purchase?\n\n"
            "Receiving it will add the purchased quantities to inventory.",
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        with SessionLocal() as session:
            service = PurchaseService(session)

            try:
                purchase = service.receive_purchase(
                    purchase_id=purchase_id,
                    received_by=self.user.id,
                )

                session.commit()

                QMessageBox.information(
                    self,
                    "Purchase Received",
                    f"{purchase.purchase_number} has been received successfully.",
                )

            except ValueError as error:
                session.rollback()

                QMessageBox.warning(
                    self,
                    "Unable to Receive Purchase",
                    str(error),
                )

                return

        self.load_purchases()

    def cancel_purchase(self):
        purchase_id = self.get_selected_purchase_id()

        if purchase_id is None:
            QMessageBox.information(
                self,
                "Select Purchase",
                "Please select a purchase first.",
            )

            return

        answer = QMessageBox.question(
            self,
            "Cancel Purchase",
            "Are you sure you want to cancel this purchase?",
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        with SessionLocal() as session:
            service = PurchaseService(session)

            try:
                purchase = service.cancel_purchase(
                    purchase_id
                )

                session.commit()

                QMessageBox.information(
                    self,
                    "Purchase Cancelled",
                    f"{purchase.purchase_number} has been cancelled.",
                )

            except ValueError as error:
                session.rollback()

                QMessageBox.warning(
                    self,
                    "Unable to Cancel Purchase",
                    str(error),
                )

                return

        self.load_purchases()


class PurchaseItemsDialog(QDialog):
    def __init__(
        self,
        parent,
        purchase_id,
        purchase_number,
        user,
    ):
        super().__init__(parent)

        self.purchase_id = purchase_id
        self.purchase_number = purchase_number
        self.user = user

        self.setWindowTitle(
            f"Purchase Items - {purchase_number}"
        )

        self.setMinimumSize(900, 600)

        self.build_ui()
        self.load_variants()
        self.load_items()

    def build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel(
            f"Purchase {self.purchase_number}"
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

        form = QFormLayout()

        self.variant_combo = QComboBox()

        self.quantity_input = QSpinBox()
        self.quantity_input.setMinimum(1)
        self.quantity_input.setMaximum(1_000_000)

        self.cost_input = QLineEdit()
        self.cost_input.setPlaceholderText(
            "0.00"
        )

        form.addRow(
            "Product / Variant:",
            self.variant_combo,
        )

        form.addRow(
            "Quantity:",
            self.quantity_input,
        )

        form.addRow(
            "Unit Cost:",
            self.cost_input,
        )

        layout.addLayout(form)

        self.add_button = QPushButton(
            "ADD ITEM"
        )

        self.add_button.setMinimumHeight(40)

        layout.addWidget(
            self.add_button
        )

        self.items_table = QTableWidget()

        self.items_table.setColumnCount(5)

        self.items_table.setHorizontalHeaderLabels(
            [
                "Product / Variant",
                "Quantity",
                "Unit Cost",
                "Total",
                "Item ID",
            ]
        )

        self.items_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.items_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.items_table.horizontalHeader().setStretchLastSection(
            True
        )

        layout.addWidget(
            self.items_table
        )

        bottom_layout = QHBoxLayout()

        self.remove_button = QPushButton(
            "REMOVE SELECTED ITEM"
        )

        self.close_button = QPushButton(
            "CLOSE"
        )

        bottom_layout.addWidget(
            self.remove_button
        )

        bottom_layout.addStretch()

        bottom_layout.addWidget(
            self.close_button
        )

        layout.addLayout(
            bottom_layout
        )

        self.add_button.clicked.connect(
            self.add_item
        )

        self.remove_button.clicked.connect(
            self.remove_item
        )

        self.close_button.clicked.connect(
            self.accept
        )

    def load_variants(self):
        with SessionLocal() as session:
            product_service = ProductService(session)

            products = product_service.list_products()

            for product in products:
                for variant in product.variants:
                    if not variant.is_active:
                        continue

                    label = product.name

                    if variant.variant_name:
                        label += f" - {variant.variant_name}"

                    if variant.size:
                        label += f" ({variant.size}"

                        if variant.unit:
                            label += f" {variant.unit}"

                        label += ")"

                    self.variant_combo.addItem(
                        label,
                        variant.id,
                    )

    def load_items(self):
        with SessionLocal() as session:
            service = PurchaseService(session)

            purchase = service.get_by_id(
                self.purchase_id
            )

            if purchase is None:
                return

            self.items_table.setRowCount(
                len(purchase.items)
            )

            for row, item in enumerate(
                purchase.items
            ):
                product = item.product_variant.product

                label = product.name

                if item.product_variant.variant_name:
                    label += (
                        f" - "
                        f"{item.product_variant.variant_name}"
                    )

                self.items_table.setItem(
                    row,
                    0,
                    QTableWidgetItem(label),
                )

                self.items_table.setItem(
                    row,
                    1,
                    QTableWidgetItem(
                        str(item.quantity)
                    ),
                )

                self.items_table.setItem(
                    row,
                    2,
                    QTableWidgetItem(
                        f"{item.unit_cost:,.2f}"
                    ),
                )

                self.items_table.setItem(
                    row,
                    3,
                    QTableWidgetItem(
                        f"{item.total_cost:,.2f}"
                    ),
                )

                self.items_table.setItem(
                    row,
                    4,
                    QTableWidgetItem(
                        str(item.id)
                    ),
                )

    def add_item(self):
        if self.variant_combo.count() == 0:
            QMessageBox.warning(
                self,
                "No Products",
                "Please create an active product variant first.",
            )

            return

        variant_id = self.variant_combo.currentData()

        quantity = self.quantity_input.value()

        cost_text = (
            self.cost_input.text()
            .strip()
        )

        if not cost_text:
            QMessageBox.warning(
                self,
                "Unit Cost Required",
                "Please enter the unit cost.",
            )

            return

        try:
            unit_cost = Decimal(cost_text)

        except InvalidOperation:
            QMessageBox.warning(
                self,
                "Invalid Cost",
                "Please enter a valid unit cost.",
            )

            return

        if unit_cost < 0:
            QMessageBox.warning(
                self,
                "Invalid Cost",
                "Unit cost cannot be negative.",
            )

            return

        with SessionLocal() as session:
            service = PurchaseService(session)

            try:
                service.add_item(
                    purchase_id=self.purchase_id,
                    product_variant_id=variant_id,
                    quantity=quantity,
                    unit_cost=unit_cost,
                )

                session.commit()

            except ValueError as error:
                session.rollback()

                QMessageBox.warning(
                    self,
                    "Unable to Add Item",
                    str(error),
                )

                return

        self.cost_input.clear()
        self.quantity_input.setValue(1)

        self.load_items()

    def remove_item(self):
        row = self.items_table.currentRow()

        if row < 0:
            QMessageBox.information(
                self,
                "Select Item",
                "Please select an item first.",
            )

            return

        item_id = int(
            self.items_table.item(
                row,
                4,
            ).text()
        )

        answer = QMessageBox.question(
            self,
            "Remove Item",
            "Are you sure you want to remove this item?",
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        with SessionLocal() as session:
            service = PurchaseService(session)

            try:
                service.remove_item(
                    item_id
                )

                session.commit()

            except ValueError as error:
                session.rollback()

                QMessageBox.warning(
                    self,
                    "Unable to Remove Item",
                    str(error),
                )

                return

        self.load_items()
