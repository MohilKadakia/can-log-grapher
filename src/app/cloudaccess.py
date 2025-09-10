import os
from PyQt5.QtWidgets import (
    QDialog, QMessageBox, QApplication
)
from PyQt5.QtCore import pyqtSignal
from api.firebase_client import FirebaseClient
from app.cloudaccessgui import CloudAccessGUI


class CloudAccessPanel(QDialog):
    """A panel for accessing files and folders stored in the cloud."""
    
    file_selected_signal = pyqtSignal(str)
    folder_selected_signal = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Cloud Access")
        self.resize(1200, 900)  # Much larger size for better visibility
        
        # Initialize Firebase client
        self.firebase = FirebaseClient.get_instance()
        
        self.cloud_data = None
        
        # Dictionaries to store data by item
        self.folder_items = {}  # Will store folder data by item id
        self.file_items = {}    # Will store file data by item id
        
        # Initialize the GUI
        self.gui = CloudAccessGUI(self)
        
        # Load data
        self.load_cloud_data()
    
    def load_cloud_data(self):
        """Load data from Firebase and populate the UI."""
        try:
            QApplication.processEvents()
            
            # Get cloud data from Firebase
            self.cloud_data = self.firebase.get_cloud_structure()
            
            # Debug: Print folder count
            print(f"Retrieved {len(self.cloud_data['folders'])} folders from Firebase")
            
            # Clear existing items and dictionaries
            self.gui.clear_ui()
            self.folder_items = {}
            self.file_items = {}
            
            # Populate folder tree
            self.gui.populate_folders(self.cloud_data["folders"], self.folder_items)
            
            # Populate files list with standalone files (this will be overridden by auto-selection)
            self.gui.populate_files(self.cloud_data["standalone_files"], self.file_items)
            
            # Populate recent files list
            self.gui.populate_files(self.cloud_data["recent_files"], self.file_items, is_recent=True)
            
            # Auto-select the root folder to show all recent files by default
            root_index = self.gui.folder_model.indexFromItem(self.gui.root_item)
            self.gui.folder_tree.setCurrentIndex(root_index)
            self.on_folder_selected(root_index)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load cloud data: {str(e)}")
    
    def filter_items(self):
        """Filter items based on search text."""
        search_text = self.gui.search_input.text().lower()
        
        # If no search text, show all items
        if not search_text:
            self.load_cloud_data()
            return
        
        # Update UI with filtered items
        self.gui.filter_items_ui(search_text)
    
    def on_folder_selected(self, index):
        """Handle folder selection in the tree view."""
        item = self.gui.folder_model.itemFromIndex(index)
        
        # Check if this is the root item
        if item == self.gui.root_item:
            # Root folder selected - show all recent files in the Files tab
            try:
                # Clear file items dictionary for this view
                self.file_items.clear()
                
                # Show all recent files in the Files tab when root is selected
                all_recent_files = self.cloud_data.get("recent_files", [])
                self.gui.populate_folder_files(all_recent_files, self.file_items)
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading recent files: {str(e)}")
            return
        
        # Get folder data from our dictionary
        folder = self.folder_items.get(id(item))
        
        if folder:
            # This is a folder with a direct database entry
            try:
                # Clear file items dictionary for this view
                self.file_items.clear()
                
                # Get files for this folder - increase limit to 500 files
                folder_id = folder["id"]
                folder_files = self.firebase.list_files(limit=500, folder_id=folder_id)
                
                # Populate files list
                self.gui.populate_folder_files(folder_files, self.file_items)
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading folder: {str(e)}")
        else:
            # This might be a dynamically created subfolder without a direct database entry
            # We need to find files that belong to this path
            try:
                # Clear file items dictionary for this view
                self.file_items.clear()
                
                # Build the full path of this folder by traversing up the tree
                folder_path = self.get_folder_path(item)
                
                # Find all files that have this path as a prefix in their relative_path
                matching_files = []
                
                # First check if we can find a parent folder with a database entry
                parent_item = item.parent()
                parent_folder = None
                while parent_item and not parent_folder:
                    parent_folder = self.folder_items.get(id(parent_item))
                    if not parent_folder:
                        parent_item = parent_item.parent()
                
                if parent_folder:
                    # We found a parent with a database entry, get all its files
                    parent_folder_id = parent_folder["id"]
                    all_files = self.firebase.list_files(limit=1000, folder_id=parent_folder_id)
                    
                    # Filter files that belong to this subfolder
                    for file in all_files:
                        file_rel_path = file.get("relative_path", "")
                        file_dir = os.path.dirname(file_rel_path)
                        
                        # Check if this file is in the selected subfolder or its children
                        if file_dir == folder_path or file_dir.startswith(folder_path + os.sep):
                            matching_files.append(file)
                    
                    # Populate files list with matching files
                    self.gui.populate_folder_files(matching_files, self.file_items)
                else:
                    # No parent folder found, show empty list
                    self.gui.populate_folder_files([], self.file_items)
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading subfolder: {str(e)}")
    
    def get_folder_path(self, item):
        """Build the full path of a folder by traversing up the tree.
        
        Args:
            item: The QStandardItem representing the folder
            
        Returns:
            str: The full path of the folder
        """
        path_parts = []
        current_item = item
        
        # Traverse up the tree until we reach the root item
        while current_item and current_item != self.gui.root_item:
            path_parts.insert(0, current_item.text())
            current_item = current_item.parent()
        
        # Join the path parts with the OS separator
        return os.path.join(*path_parts) if path_parts else ""
    
    def prepare_selected(self):
        """Download the selected file."""
        file = self.gui.get_selected_file(self.file_items)
        
        if file:
            self.prepare_file(file)
        else:
            QMessageBox.warning(self, "Warning", "Please select a file to download!")
    
    def prepare_file(self, file):
        """Download a file to the user's downloads folder."""
        try:
            filename = file["filename"]
            file_path = file["path"]
            
            QApplication.processEvents()
            
            # Download the file
            local_path = self.firebase.download_file(file_path)
            
            QMessageBox.information(self, "Download Complete", f"File downloaded to:\n{local_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to download file: {str(e)}")
            
    def download_selected_folder(self):
        """Download the selected folder with all its files and subfolders recursively."""
        folder = self.gui.get_selected_folder(self.folder_items)
        
        if not folder:
            QMessageBox.warning(self, "Warning", "Please select a folder to download!")
            return
            
        try:
            # Show processing
            QApplication.processEvents()
            
            # Get folder ID
            folder_id = folder["id"]
            folder_name = folder["name"]
            
            # Download the folder
            QMessageBox.information(self, "Download Started", f"Starting recursive download of folder '{folder_name}' and all its subfolders.\nThis may take a while depending on the folder size and structure.")
            
            # Download the folder and all its files and subfolders recursively
            local_path = self.firebase.download_folder_recursive(folder_id)
            
            QMessageBox.information(self, "Download Complete", f"Folder and all subfolders downloaded to:\n{local_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to download folder: {str(e)}")
