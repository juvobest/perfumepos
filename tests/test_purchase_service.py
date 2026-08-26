from datetime import date
from decimal import Decimal

import pytest

from app.database.connection import SessionLocal
from app.models import Category, Product, ProductVariant, Supplier
from app.services.purchase_service import PurchaseService
from uuid import uuid4


def create_test_variant(
    session,
    name: str,
) -> ProductVariant:
    category = Category(
        name=f"{name} Category"
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
        cost_price=Decimal("50000.00"),
        selling_price=Decimal("75000.00"),
    )

    session.add(variant)
    session.flush()

    return variant


def create_test_supplier(
    session,
    name: str,
) -> Supplier:
    supplier = Supplier(
        name=name,
    )

    session.add(supplier)
    session.flush()

    return supplier


def test_create_purchase():
    with SessionLocal() as session:
        supplier = create_test_supplier(
            session,
            "Purchase Supplier",
        )

        service = PurchaseService(session)

        purchase = service.create_purchase(
            supplier_id=supplier.id,
            purchase_date=date(2026, 8, 17),
        )

        assert purchase.id is not None
        assert purchase.supplier_id == supplier.id
        assert purchase.purchase_number.startswith("PUR-")
        assert len(purchase.purchase_number) == 10
        assert purchase.status == "DRAFT"
        assert purchase.total_amount == Decimal("0.00")


def test_create_purchase_requires_active_supplier():
    with SessionLocal() as session:
        supplier = create_test_supplier(
            session,
            "Inactive Purchase Supplier",
        )

        supplier.is_active = False
        session.flush()

        service = PurchaseService(session)

        with pytest.raises(
            ValueError,
            match="Cannot create a purchase for an inactive supplier.",
        ):
            service.create_purchase(
                supplier_id=supplier.id,
                purchase_date=date(2026, 8, 17),
            )


def test_create_purchase_requires_existing_supplier():
    with SessionLocal() as session:
        service = PurchaseService(session)

        with pytest.raises(
            ValueError,
            match="Supplier not found.",
        ):
            service.create_purchase(
                supplier_id=999999,
                purchase_date=date(2026, 8, 17),
            )


def test_add_purchase_item_calculates_total():
    with SessionLocal() as session:
        supplier = create_test_supplier(
            session,
            "Item Supplier",
        )

        variant = create_test_variant(
            session,
            "ItemProduct",
        )

        service = PurchaseService(session)

        purchase = service.create_purchase(
            supplier_id=supplier.id,
            purchase_date=date(2026, 8, 17),
        )

        item = service.add_item(
            purchase_id=purchase.id,
            product_variant_id=variant.id,
            quantity=10,
            unit_cost=Decimal("80000.00"),
        )

        assert item.quantity == 10
        assert item.unit_cost == Decimal("80000.00")
        assert item.total_cost == Decimal("800000.00")
        assert purchase.total_amount == Decimal("800000.00")


def test_add_multiple_items_calculates_purchase_total():
    with SessionLocal() as session:
        supplier = create_test_supplier(
            session,
            "Multi Item Supplier",
        )

        variant_one = create_test_variant(
            session,
            "MultiItemOne",
        )

        variant_two = create_test_variant(
            session,
            "MultiItemTwo",
        )

        service = PurchaseService(session)

        purchase = service.create_purchase(
            supplier_id=supplier.id,
            purchase_date=date(2026, 8, 17),
        )

        service.add_item(
            purchase_id=purchase.id,
            product_variant_id=variant_one.id,
            quantity=10,
            unit_cost=Decimal("80000.00"),
        )

        service.add_item(
            purchase_id=purchase.id,
            product_variant_id=variant_two.id,
            quantity=5,
            unit_cost=Decimal("75000.00"),
        )

        assert purchase.total_amount == Decimal(
            "1175000.00"
        )


def test_purchase_item_requires_positive_quantity():
    with SessionLocal() as session:
        supplier = create_test_supplier(
            session,
            "Quantity Supplier",
        )

        variant = create_test_variant(
            session,
            "QuantityProduct",
        )

        service = PurchaseService(session)

        purchase = service.create_purchase(
            supplier_id=supplier.id,
            purchase_date=date(2026, 8, 17),
        )

        with pytest.raises(
            ValueError,
            match="Purchase quantity must be greater than zero.",
        ):
            service.add_item(
                purchase_id=purchase.id,
                product_variant_id=variant.id,
                quantity=0,
                unit_cost=Decimal("50000.00"),
            )


def test_purchase_item_rejects_negative_cost():
    with SessionLocal() as session:
        supplier = create_test_supplier(
            session,
            "Cost Supplier",
        )

        variant = create_test_variant(
            session,
            "CostProduct",
        )

        service = PurchaseService(session)

        purchase = service.create_purchase(
            supplier_id=supplier.id,
            purchase_date=date(2026, 8, 17),
        )

        with pytest.raises(
            ValueError,
            match="Unit cost cannot be negative.",
        ):
            service.add_item(
                purchase_id=purchase.id,
                product_variant_id=variant.id,
                quantity=5,
                unit_cost=Decimal("-100.00"),
            )


def test_purchase_item_requires_existing_product_variant():
    with SessionLocal() as session:
        supplier = create_test_supplier(
            session,
            "Variant Supplier",
        )

        service = PurchaseService(session)

        purchase = service.create_purchase(
            supplier_id=supplier.id,
            purchase_date=date(2026, 8, 17),
        )

        with pytest.raises(
            ValueError,
            match="Product variant not found.",
        ):
            service.add_item(
                purchase_id=purchase.id,
                product_variant_id=999999,
                quantity=5,
                unit_cost=Decimal("50000.00"),
            )


def test_remove_purchase_item_updates_total():
    with SessionLocal() as session:
        supplier = create_test_supplier(
            session,
            "Remove Supplier",
        )

        variant = create_test_variant(
            session,
            "RemoveProduct",
        )

        service = PurchaseService(session)

        purchase = service.create_purchase(
            supplier_id=supplier.id,
            purchase_date=date(2026, 8, 17),
        )

        item = service.add_item(
            purchase_id=purchase.id,
            product_variant_id=variant.id,
            quantity=10,
            unit_cost=Decimal("80000.00"),
        )

        assert purchase.total_amount == Decimal(
            "800000.00"
        )

        service.remove_item(item.id)

        assert purchase.total_amount == Decimal(
            "0.00"
        )


def test_receive_purchase_updates_inventory():
    with SessionLocal() as session:
        supplier = create_test_supplier(
            session,
            "Receive Supplier",
        )

        variant = create_test_variant(
            session,
            "ReceiveProduct",
        )

        service = PurchaseService(session)

        purchase = service.create_purchase(
            supplier_id=supplier.id,
            purchase_date=date(2026, 8, 17),
        )

        service.add_item(
            purchase_id=purchase.id,
            product_variant_id=variant.id,
            quantity=10,
            unit_cost=Decimal("80000.00"),
        )

        received = service.receive_purchase(
            purchase.id
        )

        assert received.status == "RECEIVED"

        assert (
            service.inventory_service
            .get_current_quantity(variant.id)
            == 10
        )


def test_receive_purchase_creates_inventory_movement():
    with SessionLocal() as session:
        supplier = create_test_supplier(
            session,
            "Movement Supplier",
        )

        variant = create_test_variant(
            session,
            "MovementProduct",
        )

        service = PurchaseService(session)

        purchase = service.create_purchase(
            supplier_id=supplier.id,
            purchase_date=date(2026, 8, 17),
        )

        service.add_item(
            purchase_id=purchase.id,
            product_variant_id=variant.id,
            quantity=10,
            unit_cost=Decimal("80000.00"),
        )

        service.receive_purchase(
            purchase.id
        )

        movements = (
            service.inventory_service
            .get_movements(variant.id)
        )

        assert len(movements) == 1

        movement = movements[0]

        assert movement.movement_type == "PURCHASE"
        assert movement.quantity == 10
        assert movement.quantity_before == 0
        assert movement.quantity_after == 10
        assert movement.reference_type == "purchase"
        assert movement.reference_id == purchase.id


def test_received_purchase_cannot_be_received_again():
    with SessionLocal() as session:
        supplier = create_test_supplier(
            session,
            "Double Receive Supplier",
        )

        variant = create_test_variant(
            session,
            "DoubleReceiveProduct",
        )

        service = PurchaseService(session)

        purchase = service.create_purchase(
            supplier_id=supplier.id,
            purchase_date=date(2026, 8, 17),
        )

        service.add_item(
            purchase_id=purchase.id,
            product_variant_id=variant.id,
            quantity=10,
            unit_cost=Decimal("80000.00"),
        )

        service.receive_purchase(
            purchase.id
        )

        with pytest.raises(
            ValueError,
            match="Purchase has already been received.",
        ):
            service.receive_purchase(
                purchase.id
            )

        assert (
            service.inventory_service
            .get_current_quantity(variant.id)
            == 10
        )


def test_purchase_without_items_cannot_be_received():
    with SessionLocal() as session:
        supplier = create_test_supplier(
            session,
            "Empty Purchase Supplier",
        )

        service = PurchaseService(session)

        purchase = service.create_purchase(
            supplier_id=supplier.id,
            purchase_date=date(2026, 8, 17),
        )

        with pytest.raises(
            ValueError,
            match="Cannot receive a purchase without items.",
        ):
            service.receive_purchase(
                purchase.id
            )


def test_cancel_draft_purchase():
    with SessionLocal() as session:
        supplier = create_test_supplier(
            session,
            "Cancel Supplier",
        )

        service = PurchaseService(session)

        purchase = service.create_purchase(
            supplier_id=supplier.id,
            purchase_date=date(2026, 8, 17),
        )

        cancelled = service.cancel_purchase(
            purchase.id
        )

        assert cancelled.status == "CANCELLED"


def test_cancelled_purchase_cannot_be_received():
    with SessionLocal() as session:
        supplier = create_test_supplier(
            session,
            "Cancelled Receive Supplier",
        )

        variant = create_test_variant(
            session,
            "CancelledProduct",
        )

        service = PurchaseService(session)

        purchase = service.create_purchase(
            supplier_id=supplier.id,
            purchase_date=date(2026, 8, 17),
        )

        service.add_item(
            purchase_id=purchase.id,
            product_variant_id=variant.id,
            quantity=10,
            unit_cost=Decimal("80000.00"),
        )

        service.cancel_purchase(
            purchase.id
        )

        with pytest.raises(
            ValueError,
            match="Cancelled purchases cannot be received.",
        ):
            service.receive_purchase(
                purchase.id
            )

        assert (
            service.inventory_service
            .get_current_quantity(variant.id)
            == 0
        )


def test_received_purchase_cannot_be_cancelled():
    with SessionLocal() as session:
        supplier = create_test_supplier(
            session,
            "Received Cancel Supplier",
        )

        variant = create_test_variant(
            session,
            "ReceivedCancelProduct",
        )

        service = PurchaseService(session)

        purchase = service.create_purchase(
            supplier_id=supplier.id,
            purchase_date=date(2026, 8, 17),
        )

        service.add_item(
            purchase_id=purchase.id,
            product_variant_id=variant.id,
            quantity=5,
            unit_cost=Decimal("50000.00"),
        )

        service.receive_purchase(
            purchase.id
        )

        with pytest.raises(
            ValueError,
            match="Received purchases cannot be cancelled.",
        ):
            service.cancel_purchase(
                purchase.id
            )


def test_received_purchase_cannot_add_items():
    with SessionLocal() as session:
        supplier = create_test_supplier(
            session,
            "Received Add Supplier",
        )

        variant_one = create_test_variant(
            session,
            "ReceivedAddOne",
        )

        variant_two = create_test_variant(
            session,
            "ReceivedAddTwo",
        )

        service = PurchaseService(session)

        purchase = service.create_purchase(
            supplier_id=supplier.id,
            purchase_date=date(2026, 8, 17),
        )

        service.add_item(
            purchase_id=purchase.id,
            product_variant_id=variant_one.id,
            quantity=5,
            unit_cost=Decimal("50000.00"),
        )

        service.receive_purchase(
            purchase.id
        )

        with pytest.raises(
            ValueError,
            match="Items can only be added to a draft purchase.",
        ):
            service.add_item(
                purchase_id=purchase.id,
                product_variant_id=variant_two.id,
                quantity=5,
                unit_cost=Decimal("50000.00"),
            )


def test_received_purchase_cannot_remove_items():
    with SessionLocal() as session:
        supplier = create_test_supplier(
            session,
            "Received Remove Supplier",
        )

        variant = create_test_variant(
            session,
            "ReceivedRemoveProduct",
        )

        service = PurchaseService(session)

        purchase = service.create_purchase(
            supplier_id=supplier.id,
            purchase_date=date(2026, 8, 17),
        )

        item = service.add_item(
            purchase_id=purchase.id,
            product_variant_id=variant.id,
            quantity=5,
            unit_cost=Decimal("50000.00"),
        )

        service.receive_purchase(
            purchase.id
        )

        with pytest.raises(
            ValueError,
            match="Items can only be removed from a draft purchase.",
        ):
            service.remove_item(item.id)

def test_receive_purchase_rolls_back_when_inventory_update_fails():
    with SessionLocal() as session:
        test_id = uuid4().hex[:8]
        supplier = create_test_supplier(
            session,
            f"Rollback Supplier {test_id}",
        )

        variant_one = create_test_variant(
            session,
            f"RollbackProductOne {test_id}",
        )

        variant_two = create_test_variant(
            session,
            f"RollbackProductTwo {test_id}",
        )

        service = PurchaseService(session)

        purchase = service.create_purchase(
            supplier_id=supplier.id,
            purchase_date=date(2026, 8, 17),
        )

        service.add_item(
            purchase_id=purchase.id,
            product_variant_id=variant_one.id,
            quantity=10,
            unit_cost=Decimal("50000.00"),
        )

        service.add_item(
            purchase_id=purchase.id,
            product_variant_id=variant_two.id,
            quantity=5,
            unit_cost=Decimal("50000.00"),
        )

        # Commit the completed draft purchase.
        # This represents the transaction that created
        # the purchase before receiving begins.
        session.commit()

        # Start a fresh service using the same session.
        service = PurchaseService(session)

        original_add_stock = (
            service.inventory_service.add_stock
        )

        call_count = 0

        def failing_add_stock(*args, **kwargs):
            nonlocal call_count

            call_count += 1

            if call_count == 2:
                raise ValueError(
                    "Simulated inventory failure."
                )

            return original_add_stock(
                *args,
                **kwargs,
            )

        service.inventory_service.add_stock = (
            failing_add_stock
        )

        with pytest.raises(
            ValueError,
            match="Simulated inventory failure.",
        ):
            service.receive_purchase(
                purchase.id
            )

        # Roll back the entire receiving transaction.
        session.rollback()

        # Neither inventory update should remain.
        assert (
            service.inventory_service
            .get_current_quantity(variant_one.id)
            == 0
        )

        assert (
            service.inventory_service
            .get_current_quantity(variant_two.id)
            == 0
        )

        # The purchase itself should still exist
        # and remain DRAFT.
        refreshed_purchase = (
            service.get_by_id(purchase.id)
        )

        assert refreshed_purchase is not None
        assert refreshed_purchase.status == "DRAFT"