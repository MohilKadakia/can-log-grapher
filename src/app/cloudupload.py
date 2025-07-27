import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox, QLabel, 
    QCheckBox, QScrollArea, QFrame, QProgressBar, QHBoxLayout, QLineEdit, QDesktopWidget,
    QDialog, QApplication
)
from io import StringIO
from PyQt5.QtCore import Qt, pyqtSignal
import threading
import re
from api.firebase_client import FirebaseClient



class CloudUploadPanel(QDialog):
    """A separate panel for cloud upload functionality."""

    upload_progress_signal = pyqtSignal(int, str)
    success_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Cloud Upload")
        self.resize(600, 400)
        self.firebase = FirebaseClient.get_instance()
        self.setup_ui()

        self.upload_progress_signal.connect(self.update_progress)
        self.success_signal.connect(self._display_success)
        self.error_signal.connect(self._display_error)
        
    def setup_ui(self):
        """Set up the cloud upload panel UI."""
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("Upload to Cloud")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("title")
        layout.addWidget(title)
        
        # Description
        description = QLabel("Select folders or files to upload to the cloud storage.")
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Current selection display
        self.selection_label = QLabel("No selection")
        self.selection_label.setAlignment(Qt.AlignCenter)
        self.selection_label.setObjectName("source_label")
        self.selection_label.setWordWrap(True)
        layout.addWidget(self.selection_label)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Select folder button
        self.select_folder_btn = QPushButton("Select Folder")
        self.select_folder_btn.clicked.connect(self.select_folder)
        self.select_folder_btn.setObjectName("csv_btn")
        button_layout.addWidget(self.select_folder_btn)
        
        # Select file button
        self.select_file_btn = QPushButton("Select File")
        self.select_file_btn.clicked.connect(self.select_file)
        self.select_file_btn.setObjectName("file_btn")
        button_layout.addWidget(self.select_file_btn)
        
        layout.addLayout(button_layout)
        
        # Upload button
        self.upload_btn = QPushButton("Upload to Cloud")
        self.upload_btn.clicked.connect(self.upload_to_cloud)
        self.upload_btn.setObjectName("update_btn")
        layout.addWidget(self.upload_btn)
        
        # Progress bar for upload
        self.progress_frame = QFrame()
        self.progress_frame.setFrameStyle(QFrame.Box)
        self.progress_frame.setObjectName("loading_frame")
        progress_layout = QVBoxLayout(self.progress_frame)
        
        self.progress_label = QLabel("Uploading...")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setObjectName("loading_label")
        progress_layout.addWidget(self.progress_label)
        
        self.upload_progress = QProgressBar()
        self.upload_progress.setRange(0, 0)  # Indeterminate progress
        self.upload_progress.setObjectName("progress_bar")
        progress_layout.addWidget(self.upload_progress)
        
        self.progress_text = QLabel("")
        self.progress_text.setAlignment(Qt.AlignCenter)
        self.progress_text.setObjectName("progress_text")
        progress_layout.addWidget(self.progress_text)
        
        # Initially hide the progress frame
        self.progress_frame.hide()
        layout.addWidget(self.progress_frame)
        
        # Close button
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setObjectName("csv_btn")
        layout.addWidget(self.close_btn)
        
        # Add stretch to push content to top
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Apply parent's stylesheet if available
        if self.parent and hasattr(self.parent, 'styleSheet'):
            self.setStyleSheet(self.parent.styleSheet())
    
    def select_folder(self):
        """Select a folder for uploading."""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder to Upload")
        if folder_path:
            self.selection_label.setText(f"Selected folder: {folder_path}")
            self.selected_path = folder_path
    
    def select_file(self):
        """Select a file for uploading."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File to Upload", "", "All Files (*)")
        if file_path:
            self.selection_label.setText(f"Selected file: {file_path}")
            self.selected_path = file_path
    
    def upload_to_cloud(self):
        """Upload the selected file or folder to the cloud."""
        if not hasattr(self, 'selected_path'):
            QMessageBox.warning(self, "Warning", "Please select a file or folder first!")
            return
        
        # Show progress UI
        self.progress_frame.show()
        self.upload_btn.setEnabled(False)
        self.select_file_btn.setEnabled(False)
        self.select_folder_btn.setEnabled(False)
        
       # Start upload in a separate thread
        upload_thread = threading.Thread(
            target=self._upload_thread,
            args=(self.selected_path,),
            daemon=True
        )
        upload_thread.start()
        
    def _upload_thread(self, path):
        """Background thread to handle upload process."""
        try:
            self.upload_progress_signal.emit(10, "Preparing upload...")
            
            if os.path.isfile(path):
                self.upload_progress_signal.emit(30, f"Uploading file: {os.path.basename(path)}")
                try:
                    url = self.firebase.upload_file(path)
                    self.upload_progress_signal.emit(100, f"Upload complete: {os.path.basename(path)}")
                    self.success_signal.emit(f"Successfully uploaded file to cloud storage!\nURL: {url}")
                except ConnectionError as ce:
                    self.error_signal.emit(str(ce))
            else:
                self.upload_progress_signal.emit(20, "Scanning folder...")
                file_count = sum([len(files) for _, _, files in os.walk(path)])
                self.upload_progress_signal.emit(30, f"Uploading folder with {file_count} files...")
                try:
                    urls = self.firebase.upload_folder(path)
                    self.upload_progress_signal.emit(100, "Upload complete!")
                    self.success_signal.emit(f"Successfully uploaded {len(urls)} files to cloud storage!")
                except ConnectionError as ce:
                    self.error_signal.emit(str(ce))
                
        except Exception as e:
            self.error_signal.emit(f"Error during upload: {str(e)}")
    
    def update_progress(self, progress, message):
        """Update the progress bar and message from the signal."""
        self.upload_progress.setValue(progress)
        self.progress_text.setText(message)
        QApplication.processEvents()
        
        if progress >= 100:
            # Reset UI after upload completes
            self.progress_frame.hide()
            self.upload_btn.setEnabled(True)
            self.select_file_btn.setEnabled(True)
            self.select_folder_btn.setEnabled(True)
    

    def _display_success(self, message):
        """Display success message (called on main thread)."""
        QMessageBox.information(self, "Success", message)

    def _display_error(self, message):
        """Display error message (called on main thread)."""
        QMessageBox.critical(self, "Error", message)