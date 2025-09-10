import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox, QLabel, 
    QCheckBox, QScrollArea, QFrame, QProgressBar, QHBoxLayout, QLineEdit, QDesktopWidget,
    QDialog, QApplication
)
from PyQt5.QtCore import Qt


class CloudUploadGUI:
    """UI-related functionality for the cloud upload panel."""
    
    def __init__(self, parent):
        """Initialize the GUI components for cloud upload.
        
        Args:
            parent: The CloudUploadPanel instance that owns this GUI
        """
        self.parent = parent
        
        # Create widgets
        self.selection_label = None
        self.select_folder_btn = None
        self.upload_btn = None
        self.progress_frame = None
        self.progress_label = None
        self.upload_progress = None
        self.progress_text = None
        
        # Set up the UI
        self.setup_ui()
    
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
        self.select_folder_btn.clicked.connect(self.parent.select_folder)
        self.select_folder_btn.setObjectName("folder_btn")
        button_layout.addWidget(self.select_folder_btn)
        
        layout.addLayout(button_layout)
        
        # Upload button
        self.upload_btn = QPushButton("Upload to Cloud")
        self.upload_btn.clicked.connect(self.parent.upload_to_cloud)
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
        self.close_btn.clicked.connect(self.parent.close)
        self.close_btn.setObjectName("close_btn")
        layout.addWidget(self.close_btn)
        
        # Add stretch to push content to top
        layout.addStretch()
        
        self.parent.setLayout(layout)
        
        # Apply parent's stylesheet if available
        if hasattr(self.parent.parent, 'styleSheet'):
            self.parent.setStyleSheet(self.parent.parent.styleSheet())
    
    def show_progress(self):
        """Show the progress UI and disable buttons."""
        self.progress_frame.show()
        self.upload_btn.setEnabled(False)
        self.select_folder_btn.setEnabled(False)
    
    def hide_progress(self):
        """Hide the progress UI and enable buttons."""
        self.progress_frame.hide()
        self.upload_btn.setEnabled(True)
        self.select_folder_btn.setEnabled(True)
    
    def update_progress(self, progress, message):
        """Update the progress bar and message.
        
        Args:
            progress (int): Progress value (0-100)
            message (str): Status message
        """
        self.upload_progress.setValue(progress)
        self.progress_text.setText(message)
        QApplication.processEvents()
    
    def update_selection(self, path, is_folder=False):
        """Update the selection label.
        
        Args:
            path (str): Selected file or folder path
            is_folder (bool): Whether the selection is a folder
        """
        type_text = "folder" if is_folder else "file"
        self.selection_label.setText(f"Selected {type_text}: {path}")
