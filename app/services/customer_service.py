from sqlalchemy.orm import Session

from app.models.customer import Customer


class CustomerService:
    def __init__(self, session: Session):
        self.session = session

    def create_customer(
        self,
        name: str,
        phone: str | None = None,
        email: str | None = None,
        address: str | None = None,
        notes: str | None = None,
    ) -> Customer:
        if not name or not name.strip():
            raise ValueError(
                "Customer name cannot be empty."
            )

        customer = Customer(
            name=name.strip(),
            phone=phone.strip() if phone else None,
            email=email.strip() if email else None,
            address=address.strip() if address else None,
            notes=notes.strip() if notes else None,
        )

        self.session.add(customer)
        self.session.flush()

        return customer

    def get_customer(
        self,
        customer_id: int,
    ) -> Customer | None:
        return (
            self.session.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )

    def list_customers(self) -> list[Customer]:
        return (
            self.session.query(Customer)
            .filter(Customer.is_active.is_(True))
            .order_by(Customer.name.asc())
            .all()
        )

    def search_customers(
        self,
        query: str,
    ) -> list[Customer]:
        search_term = query.strip()

        if not search_term:
            return self.list_customers()

        pattern = f"%{search_term}%"

        return (
            self.session.query(Customer)
            .filter(
                Customer.is_active.is_(True),
                (
                    Customer.name.ilike(pattern)
                    | Customer.phone.ilike(pattern)
                    | Customer.email.ilike(pattern)
                ),
            )
            .order_by(Customer.name.asc())
            .all()
        )

    def update_customer(
        self,
        customer_id: int,
        name: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        address: str | None = None,
        notes: str | None = None,
    ) -> Customer:
        customer = self.get_customer(customer_id)

        if customer is None:
            raise ValueError(
                "Customer not found."
            )

        if name is not None:
            if not name.strip():
                raise ValueError(
                    "Customer name cannot be empty."
                )

            customer.name = name.strip()

        if phone is not None:
            customer.phone = (
                phone.strip() or None
            )

        if email is not None:
            customer.email = (
                email.strip() or None
            )

        if address is not None:
            customer.address = (
                address.strip() or None
            )

        if notes is not None:
            customer.notes = (
                notes.strip() or None
            )

        self.session.flush()

        return customer

    def deactivate_customer(
        self,
        customer_id: int,
    ) -> Customer:
        customer = self.get_customer(customer_id)

        if customer is None:
            raise ValueError(
                "Customer not found."
            )

        customer.is_active = False

        self.session.flush()

        return customer