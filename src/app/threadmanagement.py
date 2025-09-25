import os
import sys
import logging
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal

# Set up logging for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from app.server import update_data
from app.threading_scripts.shared_data import shared_data_manager
from app.threading_scripts.processing_threads import CSVConversionThread, CSVParsingThread, CSVProcessingThread


class ThreadManager(QObject):
    """Class to manage all thread operations for the CAN Log Uploader."""
    
    # Define signals for GUI updates
    progress_update = pyqtSignal(str)
    parsing_completed = pyqtSignal(str)
    processing_completed = pyqtSignal(bytes)
    show_loading = pyqtSignal(str, bool)
    hide_loading = pyqtSignal(bool)
    update_ui = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        logger.info("Initializing ThreadManager")
        self.csv_data_id = None
        # Thread instances for processing
        self.conversion_thread = None
        self.parsing_thread = None
        self.processing_thread = None
        logger.info("ThreadManager initialized successfully")
    
    def process_raw_path(self, path):
        """Process a raw path using threading."""
        logger.info(f"Processing raw path: {path}")
        self.show_loading.emit("Processing raw path...", False)
        self.progress_update.emit("Processing raw path...")
        
        # Create and start conversion thread
        logger.info("Creating CSV conversion thread")
        self.conversion_thread = CSVConversionThread(path)
        self.conversion_thread.progress_update.connect(self.on_conversion_progress)
        self.conversion_thread.conversion_complete.connect(self.on_conversion_complete)
        self.conversion_thread.start()
        logger.info("CSV conversion thread created and started")

    def on_conversion_progress(self, message):
        """Update progress text during conversion."""
        self.progress_update.emit(message)

    def on_conversion_complete(self, file_paths):
        """Handle completion of CSV conversion."""
        logger.info(f"CSV conversion complete. File paths: {file_paths}")
        file_paths = file_paths.split(',')
        logger.info(f"Starting CSV parsing for {len(file_paths)} files")
        
        self.show_loading.emit("Processing...", False)
        self.parsing_thread = CSVParsingThread(file_paths)
        self.parsing_thread.progress_update.connect(self.on_parsing_progress)
        self.parsing_thread.parsing_complete.connect(self.on_parsing_complete)
        self.parsing_thread.start()
        logger.info("CSV parsing thread started")

    def on_parsing_progress(self, message):
        """Update progress text during parsing."""
        self.progress_update.emit(message)

    def on_parsing_complete(self, data_id: str):
        """Handle completion of CSV parsing."""
        logger.info(f"CSV parsing complete. Data ID: {data_id}")
        self.delete_old_data()
        
        # Check if we have a valid data_id
        if not data_id:
            logger.warning("No valid data found in any of the files")
            self.hide_loading.emit(True)
            self.progress_update.emit("No valid data found in any of the files")
            # Still emit the empty data_id to notify listeners
            self.parsing_completed.emit("")
            return
            
        self.csv_data_id = data_id
        logger.info(f"Data ID set: {data_id}")
        self.hide_loading.emit(True)
        self.parsing_completed.emit(data_id)
        logger.info("Parsing completed signal emitted")

    def on_processing_progress(self, message):
        """Update progress text during processing."""
        self.progress_update.emit(message)
    
    def on_processing_complete(self, csv_bytes):
        """Handle completion of CSV processing."""
        try:
            self.hide_loading.emit(True)
            update_data(csv_bytes.decode('utf-8'))
            self.processing_completed.emit(csv_bytes)
            logger.info("Server data updated successfully")
        except Exception as e:
            logger.error(f"Error in on_processing_complete: {e}")
            self.hide_loading.emit(True)
            # Still emit the signal to prevent hanging
            self.processing_completed.emit(csv_bytes)

    def update_server_filtered(self, selected_senders):
        """Update server with filtered data using threading."""
        logger.info(f"Updating server with filtered data. Selected senders: {selected_senders}")
        
        if not selected_senders:
            logger.warning("No senders selected for processing")
            return False
        
        # Check if we have valid data
        if not self.csv_data_id:
            logger.error("No valid data available to process")
            self.progress_update.emit("No valid data available to process")
            return False
        
        logger.info(f"Starting server update processing for data ID: {self.csv_data_id}")
        self.show_loading.emit("Processing data for server...", True)
        
        # Create and start processing thread
        logger.info("Creating CSV processing thread")
        self.processing_thread = CSVProcessingThread(self.csv_data_id, selected_senders)
        self.processing_thread.progress_update.connect(self.on_processing_progress)
        self.processing_thread.processing_complete.connect(self.on_processing_complete)
        self.processing_thread.start()
        logger.info("CSV processing thread started")
        return True

    def process_files(self, file_list):
        """Process CSV files using threading."""
        logger.info(f"Processing {len(file_list)} CSV files")
        
        if not file_list:
            logger.warning("No files provided for processing")
            return
        
        self.show_loading.emit("Processing...", False)
        self.delete_old_data()
        
        # Create and start parsing thread
        logger.info("Creating CSV parsing thread")
        self.parsing_thread = CSVParsingThread(file_list)
        self.parsing_thread.progress_update.connect(self.on_parsing_progress)
        self.parsing_thread.parsing_complete.connect(self.on_parsing_complete)
        self.parsing_thread.start()
        logger.info("CSV parsing thread started")
    
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
