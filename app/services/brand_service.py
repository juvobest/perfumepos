from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.brand import Brand


class BrandService:
    def __init__(self, session: Session):
        self.session = session

    def create_brand(
        self,
        name: str,
        description: str | None = None,
    ) -> Brand:
        name = name.strip()

        if not name:
            raise ValueError("Brand name is required.")

        existing = self.session.scalar(
            select(Brand).where(Brand.name == name)
        )

        if existing:
            raise ValueError(
                "A brand with this name already exists."
            )

        brand = Brand(
            name=name,
            description=description.strip() if description else None,
        )

        self.session.add(brand)
        self.session.flush()

        return brand

    def get_brand(
        self,
        brand_id: int,
    ) -> Brand | None:
        return self.session.get(Brand, brand_id)

    def list_brands(
        self,
        active_only: bool = True,
    ) -> list[Brand]:
        statement = select(Brand).order_by(Brand.name)

        if active_only:
            statement = statement.where(
                Brand.is_active.is_(True)
            )

        return list(self.session.scalars(statement).all())

    def update_brand(
        self,
        brand_id: int,
        name: str | None = None,
        description: str | None = None,
    ) -> Brand:
        brand = self.session.get(Brand, brand_id)

        if brand is None:
            raise ValueError("Brand not found.")

        if name is not None:
            name = name.strip()

            if not name:
                raise ValueError("Brand name is required.")

            existing = self.session.scalar(
                select(Brand).where(
                    Brand.name == name,
                    Brand.id != brand_id,
                )
            )

            if existing:
                raise ValueError(
                    "A brand with this name already exists."
                )

            brand.name = name

        if description is not None:
            brand.description = (
                description.strip() or None
            )

        self.session.flush()

        return brand

    def deactivate_brand(
        self,
        brand_id: int,
    ) -> Brand:
        brand = self.session.get(Brand, brand_id)

        if brand is None:
            raise ValueError("Brand not found.")

        brand.is_active = False

        self.session.flush()

        return brand