import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox, QLabel, QSpacerItem, QSizePolicy, 
    QCheckBox, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt
from io import StringIO
import threading

from server import run_server, update_data
from csv_parse import parse_csv, rows_to_csv_bytes

class CANLogUploader(QWidget):
    def __init__(self):
        self.csv_data = []
        self.sender_checkboxes = {}
        self.parsed_data = StringIO()

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        self.gui()
        
    def gui(self):
        """Initialize the CAN Log Uploader GUI."""
        super().__init__()
        self.setWindowTitle("CAN Log Uploader")
        self.resize(800, 600)
        
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

        # Enhanced file selection button
        self.file_btn = QPushButton("Select CSV File")
        self.file_btn.clicked.connect(self.select_file)
        self.file_btn.setObjectName("file_btn")
        layout.addWidget(self.file_btn)

        # Enhanced folder selection button
        self.folder_btn = QPushButton("Select Folder of CSVs")
        self.folder_btn.clicked.connect(self.select_folder)
        self.folder_btn.setObjectName("folder_btn")
        layout.addWidget(self.folder_btn)

        # Enhanced sender selection area
        self.sender_frame = QFrame()
        self.sender_frame.setFrameStyle(QFrame.Box)
        self.sender_frame.setObjectName("sender_frame")
        self.sender_layout = QVBoxLayout(self.sender_frame)
        
        sender_title = QLabel("Select Signals:")
        sender_title.setObjectName("sender_title")
        self.sender_layout.addWidget(sender_title)
        
        # Add select/deselect all buttons
        from PyQt5.QtWidgets import QHBoxLayout
        button_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all_checkboxes)
        self.select_all_btn.setObjectName("select_all_btn")
        button_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self.deselect_all_checkboxes)
        self.deselect_all_btn.setObjectName("deselect_all_btn")
        button_layout.addWidget(self.deselect_all_btn)
        
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

        self.setLayout(layout)

    def create_sender_checkboxes(self):
        """Create checkboxes for each unique sender in the CSV data."""
        # Clear existing checkboxes
        for checkbox in self.sender_checkboxes.values():
            checkbox.deleteLater()
        self.sender_checkboxes.clear()
        
        # Get unique senders
        senders = set()
        for row in self.csv_data:
            if 'sender' in row:
                sender = row['sender'].strip()
                senders.add(sender)
        
        # Create ordered list with proper sorting (case-insensitive, numeric-aware)
        def sort_key(sender):
            # Convert to lowercase for case-insensitive sorting
            # Split into parts to handle numeric sorting properly
            import re
            parts = re.split(r'(\d+)', sender.lower())
            # Convert numeric parts to integers for proper numeric sorting
            result = []
            for part in parts:
                if part.isdigit():
                    result.append(int(part))
                else:
                    result.append(part)
            return result
        
        self.sender_order = sorted(senders, key=sort_key)
        self.last_clicked_index = None
        
        # Create checkboxes for each sender
        for i, sender in enumerate(self.sender_order):
            checkbox = QCheckBox(f"{sender}")
            checkbox.setChecked(True)  # Default to checked
            checkbox.setObjectName("sender_checkbox")
            
            # Connect to custom click handler that preserves normal behavior
            checkbox.mousePressEvent = lambda event, idx=i, cb=checkbox: self.checkbox_mouse_press(event, idx, cb)
            
            self.sender_checkboxes[sender] = checkbox
            self.checkbox_layout.addWidget(checkbox)

        # Show the sender frame and update button if we have data
        if senders:
            self.sender_frame.show()
            self.update_btn.show()

    def update_checkbox_highlight(self, index):
        """Update the visual highlight for the selected checkbox."""
        # Clear previous highlights
        for i, sender in enumerate(self.sender_order):
            checkbox = self.sender_checkboxes[sender]
            if i == index:
                # Highlight the selected checkbox
                checkbox.setObjectName("sender_checkbox_highlighted")
            else:
                # Reset other checkboxes to default style
                checkbox.setObjectName("sender_checkbox")
        
            # Force style refresh
            checkbox.style().unpolish(checkbox)
            checkbox.style().polish(checkbox)

    def checkbox_mouse_press(self, event, index, checkbox):
        """Handle checkbox mouse press with shift-click range selection."""
        from PyQt5.QtCore import Qt
        
        # Update visual highlight
        self.update_checkbox_highlight(index)
        
        # Check if shift is held and we have a previous click
        if event.modifiers() == Qt.ShiftModifier and self.last_clicked_index is not None:
            # Determine range
            start_idx = min(self.last_clicked_index, index)
            end_idx = max(self.last_clicked_index, index)
            
            # Get the target state from the last clicked checkbox
            last_sender = self.sender_order[self.last_clicked_index]
            target_state = self.sender_checkboxes[last_sender].isChecked()
            
            # Apply the state to all checkboxes in range
            for i in range(start_idx, end_idx + 1):
                sender = self.sender_order[i]
                self.sender_checkboxes[sender].setChecked(target_state)
            
            # Don't update last_clicked_index for shift-clicks to allow chaining
        else:
            # Normal click - let Qt handle it normally
            QCheckBox.mousePressEvent(checkbox, event)
            # Update last clicked index after the normal click is processed
            self.last_clicked_index = index

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv)")
        if file_path:
            self.process_files([file_path])
            self.update_server_filtered()

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            csv_files = [
                os.path.join(folder_path, f)
                for f in os.listdir(folder_path)
                if f.lower().endswith('.csv')
            ]
            self.process_files(csv_files)
            self.update_server_filtered()

    def process_files(self, file_list):
        self.csv_data = []
        for file in file_list:
            file_data = parse_csv(file)
            self.csv_data.extend(file_data)
            print(f"Processing {file}")
        print(f"Total rows loaded: {len(self.csv_data)}")
        
        # Create checkboxes for senders
        self.create_sender_checkboxes()
        
        # QMessageBox.information(self, "Done", f"Files processed. Found {len(self.sender_checkboxes)} unique senders.")

    def get_filtered_data(self):
        """Get CSV data filtered by selected senders."""
        selected_senders = set()
        for sender, checkbox in self.sender_checkboxes.items():
            if checkbox.isChecked():
                selected_senders.add(sender)
        
        filtered_data = []
        for row in self.csv_data:
            if 'sender' in row and row['sender'].strip() in selected_senders:
                filtered_data.append(row)
        
        return filtered_data

    def update_server_filtered(self):
        """Update server with filtered data based on selected checkboxes."""
        filtered_data = self.get_filtered_data()
        if not filtered_data:
            QMessageBox.warning(self, "Warning", "No signals selected!")
            return
        
        csv_bytes = rows_to_csv_bytes(filtered_data)
        update_data(csv_bytes.decode('utf-8'))
        QMessageBox.information(self, "Success", f"Server updated with {len(filtered_data)} rows from selected senders.")

    def load_stylesheet(self, css_file):
        """Load CSS stylesheet from file."""

        current_dir = os.path.dirname(os.path.abspath(__file__))
        css_path = os.path.join(current_dir, css_file)

        try:
            with open(css_path, 'r') as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print(f"CSS file {css_file} not found, using default styles")

    def select_all_checkboxes(self):
        """Select all sender checkboxes."""
        for checkbox in self.sender_checkboxes.values():
            checkbox.setChecked(True)

    def deselect_all_checkboxes(self):
        """Deselect all sender checkboxes."""
        for checkbox in self.sender_checkboxes.values():
            checkbox.setChecked(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Optional: set a global style
    window = CANLogUploader()
    window.show()
    sys.exit(app.exec_())