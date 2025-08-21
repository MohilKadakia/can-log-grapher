import os
import threading
from PyQt5.QtWidgets import (
    QDialog, QFileDialog, QMessageBox, QApplication
)
from PyQt5.QtCore import pyqtSignal
from api.firebase_client import FirebaseClient
from app.clouduploadgui import CloudUploadGUI


class CloudUploadPanel(QDialog):
    """A separate panel for cloud upload functionality."""

    upload_progress_signal = pyqtSignal(int, str)
    success_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Cloud Upload")
        self.resize(900, 600)
        
        # Initialize Firebase client
        self.firebase = FirebaseClient.get_instance()
        
        # Initialize the GUI
        self.gui = CloudUploadGUI(self)

        # Connect signals to UI update methods
        self.upload_progress_signal.connect(self.update_progress)
        self.success_signal.connect(self._display_success)
        self.error_signal.connect(self._display_error)
    
    def select_folder(self):
        """Select a folder for uploading."""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder to Upload")
        if folder_path:
            self.gui.update_selection(folder_path, is_folder=True)
            self.selected_path = folder_path
    
    def select_file(self):
        """Select a file for uploading."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File to Upload", "", "All Files (*)")
        if file_path:
            self.gui.update_selection(file_path)
            self.selected_path = file_path
    
    def upload_to_cloud(self):
        """Upload the selected file or folder to the cloud."""
        if not hasattr(self, 'selected_path'):
            QMessageBox.warning(self, "Warning", "Please select a file or folder first!")
            return
        
        # Show progress UI
        self.gui.show_progress()
        
        # Start upload in a background thread
        if os.path.isfile(self.selected_path):
            self.upload_file_async(self.selected_path)
        else:
            self.upload_folder_async(self.selected_path)
    
    def upload_file_async(self, file_path):
        """Upload a file in a background thread."""
        thread = threading.Thread(target=self._upload_file_thread, args=(file_path,), daemon=True)
        thread.start()
        
    def _upload_file_thread(self, file_path):
        """Thread function to upload a file."""
        try:
            # Update progress
            self.update_progress_from_thread(10, "Preparing file for upload...")
            
            # Get file name
            filename = os.path.basename(file_path)
            
            # Update progress
            self.update_progress_from_thread(30, f"Uploading {filename}...")
            
            # Upload the file
            url = self.firebase.upload_file(file_path)
            
            # Update progress
            self.update_progress_from_thread(100, "Upload complete!")
            
            # Show success message
            self.on_success_from_thread(f"File '{filename}' uploaded successfully!")
            
        except Exception as e:
            self.on_error_from_thread(f"Error uploading file: {str(e)}")
    
    def upload_folder_async(self, folder_path):
        """Upload a folder in a background thread."""
        thread = threading.Thread(target=self._upload_folder_thread, args=(folder_path,), daemon=True)
        thread.start()
        
    def _upload_folder_thread(self, folder_path):
        """Thread function to upload a folder."""
        try:
            # Update progress
            self.update_progress_from_thread(10, "Preparing folder for upload...")
            
            # Get folder name for display
            folder_name = os.path.basename(folder_path)
            
            # Update progress
            self.update_progress_from_thread(20, f"Analyzing folder structure for '{folder_name}'...")
            
            # Use the comprehensive upload_folder method that properly handles subfolders
            result = self.firebase.upload_folder(folder_path)
            
            # Update progress
            self.update_progress_from_thread(100, "Upload complete!")
            
            # Show success message with details from the upload result
            folder_name = result["folder_name"]
            file_count = result["file_count"]
            self.on_success_from_thread(f"Folder '{folder_name}' with {file_count} files uploaded successfully!")
            
        except Exception as e:
            self.on_error_from_thread(f"Error uploading folder: {str(e)}")
    
    def update_progress_from_thread(self, progress, message):
        """Update progress from the background thread via signal."""
        self.upload_progress_signal.emit(progress, message)
    
    def on_success_from_thread(self, message):
        """Handle success from the background thread via signal."""
        self.success_signal.emit(message)
    
    def on_error_from_thread(self, message):
        """Handle error from the background thread via signal."""
        self.error_signal.emit(message)
        
    def update_progress(self, progress, message):
        """Update the progress bar and message from the signal."""
        self.gui.update_progress(progress, message)
        
        if progress >= 100:
            # Reset UI after upload completes
            self.gui.hide_progress()

    def _display_success(self, message):
        """Display success message (called on main thread)."""
        QMessageBox.information(self, "Success", message)

    def _display_error(self, message):
        """Display error message (called on main thread)."""
        QMessageBox.critical(self, "Error", message)