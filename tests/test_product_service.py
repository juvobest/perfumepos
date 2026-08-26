from decimal import Decimal

import pytest

from app.database.connection import SessionLocal
from app.models import Brand, Category
from app.services.product_service import ProductService


def test_create_product_and_variant():
    with SessionLocal() as session:
        category = Category(
            name="Service Test Perfumes",
        )

        brand = Brand(
            name="Service Test Brand",
        )

        session.add_all([category, brand])
        session.flush()

        service = ProductService(session)

        product = service.create_product(
            name="Service Test Perfume",
            category_id=category.id,
            brand_id=brand.id,
            description="Product service test",
        )

        variant = service.create_variant(
            product_id=product.id,
            variant_name="100ml",
            size="100",
            unit="ml",
            sku="SERVICE-TEST-100",
            barcode="SERVICE-BARCODE-100",
            cost_price=Decimal("10000.00"),
            selling_price=Decimal("15000.00"),
            reorder_level=5,
        )

        assert product.id is not None
        assert product.name == "Service Test Perfume"

        assert variant.id is not None
        assert variant.product_id == product.id
        assert variant.cost_price == Decimal("10000.00")
        assert variant.selling_price == Decimal("15000.00")


def test_product_name_is_required():
    with SessionLocal() as session:
        service = ProductService(session)

        with pytest.raises(ValueError):
            service.create_product("   ")


def test_negative_price_is_rejected():
    with SessionLocal() as session:
        category = Category(
            name="Negative Price Test Category",
        )

        session.add(category)
        session.flush()

        service = ProductService(session)

        product = service.create_product(
            name="Negative Price Test Product",
            category_id=category.id,
        )

        with pytest.raises(ValueError):
            service.create_variant(
                product_id=product.id,
                cost_price=Decimal("-100.00"),
                selling_price=Decimal("150.00"),
            )


def test_duplicate_sku_is_rejected():
    with SessionLocal() as session:
        category = Category(
            name="Duplicate SKU Test Category",
        )

        session.add(category)
        session.flush()

        service = ProductService(session)

        product = service.create_product(
            name="Duplicate SKU Test Product",
            category_id=category.id,
        )

        service.create_variant(
            product_id=product.id,
            cost_price=Decimal("10000.00"),
            selling_price=Decimal("15000.00"),
            sku="DUPLICATE-SKU",
        )

        with pytest.raises(ValueError):
            service.create_variant(
                product_id=product.id,
                cost_price=Decimal("12000.00"),
                selling_price=Decimal("18000.00"),
                sku="DUPLICATE-SKU",
            )


def test_duplicate_barcode_is_rejected():
    with SessionLocal() as session:
        category = Category(
            name="Duplicate Barcode Test Category",
        )

        session.add(category)
        session.flush()

        service = ProductService(session)

        product = service.create_product(
            name="Duplicate Barcode Test Product",
            category_id=category.id,
        )

        service.create_variant(
            product_id=product.id,
            cost_price=Decimal("10000.00"),
            selling_price=Decimal("15000.00"),
            barcode="DUPLICATE-BARCODE",
        )

        with pytest.raises(ValueError):
            service.create_variant(
                product_id=product.id,
                cost_price=Decimal("12000.00"),
                selling_price=Decimal("18000.00"),
                barcode="DUPLICATE-BARCODE",
            )


def test_negative_reorder_level_is_rejected():
    with SessionLocal() as session:
        category = Category(
            name="Reorder Level Test Category",
        )

        session.add(category)
        session.flush()

        service = ProductService(session)

        product = service.create_product(
            name="Reorder Level Test Product",
            category_id=category.id,
        )

        with pytest.raises(ValueError):
            service.create_variant(
                product_id=product.id,
                cost_price=Decimal("10000.00"),
                selling_price=Decimal("15000.00"),
                reorder_level=-1,
            )


def test_deactivate_product_and_variant():
    with SessionLocal() as session:
        category = Category(
            name="Deactivate Test Category",
        )

        session.add(category)
        session.flush()

        service = ProductService(session)

        product = service.create_product(
            name="Deactivate Test Product",
            category_id=category.id,
        )

        variant = service.create_variant(
            product_id=product.id,
            cost_price=Decimal("10000.00"),
            selling_price=Decimal("15000.00"),
        )

        service.deactivate_variant(variant.id)
        service.deactivate_product(product.id)

        assert variant.is_active is False
        assert product.is_active is False