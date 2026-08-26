from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.config import BUSINESS_NAME
from app.database.connection import SessionLocal
from app.services.permission_service import user_has_permission

from app.ui.customers.customer_window import CustomerWindow
from app.ui.expenses.expense_window import ExpenseWindow
from app.ui.inventory.inventory_window import InventoryWindow
from app.ui.products.product_window import ProductWindow
from app.ui.purchasing.purchasing_window import PurchasingWindow
from app.ui.reports.report_window import ReportWindow
from app.ui.roles.role_window import RoleWindow
from app.ui.sales.sale_window import SaleWindow
from app.ui.suppliers.supplier_window import SupplierWindow
from app.ui.users.user_window import UserWindow
from app.ui.backup.backup_window import BackupWindow


PROJECT_ROOT = Path(__file__).resolve().parents[3]
LOGO_PATH = PROJECT_ROOT / "assets" / "logo.png"


class MainWindow(QMainWindow):

    def __init__(self, user):
        super().__init__()

        self.user = user

        # ------------------------------------------------------
        # WINDOW REFERENCES
        # ------------------------------------------------------

        self.expense_window = None
        self.sale_window = None
        self.product_window = None
        self.purchasing_window = None
        self.user_window = None
        self.customer_window = None
        self.supplier_window = None
        self.role_window = None
        self.inventory_window = None
        self.report_window = None
        self.backup_window = None

        self.setWindowTitle(
            f"{BUSINESS_NAME} - Point of Sale"
        )

        self.setMinimumSize(
            1100,
            700,
        )

        self.build_ui()

    # ==========================================================
    # PERMISSION CHECK
    # ==========================================================

    def has_permission(
        self,
        permission_name: str,
    ) -> bool:

        with SessionLocal() as session:
            return user_has_permission(
                session,
                self.user,
                permission_name,
            )

    # ==========================================================
    # UI
    # ==========================================================

    def build_ui(self):

        central_widget = QWidget()

        main_layout = QHBoxLayout(
            central_widget
        )

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        main_layout.setSpacing(
            0
        )

        sidebar = self.build_sidebar()
        content = self.build_content()

        main_layout.addWidget(
            sidebar
        )

        main_layout.addWidget(
            content
        )

        self.setCentralWidget(
            central_widget
        )

    # ==========================================================
    # SIDEBAR
    # ==========================================================

    def build_sidebar(self):

        sidebar = QFrame()

        sidebar.setFixedWidth(
            280
        )

        sidebar.setStyleSheet(
            """
            QFrame {
                background-color: #20232a;
            }

            QLabel {
                color: white;
            }

            QListWidget {
                background-color: #20232a;
                color: white;
                border: none;
                font-size: 14px;
            }

            QListWidget::item {
                padding: 14px;
            }

            QListWidget::item:selected {
                background-color: #3a3f4b;
            }

            QPushButton {
                background-color: #c0392b;
                color: white;
                border: none;
                padding: 12px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #e74c3c;
            }
            """
        )

        layout = QVBoxLayout(
            sidebar
        )

        layout.setContentsMargins(
            15,
            20,
            15,
            20,
        )

        # ======================================================
        # BRANDING
        # ======================================================

        branding_container = QVBoxLayout()

        branding_container.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        branding_container.setSpacing(
            10
        )

        logo_frame = QFrame()

        logo_frame.setFixedHeight(
            125
        )

        logo_frame.setStyleSheet(
            """
            QFrame {
                background-color: #ffffff;
                border-radius: 10px;
            }
            """
        )

        logo_layout = QVBoxLayout(
            logo_frame
        )

        logo_layout.setContentsMargins(
            15,
            10,
            15,
            10,
        )

        logo_layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        logo_label = QLabel()

        logo_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        if LOGO_PATH.exists():

            pixmap = QPixmap(
                str(LOGO_PATH)
            )

            if not pixmap.isNull():

                pixmap = pixmap.scaled(
                    105,
                    105,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

                logo_label.setPixmap(
                    pixmap
                )

        logo_layout.addWidget(
            logo_label
        )

        branding_container.addWidget(
            logo_frame
        )

        title = QLabel(
            BUSINESS_NAME
        )

        title.setWordWrap(
            True
        )

        title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title.setStyleSheet(
            """
            QLabel {
                color: white;
                font-size: 15px;
                font-weight: bold;
                padding: 2px 5px;
            }
            """
        )

        branding_container.addWidget(
            title
        )

        layout.addLayout(
            branding_container
        )

        # ======================================================
        # SEPARATOR
        # ======================================================

        separator = QFrame()

        separator.setFrameShape(
            QFrame.Shape.HLine
        )

        separator.setStyleSheet(
            """
            QFrame {
                color: #3a3f4b;
                background-color: #3a3f4b;
                max-height: 1px;
            }
            """
        )

        layout.addSpacing(
            12
        )

        layout.addWidget(
            separator
        )

        layout.addSpacing(
            12
        )

        # ======================================================
        # NAVIGATION
        # ======================================================

        self.navigation = QListWidget()

        menu_items = [
            (
                "Dashboard",
                None,
                0,
            ),

            (
                "Products",
                "products.view",
                1,
            ),

            (
                "Inventory",
                "inventory.view",
                2,
            ),

            (
                "Purchasing",
                "purchasing.view",
                3,
            ),

            (
                "Suppliers",
                "suppliers.view",
                4,
            ),

            (
                "Customers",
                "customers.view",
                5,
            ),

            (
                "Sales / POS",
                "sales.view",
                6,
            ),

            (
                "Expenses",
                None,
                7,
            ),

            (
                "Reports",
                None,
                8,
            ),

            (
                "Users",
                "users.view",
                9,
            ),

            (
                "Roles",
                "roles.view",
                10,
            ),

            (
                "Backup & Restore",
                "settings.edit",
                11,
            ),
        ]

        for name, permission, page_index in menu_items:

            if permission is not None:

                if not self.has_permission(
                    permission
                ):
                    continue

            item = QListWidgetItem(
                name
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                page_index,
            )

            self.navigation.addItem(
                item
            )

        self.navigation.currentRowChanged.connect(
            self.change_page
        )

        layout.addWidget(
            self.navigation
        )

        # ======================================================
        # USER
        # ======================================================

        user_label = QLabel(
            f"Logged in as:\n{self.user.full_name}"
        )

        user_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        user_label.setWordWrap(
            True
        )

        user_label.setStyleSheet(
            """
            QLabel {
                padding: 10px;
                font-size: 12px;
            }
            """
        )

        layout.addWidget(
            user_label
        )

        # ======================================================
        # LOGOUT
        # ======================================================

        self.logout_button = QPushButton(
            "LOGOUT"
        )

        self.logout_button.setMinimumHeight(
            40
        )

        self.logout_button.clicked.connect(
            self.handle_logout
        )

        layout.addWidget(
            self.logout_button
        )

        return sidebar

    # ==========================================================
    # CONTENT
    # ==========================================================

    def build_content(self):

        container = QWidget()

        layout = QVBoxLayout(
            container
        )

        layout.setContentsMargins(
            30,
            25,
            30,
            25,
        )

        header = QLabel(
            "Point of Sale Dashboard"
        )

        header.setStyleSheet(
            """
            QLabel {
                font-size: 26px;
                font-weight: bold;
            }
            """
        )

        layout.addWidget(
            header
        )

        self.pages = QStackedWidget()

        # ======================================================
        # 0 - DASHBOARD
        # ======================================================

        self.pages.addWidget(
            self.create_page(
                "Dashboard",
                "Welcome to your perfume POS.",
            )
        )

        # ======================================================
        # 1 - PRODUCTS
        # ======================================================

        self.pages.addWidget(
            self.create_page(
                "Products",
                "Product management will open here.",
            )
        )

        # ======================================================
        # 2 - INVENTORY
        # ======================================================

        self.pages.addWidget(
            self.create_page(
                "Inventory",
                "Inventory management.",
            )
        )

        # ======================================================
        # 3 - PURCHASING
        # ======================================================

        self.pages.addWidget(
            self.create_page(
                "Purchasing",
                "Purchasing management will open here.",
            )
        )

        # ======================================================
        # 4 - SUPPLIERS
        # ======================================================

        self.pages.addWidget(
            self.create_page(
                "Suppliers",
                "Supplier management will open here.",
            )
        )

        # ======================================================
        # 5 - CUSTOMERS
        # ======================================================

        self.pages.addWidget(
            self.create_page(
                "Customers",
                "Customer management will open here.",
            )
        )

        # ======================================================
        # 6 - SALES
        # ======================================================

        self.pages.addWidget(
            self.create_page(
                "Sales / POS",
                "Point of sale screen will open here.",
            )
        )

        # ======================================================
        # 7 - EXPENSES
        # ======================================================

        self.pages.addWidget(
            self.create_expenses_page()
        )

        # ======================================================
        # 8 - REPORTS
        # ======================================================

        self.pages.addWidget(
            self.create_page(
                "Reports",
                "Reports management.",
            )
        )

        # ======================================================
        # 9 - USERS
        # ======================================================

        self.pages.addWidget(
            self.create_page(
                "Users",
                "User management will open here.",
            )
        )

        # ======================================================
        # 10 - ROLES
        # ======================================================

        self.pages.addWidget(
            self.create_page(
                "Roles",
                "Role management will open here.",
            )
        )

        layout.addWidget(
            self.pages
        )

        return container

    # ==========================================================
    # EXPENSES
    # ==========================================================

    def create_expenses_page(self):

        page = QWidget()

        layout = QVBoxLayout(
            page
        )

        title_label = QLabel(
            "Expenses"
        )

        title_label.setStyleSheet(
            """
            QLabel {
                font-size: 22px;
                font-weight: bold;
            }
            """
        )

        description_label = QLabel(
            "Record and manage business expenses."
        )

        description_label.setStyleSheet(
            """
            QLabel {
                font-size: 15px;
            }
            """
        )

        layout.addWidget(
            title_label
        )

        layout.addSpacing(
            10
        )

        layout.addWidget(
            description_label
        )

        open_button = QPushButton(
            "OPEN EXPENSE MANAGEMENT"
        )

        open_button.setMinimumHeight(
            45
        )

        open_button.clicked.connect(
            self.open_expense_window
        )

        layout.addSpacing(
            20
        )

        layout.addWidget(
            open_button
        )

        layout.addStretch()

        return page

    # ==========================================================
    # GENERIC PAGE
    # ==========================================================

    def create_page(
        self,
        title: str,
        description: str,
    ):

        page = QWidget()

        layout = QVBoxLayout(
            page
        )

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet(
            """
            QLabel {
                font-size: 22px;
                font-weight: bold;
            }
            """
        )

        description_label = QLabel(
            description
        )

        description_label.setStyleSheet(
            """
            QLabel {
                font-size: 15px;
            }
            """
        )

        layout.addWidget(
            title_label
        )

        layout.addSpacing(
            10
        )

        layout.addWidget(
            description_label
        )

        layout.addStretch()

        return page

    # ==========================================================
    # NAVIGATION
    # ==========================================================

    def change_page(
        self,
        row: int,
    ):

        if row < 0:
            return

        item = self.navigation.item(
            row
        )

        if item is None:
            return

        index = item.data(
            Qt.ItemDataRole.UserRole
        )

        # ------------------------------------------------------
        # PRODUCTS
        # ------------------------------------------------------

        if index == 1:

            if not self.has_permission(
                "products.view"
            ):
                return

            self.open_product_window()
            return

        # ------------------------------------------------------
        # INVENTORY
        # ------------------------------------------------------

        if index == 2:

            if not self.has_permission(
                "inventory.view"
            ):
                return

            self.open_inventory_window()
            return

        # ------------------------------------------------------
        # PURCHASING
        # ------------------------------------------------------

        if index == 3:

            if not self.has_permission(
                "purchasing.view"
            ):
                return

            self.open_purchasing_window()
            return

        # ------------------------------------------------------
        # SUPPLIERS
        # ------------------------------------------------------

        if index == 4:

            if not self.has_permission(
                "suppliers.view"
            ):
                return

            self.open_supplier_window()
            return

        # ------------------------------------------------------
        # CUSTOMERS
        # ------------------------------------------------------

        if index == 5:

            if not self.has_permission(
                "customers.view"
            ):
                return

            self.open_customer_window()
            return

        # ------------------------------------------------------
        # SALES
        # ------------------------------------------------------

        if index == 6:

            if not self.has_permission(
                "sales.view"
            ):
                return

            self.open_sales_window()
            return

        # ------------------------------------------------------
        # EXPENSES
        # ------------------------------------------------------

        if index == 7:

            if not self.has_permission(
                "reports.view_profit"
            ):
                return

            self.open_expense_window()
            return

        # ------------------------------------------------------
        # REPORTS
        # ------------------------------------------------------

        if index == 8:

            if not (
                self.has_permission(
                    "reports.view_sales"
                )
                or self.has_permission(
                    "reports.view_inventory"
                )
                or self.has_permission(
                    "reports.view_profit"
                )
            ):
                return

            self.open_report_window()
            return

        # ------------------------------------------------------
        # USERS
        # ------------------------------------------------------

        if index == 9:

            if not self.has_permission(
                "users.view"
            ):
                return

            self.open_user_window()
            return

        # ------------------------------------------------------
        # ROLES
        # ------------------------------------------------------

        if index == 10:

            if not self.has_permission(
                "roles.view"
            ):
                return

            self.open_role_window()
            return

        # ------------------------------------------------------
        # BACKUP & RESTORE
        # ------------------------------------------------------

        if index == 11:

            if not self.has_permission(
                "settings.edit"
            ):
                return

            self.open_backup_window()
            return

        # ------------------------------------------------------
        # DASHBOARD
        # ------------------------------------------------------

        self.pages.setCurrentIndex(
            index
        )

    # ==========================================================
    # PRODUCT WINDOW
    # ==========================================================

    def open_product_window(self):

        if not self.has_permission(
            "products.view"
        ):
            return

        if self.product_window is None:

            self.product_window = ProductWindow(
                self.user
            )

        self.product_window.show()
        self.product_window.raise_()
        self.product_window.activateWindow()

    # ==========================================================
    # INVENTORY WINDOW
    # ==========================================================

    def open_inventory_window(self):

        if not self.has_permission(
            "inventory.view"
        ):
            return

        if self.inventory_window is None:

            self.inventory_window = InventoryWindow(
                self.user
            )

        self.inventory_window.show()
        self.inventory_window.raise_()
        self.inventory_window.activateWindow()

    # ==========================================================
    # PURCHASING WINDOW
    # ==========================================================

    def open_purchasing_window(self):

        if not self.has_permission(
            "purchasing.view"
        ):
            return

        if self.purchasing_window is None:

            self.purchasing_window = PurchasingWindow(
                self.user
            )

        self.purchasing_window.show()
        self.purchasing_window.raise_()
        self.purchasing_window.activateWindow()

    # ==========================================================
    # SALES WINDOW
    # ==========================================================

    def open_sales_window(self):

        if not self.has_permission(
            "sales.view"
        ):
            return

        if self.sale_window is None:

            self.sale_window = SaleWindow(
                self.user
            )

        self.sale_window.show()
        self.sale_window.raise_()
        self.sale_window.activateWindow()

    # ==========================================================
    # EXPENSE WINDOW
    # ==========================================================

    def open_expense_window(self):

        if not self.has_permission(
            "reports.view_profit"
        ):
            return

        if self.expense_window is None:

            self.expense_window = ExpenseWindow(
                self.user
            )

        self.expense_window.show()
        self.expense_window.raise_()
        self.expense_window.activateWindow()

    # ==========================================================
    # REPORT WINDOW
    # ==========================================================

    def open_report_window(self):

        if not (
            self.has_permission(
                "reports.view_sales"
            )
            or self.has_permission(
                "reports.view_inventory"
            )
            or self.has_permission(
                "reports.view_profit"
            )
        ):
            return

        if self.report_window is None:

            self.report_window = ReportWindow(
                self.user
            )

        self.report_window.show()
        self.report_window.raise_()
        self.report_window.activateWindow()

    # ==========================================================
    # USER WINDOW
    # ==========================================================

    def open_user_window(self):

        if not self.has_permission(
            "users.view"
        ):
            return

        if self.user_window is None:

            self.user_window = UserWindow(
                self.user
            )

        self.user_window.show()
        self.user_window.raise_()
        self.user_window.activateWindow()

    # ==========================================================
    # CUSTOMER WINDOW
    # ==========================================================

    def open_customer_window(self):

        if not self.has_permission(
            "customers.view"
        ):
            return

        if self.customer_window is None:

            self.customer_window = CustomerWindow(
                self.user
            )

        self.customer_window.show()
        self.customer_window.raise_()
        self.customer_window.activateWindow()

    # ==========================================================
    # SUPPLIER WINDOW
    # ==========================================================

    def open_supplier_window(self):

        if not self.has_permission(
            "suppliers.view"
        ):
            return

        if self.supplier_window is None:

            self.supplier_window = SupplierWindow(
                self.user
            )

        self.supplier_window.show()
        self.supplier_window.raise_()
        self.supplier_window.activateWindow()

    # ==========================================================
    # ROLE WINDOW
    # ==========================================================

    def open_role_window(self):

        if not self.has_permission(
            "roles.view"
        ):
            return

        if self.role_window is None:

            self.role_window = RoleWindow(
                self.user
            )

        self.role_window.show()
        self.role_window.raise_()
        self.role_window.activateWindow()

    # ==========================================================
    # BACKUP WINDOW
    # ==========================================================

    def open_backup_window(self):

        if not self.has_permission(
            "settings.edit"
        ):
            return

        if self.backup_window is None:
            self.backup_window = BackupWindow(
                self.user
            )

        self.backup_window.show()
        self.backup_window.raise_()
        self.backup_window.activateWindow()

    # ==========================================================
    # LOGOUT
    # ==========================================================

    def handle_logout(self):
        self.close()