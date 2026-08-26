from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import Qt, QSizeF
from PySide6.QtGui import QPageSize, QTextDocument
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QSizePolicy,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.database.connection import SessionLocal
from app.services.product_service import ProductService
from app.services.sale_service import SaleService
from app.services.inventory_service import InventoryService


class SaleWindow(QWidget):
    PAYMENT_METHODS = [
        "CASH",
        "POS",
        "TRANSFER",
        "CARD",
        "OTHER",
    ]

    def __init__(self, user):
        super().__init__()

        self.user = user

        # Draft sale is created when the first product is added.
        self.sale_id = None

        # Product data used by the search/list.
        self.products_data = []
        self.last_receipt = None

        self.setWindowTitle("New Sale")
        self.setMinimumSize(1000, 760)

        self.build_ui()
        self.load_products()

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

        main_layout.setSpacing(10)

        # ======================================================
        # HEADER
        # ======================================================

        header_layout = QHBoxLayout()

        title = QLabel("NEW SALE")

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

        main_layout.addLayout(header_layout)

        # ======================================================
        # CUSTOMER
        # ======================================================

        customer_frame = QFrame()

        customer_frame.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        customer_layout = QHBoxLayout(
            customer_frame
        )

        customer_label = QLabel(
            "Customer:"
        )

        self.customer_input = QLineEdit()

        self.customer_input.setPlaceholderText(
            "Search customer (optional)"
        )

        customer_layout.addWidget(
            customer_label
        )

        customer_layout.addWidget(
            self.customer_input
        )

        main_layout.addWidget(
            customer_frame
        )

        # ======================================================
        # MAIN POS AREA
        # ======================================================

        content_layout = QHBoxLayout()

        # ======================================================
        # PRODUCTS
        # ======================================================

        product_frame = QFrame()

        product_frame.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        product_layout = QVBoxLayout(
            product_frame
        )

        product_title = QLabel(
            "PRODUCTS"
        )

        product_title.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
            }
            """
        )

        self.product_search = QLineEdit()

        self.product_search.setPlaceholderText(
            "Search product..."
        )

        self.product_search.textChanged.connect(
            self.filter_products
        )

        self.product_list = QListWidget()

        self.product_list.itemDoubleClicked.connect(
            self.add_product_from_list
        )

        product_layout.addWidget(
            product_title
        )

        product_layout.addWidget(
            self.product_search
        )

        product_layout.addWidget(
            self.product_list
        )

        content_layout.addWidget(
            product_frame,
            1,
        )

        # ======================================================
        # CART
        # ======================================================

        cart_frame = QFrame()

        cart_frame.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        cart_layout = QVBoxLayout(
            cart_frame
        )

        # Room for the cart table plus subtotal/discount/total.
        cart_frame.setMinimumHeight(335)
        cart_layout.setSpacing(6)

        cart_title = QLabel(
            "CART"
        )

        cart_title.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
            }
            """
        )

        self.cart_table = QTableWidget(
            0,
            6,
        )

        self.cart_table.setHorizontalHeaderLabels(
            [
                "Product",
                "Qty",
                "Price",
                "Discount",
                "Total",
                "Actions",
            ]
        )

        self.cart_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        # Give the cart enough fixed vertical room for five items.
        # Totals remain outside the table and below it.
        self.cart_table.setFixedHeight(230)
        self.cart_table.verticalHeader().setDefaultSectionSize(34)
        self.cart_table.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        self.cart_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        header = self.cart_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, header.ResizeMode.Stretch)
        header.setSectionResizeMode(1, header.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, header.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, header.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, header.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, header.ResizeMode.ResizeToContents)

        cart_layout.addWidget(
            cart_title
        )

        cart_layout.addWidget(
            self.cart_table
        )

        # ======================================================
        # TOTALS
        # ======================================================

        totals_layout = QGridLayout()

        subtotal_label = QLabel(
            "Subtotal:"
        )

        self.subtotal_value = QLabel(
            "₦0.00"
        )

        discount_label = QLabel(
            "Discount:"
        )

        self.discount_value = QLabel(
            "₦0.00"
        )

        total_label = QLabel(
            "TOTAL:"
        )

        self.total_value = QLabel(
            "₦0.00"
        )

        total_label.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
            }
            """
        )

        self.total_value.setStyleSheet(
            """
            QLabel {
                font-size: 22px;
                font-weight: bold;
            }
            """
        )

        totals_layout.addWidget(
            subtotal_label,
            0,
            0,
        )

        totals_layout.addWidget(
            self.subtotal_value,
            0,
            1,
        )

        totals_layout.addWidget(
            discount_label,
            1,
            0,
        )

        totals_layout.addWidget(
            self.discount_value,
            1,
            1,
        )

        totals_layout.addWidget(
            total_label,
            2,
            0,
        )

        totals_layout.addWidget(
            self.total_value,
            2,
            1,
        )

        self.subtotal_value.setAlignment(
            Qt.AlignmentFlag.AlignRight
        )
        self.discount_value.setAlignment(
            Qt.AlignmentFlag.AlignRight
        )
        self.total_value.setAlignment(
            Qt.AlignmentFlag.AlignRight
        )

        totals_layout.setColumnStretch(0, 1)
        totals_layout.setColumnStretch(1, 1)

        cart_layout.addLayout(
            totals_layout
        )

        content_layout.addWidget(
            cart_frame,
            2,
        )

        main_layout.addLayout(
            content_layout
        )

        # ======================================================
        # PAYMENT SECTION
        # ======================================================

        payment_frame = QFrame()

        payment_frame.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        payment_layout = QVBoxLayout(
            payment_frame
        )

        payment_title_layout = QHBoxLayout()

        payment_title = QLabel(
            "PAYMENTS"
        )

        payment_title.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
            }
            """
        )

        self.add_payment_button = QPushButton(
            "+ ADD PAYMENT"
        )

        self.add_payment_button.clicked.connect(
            self.add_payment_row
        )

        payment_title_layout.addWidget(
            payment_title
        )

        payment_title_layout.addStretch()

        payment_title_layout.addWidget(
            self.add_payment_button
        )

        payment_layout.addLayout(
            payment_title_layout
        )

        # ------------------------------------------------------
        # SALE DISCOUNT
        # ------------------------------------------------------
        discount_layout = QHBoxLayout()

        discount_layout.addWidget(
            QLabel("Discount:")
        )

        self.sale_discount_input = QLineEdit()
        self.sale_discount_input.setPlaceholderText("0.00")
        self.sale_discount_input.setMaximumWidth(140)
        self.sale_discount_input.setAlignment(
            Qt.AlignmentFlag.AlignRight
        )

        discount_layout.addWidget(
            self.sale_discount_input
        )

        discount_layout.addWidget(
            QLabel("Approved By:")
        )

        self.discount_approved_by_input = QLineEdit()
        self.discount_approved_by_input.setPlaceholderText(
            "Name of person who approved discount"
        )

        discount_layout.addWidget(
            self.discount_approved_by_input,
            1,
        )

        payment_layout.addLayout(
            discount_layout
        )

        self.sale_discount_input.editingFinished.connect(
            self.apply_sale_discount
        )

        self.discount_approved_by_input.editingFinished.connect(
            self.save_discount_approval
        )

        # ------------------------------------------------------
        # PAYMENT TABLE
        # ------------------------------------------------------

        self.payment_table = QTableWidget(
            0,
            3,
        )

        self.payment_table.setHorizontalHeaderLabels(
            [
                "Payment Method",
                "Amount",
                "Action",
            ]
        )

        self.payment_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.payment_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.payment_table.horizontalHeader().setStretchLastSection(
            True
        )

        # Keep the payment area compact so the cart can show more items.
        self.payment_table.setMinimumHeight(65)
        self.payment_table.setMaximumHeight(95)

        payment_layout.addWidget(
            self.payment_table
        )

        # ------------------------------------------------------
        # PAYMENT SUMMARY
        # ------------------------------------------------------

        payment_summary = QGridLayout()

        paid_label = QLabel(
            "Paid:"
        )

        self.paid_value = QLabel(
            "₦0.00"
        )

        remaining_label = QLabel(
            "Remaining:"
        )

        self.remaining_value = QLabel(
            "₦0.00"
        )

        self.remaining_value.setStyleSheet(
            """
            QLabel {
                font-weight: bold;
            }
            """
        )

        payment_summary.addWidget(
            paid_label,
            0,
            0,
        )

        payment_summary.addWidget(
            self.paid_value,
            0,
            1,
        )

        payment_summary.addWidget(
            remaining_label,
            1,
            0,
        )

        payment_summary.addWidget(
            self.remaining_value,
            1,
            1,
        )

        payment_layout.addLayout(
            payment_summary
        )

        # ------------------------------------------------------
        # RECEIPT ACTIONS
        # ------------------------------------------------------

        receipt_actions = QHBoxLayout()

        self.print_receipt_button = QPushButton(
            "PRINT RECEIPT"
        )
        self.print_receipt_button.setEnabled(False)
        self.print_receipt_button.clicked.connect(
            self.print_receipt
        )

        self.save_receipt_button = QPushButton(
            "SAVE PDF"
        )
        self.save_receipt_button.setEnabled(False)
        self.save_receipt_button.clicked.connect(
            self.save_receipt_pdf
        )

        receipt_actions.addWidget(
            self.print_receipt_button
        )
        receipt_actions.addWidget(
            self.save_receipt_button
        )

        self.close_sale_button = QPushButton(
            "CLOSE SALE / NEW SALE"
        )
        self.close_sale_button.setMinimumHeight(40)
        self.close_sale_button.setEnabled(False)
        self.close_sale_button.setStyleSheet(
            """
            QPushButton {
                background-color: #34495e;
                color: white;
                border: none;
                padding: 10px 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2c3e50;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #eeeeee;
            }
            """
        )
        self.close_sale_button.clicked.connect(
            self.close_completed_sale
        )

        receipt_actions.addWidget(
            self.close_sale_button
        )

        payment_layout.addLayout(
            receipt_actions
        )

        # ------------------------------------------------------
        # COMPLETE SALE
        # ------------------------------------------------------

        self.complete_button = QPushButton(
            "COMPLETE SALE"
        )

        self.complete_button.setMinimumHeight(
            45
        )

        self.complete_button.setStyleSheet(
            """
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 12px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #2ecc71;
            }

            QPushButton:disabled {
                background-color: #95a5a6;
                color: #eeeeee;
            }
            """
        )

        self.complete_button.clicked.connect(
            self.complete_sale
        )

        payment_layout.addWidget(
            self.complete_button
        )

        main_layout.addWidget(
            payment_frame
        )

        # Start with one payment row.
        self.add_payment_row()

        self.update_payment_summary()

    # ==========================================================
    # PRODUCTS
    # ==========================================================

    def load_products(self):
        with SessionLocal() as session:

            product_service = ProductService(
                session
            )

            products = product_service.list_products(
                active_only=True
            )

            self.products_data = []

            for product in products:

                variants = product_service.list_variants(
                    product.id,
                    active_only=True,
                )

                for variant in variants:

                    self.products_data.append(
                        {
                            "variant_id": variant.id,
                            "product_name": product.name,
                            "variant_name": (
                                variant.variant_name
                                or ""
                            ),
                            "sku": (
                                variant.sku
                                or "N/A"
                            ),
                            "price": Decimal(
                                str(
                                    variant.selling_price
                                )
                            ),
                        }
                    )

        self.display_products(
            self.products_data
        )

    def display_products(
        self,
        products,
    ):
        self.product_list.clear()

        for product in products:

            variant_name = product[
                "variant_name"
            ]

            if variant_name:
                display_name = (
                    f"{product['product_name']} "
                    f"({variant_name})"
                )
            else:
                display_name = product[
                    "product_name"
                ]

            text = (
                f"{display_name} | "
                f"SKU: {product['sku']} | "
                f"₦{product['price']:,.2f}"
            )

            item = QListWidgetItem(
                text
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                product["variant_id"],
            )

            self.product_list.addItem(
                item
            )

    def filter_products(
        self,
        text,
    ):
        text = text.strip().lower()

        if not text:
            self.display_products(
                self.products_data
            )
            return

        filtered = []

        for product in self.products_data:

            searchable = " ".join(
                [
                    product["product_name"],
                    product["variant_name"],
                    product["sku"],
                ]
            ).lower()

            if text in searchable:
                filtered.append(
                    product
                )

        self.display_products(
            filtered
        )

    def add_product_from_list(
        self,
        item,
    ):
        variant_id = item.data(
            Qt.ItemDataRole.UserRole
        )

        if variant_id is None:
            return

        self.add_product_to_sale(
            variant_id
        )

    # ==========================================================
    # SALE / CART
    # ==========================================================

    def ensure_sale(self):
        if self.sale_id is not None:
            return self.sale_id

        with SessionLocal() as session:

            service = SaleService(
                session
            )

            sale = service.create_sale(
                sale_date=date.today(),
                created_by=self.user.id,
            )

            session.commit()

            self.sale_id = sale.id

        return self.sale_id

    def add_product_to_sale(
        self,
        variant_id,
    ):
        try:
            # Check stock BEFORE adding the product to the draft sale.
            # This gives the cashier an immediate warning instead of
            # waiting until COMPLETE SALE.
            with SessionLocal() as session:
                inventory_service = InventoryService(session)
                available = int(
                    inventory_service.get_current_quantity(variant_id)
                )

                product_name = "Selected product"
                for product in self.products_data:
                    if product["variant_id"] == variant_id:
                        product_name = product["product_name"]
                        if product.get("variant_name"):
                            product_name += f" ({product['variant_name']})"
                        break

                current_quantity = 0
                if self.sale_id is not None:
                    service = SaleService(session)
                    sale = service.get_sale(self.sale_id)
                    if sale is not None:
                        current_quantity = sum(
                            int(item.quantity)
                            for item in sale.items
                            if item.product_variant_id == variant_id
                        )

                if available <= 0:
                    QMessageBox.warning(
                        self,
                        "Out of Stock",
                        f"{product_name} is out of stock.",
                    )
                    return

                if current_quantity >= available:
                    QMessageBox.warning(
                        self,
                        "Insufficient Stock",
                        f"{product_name} has only {available} in stock.\n\n"
                        f"You already have {current_quantity} in this sale.",
                    )
                    return

            sale_id = self.ensure_sale()

            with SessionLocal() as session:
                service = SaleService(session)

                service.add_item(
                    sale_id=sale_id,
                    product_variant_id=variant_id,
                    quantity=1,
                )

                session.commit()

            self.refresh_cart()
            self.update_payment_summary()

        except Exception as exc:
            QMessageBox.warning(
                self,
                "Unable to Add Product",
                str(exc),
            )

    def refresh_cart(self):
        if self.sale_id is None:
            self.cart_table.setRowCount(0)

            self.subtotal_value.setText(
                "₦0.00"
            )

            self.discount_value.setText(
                "₦0.00"
            )

            self.total_value.setText(
                "₦0.00"
            )

            return

        with SessionLocal() as session:

            service = SaleService(
                session
            )

            sale = service.get_sale(
                self.sale_id
            )

            if sale is None:
                return

            self.cart_table.setRowCount(
                len(sale.items)
            )

            for row, item in enumerate(
                sale.items
            ):

                variant = item.product_variant

                product = variant.product

                variant_name = (
                    variant.variant_name
                    or ""
                )

                if variant_name:
                    product_name = (
                        f"{product.name} "
                        f"({variant_name})"
                    )
                else:
                    product_name = product.name

                self.cart_table.setItem(
                    row,
                    0,
                    QTableWidgetItem(
                        product_name
                    ),
                )

                self.cart_table.setItem(
                    row,
                    1,
                    QTableWidgetItem(
                        str(item.quantity)
                    ),
                )

                self.cart_table.setItem(
                    row,
                    2,
                    QTableWidgetItem(
                        f"₦{Decimal(str(item.unit_price)):,.2f}"
                    ),
                )

                self.cart_table.setItem(
                    row,
                    3,
                    QTableWidgetItem(
                        f"₦{Decimal(str(item.discount)):,.2f}"
                    ),
                )

                self.cart_table.setItem(
                    row,
                    4,
                    QTableWidgetItem(
                        f"₦{Decimal(str(item.total_price)):,.2f}"
                    ),
                )

                # ----------------------------------------------
                # CART ACTIONS: - / + / X
                # ----------------------------------------------
                actions = QWidget()
                actions_layout = QHBoxLayout(actions)
                actions_layout.setContentsMargins(4, 2, 4, 2)
                actions_layout.setSpacing(4)

                minus_button = QPushButton("−")
                minus_button.setFixedSize(32, 28)
                minus_button.setToolTip("Reduce quantity")
                minus_button.setEnabled(int(item.quantity) > 1)

                qty_label = QLabel(str(item.quantity))
                qty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                qty_label.setMinimumWidth(28)

                plus_button = QPushButton("+")
                plus_button.setFixedSize(32, 28)
                plus_button.setToolTip("Increase quantity")

                remove_button = QPushButton("×")
                remove_button.setFixedSize(32, 28)
                remove_button.setToolTip("Remove item")

                minus_button.clicked.connect(
                    lambda checked=False, item_id=item.id: self.change_cart_quantity(
                        item_id, -1
                    )
                )
                plus_button.clicked.connect(
                    lambda checked=False, item_id=item.id: self.change_cart_quantity(
                        item_id, 1
                    )
                )
                remove_button.clicked.connect(
                    lambda checked=False, item_id=item.id: self.remove_cart_item(
                        item_id
                    )
                )

                actions_layout.addWidget(minus_button)
                actions_layout.addWidget(qty_label)
                actions_layout.addWidget(plus_button)
                actions_layout.addWidget(remove_button)
                actions_layout.addStretch()

                self.cart_table.setCellWidget(
                    row,
                    5,
                    actions,
                )
                self.cart_table.setRowHeight(row, 34)

            self.subtotal_value.setText(
                f"₦{Decimal(str(sale.subtotal)):,.2f}"
            )

            self.discount_value.setText(
                f"₦{Decimal(str(sale.discount)):,.2f}"
            )

            self.total_value.setText(
                f"₦{Decimal(str(sale.total_amount)):,.2f}"
            )

            # Keep the discount controls synchronized with the draft sale.
            self.sale_discount_input.blockSignals(True)
            self.sale_discount_input.setText(
                f"{Decimal(str(sale.discount)):,.2f}"
            )
            self.sale_discount_input.blockSignals(False)

            approver = ""
            for note_line in (sale.notes or "").splitlines():
                if note_line.startswith("DISCOUNT_APPROVED_BY:"):
                    approver = note_line.split(
                        ":", 1
                    )[1].strip()

            self.discount_approved_by_input.blockSignals(True)
            self.discount_approved_by_input.setText(approver)
            self.discount_approved_by_input.blockSignals(False)

    # ==========================================================
    # CART ACTIONS
    # ==========================================================

    def change_cart_quantity(self, item_id, delta):
        if self.sale_id is None:
            return

        try:
            with SessionLocal() as session:
                service = SaleService(session)
                sale = service.get_sale(self.sale_id)

                if sale is None or sale.status != "DRAFT":
                    return

                item = next(
                    (sale_item for sale_item in sale.items if sale_item.id == item_id),
                    None,
                )

                if item is None:
                    return

                current_quantity = int(item.quantity)
                new_quantity = current_quantity + int(delta)

                if new_quantity < 1:
                    return

                if delta > 0:
                    inventory_service = InventoryService(session)
                    available = int(
                        inventory_service.get_current_quantity(
                            item.product_variant_id
                        )
                    )

                    if new_quantity > available:
                        variant = item.product_variant
                        product_name = variant.product.name
                        if variant.variant_name:
                            product_name += f" ({variant.variant_name})"

                        QMessageBox.warning(
                            self,
                            "Insufficient Stock",
                            f"Cannot increase {product_name}.\n\n"
                            f"Available stock: {available}\n"
                            f"Already in this sale: {current_quantity}",
                        )
                        return

                # SaleService does not expose an update-item method, so
                # replace this line item with the requested quantity.
                # Preserve its existing line discount.
                discount = Decimal(str(item.discount))
                service.remove_item(item.id)
                service.add_item(
                    sale_id=self.sale_id,
                    product_variant_id=item.product_variant_id,
                    quantity=new_quantity,
                    discount=discount,
                )

                session.commit()

            self.refresh_cart()
            self.update_payment_summary()

        except Exception as exc:
            QMessageBox.warning(
                self,
                "Unable to Change Quantity",
                str(exc),
            )

    def remove_cart_item(self, item_id):
        if self.sale_id is None:
            return

        try:
            with SessionLocal() as session:
                service = SaleService(session)
                sale = service.get_sale(self.sale_id)

                if sale is None or sale.status != "DRAFT":
                    return

                item = next(
                    (sale_item for sale_item in sale.items if sale_item.id == item_id),
                    None,
                )

                if item is None:
                    return

                service.remove_item(item.id)
                session.commit()

            self.refresh_cart()
            self.update_payment_summary()

        except Exception as exc:
            QMessageBox.warning(
                self,
                "Unable to Remove Item",
                str(exc),
            )

    # ==========================================================
    # SALE DISCOUNT
    # ==========================================================

    def apply_sale_discount(self):
        if self.sale_id is None:
            return

        text = self.sale_discount_input.text().strip()

        if not text:
            text = "0"

        try:
            discount = Decimal(text.replace(",", ""))

        except InvalidOperation:
            QMessageBox.warning(
                self,
                "Invalid Discount",
                "Please enter a valid discount amount.",
            )
            self.sale_discount_input.setFocus()
            return

        if discount < 0:
            QMessageBox.warning(
                self,
                "Invalid Discount",
                "Discount cannot be negative.",
            )
            return

        try:
            with SessionLocal() as session:
                service = SaleService(session)

                sale = service.get_sale(self.sale_id)

                if sale is None:
                    raise ValueError("Sale not found.")

                subtotal = Decimal(
                    str(sale.subtotal)
                )

                if discount > subtotal:
                    raise ValueError(
                        "Discount cannot exceed the sale subtotal."
                    )

                if discount > 0:
                    approver = (
                        self.discount_approved_by_input
                        .text()
                        .strip()
                    )

                    if not approver:
                        QMessageBox.warning(
                            self,
                            "Discount Approval Required",
                            "Please enter the name of the person who approved this discount.",
                        )
                        self.discount_approved_by_input.setFocus()
                        return

                service.calculate_totals(
                    self.sale_id,
                    discount=discount,
                )

                # Keep the approval record in the existing Sale.notes
                # field so no database schema change is required.
                if discount > 0:
                    marker = "DISCOUNT_APPROVED_BY:"
                    existing_notes = sale.notes or ""

                    lines = [
                        line
                        for line in existing_notes.splitlines()
                        if not line.startswith(marker)
                    ]

                    lines.append(
                        f"{marker} {self.discount_approved_by_input.text().strip()}"
                    )

                    sale.notes = "\n".join(
                        line for line in lines if line.strip()
                    )
                else:
                    marker = "DISCOUNT_APPROVED_BY:"
                    existing_notes = sale.notes or ""

                    sale.notes = "\n".join(
                        line
                        for line in existing_notes.splitlines()
                        if not line.startswith(marker)
                    ) or None

                session.commit()

            self.refresh_cart()
            self.update_payment_summary()

        except (ValueError, InvalidOperation) as exc:
            QMessageBox.warning(
                self,
                "Unable to Apply Discount",
                str(exc),
            )

    def save_discount_approval(self):
        # Approval is saved together with the discount.
        if self.sale_id is None:
            return

        if self.sale_discount_input.text().strip():
            self.apply_sale_discount()

    # ==========================================================
    # PAYMENTS
    # ==========================================================

    def add_payment_row(self):
        if self.last_receipt:
            return

        row = self.payment_table.rowCount()

        self.payment_table.insertRow(
            row
        )

        # ------------------------------------------------------
        # METHOD
        # ------------------------------------------------------

        method_combo = QComboBox()

        method_combo.addItems(
            self.PAYMENT_METHODS
        )

        method_combo.currentIndexChanged.connect(
            self.update_payment_summary
        )

        self.payment_table.setCellWidget(
            row,
            0,
            method_combo
        )

        # ------------------------------------------------------
        # AMOUNT
        # ------------------------------------------------------

        amount_input = QLineEdit()

        amount_input.setPlaceholderText(
            "Amount"
        )

        amount_input.setAlignment(
            Qt.AlignmentFlag.AlignRight
        )

        amount_input.textChanged.connect(
            self.update_payment_summary
        )

        self.payment_table.setCellWidget(
            row,
            1,
            amount_input
        )

        # ------------------------------------------------------
        # REMOVE
        # ------------------------------------------------------

        remove_button = QPushButton(
            "REMOVE"
        )

        remove_button.clicked.connect(
            lambda checked=False, r=row:
            self.remove_payment_row(
                r
            )
        )

        self.payment_table.setCellWidget(
            row,
            2,
            remove_button
        )

        self.update_payment_summary()

    def remove_payment_row(
        self,
        row,
    ):
        if self.last_receipt:
            return

        if (
            row < 0
            or row >= self.payment_table.rowCount()
        ):
            return

        self.payment_table.removeRow(
            row
        )

        self.rebuild_payment_actions()

        self.update_payment_summary()

    def rebuild_payment_actions(self):
        """
        Reconnect REMOVE buttons after rows are
        inserted or deleted so they always point
        to the correct row.
        """

        for row in range(
            self.payment_table.rowCount()
        ):

            button = QPushButton(
                "REMOVE"
            )

            button.clicked.connect(
                lambda checked=False, r=row:
                self.remove_payment_row(
                    r
                )
            )

            self.payment_table.setCellWidget(
                row,
                2,
                button
            )

    def get_pending_payments(self):
        payments = []

        for row in range(
            self.payment_table.rowCount()
        ):

            method_widget = (
                self.payment_table.cellWidget(
                    row,
                    0,
                )
            )

            amount_widget = (
                self.payment_table.cellWidget(
                    row,
                    1,
                )
            )

            if (
                method_widget is None
                or amount_widget is None
            ):
                continue

            method = (
                method_widget.currentText()
                .strip()
            )

            amount_text = (
                amount_widget.text()
                .strip()
                .replace(",", "")
                .replace("₦", "")
            )

            if not amount_text:
                continue

            try:
                amount = Decimal(
                    amount_text
                )
            except InvalidOperation:
                raise ValueError(
                    f"Invalid payment amount "
                    f"on row {row + 1}."
                )

            if amount <= 0:
                raise ValueError(
                    f"Payment amount on row "
                    f"{row + 1} must be greater than zero."
                )

            payments.append(
                (
                    method,
                    amount,
                )
            )

        return payments

    def get_total_pending_payment(
        self,
    ):
        total = Decimal(
            "0.00"
        )

        for _, amount in self.get_pending_payments():
            total += amount

        return total

    def update_payment_summary(self):
        try:
            paid = (
                self.get_total_pending_payment()
            )
        except ValueError:
            paid = Decimal(
                "0.00"
            )

        total = Decimal(
            "0.00"
        )

        if self.sale_id is not None:

            with SessionLocal() as session:

                service = SaleService(
                    session
                )

                sale = service.get_sale(
                    self.sale_id
                )

                if sale is not None:
                    total = Decimal(
                        str(
                            sale.total_amount
                        )
                    )

        remaining = (
            total - paid
        )

        if remaining < 0:
            remaining = Decimal(
                "0.00"
            )

        self.paid_value.setText(
            f"₦{paid:,.2f}"
        )

        self.remaining_value.setText(
            f"₦{remaining:,.2f}"
        )

        # Enable complete only when:
        # 1. There is a sale.
        # 2. There is a positive total.
        # 3. Payments exactly equal total.

        discount_approval_ok = True

        if self.sale_id is not None:
            with SessionLocal() as session:
                sale = SaleService(session).get_sale(
                    self.sale_id
                )

                if sale is not None:
                    sale_discount = Decimal(
                        str(sale.discount)
                    )

                    if sale_discount > 0:
                        discount_approval_ok = bool(
                            self.discount_approved_by_input
                            .text()
                            .strip()
                        )

        can_complete = (
            self.sale_id is not None
            and total > 0
            and paid == total
            and discount_approval_ok
        )

        self.complete_button.setEnabled(
            can_complete
        )

    # ==========================================================
    # COMPLETE SALE
    # ==========================================================

    def complete_sale(self):
        if self.sale_id is None:

            QMessageBox.warning(
                self,
                "No Sale",
                "Please add at least one product.",
            )

            return

        try:
            pending_payments = (
                self.get_pending_payments()
            )

        except ValueError as exc:

            QMessageBox.warning(
                self,
                "Invalid Payment",
                str(exc),
            )

            return

        if not pending_payments:

            QMessageBox.warning(
                self,
                "Payment Required",
                "Please add at least one payment.",
            )

            return

        try:
            with SessionLocal() as session:

                service = SaleService(
                    session
                )

                sale = service.get_sale(
                    self.sale_id
                )

                if sale is None:
                    raise ValueError(
                        "Sale not found."
                    )

                total = Decimal(
                    str(sale.total_amount)
                )

                pending_total = sum(
                    (
                        amount
                        for _, amount
                        in pending_payments
                    ),
                    Decimal("0.00"),
                )

                if pending_total != total:

                    difference = (
                        total
                        - pending_total
                    )

                    if difference > 0:
                        raise ValueError(
                            f"Payment is short by "
                            f"₦{difference:,.2f}."
                        )

                    raise ValueError(
                        f"Payment exceeds sale total "
                        f"by ₦{abs(difference):,.2f}."
                    )

                for method, amount in (
                    pending_payments
                ):
                    service.add_payment(
                        sale_id=self.sale_id,
                        amount=amount,
                        payment_method=method,
                        created_by=self.user.id,
                    )

                completed_sale = (
                    service.complete_sale(
                        self.sale_id
                    )
                )

                session.commit()

                sale_number = (
                    completed_sale.sale_number
                )

                total_amount = Decimal(
                    str(
                        completed_sale.total_amount
                    )
                )

                # Build a printer-independent snapshot while the
                # SQLAlchemy session is still open.
                self.last_receipt = self.build_receipt_data(
                    completed_sale
                )

            QMessageBox.information(
                self,
                "Sale Completed",
                (
                    f"Sale {sale_number} completed successfully.\n\n"
                    f"Total: ₦{total_amount:,.2f}\n\n"
                    "The completed sale remains on screen.\n"
                    "Print or save the receipt, then click CLOSE SALE / NEW SALE."
                ),
            )

            # Keep the completed transaction visible until the cashier
            # explicitly closes it. This prevents the sale from appearing
            # to reset before the receipt has been printed or saved.
            self.print_receipt_button.setEnabled(True)
            self.save_receipt_button.setEnabled(True)
            self.close_sale_button.setEnabled(True)

            self.product_search.setEnabled(False)
            self.product_list.setEnabled(False)
            self.customer_input.setEnabled(False)
            self.add_payment_button.setEnabled(False)
            self.payment_table.setEnabled(False)
            self.cart_table.setEnabled(False)
            self.complete_button.setEnabled(False)



        except Exception as exc:

            QMessageBox.critical(
                self,
                "Unable to Complete Sale",
                str(exc),
            )

    def close_completed_sale(self):
        if not self.last_receipt:
            return

        answer = QMessageBox.question(
            self,
            "Close Sale",
            "Close this completed sale and prepare the screen for the next customer?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.reset_sale()
        self.last_receipt = None

        self.product_search.setEnabled(True)
        self.product_list.setEnabled(True)
        self.customer_input.setEnabled(True)
        self.add_payment_button.setEnabled(True)
        self.payment_table.setEnabled(True)
        self.cart_table.setEnabled(True)
        self.complete_button.setEnabled(False)
        self.close_sale_button.setEnabled(False)

    # ==========================================================
    # RECEIPT
    # ==========================================================

    def build_receipt_data(self, sale):
        items = []

        for item in sale.items:
            variant = item.product_variant
            product = variant.product

            name = product.name
            if variant.variant_name:
                name += f" ({variant.variant_name})"

            items.append(
                {
                    "name": name,
                    "quantity": int(item.quantity),
                    "unit_price": Decimal(str(item.unit_price)),
                    "total": Decimal(str(item.total_price)),
                }
            )

        payments = [
            {
                "method": payment.payment_method,
                "amount": Decimal(str(payment.amount)),
            }
            for payment in sale.payments
        ]

        return {
            "sale_number": sale.sale_number,
            "date": str(sale.sale_date),
            "customer": (
                getattr(sale.customer, "name", None)
                if sale.customer is not None
                else None
            ),
            "items": items,
            "subtotal": Decimal(str(sale.subtotal)),
            "discount": Decimal(str(sale.discount)),
            "total": Decimal(str(sale.total_amount)),
            "payments": payments,
        }

    def receipt_html(self):
        """Build a compact, professional 80mm thermal receipt."""
        if not self.last_receipt:
            raise ValueError("No completed receipt is available.")

        from html import escape

        receipt = self.last_receipt

        sale_number = escape(str(receipt["sale_number"]))
        sale_date = escape(str(receipt["date"]))
        customer = (
            escape(str(receipt["customer"]))
            if receipt.get("customer")
            else ""
        )

        rows = []
        for item in receipt["items"]:
            name = escape(str(item["name"]))
            quantity = int(item["quantity"])
            unit_price = Decimal(str(item["unit_price"]))
            line_total = Decimal(str(item["total"]))

            rows.append(
                f"""
                <tr class=\"item-row\">
                    <td class=\"item-name\">{name}</td>
                    <td class=\"qty\">{quantity}</td>
                    <td class=\"amount\">₦{line_total:,.2f}</td>
                </tr>
                <tr class=\"unit-row\">
                    <td colspan=\"3\">₦{unit_price:,.2f} each</td>
                </tr>
                """
            )

        payment_rows = []
        for payment in receipt["payments"]:
            payment_rows.append(
                f"""
                <tr>
                    <td class=\"payment-method\">{escape(str(payment['method']))}</td>
                    <td class=\"amount\">₦{Decimal(str(payment['amount'])):,.2f}</td>
                </tr>
                """
            )

        customer_row = ""
        if customer:
            customer_row = f"""
                <tr>
                    <td class=\"meta-label\">Customer</td>
                    <td class=\"meta-value\">{customer}</td>
                </tr>
            """

        # Keep this as an f-string. CSS braces are escaped as {{ }} so they
        # can never be interpreted as Python format placeholders.
        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset=\"utf-8\">
<style>
    @page {{ margin: 0; }}
    * {{ box-sizing: border-box; }}

    body {{
        margin: 0;
        padding: 0;
        background: #fff;
        color: #111;
        font-family: Arial, Helvetica, sans-serif;
        font-size: 6.5pt;
    }}

    .receipt {{
        width: 72mm;
        margin: 0 auto;
        padding: 2.5mm 0 4mm 0;
    }}

    .center {{ text-align: center; }}

    /* 80mm thermal printer: deliberate two-line shop name */
    .brand {{
        font-size: 8pt;
        font-weight: 700;
        line-height: 1.12;
        margin: 0 0 1.2mm 0;
        white-space: normal;
    }}

    .brand-line {{ display: block; }}

    .phone {{
        font-size: 6pt;
        line-height: 1.1;
        margin-bottom: 0.7mm;
    }}

    .social {{
        font-size: 6pt;
        line-height: 1.1;
        margin-bottom: 2.2mm;
    }}

    .rule {{
        border-top: 0.25mm dashed #777;
        margin: 1.8mm 0;
    }}

    table {{
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
    }}

    td {{
        padding: 0.35mm 0;
        vertical-align: top;
        line-height: 1.12;
    }}

    .meta-label {{
        width: 30%;
        font-weight: 700;
        white-space: nowrap;
    }}

    .meta-value {{
        width: 70%;
        text-align: right;
        word-break: break-word;
    }}

    .section {{
        font-size: 7pt;
        font-weight: 700;
        margin: 0.5mm 0 0.8mm 0;
    }}

    .item-name {{
        width: 62%;
        padding-right: 1mm;
        word-break: break-word;
        overflow-wrap: anywhere;
    }}

    .qty {{
        width: 10%;
        text-align: center;
        white-space: nowrap;
    }}

    .amount {{
        width: 28%;
        text-align: right;
        white-space: nowrap;
    }}

    .item-header td {{
        font-size: 6.5pt;
        font-weight: 700;
        padding-bottom: 0.7mm;
    }}

    .item-row td {{
        padding-top: 1.2mm;
        font-size: 6.5pt;
    }}

    .unit-row td {{
        padding-top: 0;
        padding-bottom: 0.9mm;
        font-size: 5.8pt;
        color: #555;
    }}

    /* Deliberate breathing room after the last product */
    .after-items {{ height: 4.5mm; }}

    .summary td {{
        font-size: 6.5pt;
        padding: 0.55mm 0;
    }}

    .summary-label {{
        width: 55%;
        text-align: left;
        padding-right: 1.5mm;
    }}

    .summary .amount {{
        width: 45%;
        padding-left: 1.5mm;
        text-align: right;
    }}

    .total td {{
        font-size: 8pt;
        font-weight: 700;
        padding-top: 1.2mm;
        padding-bottom: 0.7mm;
    }}

    .payment td {{
        font-size: 6.5pt;
        padding: 0.55mm 0;
    }}

    .payment-method {{
        width: 55%;
        text-align: left;
    }}

    .footer-spacer {{
        height: 5mm;
        line-height: 1px;
        font-size: 1pt;
    }}

    .footer {{
        margin-top: 0;
        padding-top: 0;
        text-align: center;
    }}

    .motto {{
        font-size: 7.5pt;
        font-weight: 700;
        line-height: 1.15;
    }}

    .thanks {{
        margin-top: 0.8mm;
        font-size: 6pt;
        line-height: 1.1;
    }}
</style>
</head>
<body>
<div class=\"receipt\">
    <div class=\"center\">
        <div class=\"brand\">
            <span class=\"brand-line\">SHOPFAVE LUXE</span>
            <span class=\"brand-line\">SCENTS AND GIFTS</span>
        </div>
        <div class=\"phone\">PHONE: +2349036985527</div>
    </div>

    <div class=\"rule\"></div>

    <table>
        <tr>
            <td class=\"meta-label\">Receipt No:</td>
            <td class=\"meta-value\">{sale_number}</td>
        </tr>
        <tr>
            <td class=\"meta-label\">Date:</td>
            <td class=\"meta-value\">{sale_date}</td>
        </tr>
        {customer_row}
    </table>

    <div class=\"rule\"></div>
    <div class=\"section\">ITEMS</div>

    <table>
        <tr class=\"item-header\">
            <td class=\"item-name\">ITEM</td>
            <td class=\"qty\">QTY</td>
            <td class=\"amount\">AMOUNT</td>
        </tr>
        {''.join(rows)}
        <tr><td colspan=\"3\" class=\"after-items\"></td></tr>
    </table>

    <table class=\"summary\">
        <tr>
            <td class=\"summary-label\">Subtotal:</td>
            <td class=\"amount\">₦{Decimal(str(receipt['subtotal'])):,.2f}</td>
        </tr>
        <tr>
            <td class=\"summary-label\">Discount:</td>
            <td class=\"amount\">₦{Decimal(str(receipt['discount'])):,.2f}</td>
        </tr>
        <tr class=\"total\">
            <td class=\"summary-label\">TOTAL:</td>
            <td class=\"amount\">₦{Decimal(str(receipt['total'])):,.2f}</td>
        </tr>
    </table>

    <div class=\"rule\"></div>
    <div class=\"section\">PAYMENT</div>

    <table class=\"payment\">
        {''.join(payment_rows)}
    </table>

    <div class=\"footer-spacer\">&nbsp;</div>

    <div class=\"footer\">
        <div class=\"motto\">Your scent, your signature</div>
        <div class=\"thanks\">Thanks for your patronage.</div>
    </div>
</div>
</body>
</html>"""

    def _receipt_height_mm(self):
        """Estimate a single-page height suitable for an 80mm receipt."""
        item_count = len(self.last_receipt["items"]) if self.last_receipt else 1
        return max(125.0, min(300.0, 92.0 + item_count * 9.0))

    def configure_receipt_printer(self, printer, pdf_path=None):
        height_mm = self._receipt_height_mm()

        # Use the full 80mm paper width for both the real thermal printer
        # and the generated PDF. The receipt HTML itself is 76mm wide,
        # leaving a small and consistent side margin.
        printer.setFullPage(True)
        printer.setPageSize(
            QPageSize(
                QSizeF(80.0, height_mm),
                QPageSize.Unit.Millimeter,
            )
        )

        if pdf_path:
            printer.setOutputFormat(
                QPrinter.OutputFormat.PdfFormat
            )
            printer.setOutputFileName(pdf_path)

    def _print_receipt_document(self, printer, html):
        document = QTextDocument()
        document.setDocumentMargin(0)
        document.setHtml(html)

        page_rect = printer.pageRect(QPrinter.Unit.Point)
        document.setPageSize(
            QSizeF(
                page_rect.width(),
                page_rect.height(),
            )
        )

        # PySide6 uses print_(), not print().
        document.print_(printer)

    def print_receipt(self):
        try:
            html = self.receipt_html()
        except ValueError as exc:
            QMessageBox.warning(
                self,
                "No Receipt",
                str(exc),
            )
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        self.configure_receipt_printer(printer)

        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle("Print Shopfave Receipt")

        if dialog.exec() != QPrintDialog.DialogCode.Accepted:
            return

        # Reapply the receipt page size after the printer dialog so the
        # selected printer receives the same thermal receipt dimensions.
        self.configure_receipt_printer(printer)
        self._print_receipt_document(printer, html)

    def save_receipt_pdf(self):
        from PySide6.QtWidgets import QFileDialog

        try:
            html = self.receipt_html()
        except ValueError as exc:
            QMessageBox.warning(
                self,
                "No Receipt",
                str(exc),
            )
            return

        default_name = "receipt.pdf"
        if self.last_receipt:
            default_name = f"{self.last_receipt['sale_number']}.pdf"

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Receipt as PDF",
            default_name,
            "PDF Files (*.pdf)",
        )

        if not path:
            return

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        self.configure_receipt_printer(
            printer,
            pdf_path=path,
        )
        self._print_receipt_document(printer, html)

        QMessageBox.information(
            self,
            "Receipt Saved",
            f"Receipt saved successfully to:\n{path}",
        )

    # ==========================================================
    # RESET
    # ==========================================================

    def reset_sale(self, keep_receipt=False):
        self.sale_id = None

        self.cart_table.setRowCount(0)

        self.subtotal_value.setText("₦0.00")
        self.discount_value.setText("₦0.00")
        self.total_value.setText("₦0.00")

        self.sale_discount_input.clear()
        self.discount_approved_by_input.clear()

        self.payment_table.setRowCount(0)

        if not keep_receipt:
            self.last_receipt = None
            self.print_receipt_button.setEnabled(False)
            self.save_receipt_button.setEnabled(False)
            self.close_sale_button.setEnabled(False)

        self.add_payment_row()
        self.update_payment_summary()

        self.product_search.clear()
        self.product_search.setFocus()

