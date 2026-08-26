from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category


class CategoryService:
    def __init__(self, session: Session):
        self.session = session

    def create_category(
        self,
        name: str,
        description: str | None = None,
    ) -> Category:
        name = name.strip()

        if not name:
            raise ValueError("Category name is required.")

        existing = self.session.scalar(
            select(Category).where(Category.name == name)
        )

        if existing:
            raise ValueError("A category with this name already exists.")

        category = Category(
            name=name,
            description=description.strip() if description else None,
        )

        self.session.add(category)
        self.session.flush()

        return category

    def get_category(self, category_id: int) -> Category | None:
        return self.session.get(Category, category_id)

    def list_categories(
        self,
        active_only: bool = True,
    ) -> list[Category]:
        statement = select(Category).order_by(Category.name)

        if active_only:
            statement = statement.where(Category.is_active.is_(True))

        return list(self.session.scalars(statement).all())

    def update_category(
        self,
        category_id: int,
        name: str | None = None,
        description: str | None = None,
    ) -> Category:
        category = self.session.get(Category, category_id)

        if category is None:
            raise ValueError("Category not found.")

        if name is not None:
            name = name.strip()

            if not name:
                raise ValueError("Category name is required.")

            existing = self.session.scalar(
                select(Category).where(
                    Category.name == name,
                    Category.id != category_id,
                )
            )

            if existing:
                raise ValueError(
                    "A category with this name already exists."
                )

            category.name = name

        if description is not None:
            category.description = (
                description.strip() or None
            )

        self.session.flush()

        return category

    def deactivate_category(
        self,
        category_id: int,
    ) -> Category:
        category = self.session.get(Category, category_id)

        if category is None:
            raise ValueError("Category not found.")

        category.is_active = False

        self.session.flush()

        return category