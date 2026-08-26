from sqlalchemy import select

from app.database.connection import SessionLocal
from app.models.permission import Permission
from app.models.role import Role


PERMISSIONS = [
    # Sales
    ("sales.create", "Create sales transactions"),
    ("sales.view", "View sales transactions"),
    ("sales.reprint_receipt", "Reprint sales receipts"),

    # Products
    ("products.view", "View products"),
    ("products.create", "Create products"),
    ("products.edit", "Edit products"),
    ("products.deactivate", "Deactivate products"),

    # Inventory
    ("inventory.view", "View inventory"),
    ("inventory.receive", "Receive new stock"),
    ("inventory.adjust", "Adjust stock quantities"),

    # Purchasing
    ("purchasing.view", "View purchase transactions"),
    ("purchasing.create", "Create purchase transactions"),
    ("purchasing.edit", "Edit draft purchase transactions"),
    ("purchasing.cancel", "Cancel purchase transactions"),

    # Discounts
    ("discounts.authorize", "Authorize discounts"),

    # Returns
    ("returns.process", "Process refunds and exchanges"),

    # Customers
    ("customers.view", "View customers"),
    ("customers.create", "Create customers"),
    ("customers.edit", "Edit customers"),

    # Reports
    ("reports.view_sales", "View sales reports"),
    ("reports.view_inventory", "View inventory reports"),
    ("reports.view_profit", "View profit reports"),

    # Users
    ("users.view", "View users"),
    ("users.create", "Create users"),
    ("users.edit", "Edit users"),
    ("users.deactivate", "Deactivate users"),

    # Roles and permissions
    ("roles.manage", "Manage roles"),
    ("permissions.manage", "Manage permissions"),

    # Settings
    ("settings.view", "View application settings"),
    ("settings.edit", "Edit application settings"),

    # Suppliers
    ("suppliers.view", "View suppliers"),
    ("suppliers.create", "Create suppliers"),
    ("suppliers.edit", "Edit suppliers"),
]


ROLE_PERMISSIONS = {
    "Admin": [
        permission[0]
        for permission in PERMISSIONS
    ],

    "Manager": [
        # Sales
        "sales.create",
        "sales.view",
        "sales.reprint_receipt",

        # Products
        "products.view",
        "products.create",
        "products.edit",
        "products.deactivate",

        # Inventory
        "inventory.view",
        "inventory.receive",
        "inventory.adjust",

        # Purchasing
        "purchasing.view",
        "purchasing.create",
        "purchasing.edit",
        "purchasing.cancel",

        # Discounts
        "discounts.authorize",

        # Returns
        "returns.process",

        # Customers
        "customers.view",
        "customers.create",
        "customers.edit",

        # Reports
        "reports.view_sales",
        "reports.view_inventory",
        "reports.view_profit",

        # Suppliers
        "suppliers.view",
        "suppliers.create",
        "suppliers.edit",
    ],

    "Inventory Manager": [
        # Products
        "products.view",
        "products.create",
        "products.edit",

        # Inventory
        "inventory.view",
        "inventory.receive",
        "inventory.adjust",

        # Purchasing
        "purchasing.view",
        "purchasing.create",
        "purchasing.edit",
        "purchasing.cancel",

        # Suppliers
        "suppliers.view",
        "suppliers.create",
        "suppliers.edit",

        # Inventory reports
        "reports.view_inventory",
    ],

    "Sales/Cashier": [
        # Sales
        "sales.create",
        "sales.view",
        "sales.reprint_receipt",

        # Products
        "products.view",

        # Inventory
        "inventory.view",

        # Customers
        "customers.view",
        "customers.create",
        "customers.edit",
    ],

    "Store Clerk": [
        # Products
        "products.view",

        # Inventory
        "inventory.view",

        # Purchasing
        "purchasing.view",

        # Suppliers
        "suppliers.view",

        # Customers
        "customers.view",
    ],
}


ROLE_DESCRIPTIONS = {
    "Admin": "Full system administration access",
    "Manager": "Full operational management access",
    "Inventory Manager": "Manages inventory, purchasing and stock receiving",
    "Sales/Cashier": "Handles sales and customer transactions",
    "Store Clerk": "Basic product, inventory and purchasing visibility",
}


def seed_permissions() -> None:
    with SessionLocal() as session:
        for name, description in PERMISSIONS:
            existing = session.scalar(
                select(Permission).where(
                    Permission.name == name
                )
            )

            if existing is None:
                session.add(
                    Permission(
                        name=name,
                        description=description,
                    )
                )

        session.commit()

    print("Permissions seeded successfully.")


def seed_roles() -> None:
    with SessionLocal() as session:
        permissions = {
            permission.name: permission
            for permission in session.query(Permission).all()
        }

        for role_name, permission_names in ROLE_PERMISSIONS.items():
            role = session.scalar(
                select(Role).where(
                    Role.name == role_name
                )
            )

            if role is None:
                role = Role(
                    name=role_name,
                    description=ROLE_DESCRIPTIONS[role_name],
                )

                session.add(role)
                session.flush()

            role.description = ROLE_DESCRIPTIONS[role_name]

            role.permissions = [
                permissions[name]
                for name in permission_names
                if name in permissions
            ]

        session.commit()

    print("Roles seeded successfully.")


if __name__ == "__main__":
    seed_permissions()
    seed_roles()