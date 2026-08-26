from decimal import Decimal

import pytest

from app.database.connection import SessionLocal
from app.models import Category, Product, ProductVariant
from app.services.inventory_service import InventoryService


def create_test_variant(session, name: str) -> ProductVariant:
    category = Category(
        name=f"{name} Category",
    )

    session.add(category)
    session.flush()

    product = Product(
        name=f"{name} Product",
        category_id=category.id,
    )

    session.add(product)
    session.flush()

    variant = ProductVariant(
        product_id=product.id,
        variant_name="100ml",
        size="100",
        unit="ml",
        sku=f"{name.upper()}-SKU",
        cost_price=Decimal("10000.00"),
        selling_price=Decimal("15000.00"),
    )

    session.add(variant)
    session.flush()

    return variant


def test_inventory_is_created_with_zero_quantity():
    with SessionLocal() as session:
        variant = create_test_variant(
            session,
            "InventoryZero",
        )

        service = InventoryService(session)

        inventory = service.get_or_create_inventory(
            variant.id
        )

        assert inventory.id is not None
        assert inventory.product_variant_id == variant.id
        assert inventory.quantity == 0


def test_opening_stock_increases_inventory():
    with SessionLocal() as session:
        variant = create_test_variant(
            session,
            "OpeningStock",
        )

        service = InventoryService(session)

        movement = service.add_stock(
            product_variant_id=variant.id,
            quantity=20,
            movement_type="OPENING_STOCK",
            reason="Initial stock",
        )

        assert movement.quantity == 20
        assert movement.quantity_before == 0
        assert movement.quantity_after == 20

        assert (
            service.get_current_quantity(variant.id)
            == 20
        )


def test_purchase_increases_inventory():
    with SessionLocal() as session:
        variant = create_test_variant(
            session,
            "Purchase",
        )

        service = InventoryService(session)

        service.add_stock(
            product_variant_id=variant.id,
            quantity=20,
            movement_type="OPENING_STOCK",
        )

        movement = service.add_stock(
            product_variant_id=variant.id,
            quantity=10,
            movement_type="PURCHASE",
        )

        assert movement.quantity_before == 20
        assert movement.quantity == 10
        assert movement.quantity_after == 30

        assert (
            service.get_current_quantity(variant.id)
            == 30
        )


def test_sale_decreases_inventory():
    with SessionLocal() as session:
        variant = create_test_variant(
            session,
            "Sale",
        )

        service = InventoryService(session)

        service.add_stock(
            product_variant_id=variant.id,
            quantity=20,
            movement_type="OPENING_STOCK",
        )

        movement = service.remove_stock(
            product_variant_id=variant.id,
            quantity=3,
            movement_type="SALE",
        )

        assert movement.quantity == -3
        assert movement.quantity_before == 20
        assert movement.quantity_after == 17

        assert (
            service.get_current_quantity(variant.id)
            == 17
        )


def test_return_increases_inventory():
    with SessionLocal() as session:
        variant = create_test_variant(
            session,
            "Return",
        )

        service = InventoryService(session)

        service.add_stock(
            product_variant_id=variant.id,
            quantity=10,
            movement_type="OPENING_STOCK",
        )

        service.remove_stock(
            product_variant_id=variant.id,
            quantity=2,
            movement_type="SALE",
        )

        movement = service.add_stock(
            product_variant_id=variant.id,
            quantity=1,
            movement_type="RETURN",
        )

        assert movement.quantity_before == 8
        assert movement.quantity_after == 9

        assert (
            service.get_current_quantity(variant.id)
            == 9
        )


def test_damage_decreases_inventory():
    with SessionLocal() as session:
        variant = create_test_variant(
            session,
            "Damage",
        )

        service = InventoryService(session)

        service.add_stock(
            product_variant_id=variant.id,
            quantity=10,
            movement_type="OPENING_STOCK",
        )

        movement = service.remove_stock(
            product_variant_id=variant.id,
            quantity=2,
            movement_type="DAMAGE",
            reason="Damaged bottles",
        )

        assert movement.quantity == -2
        assert movement.quantity_before == 10
        assert movement.quantity_after == 8

        assert (
            service.get_current_quantity(variant.id)
            == 8
        )


def test_adjustment_can_increase_stock():
    with SessionLocal() as session:
        variant = create_test_variant(
            session,
            "AdjustmentIncrease",
        )

        service = InventoryService(session)

        service.add_stock(
            product_variant_id=variant.id,
            quantity=10,
            movement_type="OPENING_STOCK",
        )

        movement = service.add_stock(
            product_variant_id=variant.id,
            quantity=2,
            movement_type="ADJUSTMENT",
            reason="Physical count correction",
        )

        assert movement.quantity_before == 10
        assert movement.quantity_after == 12

        assert (
            service.get_current_quantity(variant.id)
            == 12
        )


def test_adjustment_can_decrease_stock():
    with SessionLocal() as session:
        variant = create_test_variant(
            session,
            "AdjustmentDecrease",
        )

        service = InventoryService(session)

        service.add_stock(
            product_variant_id=variant.id,
            quantity=10,
            movement_type="OPENING_STOCK",
        )

        movement = service.remove_stock(
            product_variant_id=variant.id,
            quantity=2,
            movement_type="ADJUSTMENT",
            reason="Physical count correction",
        )

        assert movement.quantity_before == 10
        assert movement.quantity == -2
        assert movement.quantity_after == 8

        assert (
            service.get_current_quantity(variant.id)
            == 8
        )


def test_negative_stock_is_rejected():
    with SessionLocal() as session:
        variant = create_test_variant(
            session,
            "NegativeStock",
        )

        service = InventoryService(session)

        service.add_stock(
            product_variant_id=variant.id,
            quantity=2,
            movement_type="OPENING_STOCK",
        )

        with pytest.raises(
            ValueError,
            match="Insufficient stock.",
        ):
            service.remove_stock(
                product_variant_id=variant.id,
                quantity=5,
                movement_type="SALE",
            )

        assert (
            service.get_current_quantity(variant.id)
            == 2
        )


def test_zero_quantity_is_rejected():
    with SessionLocal() as session:
        variant = create_test_variant(
            session,
            "ZeroQuantity",
        )

        service = InventoryService(session)

        with pytest.raises(
            ValueError,
            match="Stock addition quantity must be greater than zero.",
        ):
            service.add_stock(
                product_variant_id=variant.id,
                quantity=0,
                movement_type="PURCHASE",
            )


def test_invalid_movement_type_is_rejected():
    with SessionLocal() as session:
        variant = create_test_variant(
            session,
            "InvalidMovement",
        )

        service = InventoryService(session)

        with pytest.raises(
            ValueError,
            match="Invalid movement type for stock addition.",
        ):
            service.add_stock(
                product_variant_id=variant.id,
                quantity=10,
                movement_type="INVALID",
            )


def test_movement_history_is_recorded():
    with SessionLocal() as session:
        variant = create_test_variant(
            session,
            "MovementHistory",
        )

        service = InventoryService(session)

        service.add_stock(
            product_variant_id=variant.id,
            quantity=20,
            movement_type="OPENING_STOCK",
        )

        service.add_stock(
            product_variant_id=variant.id,
            quantity=10,
            movement_type="PURCHASE",
        )

        service.remove_stock(
            product_variant_id=variant.id,
            quantity=3,
            movement_type="SALE",
        )

        movements = service.get_movements(
            variant.id
        )

        assert len(movements) == 3

        assert movements[0].movement_type == (
            "OPENING_STOCK"
        )
        assert movements[0].quantity == 20

        assert movements[1].movement_type == (
            "PURCHASE"
        )
        assert movements[1].quantity == 10

        assert movements[2].movement_type == "SALE"
        assert movements[2].quantity == -3

        assert movements[2].quantity_after == 27