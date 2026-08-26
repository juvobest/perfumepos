from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.config import BUSINESS_NAME
from app.database.connection import SessionLocal
from app.services.auth_service import (
    AuthenticationError,
    authenticate_user,
)
from app.ui.main.main_window import MainWindow


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.main_window = None

        self.setWindowTitle(
            f"{BUSINESS_NAME} - Login"
        )

        self.setFixedSize(
            520,
            400,
        )

        self.build_ui()

        self.login_button.clicked.connect(
            self.handle_login
        )

        self.password_input.returnPressed.connect(
            self.handle_login
        )

    def build_ui(self):
        layout = QVBoxLayout()

        layout.setContentsMargins(
            50,
            40,
            50,
            40,
        )

        layout.setSpacing(20)

        title = QLabel(
            BUSINESS_NAME
        )

        title.setWordWrap(True)

        title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 20px;
                font-weight: bold;
            }
            """
        )

        title.setMinimumHeight(
            60
        )

        form_layout = QFormLayout()

        self.username_input = QLineEdit()

        self.username_input.setPlaceholderText(
            "Enter username"
        )

        self.password_input = QLineEdit()

        self.password_input.setPlaceholderText(
            "Enter password"
        )

        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        form_layout.addRow(
            "Username:",
            self.username_input,
        )

        form_layout.addRow(
            "Password:",
            self.password_input,
        )

        self.login_button = QPushButton(
            "LOGIN"
        )

        self.login_button.setMinimumHeight(
            42
        )

        self.message_label = QLabel(
            ""
        )

        self.message_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(
            title
        )

        layout.addSpacing(
            10
        )

        layout.addLayout(
            form_layout
        )

        layout.addSpacing(
            10
        )

        layout.addWidget(
            self.login_button
        )

        layout.addWidget(
            self.message_label
        )

        self.setLayout(
            layout
        )

    def handle_login(self):
        username = (
            self.username_input
            .text()
            .strip()
        )

        password = (
            self.password_input
            .text()
        )

        if not username or not password:
            self.show_message(
                "Please enter your username and password."
            )

            return

        with SessionLocal() as session:
            try:
                user = authenticate_user(
                    session,
                    username,
                    password,
                )

            except AuthenticationError as error:
                self.show_message(
                    str(error)
                )

                self.password_input.clear()

                self.password_input.setFocus()

                return

        self.open_main_window(
            user
        )

    def open_main_window(self, user):
        self.main_window = MainWindow(
            user
        )

        self.main_window.show()

        self.close()

    def show_message(
        self,
        message: str,
    ):
        self.message_label.setText(
            message
        )