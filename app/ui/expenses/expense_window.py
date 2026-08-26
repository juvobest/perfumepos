from datetime import datetime
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
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
from app.services.expense_service import ExpenseService


class ExpenseWindow(QWidget):
    def __init__(self, user=None):
        super().__init__()

        self.user = user

        self.setWindowTitle("Expense Management")
        self.setMinimumSize(900, 600)

        self.build_ui()
        self.load_expenses()

    def build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Expense Management")
        title.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                font-weight: bold;
            }
            """
        )

        layout.addWidget(title)

        form_layout = QFormLayout()

        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText(
            "e.g. Rent, Electricity, Transport"
        )

        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText(
            "Expense description"
        )

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText(
            "e.g. 50000.00"
        )

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())

        self.payment_method_input = QComboBox()
        self.payment_method_input.addItems(
            [
                "CASH",
                "CARD",
                "BANK_TRANSFER",
                "POS",
                "OTHER",
            ]
        )

        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText(
            "Optional reference"
        )

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText(
            "Optional notes"
        )

        form_layout.addRow(
            "Category:",
            self.category_input,
        )

        form_layout.addRow(
            "Description:",
            self.description_input,
        )

        form_layout.addRow(
            "Amount:",
            self.amount_input,
        )

        form_layout.addRow(
            "Date:",
            self.date_input,
        )

        form_layout.addRow(
            "Payment Method:",
            self.payment_method_input,
        )

        form_layout.addRow(
            "Reference:",
            self.reference_input,
        )

        form_layout.addRow(
            "Notes:",
            self.notes_input,
        )

        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()

        self.add_button = QPushButton(
            "ADD EXPENSE"
        )

        self.clear_button = QPushButton(
            "CLEAR"
        )

        self.refresh_button = QPushButton(
            "REFRESH"
        )

        self.add_button.clicked.connect(
            self.add_expense
        )

        self.clear_button.clicked.connect(
            self.clear_form
        )

        self.refresh_button.clicked.connect(
            self.load_expenses
        )

        button_layout.addWidget(
            self.add_button
        )

        button_layout.addWidget(
            self.clear_button
        )

        button_layout.addWidget(
            self.refresh_button
        )

        layout.addLayout(button_layout)

        self.total_label = QLabel(
            "Total Expenses: 0.00"
        )

        self.total_label.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
                padding: 10px 0;
            }
            """
        )

        layout.addWidget(
            self.total_label
        )

        self.expense_table = QTableWidget()

        self.expense_table.setColumnCount(7)

        self.expense_table.setHorizontalHeaderLabels(
            [
                "Date",
                "Category",
                "Description",
                "Amount",
                "Payment Method",
                "Reference",
                "Notes",
            ]
        )

        self.expense_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.expense_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.expense_table.horizontalHeader().setStretchLastSection(
            True
        )

        layout.addWidget(
            self.expense_table
        )

    def add_expense(self):
        category = self.category_input.text().strip()
        description = (
            self.description_input.text().strip()
        )
        amount_text = self.amount_input.text().strip()
        reference = self.reference_input.text().strip()
        notes = self.notes_input.text().strip()

        if not category:
            self.show_error(
                "Expense category is required."
            )
            return

        if not description:
            self.show_error(
                "Expense description is required."
            )
            return

        if not amount_text:
            self.show_error(
                "Expense amount is required."
            )
            return

        try:
            amount = Decimal(amount_text)
        except InvalidOperation:
            self.show_error(
                "Please enter a valid expense amount."
            )
            return

        if amount <= 0:
            self.show_error(
                "Expense amount must be greater than zero."
            )
            return

        qdate = self.date_input.date()

        expense_date = datetime(
            qdate.year(),
            qdate.month(),
            qdate.day(),
        )

        payment_method = (
            self.payment_method_input.currentText()
        )

        created_by = (
            self.user.id
            if self.user is not None
            else None
        )

        with SessionLocal() as session:
            try:
                service = ExpenseService(session)

                service.create_expense(
                    category=category,
                    description=description,
                    amount=amount,
                    expense_date=expense_date,
                    payment_method=payment_method,
                    reference=reference or None,
                    notes=notes or None,
                    created_by=created_by,
                )

                session.commit()

            except ValueError as error:
                session.rollback()

                self.show_error(str(error))
                return

            except Exception as error:
                session.rollback()

                self.show_error(
                    f"Unable to save expense:\n{error}"
                )
                return

        QMessageBox.information(
            self,
            "Success",
            "Expense added successfully.",
        )

        self.clear_form()
        self.load_expenses()

    def load_expenses(self):
        with SessionLocal() as session:
            service = ExpenseService(session)

            expenses = service.list_expenses()
            total = service.get_total_expenses()

            self.expense_table.setRowCount(
                len(expenses)
            )

            for row, expense in enumerate(expenses):
                self.expense_table.setItem(
                    row,
                    0,
                    QTableWidgetItem(
                        expense.expense_date.strftime(
                            "%Y-%m-%d"
                        )
                    ),
                )

                self.expense_table.setItem(
                    row,
                    1,
                    QTableWidgetItem(
                        expense.category
                    ),
                )

                self.expense_table.setItem(
                    row,
                    2,
                    QTableWidgetItem(
                        expense.description
                    ),
                )

                self.expense_table.setItem(
                    row,
                    3,
                    QTableWidgetItem(
                        f"{expense.amount:,.2f}"
                    ),
                )

                self.expense_table.setItem(
                    row,
                    4,
                    QTableWidgetItem(
                        expense.payment_method
                    ),
                )

                self.expense_table.setItem(
                    row,
                    5,
                    QTableWidgetItem(
                        expense.reference or ""
                    ),
                )

                self.expense_table.setItem(
                    row,
                    6,
                    QTableWidgetItem(
                        expense.notes or ""
                    ),
                )

            self.total_label.setText(
                f"Total Expenses: {total:,.2f}"
            )

    def clear_form(self):
        self.category_input.clear()
        self.description_input.clear()
        self.amount_input.clear()
        self.date_input.setDate(
            QDate.currentDate()
        )
        self.payment_method_input.setCurrentIndex(
            0
        )
        self.reference_input.clear()
        self.notes_input.clear()

        self.category_input.setFocus()

    def show_error(self, message: str):
        QMessageBox.warning(
            self,
            "Expense Error",
            message,
        )