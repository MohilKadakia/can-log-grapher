import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox, QLabel, 
    QCheckBox, QScrollArea, QFrame, QProgressBar, QHBoxLayout, QLineEdit, QDesktopWidget
)
from io import StringIO
from PyQt5.QtCore import Qt
import threading
import re

from app.server import run_server, update_data
from app.threading_scripts.processing_threads import CSVParsingThread, CSVProcessingThread, CSVConversionThread
from app.threading_scripts.shared_data import shared_data_manager

class CANLogUploader(QWidget):
    def __init__(self):
        self.csv_data_id = None  # Store data ID instead of data
        self.sender_checkboxes = {}
        self.parsed_data = StringIO()
        self.parsing_thread = None
        self.processing_thread = None

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

        # Create horizontal layout for buttons
        button_layout_CSV = QHBoxLayout()

        # File selection button
        self.CSV_file_btn = QPushButton("Select CSV File")
        self.CSV_file_btn.clicked.connect(self.select_CSV_file)
        self.CSV_file_btn.setObjectName("csv_btn")
        button_layout_CSV.addWidget(self.CSV_file_btn)

        # Folder selection button
        self.CSV_folder_btn = QPushButton("Select Folder of CSVs")
        self.CSV_folder_btn.clicked.connect(self.select_CSV_folder)
        self.CSV_folder_btn.setObjectName("csv_btn")
        button_layout_CSV.addWidget(self.CSV_folder_btn)

        # Create horizontal layout for buttons
        button_layout_TXT = QHBoxLayout()

        # File selection button
        self.TXT_file_btn = QPushButton("Select TXT File")
        self.TXT_file_btn.clicked.connect(self.select_TXT_file)
        self.TXT_file_btn.setObjectName("file_btn")
        button_layout_TXT.addWidget(self.TXT_file_btn)

        # Folder selection button
        self.TXT_folder_btn = QPushButton("Select Folder of TXTs")
        self.TXT_folder_btn.clicked.connect(self.select_TXT_folder)
        self.TXT_folder_btn.setObjectName("file_btn")
        button_layout_TXT.addWidget(self.TXT_folder_btn)

        layout.addLayout(button_layout_CSV)
        layout.addLayout(button_layout_TXT)

        # Current source display
        self.source_label = QLabel("No file or folder selected")
        self.source_label.setAlignment(Qt.AlignCenter)
        self.source_label.setObjectName("source_label")
        self.source_label.setWordWrap(True)
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
        self.regex_input.textChanged.connect(self.apply_regex_filter)
        regex_layout.addWidget(self.regex_input)
        
        self.regex_clear_btn = QPushButton("Clear")
        self.regex_clear_btn.clicked.connect(self.clear_regex_filter)
        self.regex_clear_btn.setObjectName("regex_clear_btn")
        regex_layout.addWidget(self.regex_clear_btn)
        
        self.sender_layout.addLayout(regex_layout)
        
        # Add select/deselect all buttons
        button_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all_checkboxes)
        self.select_all_btn.setObjectName("select_all_btn")
        button_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self.deselect_all_checkboxes)
        self.deselect_all_btn.setObjectName("deselect_all_btn")
        button_layout.addWidget(self.deselect_all_btn)
        
        # Add regex selection buttons
        self.select_regex_btn = QPushButton("Select Filtered")
        self.select_regex_btn.clicked.connect(self.select_regex_matches)
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

        self.setLayout(layout)

    def show_loading_screen(self, message="Processing...", disable_sender_controls=False):
        """Show the loading screen with customizable message and button states."""
        self.loading_frame.show()
        self.sender_frame.hide()
        self.update_btn.hide()
        self.TXT_folder_btn.setEnabled(False)
        self.TXT_file_btn.setEnabled(False)
        self.CSV_folder_btn.setEnabled(False)
        self.CSV_file_btn.setEnabled(False)
        self.loading_label.setText(message)
        self.progress_text.setText("")
        
        if disable_sender_controls:
            self.update_btn.setEnabled(False)
            self.select_all_btn.setEnabled(False)
            self.deselect_all_btn.setEnabled(False)
            self.select_regex_btn.setEnabled(False)
            self.regex_input.setEnabled(False)
            self.regex_clear_btn.setEnabled(False)

    def hide_loading_screen(self, enable_sender_controls=True):
        """Hide the loading screen and re-enable buttons."""
        self.loading_frame.hide()
        self.TXT_file_btn.setEnabled(True)
        self.TXT_folder_btn.setEnabled(True)
        self.CSV_file_btn.setEnabled(True)
        self.CSV_folder_btn.setEnabled(True)
        if enable_sender_controls:
            self.update_btn.setEnabled(True)
            self.select_all_btn.setEnabled(True)
            self.deselect_all_btn.setEnabled(True)
            self.select_regex_btn.setEnabled(True)
            self.regex_input.setEnabled(True)
            self.regex_clear_btn.setEnabled(True)

    def process_raw_path(self, path):
        """Process a raw path."""
        self.show_loading_screen("Processing raw path...")
        self.conversion_thread = CSVConversionThread(path)
        self.conversion_thread.progress_update.connect(self.on_conversion_progress)
        self.conversion_thread.conversion_complete.connect(self.on_conversion_complete)
        self.conversion_thread.start()

    def on_conversion_progress(self, message):
        """Update progress text during conversion."""
        self.progress_text.setText(message)

    def on_conversion_complete(self, file_paths):
        """Handle completion of CSV conversion."""
        file_paths = file_paths.split(',')
        self.show_loading_screen("Processing...")
        self.parsing_thread = CSVParsingThread(file_paths)
        self.parsing_thread.progress_update.connect(self.on_parsing_progress)
        self.parsing_thread.parsing_complete.connect(self.on_parsing_complete)
        self.parsing_thread.start()

    def on_parsing_progress(self, message):
        """Update progress text during parsing."""
        self.progress_text.setText(message)

    def on_parsing_complete(self, data_id: str):
        """Handle completion of CSV parsing."""
        self.csv_data_id = data_id
        self.hide_loading_screen()
        
        # Create checkboxes for senders
        self.create_sender_checkboxes()
        
        # Update server with filtered data
        self.update_server_filtered()

    def on_processing_complete(self, csv_bytes):
        """Handle completion of CSV processing."""
        self.hide_loading_screen(enable_sender_controls=True)
        update_data(csv_bytes.decode('utf-8'))

        self.sender_frame.show()
        self.update_btn.show()
        self.recenter_window()
        
        filtered_count = len(self.get_filtered_data())
        QMessageBox.information(self, "Success", f"Server updated with {filtered_count} rows from selected senders.")

    def update_server_filtered(self):
        """Update server with filtered data based on selected checkboxes."""
        selected_senders = set()
        for sender, checkbox in self.sender_checkboxes.items():
            if checkbox.isChecked():
                selected_senders.add(sender)
        
        if not selected_senders:
            QMessageBox.warning(self, "Warning", "No signals selected!")
            return
        
        # Show processing screen
        self.show_loading_screen("Processing data for server...", disable_sender_controls=True)
        
        # Create and start processing thread with data ID
        self.processing_thread = CSVProcessingThread(self.csv_data_id, selected_senders)
        self.processing_thread.progress_update.connect(self.on_parsing_progress)
        self.processing_thread.processing_complete.connect(self.on_processing_complete)
        self.processing_thread.start()

    def create_sender_checkboxes(self):
        """Create checkboxes for each unique sender in the CSV data."""
        # Clear existing checkboxes
        for checkbox in self.sender_checkboxes.values():
            checkbox.deleteLater()
        self.sender_checkboxes.clear()
        
        # Get data from shared manager
        csv_data = shared_data_manager.get_data(self.csv_data_id)
        if not csv_data:
            return
        
        # Get unique senders
        senders = set()
        for row in csv_data:
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
            checkbox.setChecked(False)  # Default to checked
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

    def select_TXT_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open TXT File", "", "TXT Files (*.txt)")
        if file_path:
            self.current_source = f"File: {file_path}"
            self.source_label.setText(self.current_source)
            self.process_raw_path(file_path)    
    def select_TXT_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            txt_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.txt')]
            self.current_source = f"Folder: {folder_path} ({len(txt_files)} TXT files)"
            self.source_label.setText(self.current_source)
            self.process_raw_path(folder_path)
    
    def select_CSV_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv)")
        if file_path:
            self.current_source = f"File: {file_path}"
            self.source_label.setText(self.current_source)
            self.process_files([file_path])

    def select_CSV_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            csv_files = [
                os.path.join(folder_path, f)
                for f in os.listdir(folder_path)
                if f.lower().endswith('.csv')
            ]
            self.current_source = f"Folder: {folder_path} ({len(csv_files)} CSV files)"
            self.source_label.setText(self.current_source)
            self.process_files(csv_files)

    def process_files(self, file_list):
        """Start CSV parsing in a separate thread."""
        if not file_list:
            return
            
        # Show loading screen
        self.show_loading_screen("Processing...")
        
        # Create and start parsing thread
        self.parsing_thread = CSVParsingThread(file_list)
        self.parsing_thread.progress_update.connect(self.on_parsing_progress)
        self.parsing_thread.parsing_complete.connect(self.on_parsing_complete)
        self.parsing_thread.start()

    def get_filtered_data(self):
        """Get CSV data filtered by selected senders."""
        if not self.csv_data_id:
            return []
        
        csv_data = shared_data_manager.get_data(self.csv_data_id)
        if not csv_data:
            return []
        
        selected_senders = set()
        for sender, checkbox in self.sender_checkboxes.items():
            if checkbox.isChecked():
                selected_senders.add(sender)
        
        filtered_data = []
        for row in csv_data:
            if 'sender' in row and row['sender'].strip() in selected_senders:
                filtered_data.append(row)
        
        return filtered_data

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

    def apply_regex_filter(self):
        """Apply regex filter to highlight matching signals."""
        pattern = self.regex_input.text().strip()
        
        if not pattern:
            # If no pattern, reset all checkboxes to normal style
            for sender in self.sender_order:
                checkbox = self.sender_checkboxes[sender]
                checkbox.setObjectName("sender_checkbox")
                checkbox.style().unpolish(checkbox)
                checkbox.style().polish(checkbox)
            return
        
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            
            for sender in self.sender_order:
                checkbox = self.sender_checkboxes[sender]
                
                if regex.search(sender):
                    # Show matching signals
                    checkbox.show()
                    # checkbox.setObjectName("sender_checkbox_highlight")
                else:
                    # Hide non-matching signals
                    checkbox.hide()
                    # checkbox.setObjectName("sender_checkbox")
                
                # Force style refresh
                checkbox.style().unpolish(checkbox)
                checkbox.style().polish(checkbox)
                
        except re.error:
            # Invalid regex - reset all to normal style
            for sender in self.sender_order:
                checkbox = self.sender_checkboxes[sender]
                checkbox.setObjectName("sender_checkbox")
                checkbox.style().unpolish(checkbox)
                checkbox.style().polish(checkbox)

    def clear_regex_filter(self):
        """Clear the regex filter and reset highlighting."""
        self.regex_input.clear()
        for sender in self.sender_order:
            checkbox = self.sender_checkboxes[sender]
            checkbox.show()

        self.apply_regex_filter()

    def select_regex_matches(self):
        """Select only the signals that match the current regex pattern."""
        pattern = self.regex_input.text().strip()
        
        if not pattern:
            QMessageBox.warning(self, "Warning", "Please enter a regex pattern first!")
            return
        
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            
            # First deselect all
            self.deselect_all_checkboxes()
            
            # Then select only matching ones
            for sender in self.sender_order:
                if regex.search(sender):
                    self.sender_checkboxes[sender].setChecked(True)
                    
        except re.error as e:
            QMessageBox.warning(self, "Invalid Regex", f"Invalid regex pattern: {str(e)}")

    def recenter_window(self):
        """Recenter the window on screen after content changes."""
        # Get screen geometry
        screen = QDesktopWidget().screenGeometry()
        
        # Get window geometry
        window = self.geometry()
        
        # Calculate center position
        x = window.x()
        y = (screen.height() - window.height()) // 2
        
        # Move window to center
        self.move(x, y)

    def closeEvent(self, event):
        """Clean up resources when window closes."""
        # Clean up shared data
        if self.csv_data_id:
            shared_data_manager.remove_data(self.csv_data_id)

        # Stop running threads
        if self.parsing_thread and self.parsing_thread.isRunning():
            self.parsing_thread.quit()
            self.parsing_thread.wait()

        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.quit()
            self.processing_thread.wait()

        event.accept()