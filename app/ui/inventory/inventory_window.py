from decimal import Decimal

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
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.database.connection import SessionLocal
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.services.inventory_service import InventoryService


class InventoryWindow(QWidget):
    def __init__(self, user):
        super().__init__()

        self.user = user

        self.setWindowTitle(
            "Inventory Management"
        )

        self.setMinimumSize(
            1100,
            650,
        )

        self.build_ui()
        self.load_inventory()

    def build_ui(self):
        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            25,
            25,
            25,
            25,
        )

        layout.setSpacing(15)

        title = QLabel(
            "Inventory Management"
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 26px;
                font-weight: bold;
            }
            """
        )

        layout.addWidget(title)

        description = QLabel(
            "View current stock, manage stock levels, "
            "and review inventory movements."
        )

        description.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
                color: #666666;
            }
            """
        )

        layout.addWidget(description)

        controls = QHBoxLayout()

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Search product, variant or SKU..."
        )

        self.search_input.textChanged.connect(
            self.filter_inventory
        )

        controls.addWidget(
            self.search_input
        )

        self.refresh_button = QPushButton(
            "REFRESH"
        )

        self.refresh_button.setMinimumHeight(
            40
        )

        self.refresh_button.clicked.connect(
            self.load_inventory
        )

        controls.addWidget(
            self.refresh_button
        )

        layout.addLayout(
            controls
        )

        self.inventory_table = QTableWidget()

        self.inventory_table.setColumnCount(
            7
        )

        self.inventory_table.setHorizontalHeaderLabels(
            [
                "Product",
                "Variant",
                "SKU",
                "Current Stock",
                "Reorder Level",
                "Status",
                "Actions",
            ]
        )

        self.inventory_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.inventory_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.inventory_table.setAlternatingRowColors(
            True
        )

        self.inventory_table.horizontalHeader().setStretchLastSection(
            True
        )

        layout.addWidget(
            self.inventory_table
        )

    def load_inventory(self):
        with SessionLocal() as session:
            variants = list(
                session.query(ProductVariant)
                .join(Product)
                .filter(
                    Product.is_active.is_(True),
                    ProductVariant.is_active.is_(True),
                )
                .order_by(
                    Product.name,
                    ProductVariant.variant_name,
                )
                .all()
            )

            inventory_service = InventoryService(
                session
            )

            rows = []

            for variant in variants:
                product = variant.product

                quantity = (
                    inventory_service.get_current_quantity(
                        variant.id
                    )
                )

                reorder_level = (
                    variant.reorder_level
                    if variant.reorder_level is not None
                    else 0
                )

                if quantity <= 0:
                    status = "OUT OF STOCK"
                elif quantity <= reorder_level:
                    status = "LOW STOCK"
                else:
                    status = "IN STOCK"

                rows.append(
                    (
                        product.name,
                        variant.variant_name or "-",
                        variant.sku or "-",
                        quantity,
                        reorder_level,
                        status,
                        variant.id,
                    )
                )

        self.inventory_table.setRowCount(
            len(rows)
        )

        for row_index, row_data in enumerate(rows):
            for column_index, value in enumerate(
                row_data[:6]
            ):
                item = QTableWidgetItem(
                    str(value)
                )

                if column_index in {
                    3,
                    4,
                }:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )

                self.inventory_table.setItem(
                    row_index,
                    column_index,
                    item,
                )

            action_widget = QWidget()

            action_layout = QHBoxLayout(
                action_widget
            )

            action_layout.setContentsMargins(
                2,
                2,
                2,
                2,
            )

            add_button = QPushButton(
                "ADD"
            )

            remove_button = QPushButton(
                "REMOVE"
            )

            history_button = QPushButton(
                "HISTORY"
            )

            variant_id = row_data[6]

            add_button.clicked.connect(
                lambda checked=False,
                variant_id=variant_id:
                self.add_stock(variant_id)
            )

            remove_button.clicked.connect(
                lambda checked=False,
                variant_id=variant_id:
                self.remove_stock(variant_id)
            )

            history_button.clicked.connect(
                lambda checked=False,
                variant_id=variant_id:
                self.show_history(variant_id)
            )

            action_layout.addWidget(
                add_button
            )

            action_layout.addWidget(
                remove_button
            )

            action_layout.addWidget(
                history_button
            )

            self.inventory_table.setCellWidget(
                row_index,
                6,
                action_widget,
            )

        self.filter_inventory(
            self.search_input.text()
        )

    def filter_inventory(
        self,
        search_text: str,
    ):
        search_text = (
            search_text.strip().lower()
        )

        for row in range(
            self.inventory_table.rowCount()
        ):
            if not search_text:
                self.inventory_table.setRowHidden(
                    row,
                    False,
                )

                continue

            values = []

            for column in range(3):
                item = self.inventory_table.item(
                    row,
                    column,
                )

                if item:
                    values.append(
                        item.text().lower()
                    )

            matches = any(
                search_text in value
                for value in values
            )

            self.inventory_table.setRowHidden(
                row,
                not matches,
            )

    def add_stock(
        self,
        product_variant_id: int,
    ):
        dialog = StockDialog(
            self,
            "Add Stock",
            [
                "OPENING_STOCK",
                "PURCHASE",
                "RETURN",
                "ADJUSTMENT",
            ],
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        quantity = dialog.quantity()
        movement_type = dialog.movement_type()
        reason = dialog.reason()

        with SessionLocal() as session:
            try:
                service = InventoryService(
                    session
                )

                service.add_stock(
                    product_variant_id=product_variant_id,
                    quantity=quantity,
                    movement_type=movement_type,
                    created_by=self.user.id,
                    reason=reason,
                )

                session.commit()

            except ValueError as error:
                session.rollback()

                QMessageBox.warning(
                    self,
                    "Inventory Error",
                    str(error),
                )

                return

        self.load_inventory()

    def remove_stock(
        self,
        product_variant_id: int,
    ):
        dialog = StockDialog(
            self,
            "Remove Stock",
            [
                "SALE",
                "DAMAGE",
                "ADJUSTMENT",
            ],
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        quantity = dialog.quantity()
        movement_type = dialog.movement_type()
        reason = dialog.reason()

        with SessionLocal() as session:
            try:
                service = InventoryService(
                    session
                )

                service.remove_stock(
                    product_variant_id=product_variant_id,
                    quantity=quantity,
                    movement_type=movement_type,
                    created_by=self.user.id,
                    reason=reason,
                )

                session.commit()

            except ValueError as error:
                session.rollback()

                QMessageBox.warning(
                    self,
                    "Inventory Error",
                    str(error),
                )

                return

        self.load_inventory()

    def show_history(
        self,
        product_variant_id: int,
    ):
        with SessionLocal() as session:
            service = InventoryService(
                session
            )

            movements = service.get_movements(
                product_variant_id
            )

            variant = session.get(
                ProductVariant,
                product_variant_id,
            )

            if variant is None:
                return

            product = variant.product

        dialog = QDialog(self)

        dialog.setWindowTitle(
            "Inventory Movement History"
        )

        dialog.setMinimumSize(
            800,
            450,
        )

        layout = QVBoxLayout(dialog)

        title = QLabel(
            f"{product.name} - "
            f"{variant.variant_name or 'Default Variant'}"
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

        table = QTableWidget()

        table.setColumnCount(
            6
        )

        table.setHorizontalHeaderLabels(
            [
                "Date",
                "Type",
                "Quantity",
                "Before",
                "After",
                "Reason",
            ]
        )

        table.setRowCount(
            len(movements)
        )

        for row, movement in enumerate(
            movements
        ):
            values = [
                movement.created_at.strftime(
                    "%Y-%m-%d %H:%M"
                ),
                movement.movement_type,
                movement.quantity,
                movement.quantity_before,
                movement.quantity_after,
                movement.reason or "-",
            ]

            for column, value in enumerate(
                values
            ):
                table.setItem(
                    row,
                    column,
                    QTableWidgetItem(
                        str(value)
                    ),
                )

        table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        table.horizontalHeader().setStretchLastSection(
            True
        )

        layout.addWidget(table)

        close_button = QPushButton(
            "CLOSE"
        )

        close_button.clicked.connect(
            dialog.accept
        )

        layout.addWidget(
            close_button
        )

        dialog.exec()


class StockDialog(QDialog):
    def __init__(
        self,
        parent,
        title: str,
        movement_types: list[str],
    ):
        super().__init__(parent)

        self.setWindowTitle(
            title
        )

        self.setMinimumWidth(
            420
        )

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.quantity_input = QSpinBox()

        self.quantity_input.setMinimum(
            1
        )

        self.quantity_input.setMaximum(
            1_000_000
        )

        form.addRow(
            "Quantity:",
            self.quantity_input,
        )

        self.type_input = QComboBox()

        self.type_input.addItems(
            movement_types
        )

        form.addRow(
            "Movement Type:",
            self.type_input,
        )

        self.reason_input = QLineEdit()

        self.reason_input.setPlaceholderText(
            "Optional reason"
        )

        form.addRow(
            "Reason:",
            self.reason_input,
        )

        layout.addLayout(
            form
        )

        buttons = QHBoxLayout()

        cancel_button = QPushButton(
            "CANCEL"
        )

        save_button = QPushButton(
            "SAVE"
        )

        cancel_button.clicked.connect(
            self.reject
        )

        save_button.clicked.connect(
            self.accept
        )

        buttons.addWidget(
            cancel_button
        )

        buttons.addWidget(
            save_button
        )

        layout.addLayout(
            buttons
        )

    def quantity(self) -> int:
        return self.quantity_input.value()

    def movement_type(self) -> str:
        return self.type_input.currentText()

    def reason(self) -> str | None:
        reason = (
            self.reason_input
            .text()
            .strip()
        )

        return reason or None