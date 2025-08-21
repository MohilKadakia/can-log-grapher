import os
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import Qt


class UploadSelection:
    """Handles file and folder selection for the CAN Log Uploader."""
    
    def __init__(self, parent):
        """Initialize with reference to parent widget."""
        self.parent = parent
    
    def select_TXT_file(self):
        """Select a TXT file for processing."""
        file_path, _ = QFileDialog.getOpenFileName(self.parent, "Open TXT File", "", "TXT Files (*.txt)")
        if file_path:
            self.parent.current_source = f"File: {file_path}"
            self.parent.source_label.setText(self.parent.current_source)
            self.parent.thread_manager.process_raw_path(file_path)    

    def select_TXT_folder(self):
        """Select a folder of TXT files for processing."""
        folder_path = QFileDialog.getExistingDirectory(self.parent, "Select Folder")
        if folder_path:
            txt_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.txt')]
            self.parent.current_source = f"Folder: {folder_path} ({len(txt_files)} TXT files)"
            self.parent.source_label.setText(self.parent.current_source)
            self.parent.thread_manager.process_raw_path(folder_path)
    
    def select_CSV_file(self):
        """Select a CSV file for processing."""
        file_path, _ = QFileDialog.getOpenFileName(self.parent, "Open CSV File", "", "CSV Files (*.csv)")
        if file_path:
            self.parent.current_source = f"File: {file_path}"
            self.parent.source_label.setText(self.parent.current_source)
            self.parent.thread_manager.process_files([file_path])

    def select_CSV_folder(self):
        """Select a folder of CSV files for processing."""
        folder_path = QFileDialog.getExistingDirectory(self.parent, "Select Folder")
        if folder_path:
            csv_files = []
            # Recursively walk through directory and subdirectories
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith('.csv'):
                        csv_files.append(os.path.join(root, file))
            
            self.parent.current_source = f"Folder: {folder_path} ({len(csv_files)} CSV files)"
            self.parent.source_label.setText(self.parent.current_source)
            self.parent.thread_manager.process_files(csv_files)
