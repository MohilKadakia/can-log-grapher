import os
import logging
from PyQt5.QtCore import QThread, pyqtSignal

# Set up logging for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from app.threading_scripts.shared_data import shared_data_manager
from parsing.csv_reading.csv_parse import parse_csv, rows_to_csv_bytes
from parsing.raw_parsing.parse_tcu_data import parse_raw_folder, parse_raw_file

class CSVConversionThread(QThread):
    """Thread for turning raw hexadecimal data into structured data for parsing."""
    progress_update = pyqtSignal(str)  # Signal to update progress text
    conversion_complete = pyqtSignal(str)  # Signal with file paths
    
    def __init__(self, path):
        super().__init__()
        self.path = path
    
    def run(self):
        """Convert raw hexadecimal data into structured data for parsing."""
        logger.info(f"CSV conversion thread running - Processing: {self.path}")
        try:
            if os.path.isfile(self.path):
                logger.info(f"Processing single file: {self.path}")
                file_path = parse_raw_file(self.path)
                file_paths = [file_path]
                logger.info(f"Single file conversion complete. Output: {file_path}")
            else:
                logger.info(f"Processing folder: {self.path}")
                self.progress_update.emit(f"Processing folder {self.path}")
                file_paths = parse_raw_folder(self.path)
                logger.info(f"Folder conversion complete. Generated {len(file_paths)} CSV files")
            
            # Emit completion signal
            file_paths_str = ','.join(str(path) for path in file_paths)
            self.conversion_complete.emit(file_paths_str)
            logger.info("CSV conversion thread completed successfully")
            
        except Exception as e:
            logger.error(f"Error in CSV conversion thread: {e}")
            self.progress_update.emit(f"Conversion error: {e}")
            # Still emit completion to prevent hanging
            self.conversion_complete.emit("")

class CSVParsingThread(QThread):
    """Thread for parsing CSV files in the background."""
    progress_update = pyqtSignal(str)  # Signal to update progress text
    parsing_complete = pyqtSignal(str)  # Signal with data_id instead of data
    
    def __init__(self, file_list):
        super().__init__()
        self.file_list = file_list
        
    def run(self):
        """Parse CSV files in background thread."""
        logger.info(f"CSV parsing thread running - Processing {len(self.file_list)} files")
        csv_data = []
        total_files = len(self.file_list)
        processed_files = 0
        skipped_files = 0
        
        for i, file in enumerate(self.file_list):
            logger.info(f"Processing file {i+1}/{total_files}: {os.path.basename(file)}")
            self.progress_update.emit(f"Processing file {i+1} of {total_files}: {os.path.basename(file)}")
            
            try:
                file_data = parse_csv(file)
                
                # Skip files that couldn't be parsed
                if file_data is None:
                    logger.warning(f"Skipping invalid file: {os.path.basename(file)}")
                    self.progress_update.emit(f"Skipping invalid file: {os.path.basename(file)}")
                    skipped_files += 1
                    continue
                    
                csv_data.extend(file_data)
                processed_files += 1
                logger.info(f"Successfully parsed {os.path.basename(file)} - {len(file_data)} rows")
                
            except Exception as e:
                logger.error(f"Error parsing file {file}: {e}")
                skipped_files += 1
                continue

        logger.info(f"Parsing complete - Processed: {processed_files}, Skipped: {skipped_files}, Total rows: {len(csv_data)}")
        
        # Check if we have any data after parsing
        if not csv_data:
            logger.warning("No valid data found in any of the files")
            self.progress_update.emit("No valid data found in any of the files")
            # Return empty data ID to signal no data
            self.parsing_complete.emit("")
            return
        
        # Store data in shared manager and emit the ID
        logger.info(f"Storing {len(csv_data)} rows in shared data manager")
        data_id = shared_data_manager.store_data(csv_data)
        logger.info(f"Data stored with ID: {data_id}")
        self.parsing_complete.emit(data_id)
        logger.info("CSV parsing thread completed successfully")

class CSVProcessingThread(QThread):
    """Thread for processing CSV data to bytes in the background."""
    progress_update = pyqtSignal(str)  # Signal to update progress text
    processing_complete = pyqtSignal(bytes)  # Signal when processing is done
    
    def __init__(self, data_id: str, selected_senders: set):
        super().__init__()
        self.data_id = data_id
        self.selected_senders = selected_senders
        
    def run(self):
        """Process CSV data to bytes in background thread."""
        logger.info(f"CSV processing thread running - Data ID: {self.data_id}")
        
        try:
            # Get data from shared manager
            logger.info("Retrieving data from shared manager")
            csv_data = shared_data_manager.get_data(self.data_id)
            if not csv_data:
                logger.error("No data found in shared manager")
                self.progress_update.emit("Error: No data found")
                return
            
            logger.info(f"Retrieved {len(csv_data)} rows from shared manager")
            
            # Filter data based on selected senders
            logger.info(f"Filtering data for {len(self.selected_senders)} selected senders")
            filtered_data = []
            for row in csv_data:
                if 'sender' in row and row['sender'].strip() in self.selected_senders:
                    filtered_data.append(row)
            
            logger.info(f"Filtered data: {len(filtered_data)} rows match selected senders")
            self.progress_update.emit(f"Processing {len(filtered_data)} rows for server update...")
            
            # Convert to CSV bytes
            logger.info("Converting filtered data to CSV bytes")
            csv_bytes = rows_to_csv_bytes(filtered_data)
            logger.info(f"Generated {len(csv_bytes)} bytes of CSV data")
            
            # Emit completion signal
            self.processing_complete.emit(csv_bytes)
            logger.info("CSV processing thread completed successfully")
            
        except Exception as e:
            logger.error(f"Error in CSV processing thread: {e}")
            self.progress_update.emit(f"Processing error: {e}")
            # Don't emit completion signal on error to prevent issues