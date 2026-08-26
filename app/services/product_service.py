from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.brand import Brand
from app.models.category import Category
from app.models.product import Product
from app.models.product_variant import ProductVariant


class ProductService:
    def __init__(self, session: Session):
        self.session = session

    def get_product(
    self,
    product_id: int,
):
        return self.session.get(
        Product,
        product_id,
    )

    # ---------------------------------------------------------
    # PRODUCTS
    # ---------------------------------------------------------

    def create_product(
        self,
        name: str,
        category_id: int | None = None,
        brand_id: int | None = None,
        description: str | None = None,
        image_path: str | None = None,
    ) -> Product:
        name = name.strip()

        if not name:
            raise ValueError(
                "Product name cannot be empty."
            )

        if category_id is not None:
            category = self.session.get(
                Category,
                category_id,
            )

            if category is None:
                raise ValueError(
                    "Category not found."
                )

        if brand_id is not None:
            brand = self.session.get(
                Brand,
                brand_id,
            )

            if brand is None:
                raise ValueError(
                    "Brand not found."
                )

        product = Product(
            name=name,
            category_id=category_id,
            brand_id=brand_id,
            description=(
                description.strip()
                if description
                else None
            ),
            image_path=(
                image_path.strip()
                if image_path
                else None
            ),
            is_active=True,
        )

        self.session.add(product)
        self.session.flush()

        return product

    def get_by_id(
        self,
        product_id: int,
    ) -> Product | None:
        return self.session.get(
            Product,
            product_id,
        )

    def get_by_name(
        self,
        name: str,
    ) -> Product | None:
        name = name.strip()

        statement = select(Product).where(
            Product.name == name
        )

        return self.session.scalar(statement)

    def list_products(
        self,
        include_inactive: bool = False,
        active_only: bool | None = None,
    ) -> list[Product]:
        statement = select(Product).order_by(
            Product.name
        )

        # Support both:
        #
        #     include_inactive=False
        #
        # and:
        #
        #     active_only=False
        #
        # This keeps compatibility with the existing
        # service/tests and the Products UI.

        if active_only is not None:
            if active_only:
                statement = statement.where(
                    Product.is_active.is_(True)
                )
        elif not include_inactive:
            statement = statement.where(
                Product.is_active.is_(True)
            )

        return list(
            self.session.scalars(statement).all()
        )

    def update_product(
        self,
        product_id: int,
        name: str | None = None,
        category_id: int | None = None,
        brand_id: int | None = None,
        description: str | None = None,
        image_path: str | None = None,
    ) -> Product:
        product = self.get_by_id(product_id)

        if product is None:
            raise ValueError(
                "Product not found."
            )

        if name is not None:
            name = name.strip()

            if not name:
                raise ValueError(
                    "Product name cannot be empty."
                )

            product.name = name

        if category_id is not None:
            category = self.session.get(
                Category,
                category_id,
            )

            if category is None:
                raise ValueError(
                    "Category not found."
                )

            product.category_id = category_id

        if brand_id is not None:
            brand = self.session.get(
                Brand,
                brand_id,
            )

            if brand is None:
                raise ValueError(
                    "Brand not found."
                )

            product.brand_id = brand_id

        if description is not None:
            product.description = (
                description.strip()
            )

        if image_path is not None:
            product.image_path = (
                image_path.strip()
            )

        self.session.flush()

        return product

    def deactivate_product(
        self,
        product_id: int,
    ) -> Product:
        product = self.get_by_id(product_id)

        if product is None:
            raise ValueError(
                "Product not found."
            )

        product.is_active = False

        self.session.flush()

        return product

    def activate_product(
        self,
        product_id: int,
    ) -> Product:
        product = self.get_by_id(product_id)

        if product is None:
            raise ValueError(
                "Product not found."
            )

        product.is_active = True

        self.session.flush()

        return product

    # ---------------------------------------------------------
    # PRODUCT VARIANTS
    # ---------------------------------------------------------

    def create_variant(
        self,
        product_id: int,
        variant_name: str | None = None,
        size: str | None = None,
        unit: str | None = None,
        sku: str | None = None,
        barcode: str | None = None,
        cost_price: Decimal = Decimal("0.00"),
        selling_price: Decimal = Decimal("0.00"),
        reorder_level: int | None = None,
    ) -> ProductVariant:
        product = self.get_by_id(product_id)

        if product is None:
            raise ValueError(
                "Product not found."
            )

        if cost_price < 0:
            raise ValueError(
                "Cost price cannot be negative."
            )

        if selling_price < 0:
            raise ValueError(
                "Selling price cannot be negative."
            )

        if (
            reorder_level is not None
            and reorder_level < 0
        ):
            raise ValueError(
                "Reorder level cannot be negative."
            )

        if sku is not None:
            sku = sku.strip()

            if sku:
                statement = select(
                    ProductVariant
                ).where(
                    ProductVariant.sku == sku
                )

                existing = self.session.scalar(
                    statement
                )

                if existing is not None:
                    raise ValueError(
                        "A variant with this SKU already exists."
                    )
            else:
                sku = None

        if barcode is not None:
            barcode = barcode.strip()

            if barcode:
                statement = select(
                    ProductVariant
                ).where(
                    ProductVariant.barcode == barcode
                )

                existing = self.session.scalar(
                    statement
                )

                if existing is not None:
                    raise ValueError(
                        "A variant with this barcode already exists."
                    )
            else:
                barcode = None

        variant = ProductVariant(
            product_id=product_id,
            variant_name=(
                variant_name.strip()
                if variant_name
                else None
            ),
            size=(
                size.strip()
                if size
                else None
            ),
            unit=(
                unit.strip()
                if unit
                else None
            ),
            sku=sku,
            barcode=barcode,
            cost_price=cost_price,
            selling_price=selling_price,
            reorder_level=reorder_level,
            is_active=True,
        )

        self.session.add(variant)
        self.session.flush()

        return variant

    def get_variant_by_id(
        self,
        variant_id: int,
    ) -> ProductVariant | None:
        return self.session.get(
            ProductVariant,
            variant_id,
        )

    def get_variant(
        self,
        variant_id: int,
    ) -> ProductVariant | None:
        return self.get_variant_by_id(
            variant_id
        )

    def get_variant_by_sku(
        self,
        sku: str,
    ) -> ProductVariant | None:
        sku = sku.strip()

        statement = select(ProductVariant).where(
            ProductVariant.sku == sku
        )

        return self.session.scalar(statement)

    def get_variant_by_barcode(
        self,
        barcode: str,
    ) -> ProductVariant | None:
        barcode = barcode.strip()

        statement = select(ProductVariant).where(
            ProductVariant.barcode == barcode
        )

        return self.session.scalar(statement)

    def list_variants(
        self,
        product_id: int | None = None,
        active_only: bool = True,
    ) -> list[ProductVariant]:
        statement = select(ProductVariant).order_by(
        ProductVariant.id
            )

        if product_id is not None:
            statement = statement.where(
            ProductVariant.product_id == product_id
            )

        if active_only:
            statement = statement.where(
            ProductVariant.is_active.is_(True)
             )

        return list(
            self.session.scalars(
            statement
             ).all()
    )

    def update_variant(
        self,
        variant_id: int,
        variant_name: str | None = None,
        size: str | None = None,
        unit: str | None = None,
        sku: str | None = None,
        barcode: str | None = None,
        cost_price: Decimal | None = None,
        selling_price: Decimal | None = None,
        reorder_level: int | None = None,
    ) -> ProductVariant:
        variant = self.get_variant_by_id(
            variant_id
        )

        if variant is None:
            raise ValueError(
                "Product variant not found."
            )

        if cost_price is not None:
            if cost_price < 0:
                raise ValueError(
                    "Cost price cannot be negative."
                )

            variant.cost_price = cost_price

        if selling_price is not None:
            if selling_price < 0:
                raise ValueError(
                    "Selling price cannot be negative."
                )

            variant.selling_price = selling_price

        if reorder_level is not None:
            if reorder_level < 0:
                raise ValueError(
                    "Reorder level cannot be negative."
                )

            variant.reorder_level = reorder_level

        if variant_name is not None:
            variant.variant_name = (
                variant_name.strip()
            )

        if size is not None:
            variant.size = size.strip()

        if unit is not None:
            variant.unit = unit.strip()

        if sku is not None:
            sku = sku.strip()

            if sku != variant.sku:
                if sku:
                    statement = select(
                        ProductVariant
                    ).where(
                        ProductVariant.sku == sku,
                        ProductVariant.id
                        != variant.id,
                    )

                    existing = self.session.scalar(
                        statement
                    )

                    if existing is not None:
                        raise ValueError(
                            "A variant with this SKU already exists."
                        )

                    variant.sku = sku
                else:
                    variant.sku = None

        if barcode is not None:
            barcode = barcode.strip()

            if barcode != variant.barcode:
                if barcode:
                    statement = select(
                        ProductVariant
                    ).where(
                        ProductVariant.barcode == barcode,
                        ProductVariant.id
                        != variant.id,
                    )

                    existing = self.session.scalar(
                        statement
                    )

                    if existing is not None:
                        raise ValueError(
                            "A variant with this barcode already exists."
                        )

                    variant.barcode = barcode
                else:
                    variant.barcode = None

        self.session.flush()

        return variant

    def deactivate_variant(
        self,
        variant_id: int,
    ) -> ProductVariant:
        variant = self.get_variant_by_id(
            variant_id
        )

        if variant is None:
            raise ValueError(
                "Product variant not found."
            )

        variant.is_active = False

        self.session.flush()

        return variant

    def activate_variant(
        self,
        variant_id: int,
    ) -> ProductVariant:
        variant = self.get_variant_by_id(
            variant_id
        )

        if variant is None:
            raise ValueError(
                "Product variant not found."
            )

        variant.is_active = True

        self.session.flush()

        return variant