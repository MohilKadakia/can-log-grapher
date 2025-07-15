from PyQt5.QtWidgets import QDesktopWidget
from PyQt5.QtCore import QObject, pyqtSignal
import re

class UITransitionManager(QObject):
    """Manages UI transitions and visual effects for the CAN Log Uploader."""
    
    def __init__(self, parent):
        """Initialize with reference to parent widget."""
        super().__init__()
        self.parent = parent
    
    def show_loading_screen(self, message="Processing...", disable_sender_controls=False):
        """Show the loading screen with customizable message and button states."""
        self.parent.loading_frame.show()
        self.parent.sender_frame.hide()
        self.parent.update_btn.hide()
        self.parent.TXT_folder_btn.setEnabled(False)
        self.parent.TXT_file_btn.setEnabled(False)
        self.parent.CSV_folder_btn.setEnabled(False)
        self.parent.CSV_file_btn.setEnabled(False)
        self.parent.loading_label.setText(message)
        self.parent.progress_text.setText("")
        
        if disable_sender_controls:
            self.parent.update_btn.setEnabled(False)
            self.parent.select_all_btn.setEnabled(False)
            self.parent.deselect_all_btn.setEnabled(False)
            self.parent.select_regex_btn.setEnabled(False)
            self.parent.regex_input.setEnabled(False)
            self.parent.regex_clear_btn.setEnabled(False)

    def hide_loading_screen(self, enable_sender_controls=True):
        """Hide the loading screen and re-enable buttons."""
        self.parent.loading_frame.hide()
        self.parent.TXT_file_btn.setEnabled(True)
        self.parent.TXT_folder_btn.setEnabled(True)
        self.parent.CSV_file_btn.setEnabled(True)
        self.parent.CSV_folder_btn.setEnabled(True)
        if enable_sender_controls:
            self.parent.update_btn.setEnabled(True)
            self.parent.select_all_btn.setEnabled(True)
            self.parent.deselect_all_btn.setEnabled(True)
            self.parent.select_regex_btn.setEnabled(True)
            self.parent.regex_input.setEnabled(True)
            self.parent.regex_clear_btn.setEnabled(True)
    
    def update_progress_text(self, message):
        """Update progress text."""
        self.parent.progress_text.setText(message)
    
    def update_checkbox_highlight(self, index):
        """Update the visual highlight for the selected checkbox."""
        # Clear previous highlights
        for i, sender in enumerate(self.parent.sender_order):
            checkbox = self.parent.sender_checkboxes[sender]
            if i == index:
                # Highlight the selected checkbox
                checkbox.setObjectName("sender_checkbox_highlighted")
            else:
                # Reset other checkboxes to default style
                checkbox.setObjectName("sender_checkbox")
        
            # Force style refresh
            checkbox.style().unpolish(checkbox)
            checkbox.style().polish(checkbox)
    
    def apply_regex_filter(self):
        """Apply regex filter to highlight matching signals."""
        pattern = self.parent.regex_input.text().strip()
        
        if not pattern:
            # If no pattern, reset all checkboxes to normal style
            for sender in self.parent.sender_order:
                checkbox = self.parent.sender_checkboxes[sender]
                checkbox.setObjectName("sender_checkbox")
                checkbox.style().unpolish(checkbox)
                checkbox.style().polish(checkbox)
            return
        
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            
            for sender in self.parent.sender_order:
                checkbox = self.parent.sender_checkboxes[sender]
                
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
            for sender in self.parent.sender_order:
                checkbox = self.parent.sender_checkboxes[sender]
                checkbox.setObjectName("sender_checkbox")
                checkbox.style().unpolish(checkbox)
                checkbox.style().polish(checkbox)

    def clear_regex_filter(self):
        """Clear the regex filter and reset highlighting."""
        self.parent.regex_input.clear()
        for sender in self.parent.sender_order:
            checkbox = self.parent.sender_checkboxes[sender]
            checkbox.show()

        self.apply_regex_filter()
    
    def recenter_window(self):
        """Recenter the window on screen after content changes."""
        # Get screen geometry
        screen = QDesktopWidget().screenGeometry()
        
        # Get window geometry
        window = self.parent.geometry()
        
        # Calculate center position
        x = window.x()
        y = (screen.height() - window.height()) // 2
        
        # Move window to center
        self.parent.move(x, y)
    
    def show_sender_frame(self):
        """Show the sender frame and update button."""
        self.parent.sender_frame.show()
        self.parent.update_btn.show()
