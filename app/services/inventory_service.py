from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement
from app.models.product_variant import ProductVariant


class InventoryService:
    ALLOWED_MOVEMENT_TYPES = {
        "OPENING_STOCK",
        "PURCHASE",
        "SALE",
        "RETURN",
        "ADJUSTMENT",
        "DAMAGE",
    }

    def __init__(self, session: Session):
        self.session = session

    def get_inventory(
        self,
        product_variant_id: int,
    ) -> Inventory | None:
        statement = select(Inventory).where(
            Inventory.product_variant_id == product_variant_id
        )

        return self.session.scalar(statement)

    def get_or_create_inventory(
        self,
        product_variant_id: int,
    ) -> Inventory:
        product = self.session.get(
            ProductVariant,
            product_variant_id,
        )

        if product is None:
            raise ValueError("Product variant not found.")

        inventory = self.get_inventory(
            product_variant_id
        )

        if inventory is None:
            inventory = Inventory(
                product_variant_id=product_variant_id,
                quantity=0,
            )

            self.session.add(inventory)
            self.session.flush()

        return inventory

    def record_movement(
        self,
        product_variant_id: int,
        movement_type: str,
        quantity: int,
        created_by: int | None = None,
        reference_type: str | None = None,
        reference_id: int | None = None,
        reason: str | None = None,
    ) -> InventoryMovement:
        if movement_type not in self.ALLOWED_MOVEMENT_TYPES:
            raise ValueError(
                f"Invalid inventory movement type: "
                f"{movement_type}"
            )

        if quantity == 0:
            raise ValueError(
                "Inventory movement quantity cannot be zero."
            )

        inventory = self.get_or_create_inventory(
            product_variant_id
        )

        quantity_before = inventory.quantity
        quantity_after = quantity_before + quantity

        if quantity_after < 0:
            raise ValueError(
                "Insufficient stock."
            )

        movement = InventoryMovement(
            inventory_id=inventory.id,
            movement_type=movement_type,
            quantity=quantity,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            reference_type=reference_type,
            reference_id=reference_id,
            reason=reason.strip() if reason else None,
            created_by=created_by,
        )

        inventory.quantity = quantity_after

        self.session.add(movement)
        self.session.flush()

        return movement

    def add_stock(
        self,
        product_variant_id: int,
        quantity: int,
        movement_type: str,
        created_by: int | None = None,
        reference_type: str | None = None,
        reference_id: int | None = None,
        reason: str | None = None,
    ) -> InventoryMovement:
        if quantity <= 0:
            raise ValueError(
                "Stock addition quantity must be greater than zero."
            )

        if movement_type not in {
            "OPENING_STOCK",
            "PURCHASE",
            "RETURN",
            "ADJUSTMENT",
        }:
            raise ValueError(
                "Invalid movement type for stock addition."
            )

        return self.record_movement(
            product_variant_id=product_variant_id,
            movement_type=movement_type,
            quantity=quantity,
            created_by=created_by,
            reference_type=reference_type,
            reference_id=reference_id,
            reason=reason,
        )

    def remove_stock(
        self,
        product_variant_id: int,
        quantity: int,
        movement_type: str,
        created_by: int | None = None,
        reference_type: str | None = None,
        reference_id: int | None = None,
        reason: str | None = None,
    ) -> InventoryMovement:
        if quantity <= 0:
            raise ValueError(
                "Stock removal quantity must be greater than zero."
            )

        if movement_type not in {
            "SALE",
            "DAMAGE",
            "ADJUSTMENT",
        }:
            raise ValueError(
                "Invalid movement type for stock removal."
            )

        return self.record_movement(
            product_variant_id=product_variant_id,
            movement_type=movement_type,
            quantity=-quantity,
            created_by=created_by,
            reference_type=reference_type,
            reference_id=reference_id,
            reason=reason,
        )

    def get_current_quantity(
        self,
        product_variant_id: int,
    ) -> int:
        inventory = self.get_inventory(
            product_variant_id
        )

        if inventory is None:
            return 0

        return inventory.quantity
    def get_movements(
        self,
        product_variant_id: int,
    ) -> list[InventoryMovement]:
        inventory = self.get_inventory(
            product_variant_id
        )

        if inventory is None:
            return []

        statement = (
            select(InventoryMovement)
            .where(
                InventoryMovement.inventory_id == inventory.id
            )
            .order_by(
                InventoryMovement.created_at,
                InventoryMovement.id,
            )
        )

        return list(
            self.session.scalars(statement).all()
        )