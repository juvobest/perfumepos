from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.purchase import Purchase
from app.models.sale import Sale
from app.models.sale_item import SaleItem


class ReportService:
    """
    Provides reporting and business-summary queries for the POS.

    Reports are generated from the existing database models.
    """

    COMPLETED_SALE_STATUS = "COMPLETED"
    RECEIVED_PURCHASE_STATUS = "RECEIVED"

    def __init__(self, session: Session):
        self.session = session

    # =========================================================
    # DATE HELPERS
    # =========================================================

    @staticmethod
    def _start_datetime(report_date: date) -> datetime:
        return datetime.combine(
            report_date,
            time.min,
        )

    @staticmethod
    def _end_datetime(report_date: date) -> datetime:
        return datetime.combine(
            report_date,
            time.max,
        )

    # =========================================================
    # SALES
    # =========================================================

    def get_sales_total(
        self,
        start_date: date,
        end_date: date,
    ) -> Decimal:
        statement = (
            select(
                func.coalesce(
                    func.sum(Sale.total_amount),
                    0,
                )
            )
            .where(
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
                Sale.status == self.COMPLETED_SALE_STATUS,
            )
        )

        result = self.session.scalar(statement)

        return Decimal(
            str(result or 0)
        )

    def get_sales_count(
        self,
        start_date: date,
        end_date: date,
    ) -> int:
        statement = select(
            func.count(Sale.id)
        ).where(
            Sale.sale_date >= start_date,
            Sale.sale_date <= end_date,
            Sale.status == self.COMPLETED_SALE_STATUS,
        )

        return int(
            self.session.scalar(statement) or 0
        )

    def get_sales_report(
        self,
        start_date: date,
        end_date: date,
    ) -> list[Sale]:
        statement = (
            select(Sale)
            .where(
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
            )
            .order_by(
                Sale.sale_date.desc(),
                Sale.id.desc(),
            )
        )

        return list(
            self.session.scalars(statement).all()
        )

    # =========================================================
    # COST OF GOODS SOLD
    # =========================================================

    def get_cost_of_goods_sold(
        self,
        start_date: date,
        end_date: date,
    ) -> Decimal:
        """
        Calculates COGS using the historical cost price
        stored on each SaleItem.

        COGS:

            quantity sold × historical cost price

        SaleItem.cost_price is captured when the sale item
        is added to a sale.

        Therefore, changing the current ProductVariant.cost_price
        later will NOT change historical COGS.
        """

        statement = (
            select(
                func.coalesce(
                    func.sum(
                        SaleItem.quantity
                        * SaleItem.cost_price
                    ),
                    0,
                )
            )
            .join(
                Sale,
                Sale.id == SaleItem.sale_id,
            )
            .where(
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
                Sale.status == self.COMPLETED_SALE_STATUS,
            )
        )

        result = self.session.scalar(statement)

        return Decimal(
            str(result or 0)
        )

    # =========================================================
    # GROSS PROFIT
    # =========================================================

    def get_gross_profit(
        self,
        start_date: date,
        end_date: date,
    ) -> Decimal:
        sales = self.get_sales_total(
            start_date,
            end_date,
        )

        cogs = self.get_cost_of_goods_sold(
            start_date,
            end_date,
        )

        return sales - cogs

    # =========================================================
    # EXPENSES
    # =========================================================

    def get_expenses_total(
        self,
        start_date: date,
        end_date: date,
    ) -> Decimal:
        """
        Expense.expense_date is a DateTime field.
        Therefore the query uses the complete day boundaries.
        """

        start_datetime = self._start_datetime(
            start_date
        )

        end_datetime = self._end_datetime(
            end_date
        )

        statement = (
            select(
                func.coalesce(
                    func.sum(Expense.amount),
                    0,
                )
            )
            .where(
                Expense.expense_date
                >= start_datetime,
                Expense.expense_date
                <= end_datetime,
            )
        )

        result = self.session.scalar(statement)

        return Decimal(
            str(result or 0)
        )

    def get_expenses_count(
        self,
        start_date: date,
        end_date: date,
    ) -> int:
        start_datetime = self._start_datetime(
            start_date
        )

        end_datetime = self._end_datetime(
            end_date
        )

        statement = select(
            func.count(Expense.id)
        ).where(
            Expense.expense_date
            >= start_datetime,
            Expense.expense_date
            <= end_datetime,
        )

        return int(
            self.session.scalar(statement) or 0
        )

    def get_expense_report(
        self,
        start_date: date,
        end_date: date,
    ) -> list[Expense]:
        start_datetime = self._start_datetime(
            start_date
        )

        end_datetime = self._end_datetime(
            end_date
        )

        statement = (
            select(Expense)
            .where(
                Expense.expense_date
                >= start_datetime,
                Expense.expense_date
                <= end_datetime,
            )
            .order_by(
                Expense.expense_date.desc(),
                Expense.id.desc(),
            )
        )

        return list(
            self.session.scalars(statement).all()
        )

    # =========================================================
    # NET PROFIT
    # =========================================================

    def get_net_profit(
        self,
        start_date: date,
        end_date: date,
    ) -> Decimal:
        gross_profit = self.get_gross_profit(
            start_date,
            end_date,
        )

        expenses = self.get_expenses_total(
            start_date,
            end_date,
        )

        return gross_profit - expenses

    # =========================================================
    # PURCHASES
    # =========================================================

    def get_purchases_total(
        self,
        start_date: date,
        end_date: date,
    ) -> Decimal:
        statement = (
            select(
                func.coalesce(
                    func.sum(Purchase.total_amount),
                    0,
                )
            )
            .where(
                Purchase.purchase_date >= start_date,
                Purchase.purchase_date <= end_date,
                Purchase.status
                == self.RECEIVED_PURCHASE_STATUS,
            )
        )

        result = self.session.scalar(statement)

        return Decimal(
            str(result or 0)
        )

    def get_purchases_count(
        self,
        start_date: date,
        end_date: date,
    ) -> int:
        statement = select(
            func.count(Purchase.id)
        ).where(
            Purchase.purchase_date >= start_date,
            Purchase.purchase_date <= end_date,
            Purchase.status
            == self.RECEIVED_PURCHASE_STATUS,
        )

        return int(
            self.session.scalar(statement) or 0
        )

    def get_purchase_report(
        self,
        start_date: date,
        end_date: date,
    ) -> list[Purchase]:
        statement = (
            select(Purchase)
            .where(
                Purchase.purchase_date >= start_date,
                Purchase.purchase_date <= end_date,
            )
            .order_by(
                Purchase.purchase_date.desc(),
                Purchase.id.desc(),
            )
        )

        return list(
            self.session.scalars(statement).all()
        )

    # =========================================================
    # INVENTORY
    # =========================================================

    def get_inventory_report(self):
        """
        Returns active product variants together with
        their current inventory quantities.
        """

        statement = (
            select(
                Product.name,
                ProductVariant.variant_name,
                ProductVariant.sku,
                ProductVariant.cost_price,
                ProductVariant.selling_price,
                ProductVariant.reorder_level,
                func.coalesce(
                    Inventory.quantity,
                    0,
                ).label("quantity"),
            )
            .join(
                ProductVariant,
                ProductVariant.product_id
                == Product.id,
            )
            .outerjoin(
                Inventory,
                Inventory.product_variant_id
                == ProductVariant.id,
            )
            .where(
                Product.is_active.is_(True),
                ProductVariant.is_active.is_(True),
            )
            .order_by(
                Product.name,
                ProductVariant.variant_name,
            )
        )

        return list(
            self.session.execute(statement).all()
        )

    def get_inventory_value(self) -> Decimal:
        """
        Current inventory value based on current cost price.
        """

        statement = (
            select(
                func.coalesce(
                    func.sum(
                        func.coalesce(
                            Inventory.quantity,
                            0,
                        )
                        * ProductVariant.cost_price
                    ),
                    0,
                )
            )
            .join(
                ProductVariant,
                ProductVariant.id
                == Inventory.product_variant_id,
            )
            .join(
                Product,
                Product.id
                == ProductVariant.product_id,
            )
            .where(
                Product.is_active.is_(True),
                ProductVariant.is_active.is_(True),
            )
        )

        result = self.session.scalar(statement)

        return Decimal(
            str(result or 0)
        )

    # =========================================================
    # PAYMENT SUMMARY
    # =========================================================

    def get_payment_summary(
        self,
        start_date: date,
        end_date: date,
    ) -> list[tuple[str, Decimal]]:
        """
        Returns total payments grouped by payment method.

        Payment is linked to Sale, so only completed sales
        within the selected period are included.
        """

        from app.models.payment import Payment

        statement = (
            select(
                Payment.payment_method,
                func.coalesce(
                    func.sum(Payment.amount),
                    0,
                ),
            )
            .join(
                Sale,
                Sale.id == Payment.sale_id,
            )
            .where(
                Sale.sale_date >= start_date,
                Sale.sale_date <= end_date,
                Sale.status
                == self.COMPLETED_SALE_STATUS,
            )
            .group_by(
                Payment.payment_method
            )
            .order_by(
                Payment.payment_method
            )
        )

        rows = self.session.execute(
            statement
        ).all()

        return [
            (
                payment_method,
                Decimal(str(amount or 0)),
            )
            for payment_method, amount in rows
        ]

    # =========================================================
    # SUMMARY
    # =========================================================

    def get_summary(
        self,
        start_date: date,
        end_date: date,
    ) -> dict:
        """
        Returns the main dashboard figures in one call.
        """

        sales = self.get_sales_total(
            start_date,
            end_date,
        )

        cogs = self.get_cost_of_goods_sold(
            start_date,
            end_date,
        )

        gross_profit = sales - cogs

        expenses = self.get_expenses_total(
            start_date,
            end_date,
        )

        net_profit = gross_profit - expenses

        purchases = self.get_purchases_total(
            start_date,
            end_date,
        )

        return {
            "sales": sales,
            "cogs": cogs,
            "gross_profit": gross_profit,
            "expenses": expenses,
            "net_profit": net_profit,
            "purchases": purchases,
            "sales_count": self.get_sales_count(
                start_date,
                end_date,
            ),
            "purchase_count": self.get_purchases_count(
                start_date,
                end_date,
            ),
            "expense_count": self.get_expenses_count(
                start_date,
                end_date,
            ),
        }