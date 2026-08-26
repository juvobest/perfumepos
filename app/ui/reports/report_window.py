from datetime import date, timedelta
from decimal import Decimal

from PySide6.QtCore import Qt
from sqlalchemy import select

from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QHeaderView,
    QMessageBox,
)

from app.database.connection import SessionLocal
from app.models.user import User
from app.services.report_service import ReportService


class ReportWindow(QWidget):
    def __init__(self, user):
        super().__init__()

        self.user = user
        self.session = SessionLocal()
        self.report_service = ReportService(self.session)

        self.setWindowTitle("Reports")
        self.setMinimumSize(1200, 750)

        self.build_ui()
        self.set_default_dates()
        self.load_reports()

    # =========================================================
    # UI
    # =========================================================

    def build_ui(self):
        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            25,
            25,
            25,
            25,
        )

        main_layout.setSpacing(15)

        # -----------------------------------------------------
        # HEADER
        # -----------------------------------------------------

        header_layout = QHBoxLayout()

        title = QLabel("REPORTS")

        title.setStyleSheet(
            """
            QLabel {
                font-size: 28px;
                font-weight: bold;
            }
            """
        )

        header_layout.addWidget(title)
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

        header_layout.addWidget(user_label)

        main_layout.addLayout(header_layout)

        # -----------------------------------------------------
        # DATE FILTER
        # -----------------------------------------------------

        filter_frame = QFrame()

        filter_frame.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        filter_layout = QHBoxLayout(
            filter_frame
        )

        period_label = QLabel("Period:")

        self.period_combo = QComboBox()

        self.period_combo.addItems(
            [
                "Today",
                "Yesterday",
                "This Week",
                "This Month",
                "Last Month",
                "Custom",
            ]
        )

        self.start_date = QDateEdit()

        self.start_date.setCalendarPopup(True)

        self.end_date = QDateEdit()

        self.end_date.setCalendarPopup(True)

        start_label = QLabel("From:")

        end_label = QLabel("To:")

        self.refresh_button = QPushButton(
            "REFRESH REPORT"
        )

        self.refresh_button.setMinimumHeight(
            35
        )

        self.refresh_button.clicked.connect(
            self.load_reports
        )

        filter_layout.addWidget(
            period_label
        )

        filter_layout.addWidget(
            self.period_combo
        )

        filter_layout.addWidget(
            start_label
        )

        filter_layout.addWidget(
            self.start_date
        )

        filter_layout.addWidget(
            end_label
        )

        filter_layout.addWidget(
            self.end_date
        )

        filter_layout.addWidget(
            self.refresh_button
        )

        main_layout.addWidget(
            filter_frame
        )

        self.period_combo.currentTextChanged.connect(
            self.period_changed
        )

        # -----------------------------------------------------
        # SUMMARY CARDS
        # -----------------------------------------------------

        summary_grid = QGridLayout()

        self.sales_card = self.create_summary_card(
            "TOTAL SALES",
            "₦0.00",
        )

        self.cogs_card = self.create_summary_card(
            "COST OF GOODS",
            "₦0.00",
        )

        self.gross_card = self.create_summary_card(
            "GROSS PROFIT",
            "₦0.00",
        )

        self.expense_card = self.create_summary_card(
            "EXPENSES",
            "₦0.00",
        )

        self.net_card = self.create_summary_card(
            "NET PROFIT",
            "₦0.00",
        )

        self.purchase_card = self.create_summary_card(
            "PURCHASES",
            "₦0.00",
        )

        summary_grid.addWidget(
            self.sales_card,
            0,
            0,
        )

        summary_grid.addWidget(
            self.cogs_card,
            0,
            1,
        )

        summary_grid.addWidget(
            self.gross_card,
            0,
            2,
        )

        summary_grid.addWidget(
            self.expense_card,
            1,
            0,
        )

        summary_grid.addWidget(
            self.net_card,
            1,
            1,
        )

        summary_grid.addWidget(
            self.purchase_card,
            1,
            2,
        )

        main_layout.addLayout(
            summary_grid
        )

        # -----------------------------------------------------
        # COUNTS
        # -----------------------------------------------------

        count_layout = QHBoxLayout()

        self.sales_count_label = QLabel(
            "Sales: 0"
        )

        self.purchase_count_label = QLabel(
            "Purchases: 0"
        )

        self.expense_count_label = QLabel(
            "Expenses: 0"
        )

        for label in (
            self.sales_count_label,
            self.purchase_count_label,
            self.expense_count_label,
        ):
            label.setStyleSheet(
                """
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    padding: 8px;
                }
                """
            )

        count_layout.addWidget(
            self.sales_count_label
        )

        count_layout.addWidget(
            self.purchase_count_label
        )

        count_layout.addWidget(
            self.expense_count_label
        )

        count_layout.addStretch()

        main_layout.addLayout(
            count_layout
        )

        # -----------------------------------------------------
        # TABS
        # -----------------------------------------------------

        self.tabs = QTabWidget()

        self.sales_table = QTableWidget()

        self.purchases_table = QTableWidget()

        self.expenses_table = QTableWidget()

        self.inventory_table = QTableWidget()

        self.payment_table = QTableWidget()

        self.setup_sales_table()
        self.setup_purchase_table()
        self.setup_expense_table()
        self.setup_inventory_table()
        self.setup_payment_table()

        self.tabs.addTab(
            self.sales_table,
            "Sales",
        )

        self.tabs.addTab(
            self.purchases_table,
            "Purchases",
        )

        self.tabs.addTab(
            self.expenses_table,
            "Expenses",
        )

        self.tabs.addTab(
            self.inventory_table,
            "Inventory",
        )

        self.tabs.addTab(
            self.payment_table,
            "Payments",
        )

        main_layout.addWidget(
            self.tabs
        )

    # =========================================================
    # SUMMARY CARD
    # =========================================================

    def create_summary_card(
        self,
        title: str,
        value: str,
    ):
        frame = QFrame()

        frame.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        layout = QVBoxLayout(frame)

        title_label = QLabel(title)

        title_label.setStyleSheet(
            """
            QLabel {
                font-size: 13px;
                font-weight: bold;
            }
            """
        )

        value_label = QLabel(value)

        value_label.setStyleSheet(
            """
            QLabel {
                font-size: 22px;
                font-weight: bold;
            }
            """
        )

        value_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            value_label
        )

        frame.value_label = value_label

        return frame

    # =========================================================
    # DEFAULT DATES
    # =========================================================

    def set_default_dates(self):
        today = date.today()

        self.start_date.setDate(
            today
        )

        self.end_date.setDate(
            today
        )

        self.period_combo.setCurrentText(
            "Today"
        )

    # =========================================================
    # PERIOD SELECTION
    # =========================================================

    def period_changed(self, period):
        today = date.today()

        if period == "Today":
            start = today
            end = today

        elif period == "Yesterday":
            yesterday = today - timedelta(
                days=1
            )

            start = yesterday
            end = yesterday

        elif period == "This Week":
            start = today - timedelta(
                days=today.weekday()
            )

            end = today

        elif period == "This Month":
            start = today.replace(
                day=1
            )

            end = today

        elif period == "Last Month":
            first_this_month = today.replace(
                day=1
            )

            end = first_this_month - timedelta(
                days=1
            )

            start = end.replace(
                day=1
            )

        else:
            return

        self.start_date.setDate(
            start
        )

        self.end_date.setDate(
            end
        )

        self.load_reports()

    # =========================================================
    # DATE RANGE
    # =========================================================

    def get_date_range(self):
        start = self.start_date.date().toPython()
        end = self.end_date.date().toPython()

        if start > end:
            raise ValueError(
                "Start date cannot be after end date."
            )

        return start, end

    # =========================================================
    # LOAD REPORTS
    # =========================================================

    def load_reports(self):
        try:
            start_date, end_date = (
                self.get_date_range()
            )

            summary = (
                self.report_service.get_summary(
                    start_date,
                    end_date,
                )
            )

            self.update_summary(
                summary
            )

            self.load_sales(
                start_date,
                end_date,
            )

            self.load_purchases(
                start_date,
                end_date,
            )

            self.load_expenses(
                start_date,
                end_date,
            )

            self.load_inventory()

            self.load_payments(
                start_date,
                end_date,
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Report Error",
                str(exc),
            )

    # =========================================================
    # SUMMARY
    # =========================================================

    def update_summary(
        self,
        summary: dict,
    ):
        self.sales_card.value_label.setText(
            self.money(
                summary["sales"]
            )
        )

        self.cogs_card.value_label.setText(
            self.money(
                summary["cogs"]
            )
        )

        self.gross_card.value_label.setText(
            self.money(
                summary["gross_profit"]
            )
        )

        self.expense_card.value_label.setText(
            self.money(
                summary["expenses"]
            )
        )

        self.net_card.value_label.setText(
            self.money(
                summary["net_profit"]
            )
        )

        self.purchase_card.value_label.setText(
            self.money(
                summary["purchases"]
            )
        )

        self.sales_count_label.setText(
            f"Sales: {summary['sales_count']}"
        )

        self.purchase_count_label.setText(
            f"Purchases: {summary['purchase_count']}"
        )

        self.expense_count_label.setText(
            f"Expenses: {summary['expense_count']}"
        )

    # =========================================================
    # SALES
    # =========================================================

    def setup_sales_table(self):
        self.sales_table.setColumnCount(8)

        self.sales_table.setHorizontalHeaderLabels(
            [
                "Sale #",
                "Date",
                "Cashier",
                "Status",
                "Subtotal",
                "Discount",
                "Approved By",
                "Total",
            ]
        )

        self.configure_table(
            self.sales_table
        )

    @staticmethod
    def _discount_approved_by(sale):
        """Read the discount approver saved in the sale notes."""
        notes = (sale.notes or "").splitlines()

        for line in notes:
            line = line.strip()

            if line.startswith("DISCOUNT_APPROVED_BY:"):
                approver = line.split(":", 1)[1].strip()
                return approver or "—"

        return "—"

    def load_sales(
        self,
        start_date,
        end_date,
    ):
        rows = (
            self.report_service.get_sales_report(
                start_date,
                end_date,
            )
        )

        # Resolve all cashier names in one query instead of making
        # one database query for every sale row.
        cashier_ids = {
            sale.created_by
            for sale in rows
            if sale.created_by is not None
        }

        cashier_names = {}

        if cashier_ids:
            users = self.session.scalars(
                select(User).where(
                    User.id.in_(cashier_ids)
                )
            ).all()

            cashier_names = {
                user.id: user.full_name
                for user in users
            }

        self.sales_table.setRowCount(
            len(rows)
        )

        for row, sale in enumerate(rows):
            cashier_name = cashier_names.get(
                sale.created_by,
                "—",
            )

            approved_by = self._discount_approved_by(
                sale
            )

            values = [
                sale.sale_number,
                str(sale.sale_date),
                cashier_name,
                sale.status,
                self.money(sale.subtotal),
                self.money(sale.discount),
                approved_by,
                self.money(sale.total_amount),
            ]

            for column, value in enumerate(values):
                self.sales_table.setItem(
                    row,
                    column,
                    QTableWidgetItem(str(value)),
                )

    # =========================================================
    # PURCHASES
    # =========================================================

    def setup_purchase_table(self):
        self.purchases_table.setColumnCount(
            5
        )

        self.purchases_table.setHorizontalHeaderLabels(
            [
                "Purchase #",
                "Date",
                "Status",
                "Supplier",
                "Total",
            ]
        )

        self.configure_table(
            self.purchases_table
        )

    def load_purchases(
        self,
        start_date,
        end_date,
    ):
        rows = (
            self.report_service.get_purchase_report(
                start_date,
                end_date,
            )
        )

        self.purchases_table.setRowCount(
            len(rows)
        )

        for row, purchase in enumerate(rows):
            self.purchases_table.setItem(
                row,
                0,
                QTableWidgetItem(
                    purchase.purchase_number
                ),
            )

            self.purchases_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    str(
                        purchase.purchase_date
                    )
                ),
            )

            self.purchases_table.setItem(
                row,
                2,
                QTableWidgetItem(
                    purchase.status
                ),
            )

            supplier_name = ""

            if purchase.supplier:
                supplier_name = (
                    purchase.supplier.name
                )

            self.purchases_table.setItem(
                row,
                3,
                QTableWidgetItem(
                    supplier_name
                ),
            )

            self.purchases_table.setItem(
                row,
                4,
                QTableWidgetItem(
                    self.money(
                        purchase.total_amount
                    )
                ),
            )

    # =========================================================
    # EXPENSES
    # =========================================================

    def setup_expense_table(self):
        self.expenses_table.setColumnCount(
            6
        )

        self.expenses_table.setHorizontalHeaderLabels(
            [
                "Date",
                "Category",
                "Description",
                "Amount",
                "Payment",
                "Reference",
            ]
        )

        self.configure_table(
            self.expenses_table
        )

    def load_expenses(
        self,
        start_date,
        end_date,
    ):
        rows = (
            self.report_service.get_expense_report(
                start_date,
                end_date,
            )
        )

        self.expenses_table.setRowCount(
            len(rows)
        )

        for row, expense in enumerate(rows):
            self.expenses_table.setItem(
                row,
                0,
                QTableWidgetItem(
                    str(
                        expense.expense_date
                    )
                ),
            )

            self.expenses_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    expense.category
                ),
            )

            self.expenses_table.setItem(
                row,
                2,
                QTableWidgetItem(
                    expense.description
                ),
            )

            self.expenses_table.setItem(
                row,
                3,
                QTableWidgetItem(
                    self.money(
                        expense.amount
                    )
                ),
            )

            self.expenses_table.setItem(
                row,
                4,
                QTableWidgetItem(
                    expense.payment_method
                ),
            )

            self.expenses_table.setItem(
                row,
                5,
                QTableWidgetItem(
                    expense.reference or ""
                ),
            )

    # =========================================================
    # INVENTORY
    # =========================================================

    def setup_inventory_table(self):
        self.inventory_table.setColumnCount(
            8
        )

        self.inventory_table.setHorizontalHeaderLabels(
            [
                "Product",
                "Variant",
                "SKU",
                "Cost",
                "Selling Price",
                "Reorder Level",
                "Quantity",
                "Stock Value",
            ]
        )

        self.configure_table(
            self.inventory_table
        )

    def load_inventory(self):
        rows = (
            self.report_service.get_inventory_report()
        )

        self.inventory_table.setRowCount(
            len(rows)
        )

        for row, item in enumerate(rows):
            product_name = (
                item.name
            )

            variant_name = (
                item.variant_name
                or ""
            )

            sku = (
                item.sku
                or ""
            )

            cost = Decimal(
                str(
                    item.cost_price
                    or 0
                )
            )

            selling_price = Decimal(
                str(
                    item.selling_price
                    or 0
                )
            )

            reorder_level = (
                item.reorder_level
            )

            quantity = int(
                item.quantity
                or 0
            )

            stock_value = (
                cost * quantity
            )

            values = [
                product_name,
                variant_name,
                sku,
                self.money(cost),
                self.money(
                    selling_price
                ),
                (
                    str(reorder_level)
                    if reorder_level
                    is not None
                    else ""
                ),
                str(quantity),
                self.money(
                    stock_value
                ),
            ]

            for column, value in enumerate(
                values
            ):
                self.inventory_table.setItem(
                    row,
                    column,
                    QTableWidgetItem(
                        value
                    ),
                )

    # =========================================================
    # PAYMENTS
    # =========================================================

    def setup_payment_table(self):
        self.payment_table.setColumnCount(
            2
        )

        self.payment_table.setHorizontalHeaderLabels(
            [
                "Payment Method",
                "Amount",
            ]
        )

        self.configure_table(
            self.payment_table
        )

    def load_payments(
        self,
        start_date,
        end_date,
    ):
        rows = (
            self.report_service.get_payment_summary(
                start_date,
                end_date,
            )
        )

        self.payment_table.setRowCount(
            len(rows)
        )

        for row, (
            method,
            amount,
        ) in enumerate(rows):
            self.payment_table.setItem(
                row,
                0,
                QTableWidgetItem(
                    method
                ),
            )

            self.payment_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    self.money(amount)
                ),
            )

    # =========================================================
    # TABLE CONFIG
    # =========================================================

    def configure_table(
        self,
        table,
    ):
        table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        table.setAlternatingRowColors(
            True
        )

        table.horizontalHeader().setStretchLastSection(
            True
        )

        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

    # =========================================================
    # MONEY
    # =========================================================

    @staticmethod
    def money(value):
        value = Decimal(
            str(value or 0)
        )

        return (
            f"₦{value:,.2f}"
        )

    # =========================================================
    # CLOSE
    # =========================================================

    def closeEvent(self, event):
        try:
            self.session.close()
        finally:
            event.accept()