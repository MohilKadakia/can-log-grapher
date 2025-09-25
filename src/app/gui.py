import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox, QLabel, 
    QCheckBox, QScrollArea, QFrame, QProgressBar, QHBoxLayout, QLineEdit, QDesktopWidget,
    QDialog, QApplication
)
from io import StringIO
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
# Threading import removed - all processing is now synchronous
import re
import webbrowser

from app.server import run_server
from app.threadmanagement import ThreadManager
from app.apptransitions import UITransitionManager
from app.uploadselection import UploadSelection
from app.checkboxmanagement import CheckboxManager
from app.threading_scripts.shared_data import shared_data_manager
from app.cloudupload import CloudUploadPanel
from app.cloudaccess import CloudAccessPanel
from api.login import LoginDialog
from app.docker_manager import DockerManager


class CANLogUploader(QWidget):
    def __init__(self):
        self.csv_data_id = None  # Store data ID instead of data
        self.sender_checkboxes = {}
        self.parsed_data = StringIO()
        self.current_source = "No file or folder selected"
        
        # Create thread manager
        self.thread_manager = ThreadManager()
        self.thread_manager.parsing_completed.connect(self.on_parsing_completed)
        self.thread_manager.processing_completed.connect(self.on_processing_completed)

        # Start HTTP server in background thread
        self.start_http_server()

        super().__init__()
        
        # Create UI managers after initializing QWidget
        self.ui_transitions = UITransitionManager(self)
        self.upload_selection = UploadSelection(self)
        self.checkbox_manager = CheckboxManager(self)
        
        # Connect thread manager signals directly to UI transition manager methods
        self.thread_manager.progress_update.connect(self.ui_transitions.update_progress_text)
        self.thread_manager.show_loading.connect(self.ui_transitions.show_loading_screen)
        self.thread_manager.hide_loading.connect(self.ui_transitions.hide_loading_screen)
        
        # Initialize Docker manager
        self.docker_manager = DockerManager(self)
        
        # Start Docker check after a short delay to let UI load
        QTimer.singleShot(2000, self.docker_manager.check_docker_availability)
        
        self.gui()
        
    def gui(self):
        """Initialize the CAN Log Uploader GUI."""
        self.setWindowTitle("CAN Log Uploader")
        self.resize(1000, 700)
        
        # Load external CSS file
        self.load_stylesheet('styles.css')
        
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setAlignment(Qt.AlignTop)

        # Title with enhanced styling
        title = QLabel("CAN Log Uploader")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("title")
        layout.addWidget(title)

        # Create horizontal layout for buttons
        button_layout_CSV = QHBoxLayout()

        # File selection button
        self.CSV_file_btn = QPushButton("Select CSV File")
        self.CSV_file_btn.clicked.connect(self.upload_selection.select_CSV_file)
        self.CSV_file_btn.setObjectName("csv_btn")
        button_layout_CSV.addWidget(self.CSV_file_btn)

        # Folder selection button
        self.CSV_folder_btn = QPushButton("Select Folder of CSVs")
        self.CSV_folder_btn.clicked.connect(self.upload_selection.select_CSV_folder)
        self.CSV_folder_btn.setObjectName("csv_btn")
        button_layout_CSV.addWidget(self.CSV_folder_btn)

        # Create horizontal layout for buttons
        button_layout_TXT = QHBoxLayout()

        # File selection button
        self.TXT_file_btn = QPushButton("Select TXT File")
        self.TXT_file_btn.clicked.connect(self.upload_selection.select_TXT_file)
        self.TXT_file_btn.setObjectName("file_btn")
        button_layout_TXT.addWidget(self.TXT_file_btn)

        # Folder selection button
        self.TXT_folder_btn = QPushButton("Select Folder of TXTs")
        self.TXT_folder_btn.clicked.connect(self.upload_selection.select_TXT_folder)
        self.TXT_folder_btn.setObjectName("file_btn")
        button_layout_TXT.addWidget(self.TXT_folder_btn)

        layout.addLayout(button_layout_CSV)
        layout.addLayout(button_layout_TXT)

        # Cloud buttons layout
        cloud_buttons_layout = QHBoxLayout()
        
        # Add Cloud Upload button
        self.cloud_upload_btn = QPushButton("Upload to Cloud")
        self.cloud_upload_btn.clicked.connect(self.open_cloud_upload_panel)
        self.cloud_upload_btn.setObjectName("update_btn")
        cloud_buttons_layout.addWidget(self.cloud_upload_btn)
        
        # Add Cloud Access button
        self.cloud_access_btn = QPushButton("Access Cloud Files")
        self.cloud_access_btn.clicked.connect(self.open_cloud_access_panel)
        self.cloud_access_btn.setObjectName("file_btn")
        cloud_buttons_layout.addWidget(self.cloud_access_btn)
        
        layout.addLayout(cloud_buttons_layout)

        # Source label to display the current file/folder being processed
        self.source_label = QLabel(self.current_source)
        self.source_label.setAlignment(Qt.AlignCenter)
        self.source_label.setObjectName("source_label")
        layout.addWidget(self.source_label)


        # Loading screen elements
        self.loading_frame = QFrame()
        self.loading_frame.setFrameStyle(QFrame.Box)
        self.loading_frame.setObjectName("loading_frame")
        loading_layout = QVBoxLayout(self.loading_frame)
        
        self.loading_label = QLabel("Loading...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setObjectName("loading_label")
        loading_layout.addWidget(self.loading_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.progress_bar.setObjectName("progress_bar")
        loading_layout.addWidget(self.progress_bar)
        
        self.progress_text = QLabel("")
        self.progress_text.setAlignment(Qt.AlignCenter)
        self.progress_text.setObjectName("progress_text")
        loading_layout.addWidget(self.progress_text)
        
        # Initially hide the loading frame
        self.loading_frame.hide()
        layout.addWidget(self.loading_frame)

        # Enhanced sender selection area
        self.sender_frame = QFrame()
        self.sender_frame.setFrameStyle(QFrame.Box)
        self.sender_frame.setObjectName("sender_frame")
        self.sender_layout = QVBoxLayout(self.sender_frame)
        
        sender_title = QLabel("Select Signals:")
        sender_title.setObjectName("sender_title")
        self.sender_layout.addWidget(sender_title)
        
        # Add regex filter
        regex_layout = QHBoxLayout()
        regex_label = QLabel("Search:")
        regex_label.setObjectName("regex_label")
        regex_layout.addWidget(regex_label)
        
        self.regex_input = QLineEdit()
        self.regex_input.setPlaceholderText("Enter regex pattern")
        self.regex_input.setObjectName("regex_input")
        self.regex_input.textChanged.connect(self.ui_transitions.apply_regex_filter)
        regex_layout.addWidget(self.regex_input)
        
        self.regex_clear_btn = QPushButton("Clear")
        self.regex_clear_btn.clicked.connect(self.ui_transitions.clear_regex_filter)
        self.regex_clear_btn.setObjectName("regex_clear_btn")
        regex_layout.addWidget(self.regex_clear_btn)
        
        self.sender_layout.addLayout(regex_layout)
        
        # Add select/deselect all buttons
        button_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.checkbox_manager.select_all_checkboxes)
        self.select_all_btn.setObjectName("select_all_btn")
        button_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self.checkbox_manager.deselect_all_checkboxes)
        self.deselect_all_btn.setObjectName("deselect_all_btn")
        button_layout.addWidget(self.deselect_all_btn)
        
        # Add regex selection buttons
        self.select_regex_btn = QPushButton("Select Filtered")
        self.select_regex_btn.clicked.connect(self.checkbox_manager.select_regex_matches)
        self.select_regex_btn.setObjectName("select_regex_btn")
        button_layout.addWidget(self.select_regex_btn)
        
        self.sender_layout.addLayout(button_layout)
        
        # Enhanced scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("scroll_area")
        
        self.checkbox_widget = QWidget()
        self.checkbox_layout = QVBoxLayout(self.checkbox_widget)
        self.checkbox_layout.setSpacing(5)
        self.scroll_area.setWidget(self.checkbox_widget)
        
        self.sender_layout.addWidget(self.scroll_area)
        
        # Initially hide the sender frame
        self.sender_frame.hide()
        layout.addWidget(self.sender_frame)

        # Enhanced update button
        self.update_btn = QPushButton("Update Server with Selected Data")
        self.update_btn.clicked.connect(self.update_server_filtered)
        self.update_btn.setObjectName("update_btn")
        self.update_btn.hide()
        layout.addWidget(self.update_btn)

        # Add stretch to push content to top
        layout.addStretch()
        
        # Add the UWFE logo at the bottom
        logo_layout = QHBoxLayout()
        logo_layout.setAlignment(Qt.AlignCenter)
        
        logo_label = QLabel()
        logo_label.setObjectName("logo_label")
        
        # Handle path differently for executable vs development mode
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            app_path = os.path.dirname(sys.executable)
            logo_path = os.path.join(app_path, "public", "UWFElogo.png")
        else:
            # Running as Python script
            logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                    "public", "UWFElogo.png")
        logo_pixmap = QPixmap(logo_path)
        # Scale the logo to an appropriate size (adjust width as needed)
        logo_pixmap = logo_pixmap.scaledToWidth(400, Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(logo_label)
        
        layout.addLayout(logo_layout)

        self.setLayout(layout)
    
    def open_cloud_upload_panel(self):
        """Open the cloud upload panel."""
        login_dialog = LoginDialog(self)
        result = login_dialog.exec_()
            
        if result == QDialog.Accepted:
            cloud_panel = CloudUploadPanel(self)
            cloud_panel.exec_()
    
    def open_cloud_access_panel(self):
        """Open the cloud access panel."""
        login_dialog = LoginDialog(self)
        result = login_dialog.exec_()
            
        if result == QDialog.Accepted:
            cloud_panel = CloudAccessPanel(self)
            cloud_panel.exec_()

    def on_parsing_completed(self, data_id):
        """Handle completion of CSV parsing."""
        self.csv_data_id = data_id
        
        # Create checkboxes for senders
        self.checkbox_manager.create_sender_checkboxes()
        
        # Auto-update server with all senders after checkboxes are created
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(500, self.auto_update_server)
    
    
    def auto_update_server(self):
        """Auto-update server with all senders after a short delay."""
        from PyQt5.QtWidgets import QMessageBox
        
        # Get all available senders
        all_senders = self.checkbox_manager.get_all_senders()
        
        if all_senders:
            # Select all senders automatically
            for sender in all_senders:
                if sender in self.sender_checkboxes:
                    self.sender_checkboxes[sender].setChecked(True)
            
            # Update server with all data automatically
            success = self.thread_manager.update_server_filtered(all_senders)
            
            if success:
                QMessageBox.information(self, "Data Uploaded", 
                    f"Successfully uploaded data with {len(all_senders)} signals to Grafana!\n\n"
                    f"Visit http://localhost:3001 to view your dashboard.")
            else:
                QMessageBox.warning(self, "Upload Failed", 
                    "Failed to upload data to server. Please try manually selecting signals and clicking 'Update Server'.")
        else:
            QMessageBox.warning(self, "No Data", 
                "No signals found in the selected files. Please check your data format.")
    
    def on_processing_completed(self, csv_bytes):
        """Handle completion of CSV processing."""
        self.ui_transitions.show_sender_frame()
        self.ui_transitions.recenter_window()
        
        filtered_count = len(self.checkbox_manager.get_filtered_data())
        QMessageBox.information(self, "Success", f"Server updated with {filtered_count} rows from selected senders.")

    def update_server_filtered(self):
        """Update server with filtered data based on selected checkboxes."""
        selected_senders = self.checkbox_manager.get_selected_senders()
        
        if not selected_senders:
            QMessageBox.warning(self, "Warning", "No signals selected!")
            return
        
        # Use thread manager to update server
        self.thread_manager.update_server_filtered(selected_senders)

    def load_stylesheet(self, css_file):
        """Load CSS stylesheet from file."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        css_path = os.path.join(current_dir, css_file)

        try:
            with open(css_path, 'r') as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print(f"CSS file {css_file} not found, using default styles")

    def start_http_server(self):
        """Start HTTP server in background thread"""
        import threading
        from app.server import run_server
        
        def run_server_thread():
            try:
                # Check if port is already in use (prevents multiple instances)
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', 8000))
                sock.close()
                
                if result == 0:
                    print("HTTP server already running on port 8000")
                    return
                
                print("Starting HTTP server on port 8000...")
                run_server()
            except Exception as e:
                print(f"HTTP server error: {e}")
                # Fail silently - app can work without server
        
        # Start server in daemon thread so it doesn't prevent app shutdown
        server_thread = threading.Thread(target=run_server_thread, daemon=True)
        server_thread.start()
        print("HTTP server thread started")

    def _safe_run_server(self):
        """Safely run the HTTP server with error handling for .exe deployment"""
        try:
            # Check if port is already in use (prevents multiple instances)
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 8000))
            sock.close()
            
            if result == 0:
                print("HTTP server already running on port 8000")
                return
            
            # Start the server
            run_server()
        except Exception as e:
            print(f"HTTP server error: {e}")
            # Fail silently - app can work without server

    def closeEvent(self, event):
        """Clean up resources when window closes."""
        # Clean up Docker resources
        self.docker_manager.cleanup()
        
        # Clean up other resources using thread manager
        self.thread_manager.cleanup()
        event.accept()