from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
    )

    variant_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    size: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    unit: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    sku: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
    )

    barcode: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
    )

    cost_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    selling_price: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    reorder_level: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    product = relationship(
        "Product",
        back_populates="variants",
    )

    inventory = relationship(
        "Inventory",
        back_populates="product_variant",
        uselist=False,
    )