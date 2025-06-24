import csv

class CANLogParser:
    def __init__(self, filepath):
        self.filepath = filepath
        self.rows = []

    def parse(self):
        """
        Parses a CSV file with format: CAN_ID, SignalName, Value
        Populates self.rows with dicts: [{'timestamp': ..., 'signal': ..., 'value': ...}, ...]
        """
        self.rows = []
        with open(self.filepath, newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) != 3:
                    continue  # skip malformed rows
                timestamp, signal, value = [item.strip() for item in row]
                try:
                    value = float(value)
                except ValueError:
                    continue  # skip rows with invalid float
                self.rows.append({'timestamp': timestamp, 'signal': signal, 'value': value})
        return self.rows