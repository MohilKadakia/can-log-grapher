import os
from PyQt5.QtCore import QThread, pyqtSignal
from app.shared_data import shared_data_manager
from app.csv_parse import parse_csv, rows_to_csv_bytes

class CSVParsingThread(QThread):
    """Thread for parsing CSV files in the background."""
    progress_update = pyqtSignal(str)  # Signal to update progress text
    parsing_complete = pyqtSignal(str)  # Signal with data_id instead of data
    
    def __init__(self, file_list):
        super().__init__()
        self.file_list = file_list
        
    def run(self):
        """Parse CSV files in background thread."""
        csv_data = []
        total_files = len(self.file_list)
        
        for i, file in enumerate(self.file_list):
            print(f"Processing {file}")
            self.progress_update.emit(f"Processing file {i+1} of {total_files}: {os.path.basename(file)}")
            file_data = parse_csv(file)
            csv_data.extend(file_data)

        print(f"Total rows loaded: {len(csv_data)}")
        
        # Store data in shared manager and emit the ID
        data_id = shared_data_manager.store_data(csv_data)
        self.parsing_complete.emit(data_id)

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
        # Get data from shared manager
        csv_data = shared_data_manager.get_data(self.data_id)
        if not csv_data:
            self.progress_update.emit("Error: No data found")
            return
        
        # Filter data based on selected senders
        filtered_data = []
        for row in csv_data:
            if 'sender' in row and row['sender'].strip() in self.selected_senders:
                filtered_data.append(row)
        
        self.progress_update.emit(f"Processing {len(filtered_data)} rows for server update...")
        csv_bytes = rows_to_csv_bytes(filtered_data)
        self.processing_complete.emit(csv_bytes)