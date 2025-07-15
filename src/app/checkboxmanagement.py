import re
from PyQt5.QtWidgets import QCheckBox, QMessageBox
from PyQt5.QtCore import Qt, QObject

class CheckboxManager(QObject):
    """Manages checkbox creation and interaction for the CAN Log Uploader."""
    
    def __init__(self, parent):
        """Initialize with reference to parent widget."""
        super().__init__()
        self.parent = parent
        self.last_clicked_index = None
    
    def create_sender_checkboxes(self):
        """Create checkboxes for each unique sender in the CSV data."""
        # Clear existing checkboxes
        for checkbox in self.parent.sender_checkboxes.values():
            checkbox.deleteLater()
        self.parent.sender_checkboxes.clear()
        
        # Get data from thread manager
        csv_data = self.parent.thread_manager.get_data()
        if not csv_data:
            return
        
        # Get unique senders
        senders = set()
        for row in csv_data:
            if 'sender' in row:
                sender = row['sender'].strip()
                senders.add(sender)
        
        # Create ordered list with proper sorting (case-insensitive, numeric-aware)
        self.parent.sender_order = sorted(senders, key=self.sort_key)
        self.last_clicked_index = None
        
        # Create checkboxes for each sender
        for i, sender in enumerate(self.parent.sender_order):
            checkbox = QCheckBox(f"{sender}")
            checkbox.setChecked(False)  # Default to unchecked
            checkbox.setObjectName("sender_checkbox")
            
            # Connect to custom click handler that preserves normal behavior
            checkbox.mousePressEvent = lambda event, idx=i, cb=checkbox: self.checkbox_mouse_press(event, idx, cb)
            
            self.parent.sender_checkboxes[sender] = checkbox
            self.parent.checkbox_layout.addWidget(checkbox)
        
        # Show the sender frame and update button if we have data
        if senders:
            self.parent.ui_transitions.show_sender_frame()
    
    def sort_key(self, sender):
        """Sort key function for ordering senders."""
        # Convert to lowercase for case-insensitive sorting
        # Split into parts to handle numeric sorting properly
        parts = re.split(r'(\d+)', sender.lower())
        # Convert numeric parts to integers for proper numeric sorting
        result = []
        for part in parts:
            if part.isdigit():
                result.append(int(part))
            else:
                result.append(part)
        return result

    def checkbox_mouse_press(self, event, index, checkbox):
        """Handle checkbox mouse press with shift-click range selection."""
        # Update visual highlight
        self.parent.ui_transitions.update_checkbox_highlight(index)
        
        # Check if shift is held and we have a previous click
        if event.modifiers() == Qt.ShiftModifier and self.last_clicked_index is not None:
            # Determine range
            start_idx = min(self.last_clicked_index, index)
            end_idx = max(self.last_clicked_index, index)
            
            # Get the target state from the last clicked checkbox
            last_sender = self.parent.sender_order[self.last_clicked_index]
            target_state = self.parent.sender_checkboxes[last_sender].isChecked()
            
            # Apply the state to all checkboxes in range
            for i in range(start_idx, end_idx + 1):
                sender = self.parent.sender_order[i]
                self.parent.sender_checkboxes[sender].setChecked(target_state)
            
            # Don't update last_clicked_index for shift-clicks to allow chaining
        else:
            # Normal click - let Qt handle it normally
            QCheckBox.mousePressEvent(checkbox, event)
            # Update last clicked index after the normal click is processed
            self.last_clicked_index = index

    def select_all_checkboxes(self):
        """Select all sender checkboxes."""
        for checkbox in self.parent.sender_checkboxes.values():
            checkbox.setChecked(True)

    def deselect_all_checkboxes(self):
        """Deselect all sender checkboxes."""
        for checkbox in self.parent.sender_checkboxes.values():
            checkbox.setChecked(False)

    def select_regex_matches(self):
        """Select only the signals that match the current regex pattern."""
        pattern = self.parent.regex_input.text().strip()
        
        if not pattern:
            QMessageBox.warning(self.parent, "Warning", "Please enter a regex pattern first!")
            return
        
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            
            # First deselect all
            self.deselect_all_checkboxes()
            
            # Then select only matching ones
            for sender in self.parent.sender_order:
                if regex.search(sender):
                    self.parent.sender_checkboxes[sender].setChecked(True)
                    
        except re.error as e:
            QMessageBox.warning(self.parent, "Invalid Regex", f"Invalid regex pattern: {str(e)}")
    
    def get_filtered_data(self):
        """Get CSV data filtered by selected senders."""
        csv_data = self.parent.thread_manager.get_data()
        if not csv_data:
            return []
        
        selected_senders = set()
        for sender, checkbox in self.parent.sender_checkboxes.items():
            if checkbox.isChecked():
                selected_senders.add(sender)
        
        filtered_data = []
        for row in csv_data:
            if 'sender' in row and row['sender'].strip() in selected_senders:
                filtered_data.append(row)
        
        return filtered_data
        
    def get_selected_senders(self):
        """Get set of selected sender names."""
        selected_senders = set()
        for sender, checkbox in self.parent.sender_checkboxes.items():
            if checkbox.isChecked():
                selected_senders.add(sender)
        return selected_senders
