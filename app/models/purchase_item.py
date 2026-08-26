from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    purchase_id: Mapped[int] = mapped_column(
        ForeignKey("purchases.id"),
        nullable=False,
    )

    product_variant_id: Mapped[int] = mapped_column(
        ForeignKey("product_variants.id"),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        nullable=False,
    )

    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
    )

    # Cost price of the product before this purchase
    # was received. Used when reversing a purchase.
    previous_cost_price: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        nullable=True,
    )

    purchase = relationship(
        "Purchase",
        back_populates="items",
    )

    product_variant = relationship(
        "ProductVariant",
    )