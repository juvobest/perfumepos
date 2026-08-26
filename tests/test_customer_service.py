import pytest

from app.database.connection import SessionLocal
from app.services.customer_service import CustomerService


def test_create_customer():
    with SessionLocal() as session:
        service = CustomerService(session)

        customer = service.create_customer(
            name="Jane Doe",
            phone="08012345678",
            email="jane@example.com",
            address="Lagos",
            notes="Regular customer",
        )

        assert customer.id is not None
        assert customer.name == "Jane Doe"
        assert customer.phone == "08012345678"
        assert customer.email == "jane@example.com"
        assert customer.address == "Lagos"
        assert customer.notes == "Regular customer"
        assert customer.is_active is True


def test_customer_name_is_trimmed():
    with SessionLocal() as session:
        service = CustomerService(session)

        customer = service.create_customer(
            name="   Jane Doe   "
        )

        assert customer.name == "Jane Doe"


def test_empty_customer_name_is_rejected():
    with SessionLocal() as session:
        service = CustomerService(session)

        with pytest.raises(
            ValueError,
            match="Customer name cannot be empty.",
        ):
            service.create_customer("   ")


def test_get_customer():
    with SessionLocal() as session:
        service = CustomerService(session)

        created = service.create_customer(
            name="Find Customer"
        )

        customer = service.get_customer(
            created.id
        )

        assert customer is not None
        assert customer.id == created.id
        assert customer.name == "Find Customer"


def test_list_customers():
    with SessionLocal() as session:
        service = CustomerService(session)

        active = service.create_customer(
            name="Active Customer"
        )

        inactive = service.create_customer(
            name="Inactive Customer"
        )

        service.deactivate_customer(
            inactive.id
        )

        customers = service.list_customers()

        customer_ids = [
            customer.id
            for customer in customers
        ]

        assert active.id in customer_ids
        assert inactive.id not in customer_ids


def test_search_customers_by_name():
    with SessionLocal() as session:
        service = CustomerService(session)

        customer = service.create_customer(
            name="Luxury Customer"
        )

        results = service.search_customers(
            "Luxury"
        )

        assert customer.id in [
            item.id for item in results
        ]


def test_search_customers_by_phone():
    with SessionLocal() as session:
        service = CustomerService(session)

        customer = service.create_customer(
            name="Phone Customer",
            phone="08098765432",
        )

        results = service.search_customers(
            "08098765432"
        )

        assert customer.id in [
            item.id for item in results
        ]


def test_update_customer():
    with SessionLocal() as session:
        service = CustomerService(session)

        customer = service.create_customer(
            name="Original Customer"
        )

        updated = service.update_customer(
            customer.id,
            name="Updated Customer",
            phone="08111111111",
            email="updated@example.com",
        )

        assert updated.name == "Updated Customer"
        assert updated.phone == "08111111111"
        assert updated.email == (
            "updated@example.com"
        )


def test_deactivate_customer():
    with SessionLocal() as session:
        service = CustomerService(session)

        customer = service.create_customer(
            name="Customer To Deactivate"
        )

        service.deactivate_customer(
            customer.id
        )

        assert customer.is_active is False


def test_update_missing_customer_is_rejected():
    with SessionLocal() as session:
        service = CustomerService(session)

        with pytest.raises(
            ValueError,
            match="Customer not found.",
        ):
            service.update_customer(
                999999,
                name="Missing Customer",
            )


def test_deactivate_missing_customer_is_rejected():
    with SessionLocal() as session:
        service = CustomerService(session)

        with pytest.raises(
            ValueError,
            match="Customer not found.",
        ):
            service.deactivate_customer(
                999999
            )