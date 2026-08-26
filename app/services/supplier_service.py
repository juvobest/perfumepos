from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.supplier import Supplier


class SupplierService:
    def __init__(self, session: Session):
        self.session = session

    def create_supplier(
        self,
        name: str,
        contact_person: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        address: str | None = None,
        notes: str | None = None,
    ) -> Supplier:
        name = name.strip()

        if not name:
            raise ValueError(
                "Supplier name cannot be empty."
            )

        existing = self.get_by_name(name)

        if existing is not None:
            raise ValueError(
                "A supplier with this name already exists."
            )

        supplier = Supplier(
            name=name,
            contact_person=(
                contact_person.strip()
                if contact_person
                else None
            ),
            phone=(
                phone.strip()
                if phone
                else None
            ),
            email=(
                email.strip()
                if email
                else None
            ),
            address=(
                address.strip()
                if address
                else None
            ),
            notes=(
                notes.strip()
                if notes
                else None
            ),
        )

        self.session.add(supplier)
        self.session.flush()

        return supplier

    def get_by_id(
        self,
        supplier_id: int,
    ) -> Supplier | None:
        return self.session.get(
            Supplier,
            supplier_id,
        )

    def get_by_name(
        self,
        name: str,
    ) -> Supplier | None:
        name = name.strip()

        statement = select(Supplier).where(
            Supplier.name == name
        )

        return self.session.scalar(statement)

    def list_suppliers(
        self,
        include_inactive: bool = False,
    ) -> list[Supplier]:
        statement = select(Supplier).order_by(
            Supplier.name
        )

        if not include_inactive:
            statement = statement.where(
                Supplier.is_active.is_(True)
            )

        return list(
            self.session.scalars(statement).all()
        )

    def update_supplier(
        self,
        supplier_id: int,
        name: str | None = None,
        contact_person: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        address: str | None = None,
        notes: str | None = None,
    ) -> Supplier:
        supplier = self.get_by_id(
            supplier_id
        )

        if supplier is None:
            raise ValueError(
                "Supplier not found."
            )

        if name is not None:
            name = name.strip()

            if not name:
                raise ValueError(
                    "Supplier name cannot be empty."
                )

            existing = self.get_by_name(name)

            if (
                existing is not None
                and existing.id != supplier.id
            ):
                raise ValueError(
                    "A supplier with this name already exists."
                )

            supplier.name = name

        if contact_person is not None:
            supplier.contact_person = (
                contact_person.strip()
            )

        if phone is not None:
            supplier.phone = phone.strip()

        if email is not None:
            supplier.email = email.strip()

        if address is not None:
            supplier.address = address.strip()

        if notes is not None:
            supplier.notes = notes.strip()

        self.session.flush()

        return supplier

    def deactivate_supplier(
        self,
        supplier_id: int,
    ) -> Supplier:
        supplier = self.get_by_id(
            supplier_id
        )

        if supplier is None:
            raise ValueError(
                "Supplier not found."
            )

        supplier.is_active = False

        self.session.flush()

        return supplier

    def activate_supplier(
        self,
        supplier_id: int,
    ) -> Supplier:
        supplier = self.get_by_id(
            supplier_id
        )

        if supplier is None:
            raise ValueError(
                "Supplier not found."
            )

        supplier.is_active = True

        self.session.flush()

        return supplier