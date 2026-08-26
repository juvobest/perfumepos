from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QDoubleSpinBox,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.database.connection import SessionLocal
from app.services.brand_service import BrandService
from app.services.category_service import CategoryService
from app.services.product_service import ProductService


class ProductWindow(QWidget):
    def __init__(self, user):
        super().__init__()

        self.user = user

        self.setWindowTitle("Product Management")
        self.setMinimumSize(1100, 700)

        self.build_ui()
        self.load_products()

    # ==========================================================
    # MAIN UI
    # ==========================================================

    def build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Product Management")

        title.setStyleSheet(
            """
            QLabel {
                font-size: 24px;
                font-weight: bold;
            }
            """
        )

        layout.addWidget(title)

        description = QLabel(
            "Create, manage and maintain products and their variants."
        )

        description.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
                color: #555;
            }
            """
        )

        layout.addWidget(description)

        toolbar = QHBoxLayout()

        self.search_input = QLineEdit()

        self.search_input.setPlaceholderText(
            "Search products..."
        )

        self.search_input.textChanged.connect(
            self.filter_products
        )

        toolbar.addWidget(
            self.search_input
        )

        self.add_button = QPushButton(
            "ADD PRODUCT"
        )

        self.add_button.setMinimumHeight(40)

        self.add_button.clicked.connect(
            self.open_add_product_dialog
        )

        toolbar.addWidget(
            self.add_button
        )

        self.refresh_button = QPushButton(
            "REFRESH"
        )

        self.refresh_button.setMinimumHeight(40)

        self.refresh_button.clicked.connect(
            self.load_products
        )

        toolbar.addWidget(
            self.refresh_button
        )

        layout.addLayout(toolbar)

        self.products_table = QTableWidget()

        self.products_table.setColumnCount(7)

        self.products_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Product",
                "Brand",
                "Category",
                "Variants",
                "Status",
                "Actions",
            ]
        )

        self.products_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.products_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.products_table.verticalHeader().setVisible(True)

        self.products_table.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        self.products_table.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )

        self.products_table.horizontalHeader().setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.Stretch,
        )

        self.products_table.horizontalHeader().setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.Stretch,
        )

        self.products_table.horizontalHeader().setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        self.products_table.horizontalHeader().setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        self.products_table.horizontalHeader().setSectionResizeMode(
            6,
            QHeaderView.ResizeMode.Stretch,
        )

        layout.addWidget(
            self.products_table
        )

    # ==========================================================
    # LOAD PRODUCTS
    # ==========================================================

    def load_products(self):
        with SessionLocal() as session:
            product_service = ProductService(session)

            products = product_service.list_products(
                active_only=False
            )

            self.products_data = []

            for product in products:
                self.products_data.append(
                    {
                        "id": product.id,
                        "name": product.name,
                        "brand": (
                            product.brand.name
                            if product.brand
                            else ""
                        ),
                        "category": (
                            product.category.name
                            if product.category
                            else ""
                        ),
                        "variants": len(
                            product.variants
                        ),
                        "status": (
                            "Active"
                            if product.is_active
                            else "Inactive"
                        ),
                    }
                )

        self.display_products(
            self.products_data
        )

    # ==========================================================
    # DISPLAY PRODUCTS
    # ==========================================================

    def display_products(
        self,
        products,
    ):
        self.products_table.setRowCount(0)

        for product in products:
            row = self.products_table.rowCount()

            self.products_table.insertRow(row)

            values = [
                product["id"],
                product["name"],
                product["brand"],
                product["category"],
                product["variants"],
                product["status"],
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(
                    str(value)
                )

                self.products_table.setItem(
                    row,
                    column,
                    item,
                )

            actions_widget = QWidget()

            actions_layout = QHBoxLayout(
                actions_widget
            )

            actions_layout.setContentsMargins(
                2,
                2,
                2,
                2,
            )

            edit_button = QPushButton(
                "EDIT"
            )

            edit_button.clicked.connect(
                lambda checked=False,
                product_id=product["id"]:
                self.edit_product(product_id)
            )

            actions_layout.addWidget(
                edit_button
            )

            variant_button = QPushButton(
                "VARIANTS"
            )

            variant_button.clicked.connect(
                lambda checked=False,
                product_id=product["id"]:
                self.manage_variants(product_id)
            )

            actions_layout.addWidget(
                variant_button
            )

            self.products_table.setCellWidget(
                row,
                6,
                actions_widget,
            )

    # ==========================================================
    # SEARCH
    # ==========================================================

    def filter_products(
        self,
        text,
    ):
        search_term = text.strip().lower()

        if not search_term:
            self.display_products(
                self.products_data
            )

            return

        filtered = [
            product
            for product in self.products_data
            if (
                search_term
                in product["name"].lower()
            )
            or (
                search_term
                in product["brand"].lower()
            )
            or (
                search_term
                in product["category"].lower()
            )
        ]

        self.display_products(
            filtered
        )

    # ==========================================================
    # PRODUCT FORM
    # ==========================================================

    def build_product_form(
        self,
        product=None,
    ):
        dialog = QDialog(self)

        dialog.setWindowTitle(
            "Edit Product"
            if product
            else "Add Product"
        )

        dialog.setMinimumWidth(600)

        layout = QVBoxLayout(dialog)

        form = QFormLayout()

        name_input = QLineEdit()

        name_input.setPlaceholderText(
            "Enter product name"
        )

        form.addRow(
            "Product Name:",
            name_input,
        )

        with SessionLocal() as session:
            brands = BrandService(
                session
            ).list_brands()

            categories = CategoryService(
                session
            ).list_categories()

            brand_data = [
                (
                    brand.id,
                    brand.name,
                )
                for brand in brands
            ]

            category_data = [
                (
                    category.id,
                    category.name,
                )
                for category in categories
            ]

        brand_input = QComboBox()

        brand_input.addItem(
            "Select brand",
            None,
        )

        for brand_id, brand_name in brand_data:
            brand_input.addItem(
                brand_name,
                brand_id,
            )

        form.addRow(
            "Brand:",
            brand_input,
        )

        category_input = QComboBox()

        category_input.addItem(
            "Select category",
            None,
        )

        for category_id, category_name in category_data:
            category_input.addItem(
                category_name,
                category_id,
            )

        form.addRow(
            "Category:",
            category_input,
        )

        description_input = QLineEdit()

        description_input.setPlaceholderText(
            "Optional description"
        )

        form.addRow(
            "Description:",
            description_input,
        )

        image_layout = QHBoxLayout()

        image_input = QLineEdit()

        image_input.setPlaceholderText(
            "Optional product image"
        )

        browse_button = QPushButton(
            "BROWSE"
        )

        image_layout.addWidget(
            image_input
        )

        image_layout.addWidget(
            browse_button
        )

        browse_button.clicked.connect(
            lambda: self.browse_image(
                image_input
            )
        )

        form.addRow(
            "Image:",
            image_layout,
        )

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(
            dialog.accept
        )

        buttons.rejected.connect(
            dialog.reject
        )

        layout.addWidget(buttons)

        # Load existing product data
        if product:
            name_input.setText(
                product.name
            )

            description_input.setText(
                product.description or ""
            )

            image_input.setText(
                product.image_path or ""
            )

            if product.brand_id is not None:
                index = brand_input.findData(
                    product.brand_id
                )

                if index >= 0:
                    brand_input.setCurrentIndex(
                        index
                    )

            if product.category_id is not None:
                index = category_input.findData(
                    product.category_id
                )

                if index >= 0:
                    category_input.setCurrentIndex(
                        index
                    )

        return (
            dialog,
            name_input,
            brand_input,
            category_input,
            description_input,
            image_input,
        )

    # ==========================================================
    # ADD PRODUCT
    # ==========================================================

    def open_add_product_dialog(self):
        (
            dialog,
            name_input,
            brand_input,
            category_input,
            description_input,
            image_input,
        ) = self.build_product_form()

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        name = name_input.text().strip()

        if not name:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Product name is required.",
            )

            return

        try:
            with SessionLocal() as session:
                service = ProductService(
                    session
                )

                service.create_product(
                    name=name,
                    category_id=(
                        category_input.currentData()
                    ),
                    brand_id=(
                        brand_input.currentData()
                    ),
                    description=(
                        description_input.text().strip()
                        or None
                    ),
                    image_path=(
                        image_input.text().strip()
                        or None
                    ),
                )

                session.commit()

            QMessageBox.information(
                self,
                "Success",
                "Product created successfully.",
            )

            self.load_products()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Error",
                str(error),
            )

    # ==========================================================
    # EDIT PRODUCT
    # ==========================================================

    def edit_product(
        self,
        product_id: int,
    ):
        with SessionLocal() as session:
            product = session.get(
                __import__(
                    "app.models.product",
                    fromlist=["Product"],
                ).Product,
                product_id,
            )

            if product is None:
                QMessageBox.warning(
                    self,
                    "Not Found",
                    "Product not found.",
                )

                return

            (
                dialog,
                name_input,
                brand_input,
                category_input,
                description_input,
                image_input,
            ) = self.build_product_form(
                product
            )

            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            name = name_input.text().strip()

            if not name:
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    "Product name is required.",
                )

                return

            try:
                service = ProductService(
                    session
                )

                service.update_product(
                    product_id=product_id,
                    name=name,
                    category_id=(
                        category_input.currentData()
                    ),
                    brand_id=(
                        brand_input.currentData()
                    ),
                    description=(
                        description_input.text().strip()
                        or None
                    ),
                    image_path=(
                        image_input.text().strip()
                        or None
                    ),
                )

                session.commit()

            except Exception as error:
                QMessageBox.critical(
                    self,
                    "Error",
                    str(error),
                )

                return

        QMessageBox.information(
            self,
            "Success",
            "Product updated successfully.",
        )

        self.load_products()

    # ==========================================================
    # IMAGE BROWSER
    # ==========================================================

    def browse_image(
        self,
        image_input,
    ):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Product Image",
            "",
            "Images (*.png *.jpg *.jpeg *.webp)",
        )

        if file_path:
            image_input.setText(
                file_path
            )

    # ==========================================================
    # VARIANT MANAGEMENT
    # ==========================================================

    def manage_variants(
        self,
        product_id: int,
    ):
        dialog = QDialog(self)

        dialog.setWindowTitle(
            "Product Variants"
        )

        dialog.setMinimumSize(
            950,
            550,
        )

        layout = QVBoxLayout(dialog)

        with SessionLocal() as session:
            product_service = ProductService(
                session
            )

            product = product_service.get_product(
                product_id
            )

            if product is None:
                QMessageBox.warning(
                    self,
                    "Not Found",
                    "Product not found.",
                )

                return

            product_name = product.name

        title = QLabel(
            f"Variants — {product_name}"
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 20px;
                font-weight: bold;
            }
            """
        )

        layout.addWidget(title)

        toolbar = QHBoxLayout()

        add_variant_button = QPushButton(
            "ADD VARIANT"
        )

        add_variant_button.setMinimumHeight(
            40
        )

        refresh_button = QPushButton(
            "REFRESH"
        )

        refresh_button.setMinimumHeight(
            40
        )

        toolbar.addWidget(
            add_variant_button
        )

        toolbar.addWidget(
            refresh_button
        )

        toolbar.addStretch()

        layout.addLayout(toolbar)

        variants_table = QTableWidget()

        variants_table.setColumnCount(9)

        variants_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Variant",
                "Size",
                "Unit",
                "SKU",
                "Barcode",
                "Cost",
                "Selling",
                "Status",
            ]
        )

        variants_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        variants_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        variants_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        layout.addWidget(
            variants_table
        )

        close_button = QPushButton(
            "CLOSE"
        )

        close_button.clicked.connect(
            dialog.accept
        )

        layout.addWidget(
            close_button
        )

        def load_variants():
            with SessionLocal() as session:
                service = ProductService(
                    session
                )

                variants = service.list_variants(
                    product_id,
                    active_only=False,
                )

                variants_table.setRowCount(0)

                for variant in variants:
                    row = variants_table.rowCount()

                    variants_table.insertRow(row)

                    values = [
                        variant.id,
                        variant.variant_name or "",
                        variant.size or "",
                        variant.unit or "",
                        variant.sku or "",
                        variant.barcode or "",
                        f"{variant.cost_price:.2f}",
                        f"{variant.selling_price:.2f}",
                        (
                            "Active"
                            if variant.is_active
                            else "Inactive"
                        ),
                    ]

                    for column, value in enumerate(
                        values
                    ):
                        variants_table.setItem(
                            row,
                            column,
                            QTableWidgetItem(
                                str(value)
                            ),
                        )

        def add_variant():
            self.open_variant_dialog(
                product_id,
                None,
                load_variants,
            )

        def edit_selected_variant():
            selected_rows = (
                variants_table.selectionModel()
                .selectedRows()
            )

            if not selected_rows:
                QMessageBox.warning(
                    dialog,
                    "Select Variant",
                    "Please select a variant first.",
                )

                return

            row = selected_rows[0].row()

            item = variants_table.item(
                row,
                0,
            )

            if item is None:
                return

            variant_id = int(
                item.text()
            )

            self.open_variant_dialog(
                product_id,
                variant_id,
                load_variants,
            )

        variants_table.doubleClicked.connect(
            lambda: edit_selected_variant()
        )

        add_variant_button.clicked.connect(
            add_variant
        )

        refresh_button.clicked.connect(
            load_variants
        )

        load_variants()

        dialog.exec()

    # ==========================================================
    # VARIANT FORM
    # ==========================================================

    def open_variant_dialog(
        self,
        product_id: int,
        variant_id: int | None,
        refresh_callback,
    ):
        dialog = QDialog(self)

        dialog.setWindowTitle(
            "Edit Variant"
            if variant_id
            else "Add Variant"
        )

        dialog.setMinimumWidth(600)

        layout = QVBoxLayout(dialog)

        form = QFormLayout()

        variant_name_input = QLineEdit()

        variant_name_input.setPlaceholderText(
            "e.g. 100ml"
        )

        form.addRow(
            "Variant Name:",
            variant_name_input,
        )

        size_input = QLineEdit()

        size_input.setPlaceholderText(
            "e.g. 100"
        )

        form.addRow(
            "Size:",
            size_input,
        )

        unit_input = QLineEdit()

        unit_input.setPlaceholderText(
            "e.g. ml"
        )

        form.addRow(
            "Unit:",
            unit_input,
        )

        sku_input = QLineEdit()

        sku_input.setPlaceholderText(
            "Optional SKU"
        )

        form.addRow(
            "SKU:",
            sku_input,
        )

        barcode_input = QLineEdit()

        barcode_input.setPlaceholderText(
            "Optional barcode"
        )

        form.addRow(
            "Barcode:",
            barcode_input,
        )

        cost_input = QDoubleSpinBox()

        cost_input.setRange(
            0,
            999999999,
        )

        cost_input.setDecimals(
            2
        )

        cost_input.setSingleStep(
            100
        )

        form.addRow(
            "Cost Price:",
            cost_input,
        )

        selling_input = QDoubleSpinBox()

        selling_input.setRange(
            0,
            999999999,
        )

        selling_input.setDecimals(
            2
        )

        selling_input.setSingleStep(
            100
        )

        form.addRow(
            "Selling Price:",
            selling_input,
        )

        reorder_enabled = QCheckBox(
            "Enable reorder level"
        )

        reorder_input = QSpinBox()

        reorder_input.setRange(
            0,
            999999,
        )

        reorder_input.setValue(
            0
        )

        reorder_input.setEnabled(
            False
        )

        reorder_enabled.toggled.connect(
            reorder_input.setEnabled
        )

        reorder_layout = QHBoxLayout()

        reorder_layout.addWidget(
            reorder_enabled
        )

        reorder_layout.addWidget(
            reorder_input
        )

        form.addRow(
            "Reorder Level:",
            reorder_layout,
        )

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(
            dialog.accept
        )

        buttons.rejected.connect(
            dialog.reject
        )

        layout.addWidget(buttons)

        # Load existing variant
        if variant_id is not None:
            with SessionLocal() as session:
                service = ProductService(
                    session
                )

                variant = service.get_variant(
                    variant_id
                )

                if variant is None:
                    QMessageBox.warning(
                        self,
                        "Not Found",
                        "Variant not found.",
                    )

                    return

                variant_name_input.setText(
                    variant.variant_name or ""
                )

                size_input.setText(
                    variant.size or ""
                )

                unit_input.setText(
                    variant.unit or ""
                )

                sku_input.setText(
                    variant.sku or ""
                )

                barcode_input.setText(
                    variant.barcode or ""
                )

                cost_input.setValue(
                    float(
                        variant.cost_price
                    )
                )

                selling_input.setValue(
                    float(
                        variant.selling_price
                    )
                )

                if variant.reorder_level is not None:
                    reorder_enabled.setChecked(
                        True
                    )

                    reorder_input.setValue(
                        variant.reorder_level
                    )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        variant_name = (
            variant_name_input
            .text()
            .strip()
            or None
        )

        size = (
            size_input
            .text()
            .strip()
            or None
        )

        unit = (
            unit_input
            .text()
            .strip()
            or None
        )

        sku = (
            sku_input
            .text()
            .strip()
            or None
        )

        barcode = (
            barcode_input
            .text()
            .strip()
            or None
        )

        cost_price = Decimal(
            str(
                cost_input.value()
            )
        )

        selling_price = Decimal(
            str(
                selling_input.value()
            )
        )

        reorder_level = (
            reorder_input.value()
            if reorder_enabled.isChecked()
            else None
        )

        try:
            with SessionLocal() as session:
                service = ProductService(
                    session
                )

                if variant_id is None:
                    service.create_variant(
                        product_id=product_id,
                        cost_price=cost_price,
                        selling_price=selling_price,
                        variant_name=variant_name,
                        size=size,
                        unit=unit,
                        sku=sku,
                        barcode=barcode,
                        reorder_level=reorder_level,
                    )

                    success_message = (
                        "Variant created successfully."
                    )

                else:
                    service.update_variant(
                        variant_id=variant_id,
                        cost_price=cost_price,
                        selling_price=selling_price,
                        variant_name=variant_name,
                        size=size,
                        unit=unit,
                        sku=sku,
                        barcode=barcode,
                        reorder_level=reorder_level,
                    )

                    success_message = (
                        "Variant updated successfully."
                    )

                session.commit()

            QMessageBox.information(
                self,
                "Success",
                success_message,
            )

            refresh_callback()

            self.load_products()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Error",
                str(error),
            )