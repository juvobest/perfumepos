from decimal import Decimal

from app.database.connection import SessionLocal
from app.models import Brand, Category, Product, ProductVariant


def test_create_product_with_variant():
    with SessionLocal() as session:
        category = Category(
            name="Test Perfumes",
            description="Temporary test category",
        )

        brand = Brand(
            name="Test Brand",
            description="Temporary test brand",
        )

        session.add_all([category, brand])
        session.flush()

        product = Product(
            name="Test Perfume",
            category=category,
            brand=brand,
            description="Temporary test product",
        )

        session.add(product)
        session.flush()

        variant = ProductVariant(
            product=product,
            variant_name="100ml",
            size="100",
            unit="ml",
            sku="TEST-100",
            barcode="TEST-BARCODE-100",
            cost_price=Decimal("10000.00"),
            selling_price=Decimal("15000.00"),
            reorder_level=5,
        )

        session.add(variant)
        session.flush()

        assert product.id is not None
        assert variant.id is not None
        assert variant.cost_price == Decimal("10000.00")
        assert variant.selling_price == Decimal("15000.00")
        assert product.category.name == "Test Perfumes"
        assert product.brand.name == "Test Brand"