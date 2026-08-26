from app.database.base import Base
from app.database.connection import engine

# Import all models so SQLAlchemy registers every table
from app.models.associations import user_roles, role_permissions
from app.models.brand import Brand
from app.models.business_settings import BusinessSettings
from app.models.category import Category
from app.models.customer import Customer
from app.models.expense import Expense
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement
from app.models.payment import Payment
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.purchase import Purchase
from app.models.purchase_item import PurchaseItem
from app.models.role import Role
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.supplier import Supplier
from app.models.user import User


def init_database() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_database()
    print("Database initialized successfully.")