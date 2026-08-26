from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.services.inventory_service import InventoryService
from app.services.product_service import ProductService


class SaleService:
    def __init__(self, session: Session):
        self.session = session
        self.inventory_service = InventoryService(session)
        self.product_service = ProductService(session)

    def _generate_sale_number(self) -> str:
        result = self.session.execute(
            select(Sale.id)
            .order_by(Sale.id.desc())
            .limit(1)
        ).scalar_one_or_none()

        next_id = (result or 0) + 1

        return f"SALE-{next_id:06d}"

    def create_sale(
        self,
        sale_date: date,
        customer_id: int | None = None,
        notes: str | None = None,
        created_by: int | None = None,
    ) -> Sale:
        if customer_id is not None:
            from app.models.customer import Customer

            customer = self.session.get(
                Customer,
                customer_id,
            )

            if customer is None:
                raise ValueError(
                    "Customer not found."
                )

            if not customer.is_active:
                raise ValueError(
                    "Customer is inactive."
                )

        sale = Sale(
            customer_id=customer_id,
            sale_number=self._generate_sale_number(),
            status="DRAFT",
            sale_date=sale_date,
            subtotal=Decimal("0.00"),
            discount=Decimal("0.00"),
            total_amount=Decimal("0.00"),
            notes=notes.strip() if notes else None,
            created_by=created_by,
        )

        self.session.add(sale)
        self.session.flush()

        return sale

    def get_sale(
        self,
        sale_id: int,
    ) -> Sale | None:
        return self.session.get(
            Sale,
            sale_id,
        )

    def list_sales(
        self,
        active_only: bool = False,
    ) -> list[Sale]:
        statement = (
            select(Sale)
            .order_by(
                Sale.sale_date.desc(),
                Sale.id.desc(),
            )
        )

        if active_only:
            statement = statement.where(
                Sale.status != "CANCELLED"
            )

        return list(
            self.session.scalars(statement).all()
        )

    def add_item(
        self,
        sale_id: int,
        product_variant_id: int,
        quantity: int,
        discount: Decimal = Decimal("0.00"),
    ) -> SaleItem:
        sale = self.get_sale(sale_id)

        if sale is None:
            raise ValueError(
                "Sale not found."
            )

        if sale.status != "DRAFT":
            raise ValueError(
                "Only draft sales can be modified."
            )

        if quantity <= 0:
            raise ValueError(
                "Sale quantity must be greater than zero."
            )

        if discount < 0:
            raise ValueError(
                "Item discount cannot be negative."
            )

        variant = self.product_service.get_variant(
            product_variant_id
        )

        if variant is None:
            raise ValueError(
                "Product variant not found."
            )

        if not variant.is_active:
            raise ValueError(
                "Product variant is inactive."
            )

        existing_item = self.session.scalar(
            select(SaleItem).where(
                SaleItem.sale_id == sale_id,
                SaleItem.product_variant_id
                == product_variant_id,
            )
        )

        if existing_item is not None:
            existing_item.quantity += quantity
            existing_item.discount += discount

            self._recalculate_item(
                existing_item
            )

            self.calculate_totals(
                sale_id
            )

            return existing_item

        # Capture both selling price and cost price
        # at the time the item is added to the sale.
        unit_price = Decimal(
            str(variant.selling_price)
        )

        cost_price = Decimal(
            str(variant.cost_price)
        )

        line_subtotal = (
            unit_price * quantity
        )

        if discount > line_subtotal:
            raise ValueError(
                "Item discount cannot exceed item total."
            )

        total_price = (
            line_subtotal - discount
        )

        item = SaleItem(
            sale_id=sale_id,
            product_variant_id=product_variant_id,
            quantity=quantity,
            unit_price=unit_price,
            cost_price=cost_price,
            discount=discount,
            total_price=total_price,
        )

        self.session.add(item)
        self.session.flush()

        self.calculate_totals(
            sale_id
        )

        return item

    def _recalculate_item(
        self,
        item: SaleItem,
    ) -> None:
        line_subtotal = (
            item.unit_price * item.quantity
        )

        if item.discount > line_subtotal:
            raise ValueError(
                "Item discount cannot exceed item total."
            )

        item.total_price = (
            line_subtotal - item.discount
        )

        self.session.flush()

    def remove_item(
        self,
        sale_item_id: int,
    ) -> None:
        item = self.session.get(
            SaleItem,
            sale_item_id,
        )

        if item is None:
            raise ValueError(
                "Sale item not found."
            )

        sale = self.get_sale(
            item.sale_id
        )

        if sale is None:
            raise ValueError(
                "Sale not found."
            )

        if sale.status != "DRAFT":
            raise ValueError(
                "Only draft sales can be modified."
            )

        self.session.delete(item)
        self.session.flush()

        self.calculate_totals(
            sale.id
        )

    def calculate_totals(
        self,
        sale_id: int,
        discount: Decimal | None = None,
    ) -> Sale:
        sale = self.get_sale(
            sale_id
        )

        if sale is None:
            raise ValueError(
                "Sale not found."
            )

        if sale.status != "DRAFT":
            raise ValueError(
                "Only draft sales can be modified."
            )

        items = list(
            self.session.scalars(
                select(SaleItem).where(
                    SaleItem.sale_id == sale_id
                )
            ).all()
        )

        subtotal = sum(
            (
                Decimal(
                    str(item.total_price)
                )
                for item in items
            ),
            Decimal("0.00"),
        )

        if discount is not None:
            if discount < 0:
                raise ValueError(
                    "Sale discount cannot be negative."
                )

            if discount > subtotal:
                raise ValueError(
                    "Sale discount cannot exceed subtotal."
                )

            sale.discount = discount

        sale.subtotal = subtotal
        sale.total_amount = (
            subtotal - sale.discount
        )

        self.session.flush()

        return sale

    def add_payment(
        self,
        sale_id: int,
        amount: Decimal,
        payment_method: str,
        reference: str | None = None,
        created_by: int | None = None,
    ) -> Payment:
        sale = self.get_sale(
            sale_id
        )

        if sale is None:
            raise ValueError(
                "Sale not found."
            )

        if sale.status != "DRAFT":
            raise ValueError(
                "Payments can only be added to draft sales."
            )

        if amount <= 0:
            raise ValueError(
                "Payment amount must be greater than zero."
            )

        payment_method = payment_method.strip()

        if not payment_method:
            raise ValueError(
                "Payment method is required."
            )

        self.calculate_totals(
            sale_id
        )

        total_paid = self.get_total_paid(
            sale_id
        )

        if total_paid + amount > sale.total_amount:
            raise ValueError(
                "Payment cannot exceed sale total."
            )

        payment = Payment(
            sale_id=sale_id,
            amount=amount,
            payment_method=payment_method,
            reference=(
                reference.strip()
                if reference
                else None
            ),
            created_by=created_by,
        )

        self.session.add(payment)
        self.session.flush()

        return payment

    def get_total_paid(
        self,
        sale_id: int,
    ) -> Decimal:
        sale = self.get_sale(
            sale_id
        )

        if sale is None:
            raise ValueError(
                "Sale not found."
            )

        total_paid = self.session.scalar(
            select(
                func.coalesce(
                    func.sum(Payment.amount),
                    0,
                )
            ).where(
                Payment.sale_id == sale_id
            )
        )

        return Decimal(
            str(total_paid)
        )

    def complete_sale(
        self,
        sale_id: int,
    ) -> Sale:
        sale = self.get_sale(
            sale_id
        )

        if sale is None:
            raise ValueError(
                "Sale not found."
            )

        if sale.status != "DRAFT":
            raise ValueError(
                "Only draft sales can be completed."
            )

        items = list(
            self.session.scalars(
                select(SaleItem).where(
                    SaleItem.sale_id == sale_id
                )
            ).all()
        )

        if not items:
            raise ValueError(
                "Cannot complete a sale without items."
            )

        self.calculate_totals(
            sale_id
        )

        total_paid = self.get_total_paid(
            sale_id
        )

        if total_paid != sale.total_amount:
            raise ValueError(
                "Sale must be fully paid before completion."
            )

        for item in items:
            self.inventory_service.remove_stock(
                product_variant_id=(
                    item.product_variant_id
                ),
                quantity=item.quantity,
                movement_type="SALE",
                created_by=sale.created_by,
                reference_type="SALE",
                reference_id=sale.id,
                reason=(
                    f"Sale {sale.sale_number}"
                ),
            )

        sale.status = "COMPLETED"

        self.session.flush()

        return sale

    def cancel_sale(
        self,
        sale_id: int,
    ) -> Sale:
        sale = self.get_sale(
            sale_id
        )

        if sale is None:
            raise ValueError(
                "Sale not found."
            )

        if sale.status != "DRAFT":
            raise ValueError(
                "Only draft sales can be cancelled."
            )

        sale.status = "CANCELLED"

        self.session.flush()

        return sale