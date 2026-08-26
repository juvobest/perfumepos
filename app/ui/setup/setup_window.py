from sqlalchemy import select
from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.core.security import hash_password
from app.database.connection import SessionLocal
from app.models.business_settings import BusinessSettings
from app.models.role import Role
from app.models.user import User


class SetupWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Welcome - Business Setup")
        self.setMinimumSize(650, 700)

        self.build_ui()

        self.setup_button.clicked.connect(
            self.complete_setup
        )

    def build_ui(self):
        outer_layout = QVBoxLayout(self)

        outer_layout.setContentsMargins(
            35,
            30,
            35,
            30,
        )

        title = QLabel(
            "WELCOME TO YOUR POS"
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 28px;
                font-weight: bold;
            }
            """
        )

        subtitle = QLabel(
            "Let's set up your business and administrator account."
        )

        subtitle.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
            }
            """
        )

        outer_layout.addWidget(title)
        outer_layout.addWidget(subtitle)
        outer_layout.addSpacing(20)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        layout = QVBoxLayout(container)

        # ======================================================
        # BUSINESS INFORMATION
        # ======================================================

        business_title = QLabel(
            "BUSINESS INFORMATION"
        )

        business_title.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
            }
            """
        )

        layout.addWidget(business_title)

        form = QFormLayout()

        self.business_name = QLineEdit()
        self.business_name.setPlaceholderText(
            "e.g. Shopfave Luxe Scents and Gifts"
        )

        self.phone = QLineEdit()
        self.phone.setPlaceholderText(
            "Business phone number"
        )

        self.address = QLineEdit()
        self.address.setPlaceholderText(
            "Business address"
        )

        self.instagram = QLineEdit()
        self.instagram.setPlaceholderText(
            "@yourinstagram"
        )

        self.tiktok = QLineEdit()
        self.tiktok.setPlaceholderText(
            "@yourtiktok"
        )

        self.motto = QLineEdit()
        self.motto.setPlaceholderText(
            "e.g. Your scent, your signature"
        )

        form.addRow(
            "Business Name *:",
            self.business_name,
        )

        form.addRow(
            "Phone:",
            self.phone,
        )

        form.addRow(
            "Address:",
            self.address,
        )

        form.addRow(
            "Instagram:",
            self.instagram,
        )

        form.addRow(
            "TikTok:",
            self.tiktok,
        )

        form.addRow(
            "Receipt Motto:",
            self.motto,
        )

        layout.addLayout(form)

        layout.addSpacing(25)

        # ======================================================
        # ADMINISTRATOR
        # ======================================================

        admin_title = QLabel(
            "ADMINISTRATOR ACCOUNT"
        )

        admin_title.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
            }
            """
        )

        layout.addWidget(admin_title)

        admin_form = QFormLayout()

        self.full_name = QLineEdit()
        self.full_name.setPlaceholderText(
            "Administrator full name"
        )

        self.username = QLineEdit()
        self.username.setPlaceholderText(
            "Login username"
        )

        self.password = QLineEdit()
        self.password.setPlaceholderText(
            "Password"
        )

        self.password.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.confirm_password = QLineEdit()
        self.confirm_password.setPlaceholderText(
            "Confirm password"
        )

        self.confirm_password.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        admin_form.addRow(
            "Full Name *:",
            self.full_name,
        )

        admin_form.addRow(
            "Username *:",
            self.username,
        )

        admin_form.addRow(
            "Password *:",
            self.password,
        )

        admin_form.addRow(
            "Confirm Password *:",
            self.confirm_password,
        )

        layout.addLayout(admin_form)

        layout.addSpacing(25)

        self.message = QLabel("")
        self.message.setWordWrap(True)

        layout.addWidget(self.message)

        self.setup_button = QPushButton(
            "COMPLETE SETUP"
        )

        self.setup_button.setMinimumHeight(50)

        self.setup_button.setStyleSheet(
            """
            QPushButton {
                font-size: 15px;
                font-weight: bold;
            }
            """
        )

        layout.addWidget(self.setup_button)

        layout.addStretch()

        scroll.setWidget(container)

        outer_layout.addWidget(scroll)

    def complete_setup(self):
        business_name = (
            self.business_name.text().strip()
        )

        phone = self.phone.text().strip()
        address = self.address.text().strip()
        instagram = self.instagram.text().strip()
        tiktok = self.tiktok.text().strip()
        motto = self.motto.text().strip()

        full_name = (
            self.full_name.text().strip()
        )

        username = (
            self.username.text().strip()
        )

        password = self.password.text()
        confirm_password = (
            self.confirm_password.text()
        )

        # ======================================================
        # VALIDATION
        # ======================================================

        if not business_name:
            self.show_error(
                "Business name is required."
            )
            self.business_name.setFocus()
            return

        if not full_name:
            self.show_error(
                "Administrator full name is required."
            )
            self.full_name.setFocus()
            return

        if not username:
            self.show_error(
                "Administrator username is required."
            )
            self.username.setFocus()
            return

        if not password:
            self.show_error(
                "Administrator password is required."
            )
            self.password.setFocus()
            return

        if len(password) < 6:
            self.show_error(
                "Password must be at least 6 characters."
            )
            self.password.setFocus()
            return

        if password != confirm_password:
            self.show_error(
                "Passwords do not match."
            )
            self.confirm_password.clear()
            self.confirm_password.setFocus()
            return

        try:
            with SessionLocal() as session:

                # --------------------------------------------------
                # Prevent duplicate setup
                # --------------------------------------------------

                existing_settings = session.scalar(
                    select(BusinessSettings)
                )

                if existing_settings is not None:
                    QMessageBox.warning(
                        self,
                        "Already Configured",
                        "Business setup has already been completed.",
                    )
                    self.close()
                    return

                # --------------------------------------------------
                # Check username
                # --------------------------------------------------

                existing_user = session.scalar(
                    select(User).where(
                        User.username == username
                    )
                )

                if existing_user is not None:
                    self.show_error(
                        f"Username '{username}' already exists."
                    )
                    self.username.setFocus()
                    return

                # --------------------------------------------------
                # Find Admin role
                # --------------------------------------------------

                admin_role = session.scalar(
                    select(Role).where(
                        Role.name == "Admin"
                    )
                )

                if admin_role is None:
                    raise ValueError(
                        "Admin role does not exist. "
                        "Please seed the database roles first."
                    )

                # --------------------------------------------------
                # Save business settings
                # --------------------------------------------------

                settings = BusinessSettings(
                    business_name=business_name,
                    phone=phone or None,
                    address=address or None,
                    instagram=instagram or None,
                    tiktok=tiktok or None,
                    motto=motto or None,
                )

                session.add(settings)

                # --------------------------------------------------
                # Create administrator
                # --------------------------------------------------

                admin_user = User(
                    username=username,
                    full_name=full_name,
                    password_hash=hash_password(
                        password
                    ),
                    is_active=True,
                )

                admin_user.roles.append(
                    admin_role
                )

                session.add(admin_user)

                session.commit()

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Setup Failed",
                str(exc),
            )
            return

        QMessageBox.information(
            self,
            "Setup Complete",
            (
                "Your business has been configured successfully.\n\n"
                "Your administrator account has been created.\n\n"
                "You can now log in."
            ),
        )

        self.close()

    def show_error(self, message):
        self.message.setText(message)

        QMessageBox.warning(
            self,
            "Setup Required",
            message,
        )