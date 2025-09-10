import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QMessageBox, QLabel, 
    QCheckBox, QScrollArea, QFrame, QHBoxLayout, QLineEdit, QTreeView,
    QDialog, QApplication, QSplitter, QTabWidget, QListWidget, QListWidgetItem,
    QFileIconProvider, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon


class CloudAccessGUI:
    """UI-related functionality for the cloud access panel."""
    
    def __init__(self, parent):
        """Initialize the GUI components for cloud access.
        
        Args:
            parent: The CloudAccessPanel instance that owns this GUI
        """
        self.parent = parent
        
        # Create models and widgets
        self.folder_model = None
        self.root_item = None
        self.folder_tree = None
        self.files_list = None
        self.recent_list = None
        self.download_btn = None
        self.download_folder_btn = None
        self.search_input = None
        
        # Set up the UI
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the cloud access panel UI."""
        layout = QVBoxLayout()
        layout.setSpacing(15)  # Reduced spacing to allow more content
        layout.setContentsMargins(20, 20, 20, 20)  # Reduced margins to maximize space
        
        # Title
        title = QLabel("Cloud File Access")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("title")
        layout.addWidget(title)
        
        # Description
        description = QLabel("Browse and access your files and folders stored in the cloud.")
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for files or folders...")
        self.search_input.setObjectName("regex_input")
        self.search_input.textChanged.connect(self.parent.filter_items)
        search_layout.addWidget(self.search_input)
        
        self.search_btn = QPushButton("Search")
        self.search_btn.setObjectName("select_regex_btn")
        self.search_btn.clicked.connect(self.parent.filter_items)
        search_layout.addWidget(self.search_btn)
        
        layout.addLayout(search_layout)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Folder navigation tree
        folder_frame = QFrame()
        folder_frame.setObjectName("sender_frame")
        folder_layout = QVBoxLayout(folder_frame)
        folder_layout.setContentsMargins(5, 5, 5, 5)  # Reduced margins
        
        folder_title = QLabel("Folders")
        folder_title.setObjectName("sender_title")
        folder_layout.addWidget(folder_title)
        
        self.folder_tree = QTreeView()
        self.folder_tree.setObjectName("scroll_area")
        self.folder_tree.setHeaderHidden(True)
        self.folder_tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.folder_tree.clicked.connect(self.parent.on_folder_selected)
        self.folder_tree.setMinimumWidth(250)  # Set minimum width
        
        # Create a model for the folder tree
        self.folder_model = QStandardItemModel()
        self.folder_model.setHorizontalHeaderLabels(["Name"])
        
        # Root item will be populated from Firebase
        self.root_item = QStandardItem("All Files")
        self.root_item.setIcon(QIcon.fromTheme("folder"))
        self.folder_model.appendRow(self.root_item)
        
        self.folder_tree.setModel(self.folder_model)
        # Set the tree to expand all items by default
        self.folder_tree.setRootIsDecorated(True)
        folder_layout.addWidget(self.folder_tree)
        
        # Right side - Tab widget for Files and Recent
        tab_widget = QTabWidget()
        
        # Files tab
        files_widget = QWidget()
        files_layout = QVBoxLayout(files_widget)
        files_layout.setContentsMargins(5, 5, 5, 5)  # Reduced margins
        
        self.files_list = QListWidget()
        self.files_list.setObjectName("scroll_area")
        self.files_list.setMinimumHeight(400)  # Set minimum height
        files_layout.addWidget(self.files_list)
        
        # Recent tab
        recent_widget = QWidget()
        recent_layout = QVBoxLayout(recent_widget)
        recent_layout.setContentsMargins(5, 5, 5, 5)  # Reduced margins
        
        self.recent_list = QListWidget()
        self.recent_list.setObjectName("scroll_area")
        self.recent_list.setMinimumHeight(400)  # Set minimum height
        recent_layout.addWidget(self.recent_list)
        
        # Add tabs to tab widget
        tab_widget.addTab(files_widget, "Files")
        tab_widget.addTab(recent_widget, "Recent")
        
        # Add widgets to splitter
        splitter.addWidget(folder_frame)
        splitter.addWidget(tab_widget)
        splitter.setSizes([350, 850])  # Set initial sizes to give more space to files
        
        layout.addWidget(splitter, 1)  # Give the splitter a stretch factor of 1
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        # Download button
        self.download_btn = QPushButton("Download Selected File")
        self.download_btn.setObjectName("file_btn")
        self.download_btn.clicked.connect(self.parent.prepare_selected)
        button_layout.addWidget(self.download_btn)
        
        # Download Folder button
        self.download_folder_btn = QPushButton("Download Selected Folder")
        self.download_folder_btn.setObjectName("folder_btn")
        self.download_folder_btn.clicked.connect(self.parent.download_selected_folder)
        button_layout.addWidget(self.download_folder_btn)
        
        layout.addLayout(button_layout)
        
        # Bottom buttons in horizontal layout to save vertical space
        bottom_buttons = QHBoxLayout()
        
        
        # Close button
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.parent.close)
        self.close_btn.setObjectName("deselect_all_btn")
        bottom_buttons.addWidget(self.close_btn)
        
        layout.addLayout(bottom_buttons)
        
        self.parent.setLayout(layout)
        
        # Apply parent's stylesheet if available
        if hasattr(self.parent.parent, 'styleSheet'):
            self.parent.setStyleSheet(self.parent.parent.styleSheet())
    
    def filter_items_ui(self, search_text):
        """Update UI elements based on search filter.
        
        Args:
            search_text (str): Text to filter items by
        """
        # Filter folders
        for i in range(self.root_item.rowCount()):
            folder_item = self.root_item.child(i)
            folder_name = folder_item.text().lower()
            # Use setRowHidden on the tree view instead of setVisible on the item
            self.folder_tree.setRowHidden(i, self.folder_model.indexFromItem(self.root_item), 
                                         search_text not in folder_name)
        
        # Filter files
        for i in range(self.files_list.count()):
            item = self.files_list.item(i)
            file_name = item.text().lower()
            item.setHidden(search_text not in file_name)
        
        # Filter recent files
        for i in range(self.recent_list.count()):
            item = self.recent_list.item(i)
            file_name = item.text().lower()
            item.setHidden(search_text not in file_name)
    
    def clear_ui(self):
        """Clear all UI elements."""
        self.root_item.removeRows(0, self.root_item.rowCount())
        self.files_list.clear()
        self.recent_list.clear()
    
    def populate_folders(self, folders, folder_items):
        """Populate the folder tree with folder data.
        
        Args:
            folders (list): List of folder data dictionaries
            folder_items (dict): Dictionary to store folder items by ID
        """
        # Create a dictionary to track folder items by their ID for building hierarchy
        folder_items_by_id = {}
        root_folders = []  # Folders without parent
        
        # First pass: create all folder items and categorize them
        for folder in folders:
            folder_item = QStandardItem(folder["name"])
            folder_item.setIcon(QIcon.fromTheme("folder"))
            
            # Store folder data in our dictionary
            item_id = id(folder_item)
            folder_items[item_id] = folder
            folder_items_by_id[folder.get("id", "")] = {
                "item": folder_item,
                "data": folder
            }
            
            # Check if this is a root folder (no parent_folder_id)
            if not folder.get("parent_folder_id"):
                root_folders.append(folder_item)
        
        # Second pass: build the hierarchy by identifying parent-child relationships
        # We need to handle nested subfolders by finding the correct parent for each folder
        for folder in folders:
            parent_folder_id = folder.get("parent_folder_id")
            if parent_folder_id and parent_folder_id in folder_items_by_id:
                # This is a subfolder, add it to its parent
                parent_item = folder_items_by_id[parent_folder_id]["item"]
                current_item = folder_items_by_id[folder.get("id", "")]["item"]
                parent_item.appendRow(current_item)
        
        # Add root folders to the tree
        for folder_item in root_folders:
            self.root_item.appendRow(folder_item)
            
        # Third pass: process subfolders array for folders that use the old structure
        for folder in folders:
            if "subfolders" in folder and folder["subfolders"]:
                # Find the corresponding item for this folder
                folder_id = folder.get("id", "")
                if folder_id in folder_items_by_id:
                    folder_item = folder_items_by_id[folder_id]["item"]
                    
                    # Process each subfolder path
                    for subfolder_path in folder["subfolders"]:
                        # Check if this subfolder already exists as a separate folder document
                        subfolder_exists = False
                        for existing_folder in folders:
                            if existing_folder.get("relative_path") == subfolder_path:
                                subfolder_exists = True
                                break
                        
                        # Only create subfolder item if it doesn't exist as separate document
                        if not subfolder_exists:
                            # Handle multi-level paths by creating each level as needed
                            parts = subfolder_path.split(os.sep)
                            current_item = folder_item
                            current_path = ""
                            
                            for i, part in enumerate(parts):
                                # Build the path incrementally
                                if current_path:
                                    current_path = os.path.join(current_path, part)
                                else:
                                    current_path = part
                                
                                # Check if this part already exists as a child
                                child_exists = False
                                for row in range(current_item.rowCount()):
                                    if current_item.child(row).text() == part:
                                        # This part exists, move to it and continue
                                        current_item = current_item.child(row)
                                        child_exists = True
                                        break
                                
                                if not child_exists:
                                    # Create a new item for this part
                                    new_item = QStandardItem(part)
                                    new_item.setIcon(QIcon.fromTheme("folder"))
                                    current_item.appendRow(new_item)
                                    current_item = new_item
        
        # Expand the folder tree to show the hierarchy
        self.folder_tree.expandAll()
        
        # Ensure the root item is visible and selectable
        root_index = self.folder_model.indexFromItem(self.root_item)
        self.folder_tree.setCurrentIndex(root_index)
    
    def populate_files(self, files, file_items, is_recent=False):
        """Populate the files list with file data.
        
        Args:
            files (list): List of file data dictionaries
            file_items (dict): Dictionary to store file items by ID
            is_recent (bool): Whether these are recent files
        """
        list_widget = self.recent_list if is_recent else self.files_list
        icon_name = "document-open-recent" if is_recent else "text-x-generic"
        
        for file in files:
            item = QListWidgetItem(file["filename"])
            item.setIcon(QIcon.fromTheme(icon_name))
            list_widget.addItem(item)
            
            # Store file data in our dictionary
            item_id = id(item)
            file_items[item_id] = file
    
    def populate_folder_files(self, files, file_items):
        """Populate the files list with files from a selected folder.
        
        Args:
            files (list): List of file data dictionaries
            file_items (dict): Dictionary to store file items by ID
        """
        self.files_list.clear()
        
        for file in files:
            file_item = QListWidgetItem(file["filename"])
            file_item.setIcon(QIcon.fromTheme("text-x-generic"))
            self.files_list.addItem(file_item)
            
            # Store file data in our dictionary
            item_id = id(file_item)
            file_items[item_id] = file
            
        # Add a note if we're showing a lot of files (might be hitting a limit)
        if len(files) >= 500:
            note_item = QListWidgetItem("Note: Only showing the first 500 files. There may be more files in this folder.")
            note_item.setFlags(Qt.NoItemFlags)  # Make it non-selectable
            self.files_list.addItem(note_item)
    
    def get_selected_file(self, file_items):
        """Get the selected file from either list.
        
        Args:
            file_items (dict): Dictionary of file items by ID
            
        Returns:
            dict or None: Selected file data or None if no file is selected
        """
        # Check if a file is selected in the files list
        selected_files = self.files_list.selectedItems()
        if selected_files:
            return file_items.get(id(selected_files[0]))
            
        # Check if a file is selected in the recent list
        selected_recent = self.recent_list.selectedItems()
        if selected_recent:
            return file_items.get(id(selected_recent[0]))
            
        return None
    
    def get_selected_folder(self, folder_items):
        """Get the selected folder from the tree view.
        
        Args:
            folder_items (dict): Dictionary of folder items by ID
            
        Returns:
            dict or None: Selected folder data or None if no folder is selected
        """
        selected_indexes = self.folder_tree.selectedIndexes()
        if not selected_indexes:
            return None
            
        # Get the first selected index
        index = selected_indexes[0]
        item = self.folder_model.itemFromIndex(index)
        
        # Get folder data from our dictionary
        return folder_items.get(id(item))
