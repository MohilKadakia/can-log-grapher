from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import Qt
from api.auth_config import TEAM_USERNAME, TEAM_PASSWORD

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Team Login")
        self.resize(350, 280)
        self.setup_ui()
        
        # Apply parent's stylesheet if available
        if parent and hasattr(parent, 'styleSheet'):
            self.setStyleSheet(parent.styleSheet())
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("Authentication Required")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("title")
        layout.addWidget(title)
        
        # Description
        description = QLabel("Please enter your credentials to access cloud upload")
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Username field
        username_label = QLabel("Username:")
        username_label.setObjectName("regex_label")
        layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        self.username_input.setObjectName("regex_input")
        layout.addWidget(self.username_input)
        
        # Password field
        password_label = QLabel("Password:")
        password_label.setObjectName("regex_label")
        layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setObjectName("regex_input")
        layout.addWidget(self.password_input)
        
        # Login button
        login_btn = QPushButton("Login")
        login_btn.clicked.connect(self.attempt_login)
        login_btn.setObjectName("update_btn")
        layout.addWidget(login_btn)
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setObjectName("csv_btn")
        layout.addWidget(cancel_btn)
        
        # Status message
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setObjectName("progress_text")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
    def attempt_login(self):
        
        username = self.username_input.text()
        password = self.password_input.text()
        
        if username == TEAM_USERNAME and password == TEAM_PASSWORD:
            self.accept()  # Close dialog with success
        else:
            self.status_label.setText("Invalid username or password")
            self.status_label.setStyleSheet("color: #f87171;")