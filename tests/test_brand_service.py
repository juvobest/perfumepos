from app.database.connection import SessionLocal
from app.services.brand_service import BrandService


def test_create_and_get_brand():
    with SessionLocal() as session:
        service = BrandService(session)

        brand = service.create_brand(
            "Test Brand Service"
        )

        assert brand.id is not None
        assert brand.name == "Test Brand Service"

        fetched = service.get_brand(brand.id)

        assert fetched is not None
        assert fetched.name == "Test Brand Service"


def test_duplicate_brand_is_rejected():
    with SessionLocal() as session:
        service = BrandService(session)

        service.create_brand(
            "Duplicate Brand Test"
        )

        try:
            service.create_brand(
                "Duplicate Brand Test"
            )
            assert False, "Expected duplicate brand error."

        except ValueError as error:
            assert str(error) == (
                "A brand with this name already exists."
            )


def test_deactivate_brand():
    with SessionLocal() as session:
        service = BrandService(session)

        brand = service.create_brand(
            "Brand To Deactivate"
        )

        service.deactivate_brand(brand.id)

        assert brand.is_active is False