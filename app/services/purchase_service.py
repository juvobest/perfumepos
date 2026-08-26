from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product_variant import ProductVariant
from app.models.purchase import Purchase
from app.models.purchase_item import PurchaseItem
from app.models.supplier import Supplier
from app.models.user import User
from app.services.inventory_service import InventoryService
from app.services.permission_service import require_permission


class PurchaseService:
    ALLOWED_STATUSES = {
        "DRAFT",
        "RECEIVED",
        "CANCELLED",
    }

    def __init__(self, session: Session):
        self.session = session
        self.inventory_service = InventoryService(session)

    def _generate_purchase_number(self) -> str:
        statement = (
            select(Purchase)
            .order_by(Purchase.id.desc())
            .limit(1)
        )

        last_purchase = self.session.scalar(statement)

        if last_purchase is None:
            next_number = 1
        else:
            next_number = last_purchase.id + 1

        return f"PUR-{next_number:06d}"

    def create_purchase(
        self,
        supplier_id: int,
        purchase_date: date,
        created_by: int | None = None,
        notes: str | None = None,
        user: User | None = None,
    ) -> Purchase:
        if user is not None:
            require_permission(
                self.session,
                user,
                "purchasing.create",
            )

        supplier = self.session.get(
            Supplier,
            supplier_id,
        )

        if supplier is None:
            raise ValueError(
                "Supplier not found."
            )

        if not supplier.is_active:
            raise ValueError(
                "Cannot create a purchase for an inactive supplier."
            )

        purchase = Purchase(
            supplier_id=supplier_id,
            purchase_number=self._generate_purchase_number(),
            status="DRAFT",
            purchase_date=purchase_date,
            total_amount=Decimal("0.00"),
            created_by=created_by,
            notes=(
                notes.strip()
                if notes
                else None
            ),
        )

        self.session.add(purchase)
        self.session.flush()

        return purchase

    def get_by_id(
        self,
        purchase_id: int,
    ) -> Purchase | None:
        return self.session.get(
            Purchase,
            purchase_id,
        )

    def get_by_number(
        self,
        purchase_number: str,
    ) -> Purchase | None:
        statement = select(Purchase).where(
            Purchase.purchase_number == purchase_number
        )

        return self.session.scalar(statement)

    def add_item(
        self,
        purchase_id: int,
        product_variant_id: int,
        quantity: int,
        unit_cost: Decimal,
        user: User | None = None,
    ) -> PurchaseItem:
        if user is not None:
            require_permission(
                self.session,
                user,
                "purchasing.edit",
            )

        purchase = self.get_by_id(purchase_id)

        if purchase is None:
            raise ValueError(
                "Purchase not found."
            )

        if purchase.status != "DRAFT":
            raise ValueError(
                "Items can only be added to a draft purchase."
            )

        if quantity <= 0:
            raise ValueError(
                "Purchase quantity must be greater than zero."
            )

        if unit_cost < 0:
            raise ValueError(
                "Unit cost cannot be negative."
            )

        product_variant = self.session.get(
            ProductVariant,
            product_variant_id,
        )

        if product_variant is None:
            raise ValueError(
                "Product variant not found."
            )

        total_cost = (
            Decimal(quantity) * unit_cost
        )

        item = PurchaseItem(
            purchase_id=purchase_id,
            product_variant_id=product_variant_id,
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=total_cost,
        )

        self.session.add(item)

        purchase.total_amount += total_cost

        self.session.flush()

        return item

    def remove_item(
        self,
        purchase_item_id: int,
        user: User | None = None,
    ) -> None:
        if user is not None:
            require_permission(
                self.session,
                user,
                "purchasing.edit",
            )

        statement = select(PurchaseItem).where(
            PurchaseItem.id == purchase_item_id
        )

        item = self.session.scalar(statement)

        if item is None:
            raise ValueError(
                "Purchase item not found."
            )

        purchase = self.get_by_id(
            item.purchase_id
        )

        if purchase is None:
            raise ValueError(
                "Purchase not found."
            )

        if purchase.status != "DRAFT":
            raise ValueError(
                "Items can only be removed from a draft purchase."
            )

        purchase.total_amount -= item.total_cost

        self.session.delete(item)

        self.session.flush()

    def receive_purchase(
        self,
        purchase_id: int,
        received_by: int | None = None,
        user: User | None = None,
    ) -> Purchase:
        if user is not None:
            require_permission(
                self.session,
                user,
                "inventory.receive",
            )

        purchase = self.get_by_id(
            purchase_id
        )

        if purchase is None:
            raise ValueError(
                "Purchase not found."
            )

        if purchase.status == "RECEIVED":
            raise ValueError(
                "Purchase has already been received."
            )

        if purchase.status == "CANCELLED":
            raise ValueError(
                "Cancelled purchases cannot be received."
            )

        if not purchase.items:
            raise ValueError(
                "Cannot receive a purchase without items."
            )

        for item in purchase.items:
            product_variant = self.session.get(
                ProductVariant,
                item.product_variant_id,
            )

            if product_variant is None:
                raise ValueError(
                    "Product variant not found."
                )

            # Store the cost price that existed immediately
            # before this purchase was received.
            item.previous_cost_price = (
                product_variant.cost_price
            )

            # Add the purchased quantity to inventory.
            self.inventory_service.add_stock(
                product_variant_id=item.product_variant_id,
                quantity=item.quantity,
                movement_type="PURCHASE",
                created_by=received_by,
                reference_type="purchase",
                reference_id=purchase.id,
                reason=(
                    f"Received purchase "
                    f"{purchase.purchase_number}"
                ),
            )

            # Update the current cost price.
            #
            # This affects FUTURE sales only.
            # Existing SaleItem records retain their own
            # historical cost_price.
            product_variant.cost_price = Decimal(
                str(item.unit_cost)
            )

        purchase.status = "RECEIVED"

        self.session.flush()

        return purchase

    def correct_received_purchase(
        self,
        purchase_id: int,
        quantity: int,
        unit_cost: Decimal,
        corrected_by: int | None = None,
        user: User | None = None,
    ) -> Purchase:
        """
        Correct a received purchase containing one item.

        The original received stock is reversed and the
        corrected quantity is applied.

        This method intentionally handles one-item purchases.
        Multi-item purchase correction should be implemented
        separately so each item can be corrected independently.
        """

        if user is not None:
            require_permission(
                self.session,
                user,
                "purchasing.edit",
            )

        purchase = self.get_by_id(
            purchase_id
        )

        if purchase is None:
            raise ValueError(
                "Purchase not found."
            )

        if purchase.status != "RECEIVED":
            raise ValueError(
                "Only received purchases can be corrected."
            )

        if not purchase.items:
            raise ValueError(
                "Cannot correct a purchase without items."
            )

        if len(purchase.items) != 1:
            raise ValueError(
                "Received purchase correction currently supports "
                "one-item purchases only."
            )

        if quantity <= 0:
            raise ValueError(
                "Corrected quantity must be greater than zero."
            )

        if unit_cost < 0:
            raise ValueError(
                "Corrected unit cost cannot be negative."
            )

        item = purchase.items[0]

        product_variant = self.session.get(
            ProductVariant,
            item.product_variant_id,
        )

        if product_variant is None:
            raise ValueError(
                "Product variant not found."
            )

        inventory = self.inventory_service.get_inventory(
            item.product_variant_id
        )

        if inventory is None:
            raise ValueError(
                "Inventory record not found."
            )

        # We need to know how much stock remains from the
        # original purchase before reversing it.
        #
        # If the current quantity is less than the original
        # purchase quantity, some of that stock has already
        # been consumed. We refuse to silently alter history.
        if inventory.quantity < item.quantity:
            raise ValueError(
                "This purchase cannot be corrected because "
                "some of its received stock has already been sold "
                "or otherwise removed from inventory."
            )

        original_quantity = item.quantity
        original_unit_cost = item.unit_cost

        # Reverse the original purchase movement.
        self.inventory_service.remove_stock(
            product_variant_id=item.product_variant_id,
            quantity=original_quantity,
            movement_type="ADJUSTMENT",
            created_by=corrected_by,
            reference_type="purchase_correction",
            reference_id=purchase.id,
            reason=(
                f"Reverse original received purchase "
                f"{purchase.purchase_number}"
            ),
        )

        # Apply the corrected quantity.
        self.inventory_service.add_stock(
            product_variant_id=item.product_variant_id,
            quantity=quantity,
            movement_type="ADJUSTMENT",
            created_by=corrected_by,
            reference_type="purchase_correction",
            reference_id=purchase.id,
            reason=(
                f"Apply corrected purchase "
                f"{purchase.purchase_number}"
            ),
        )

        # Preserve the old cost price if this was the value
        # immediately before the original purchase.
        #
        # For a correction, the current purchase's cost becomes
        # the new current cost.
        item.quantity = quantity
        item.unit_cost = unit_cost
        item.total_cost = (
            Decimal(quantity) * unit_cost
        )

        purchase.total_amount = item.total_cost

        product_variant.cost_price = Decimal(
            str(unit_cost)
        )

        self.session.flush()

        return purchase

    def cancel_purchase(
        self,
        purchase_id: int,
        user: User | None = None,
    ) -> Purchase:
        if user is not None:
            require_permission(
                self.session,
                user,
                "purchasing.cancel",
            )

        purchase = self.get_by_id(
            purchase_id
        )

        if purchase is None:
            raise ValueError(
                "Purchase not found."
            )

        if purchase.status == "RECEIVED":
            raise ValueError(
                "Received purchases cannot be cancelled."
            )

        if purchase.status == "CANCELLED":
            raise ValueError(
                "Purchase has already been cancelled."
            )

        purchase.status = "CANCELLED"

        self.session.flush()

        return purchase

    def list_purchases(
        self,
        status: str | None = None,
    ) -> list[Purchase]:
        statement = select(Purchase).order_by(
            Purchase.id.desc()
        )

        if status is not None:
            if status not in self.ALLOWED_STATUSES:
                raise ValueError(
                    f"Invalid purchase status: {status}"
                )

            statement = statement.where(
                Purchase.status == status
            )

        return list(
            self.session.scalars(statement).all()
        )