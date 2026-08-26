import pytest

from app.database.connection import SessionLocal
from app.services.supplier_service import SupplierService


def test_create_supplier():
    with SessionLocal() as session:
        service = SupplierService(session)

        supplier = service.create_supplier(
            name="ABC Fragrances",
            contact_person="John Doe",
            phone="08012345678",
            email="abc@example.com",
            address="Lagos",
            notes="Main fragrance supplier",
        )

        assert supplier.id is not None
        assert supplier.name == "ABC Fragrances"
        assert supplier.contact_person == "John Doe"
        assert supplier.phone == "08012345678"
        assert supplier.email == "abc@example.com"
        assert supplier.address == "Lagos"
        assert supplier.notes == (
            "Main fragrance supplier"
        )
        assert supplier.is_active is True


def test_supplier_name_is_trimmed():
    with SessionLocal() as session:
        service = SupplierService(session)

        supplier = service.create_supplier(
            name="   XYZ Cosmetics   "
        )

        assert supplier.name == "XYZ Cosmetics"


def test_empty_supplier_name_is_rejected():
    with SessionLocal() as session:
        service = SupplierService(session)

        with pytest.raises(
            ValueError,
            match="Supplier name cannot be empty.",
        ):
            service.create_supplier("   ")


def test_duplicate_supplier_is_rejected():
    with SessionLocal() as session:
        service = SupplierService(session)

        service.create_supplier(
            name="Unique Supplier"
        )

        with pytest.raises(
            ValueError,
            match="A supplier with this name already exists.",
        ):
            service.create_supplier(
                name="Unique Supplier"
            )


def test_get_supplier_by_id():
    with SessionLocal() as session:
        service = SupplierService(session)

        created = service.create_supplier(
            name="Find By ID"
        )

        supplier = service.get_by_id(
            created.id
        )

        assert supplier is not None
        assert supplier.id == created.id
        assert supplier.name == "Find By ID"


def test_get_supplier_by_name():
    with SessionLocal() as session:
        service = SupplierService(session)

        service.create_supplier(
            name="Find By Name"
        )

        supplier = service.get_by_name(
            "Find By Name"
        )

        assert supplier is not None
        assert supplier.name == "Find By Name"


def test_list_active_suppliers():
    with SessionLocal() as session:
        service = SupplierService(session)

        active = service.create_supplier(
            name="Active Supplier"
        )

        inactive = service.create_supplier(
            name="Inactive Supplier"
        )

        service.deactivate_supplier(
            inactive.id
        )

        suppliers = service.list_suppliers()

        ids = [supplier.id for supplier in suppliers]

        assert active.id in ids
        assert inactive.id not in ids


def test_list_suppliers_can_include_inactive():
    with SessionLocal() as session:
        service = SupplierService(session)

        active = service.create_supplier(
            name="Active Supplier 2"
        )

        inactive = service.create_supplier(
            name="Inactive Supplier 2"
        )

        service.deactivate_supplier(
            inactive.id
        )

        suppliers = service.list_suppliers(
            include_inactive=True
        )

        ids = [supplier.id for supplier in suppliers]

        assert active.id in ids
        assert inactive.id in ids


def test_update_supplier():
    with SessionLocal() as session:
        service = SupplierService(session)

        supplier = service.create_supplier(
            name="Original Supplier",
            phone="08000000000",
        )

        updated = service.update_supplier(
            supplier.id,
            name="Updated Supplier",
            phone="08111111111",
            email="updated@example.com",
        )

        assert updated.name == "Updated Supplier"
        assert updated.phone == "08111111111"
        assert updated.email == (
            "updated@example.com"
        )


def test_update_supplier_rejects_duplicate_name():
    with SessionLocal() as session:
        service = SupplierService(session)

        first = service.create_supplier(
            name="First Supplier"
        )

        second = service.create_supplier(
            name="Second Supplier"
        )

        with pytest.raises(
            ValueError,
            match="A supplier with this name already exists.",
        ):
            service.update_supplier(
                second.id,
                name=first.name,
            )


def test_deactivate_supplier():
    with SessionLocal() as session:
        service = SupplierService(session)

        supplier = service.create_supplier(
            name="Deactivate Supplier"
        )

        service.deactivate_supplier(
            supplier.id
        )

        assert supplier.is_active is False


def test_activate_supplier():
    with SessionLocal() as session:
        service = SupplierService(session)

        supplier = service.create_supplier(
            name="Reactivate Supplier"
        )

        service.deactivate_supplier(
            supplier.id
        )

        assert supplier.is_active is False

        service.activate_supplier(
            supplier.id
        )

        assert supplier.is_active is True


def test_update_missing_supplier_is_rejected():
    with SessionLocal() as session:
        service = SupplierService(session)

        with pytest.raises(
            ValueError,
            match="Supplier not found.",
        ):
            service.update_supplier(
                999999,
                name="Does Not Exist",
            )