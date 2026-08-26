from datetime import date
from decimal import Decimal

import pytest

from app.database.connection import SessionLocal
from app.models.sale import Sale
from app.services.product_service import ProductService
from app.services.sale_service import SaleService
from app.database.transaction import transaction


def create_test_variant(
    session,
    name="Sale Test Product",
    selling_price=Decimal("50000.00"),
):
    product_service = ProductService(session)

    product = product_service.create_product(
        name=name,
    )

    return product_service.create_variant(
        product_id=product.id,
        cost_price=Decimal("30000.00"),
        selling_price=selling_price,
        variant_name="100ml",
        unit="ml",
    )


def test_create_sale():
    with SessionLocal() as session:
        service = SaleService(session)

        sale = service.create_sale(
            sale_date=date(2026, 8, 17),
        )

        assert sale.id is not None
        assert sale.sale_number.startswith(
            "SALE-"
        )
        assert sale.status == "DRAFT"
        assert sale.subtotal == Decimal("0.00")
        assert sale.discount == Decimal("0.00")
        assert sale.total_amount == Decimal("0.00")


def test_create_sale_with_customer():
    with SessionLocal() as session:
        from app.services.customer_service import (
            CustomerService,
        )

        customer_service = CustomerService(
            session
        )

        customer = customer_service.create_customer(
            name="Sales Customer"
        )

        service = SaleService(session)

        sale = service.create_sale(
            sale_date=date(2026, 8, 17),
            customer_id=customer.id,
        )

        assert sale.customer_id == customer.id


def test_create_sale_rejects_missing_customer():
    with SessionLocal() as session:
        service = SaleService(session)

        with pytest.raises(
            ValueError,
            match="Customer not found.",
        ):
            service.create_sale(
                sale_date=date(2026, 8, 17),
                customer_id=999999,
            )


def test_add_item():
    with SessionLocal() as session:
        variant = create_test_variant(
            session,
            name="Add Sale Item Product",
        )

        service = SaleService(session)

        sale = service.create_sale(
            sale_date=date(2026, 8, 17),
        )

        item = service.add_item(
            sale_id=sale.id,
            product_variant_id=variant.id,
            quantity=2,
        )

        assert item.id is not None
        assert item.quantity == 2
        assert item.unit_price == Decimal(
            "50000.00"
        )
        assert item.total_price == Decimal(
            "100000.00"
        )

        assert sale.subtotal == Decimal(
            "100000.00"
        )
        assert sale.total_amount == Decimal(
            "100000.00"
        )


def test_add_item_applies_item_discount():
    with SessionLocal() as session:
        variant = create_test_variant(
            session,
            name="Discount Sale Product",
        )

        service = SaleService(session)

        sale = service.create_sale(
            sale_date=date(2026, 8, 17),
        )

        item = service.add_item(
            sale_id=sale.id,
            product_variant_id=variant.id,
            quantity=2,
            discount=Decimal("5000.00"),
        )

        assert item.discount == Decimal(
            "5000.00"
        )
        assert item.total_price == Decimal(
            "95000.00"
        )

        assert sale.subtotal == Decimal(
            "95000.00"
        )


def test_add_same_variant_increases_quantity():
    with SessionLocal() as session:
        variant = create_test_variant(
            session,
            name="Duplicate Sale Product",
        )

        service = SaleService(session)

        sale = service.create_sale(
            sale_date=date(2026, 8, 17),
        )

        service.add_item(
            sale.id,
            variant.id,
            2,
        )

        item = service.add_item(
            sale.id,
            variant.id,
            3,
        )

        assert item.quantity == 5
        assert item.total_price == Decimal(
            "250000.00"
        )


def test_add_item_rejects_zero_quantity():
    with SessionLocal() as session:
        variant = create_test_variant(
            session,
            name="Zero Quantity Product",
        )

        service = SaleService(session)

        sale = service.create_sale(
            sale_date=date(2026, 8, 17),
        )

        with pytest.raises(
            ValueError,
            match="Sale quantity must be greater than zero.",
        ):
            service.add_item(
                sale.id,
                variant.id,
                0,
            )


def test_remove_item():
    with SessionLocal() as session:
        variant = create_test_variant(
            session,
            name="Remove Sale Product",
        )

        service = SaleService(session)

        sale = service.create_sale(
            sale_date=date(2026, 8, 17),
        )

        item = service.add_item(
            sale.id,
            variant.id,
            2,
        )

        service.remove_item(item.id)

        assert sale.items == []
        assert sale.subtotal == Decimal(
            "0.00"
        )
        assert sale.total_amount == Decimal(
            "0.00"
        )


def test_sale_discount():
    with SessionLocal() as session:
        variant = create_test_variant(
            session,
            name="Sale Discount Product",
        )

        service = SaleService(session)

        sale = service.create_sale(
            sale_date=date(2026, 8, 17),
        )

        service.add_item(
            sale.id,
            variant.id,
            2,
        )

        service.calculate_totals(
            sale.id,
            discount=Decimal("10000.00"),
        )

        assert sale.subtotal == Decimal(
            "100000.00"
        )
        assert sale.discount == Decimal(
            "10000.00"
        )
        assert sale.total_amount == Decimal(
            "90000.00"
        )


def test_add_payment():
    with SessionLocal() as session:
        variant = create_test_variant(
            session,
            name="Payment Sale Product",
        )

        service = SaleService(session)

        sale = service.create_sale(
            sale_date=date(2026, 8, 17),
        )

        service.add_item(
            sale.id,
            variant.id,
            2,
        )

        payment = service.add_payment(
            sale.id,
            Decimal("100000.00"),
            "TRANSFER",
            reference="TRX-001",
        )

        assert payment.id is not None
        assert payment.amount == Decimal(
            "100000.00"
        )
        assert payment.payment_method == (
            "TRANSFER"
        )
        assert payment.reference == "TRX-001"

        assert service.get_total_paid(
            sale.id
        ) == Decimal("100000.00")


def test_payment_cannot_exceed_sale_total():
    with SessionLocal() as session:
        variant = create_test_variant(
            session,
            name="Overpayment Product",
        )

        service = SaleService(session)

        sale = service.create_sale(
            sale_date=date(2026, 8, 17),
        )

        service.add_item(
            sale.id,
            variant.id,
            1,
        )

        with pytest.raises(
            ValueError,
            match="Payment cannot exceed sale total.",
        ):
            service.add_payment(
                sale.id,
                Decimal("50001.00"),
                "CASH",
            )


def test_complete_sale_reduces_inventory():
    with SessionLocal() as session:
        variant = create_test_variant(
            session,
            name="Complete Sale Product",
        )

        service = SaleService(session)

        service.inventory_service.add_stock(
            product_variant_id=variant.id,
            quantity=10,
            movement_type="OPENING_STOCK",
        )

        sale = service.create_sale(
            sale_date=date(2026, 8, 17),
        )

        service.add_item(
            sale.id,
            variant.id,
            3,
        )

        service.add_payment(
            sale.id,
            Decimal("150000.00"),
            "CASH",
        )

        completed = service.complete_sale(
            sale.id
        )

        assert completed.status == "COMPLETED"

        assert (
            service.inventory_service
            .get_current_quantity(variant.id)
            == 7
        )


def test_complete_sale_requires_items():
    with SessionLocal() as session:
        service = SaleService(session)

        sale = service.create_sale(
            sale_date=date(2026, 8, 17),
        )

        with pytest.raises(
            ValueError,
            match="Cannot complete a sale without items.",
        ):
            service.complete_sale(sale.id)


def test_complete_sale_requires_full_payment():
    with SessionLocal() as session:
        variant = create_test_variant(
            session,
            name="Partial Payment Product",
        )

        service = SaleService(session)

        service.inventory_service.add_stock(
            variant.id,
            10,
            "OPENING_STOCK",
        )

        sale = service.create_sale(
            sale_date=date(2026, 8, 17),
        )

        service.add_item(
            sale.id,
            variant.id,
            2,
        )

        service.add_payment(
            sale.id,
            Decimal("50000.00"),
            "CASH",
        )

        with pytest.raises(
            ValueError,
            match="Sale must be fully paid before completion.",
        ):
            service.complete_sale(
                sale.id
            )

        assert sale.status == "DRAFT"


def test_complete_sale_rejects_insufficient_stock():
    with SessionLocal() as session:
        variant = create_test_variant(
            session,
            name="Insufficient Stock Product",
        )

        service = SaleService(session)

        service.inventory_service.add_stock(
            variant.id,
            2,
            "OPENING_STOCK",
        )

        sale = service.create_sale(
            sale_date=date(2026, 8, 17),
        )

        service.add_item(
            sale.id,
            variant.id,
            5,
        )

        service.add_payment(
            sale.id,
            Decimal("250000.00"),
            "CASH",
        )

        with pytest.raises(
            ValueError,
            match="Insufficient stock.",
        ):
            service.complete_sale(
                sale.id
            )

        assert sale.status == "DRAFT"

        assert (
            service.inventory_service
            .get_current_quantity(variant.id)
            == 2
        )


def test_completed_sale_cannot_be_modified():
    with SessionLocal() as session:
        variant = create_test_variant(
            session,
            name="Immutable Sale Product",
        )

        service = SaleService(session)

        service.inventory_service.add_stock(
            variant.id,
            10,
            "OPENING_STOCK",
        )

        sale = service.create_sale(
            sale_date=date(2026, 8, 17),
        )

        service.add_item(
            sale.id,
            variant.id,
            1,
        )

        service.add_payment(
            sale.id,
            Decimal("50000.00"),
            "CASH",
        )

        service.complete_sale(
            sale.id
        )

        with pytest.raises(
            ValueError,
            match="Only draft sales can be modified.",
        ):
            service.add_item(
                sale.id,
                variant.id,
                1,
            )


def test_cancel_sale():
    with SessionLocal() as session:
        service = SaleService(session)

        sale = service.create_sale(
            sale_date=date(2026, 8, 17),
        )

        cancelled = service.cancel_sale(
            sale.id
        )

        assert cancelled.status == (
            "CANCELLED"
        )

def test_complete_sale_rolls_back_when_inventory_update_fails():
    with SessionLocal() as session:
        variant_one = create_test_variant(
            session,
            name="Rollback Sale Product One",
        )

        variant_two = create_test_variant(
            session,
            name="Rollback Sale Product Two",
        )

        service = SaleService(session)

        service.inventory_service.add_stock(
            variant_one.id,
            10,
            "OPENING_STOCK",
        )

        service.inventory_service.add_stock(
            variant_two.id,
            10,
            "OPENING_STOCK",
        )

        sale = service.create_sale(
            sale_date=date(2026, 8, 17),
        )

        service.add_item(
            sale.id,
            variant_one.id,
            3,
        )

        service.add_item(
            sale.id,
            variant_two.id,
            2,
        )


        service.add_payment(
            sale.id,
            Decimal("250000.00"),
            "CASH",
        )

        session.commit()

        

        original_remove_stock = (
            service.inventory_service.remove_stock
        )

        call_count = 0

        def failing_remove_stock(
            *args,
            **kwargs,
        ):
            nonlocal call_count

            call_count += 1

            if call_count == 2:
                raise ValueError(
                    "Simulated inventory failure."
                )

            return original_remove_stock(
                *args,
                **kwargs,
            )

        service.inventory_service.remove_stock = (
            failing_remove_stock
        )

        with pytest.raises(
            ValueError,
            match="Simulated inventory failure.",
        ):
            with transaction(session):
                service.complete_sale(
                    sale.id
                )

        session.rollback()

        refreshed_sale = service.get_sale(
            sale.id
        )

        assert refreshed_sale is not None

        assert refreshed_sale.status == (
            "DRAFT"
        )

        assert (
            service.inventory_service
            .get_current_quantity(
                variant_one.id
            )
            == 10
        )

        assert (
            service.inventory_service
            .get_current_quantity(
                variant_two.id
            )
            == 10
        )
