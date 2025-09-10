import os
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal

from app.server import update_data
from app.threading_scripts.processing_threads import CSVParsingThread, CSVProcessingThread, CSVConversionThread
from app.threading_scripts.shared_data import shared_data_manager


class ThreadManager(QObject):
    """Class to manage all thread operations for the CAN Log Uploader."""
    
    # Define signals for GUI updates
    progress_update = pyqtSignal(str)
    conversion_completed = pyqtSignal(str)
    parsing_completed = pyqtSignal(str)
    processing_completed = pyqtSignal(bytes)
    show_loading = pyqtSignal(str, bool)
    hide_loading = pyqtSignal(bool)
    update_ui = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.csv_data_id = None
        self.conversion_thread = None
        self.parsing_thread = None
        self.processing_thread = None
    
    def process_raw_path(self, path):
        """Process a raw path."""
        self.show_loading.emit("Processing raw path...", False)
        self.conversion_thread = CSVConversionThread(path)
        self.conversion_thread.progress_update.connect(self.on_conversion_progress)
        self.conversion_thread.conversion_complete.connect(self.on_conversion_complete)
        self.conversion_thread.start()

    def on_conversion_progress(self, message):
        """Update progress text during conversion."""
        self.progress_update.emit(message)

    def on_conversion_complete(self, file_paths):
        """Handle completion of CSV conversion."""
        file_paths = file_paths.split(',')
        self.show_loading.emit("Processing...", False)
        self.parsing_thread = CSVParsingThread(file_paths)
        self.parsing_thread.progress_update.connect(self.on_parsing_progress)
        self.parsing_thread.parsing_complete.connect(self.on_parsing_complete)
        self.parsing_thread.start()

    def on_parsing_progress(self, message):
        """Update progress text during parsing."""
        self.progress_update.emit(message)

    def on_parsing_complete(self, data_id: str):
        """Handle completion of CSV parsing."""
        self.delete_old_data()
        
        # Check if we have a valid data_id
        if not data_id:
            self.hide_loading.emit(True)
            self.progress_update.emit("No valid data found in any of the files")
            # Still emit the empty data_id to notify listeners
            self.parsing_completed.emit("")
            return
            
        self.csv_data_id = data_id
        self.hide_loading.emit(True)
        self.parsing_completed.emit(data_id)

    def on_processing_complete(self, csv_bytes):
        """Handle completion of CSV processing."""
        self.hide_loading.emit(True)
        update_data(csv_bytes.decode('utf-8'))
        self.processing_completed.emit(csv_bytes)

    def update_server_filtered(self, selected_senders):
        """Update server with filtered data based on selected senders."""
        if not selected_senders:
            return False
        
        # Check if we have valid data
        if not self.csv_data_id:
            self.progress_update.emit("No valid data available to process")
            return False
            
        # Show processing screen
        self.show_loading.emit("Processing data for server...", True)
        
        # Create and start processing thread with data ID
        self.processing_thread = CSVProcessingThread(self.csv_data_id, selected_senders)
        self.processing_thread.progress_update.connect(self.on_parsing_progress)
        self.processing_thread.processing_complete.connect(self.on_processing_complete)
        self.processing_thread.start()
        return True

    def process_files(self, file_list):
        """Start CSV parsing in a separate thread."""
        if not file_list:
            return
            
        # Show loading screen
        self.show_loading.emit("Processing...", False)
        self.delete_old_data()
        
        # Create and start parsing thread
        self.parsing_thread = CSVParsingThread(file_list)
        self.parsing_thread.progress_update.connect(self.on_parsing_progress)
        self.parsing_thread.parsing_complete.connect(self.on_parsing_complete)
        self.parsing_thread.start()
    
    def get_data(self):
        """Get data from shared manager."""
        if not self.csv_data_id:
            return None
        return shared_data_manager.get_data(self.csv_data_id)
    
    def delete_old_data(self):
        """Delete old data from shared manager."""
        if self.csv_data_id:
            shared_data_manager.remove_data(self.csv_data_id)
            self.csv_data_id = None
    
    def cleanup(self):
        """Clean up resources when window closes."""
        # Clean up shared data
        self.delete_old_data()

        # Stop running threads
        if self.parsing_thread and self.parsing_thread.isRunning():
            self.parsing_thread.quit()
            self.parsing_thread.wait()

        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.quit()
            self.processing_thread.wait()
            
        if self.conversion_thread and self.conversion_thread.isRunning():
            self.conversion_thread.quit()
            self.conversion_thread.wait()
