from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.expense import Expense


class ExpenseService:
    def __init__(self, session: Session):
        self.session = session

    def create_expense(
        self,
        category: str,
        description: str,
        amount: Decimal,
        expense_date: datetime,
        payment_method: str,
        reference: str | None = None,
        notes: str | None = None,
        created_by: int | None = None,
    ) -> Expense:
        if not category or not category.strip():
            raise ValueError(
                "Expense category cannot be empty."
            )

        if not description or not description.strip():
            raise ValueError(
                "Expense description cannot be empty."
            )

        if amount <= 0:
            raise ValueError(
                "Expense amount must be greater than zero."
            )

        if not payment_method or not payment_method.strip():
            raise ValueError(
                "Payment method is required."
            )

        if expense_date is None:
            raise ValueError(
                "Expense date is required."
            )

        expense = Expense(
            category=category.strip(),
            description=description.strip(),
            amount=amount,
            expense_date=expense_date,
            payment_method=payment_method.strip(),
            reference=(
                reference.strip()
                if reference
                else None
            ),
            notes=(
                notes.strip()
                if notes
                else None
            ),
            created_by=created_by,
        )

        self.session.add(expense)
        self.session.flush()

        return expense

    def get_expense(
        self,
        expense_id: int,
    ) -> Expense | None:
        return (
            self.session.query(Expense)
            .filter(Expense.id == expense_id)
            .first()
        )

    def list_expenses(self) -> list[Expense]:
        return (
            self.session.query(Expense)
            .order_by(
                Expense.expense_date.desc(),
                Expense.id.desc(),
            )
            .all()
        )

    def list_expenses_by_category(
        self,
        category: str,
    ) -> list[Expense]:
        search_category = category.strip()

        if not search_category:
            return self.list_expenses()

        return (
            self.session.query(Expense)
            .filter(
                Expense.category.ilike(
                    search_category
                )
            )
            .order_by(
                Expense.expense_date.desc(),
                Expense.id.desc(),
            )
            .all()
        )

    def search_expenses(
        self,
        query: str,
    ) -> list[Expense]:
        search_term = query.strip()

        if not search_term:
            return self.list_expenses()

        pattern = f"%{search_term}%"

        return (
            self.session.query(Expense)
            .filter(
                Expense.category.ilike(pattern)
                | Expense.description.ilike(pattern)
                | Expense.payment_method.ilike(pattern)
                | Expense.reference.ilike(pattern)
            )
            .order_by(
                Expense.expense_date.desc(),
                Expense.id.desc(),
            )
            .all()
        )

    def update_expense(
        self,
        expense_id: int,
        category: str | None = None,
        description: str | None = None,
        amount: Decimal | None = None,
        expense_date: datetime | None = None,
        payment_method: str | None = None,
        reference: str | None = None,
        notes: str | None = None,
    ) -> Expense:
        expense = self.get_expense(
            expense_id
        )

        if expense is None:
            raise ValueError(
                "Expense not found."
            )

        if category is not None:
            if not category.strip():
                raise ValueError(
                    "Expense category cannot be empty."
                )

            expense.category = category.strip()

        if description is not None:
            if not description.strip():
                raise ValueError(
                    "Expense description cannot be empty."
                )

            expense.description = (
                description.strip()
            )

        if amount is not None:
            if amount <= 0:
                raise ValueError(
                    "Expense amount must be greater than zero."
                )

            expense.amount = amount

        if expense_date is not None:
            expense.expense_date = expense_date

        if payment_method is not None:
            if not payment_method.strip():
                raise ValueError(
                    "Payment method is required."
                )

            expense.payment_method = (
                payment_method.strip()
            )

        if reference is not None:
            expense.reference = (
                reference.strip() or None
            )

        if notes is not None:
            expense.notes = (
                notes.strip() or None
            )

        self.session.flush()

        return expense

    def delete_expense(
        self,
        expense_id: int,
    ) -> None:
        expense = self.get_expense(
            expense_id
        )

        if expense is None:
            raise ValueError(
                "Expense not found."
            )

        self.session.delete(expense)
        self.session.flush()

    def get_total_expenses(self) -> Decimal:
        expenses = self.list_expenses()

        return sum(
            (
                expense.amount
                for expense in expenses
            ),
            Decimal("0.00"),
        )