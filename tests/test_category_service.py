from app.database.connection import SessionLocal
from app.services.category_service import CategoryService


def test_create_and_get_category():
    with SessionLocal() as session:
        service = CategoryService(session)

        category = service.create_category(
            "Test Category Service"
        )

        assert category.id is not None
        assert category.name == "Test Category Service"

        fetched = service.get_category(category.id)

        assert fetched is not None
        assert fetched.name == "Test Category Service"


def test_duplicate_category_is_rejected():
    with SessionLocal() as session:
        service = CategoryService(session)

        service.create_category(
            "Duplicate Category Test"
        )

        try:
            service.create_category(
                "Duplicate Category Test"
            )
            assert False, "Expected duplicate category error."

        except ValueError as error:
            assert str(error) == (
                "A category with this name already exists."
            )


def test_deactivate_category():
    with SessionLocal() as session:
        service = CategoryService(session)

        category = service.create_category(
            "Category To Deactivate"
        )

        service.deactivate_category(category.id)

        assert category.is_active is False