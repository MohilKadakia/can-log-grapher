import pandas as pd
from datetime import datetime

def parse_csv(filepath):
    """
    Parses a CSV file with format: Timestamp, SignalName, Value
    Populates self.rows with dicts: [{'date_time': ..., 'signal': ..., 'value': ...}, ...]
    Returns None if the file is empty or doesn't have the expected format.
    """
    BASE_TIME = datetime(2025, 1, 1, 0, 0, 0)
    
    try:
        # Read entire file at once if memory allows, or use larger chunks
        df = pd.read_csv(filepath, names=["timestamp", "sender", "value"])
        
        # Check if DataFrame is empty or missing required columns
        if df.empty:
            print(f"Warning: Empty CSV file: {filepath}")
            return None
            
        if "timestamp" not in df.columns or "sender" not in df.columns or "value" not in df.columns:
            print(f"Warning: CSV file missing required columns: {filepath}")
            return None
            
        # Check if there's at least one row of data
        if len(df) == 0:
            print(f"Warning: No data rows in CSV file: {filepath}")
            return None
        
        if '.' in str(df["timestamp"].iloc[0]):
            # If timestamp contains a decimal point, treat as float
            df["timestamp_int"] = df["timestamp"].astype(int)
        else:
            # Otherwise, assume it's in hex format (like "000000BB")
            df["timestamp_int"] = df["timestamp"].apply(lambda x: int(x, 16))

        df["date_time"] = pd.to_datetime(BASE_TIME) + pd.to_timedelta(df["timestamp_int"], unit='ms')

        # Convert datetime to string immediately
        df["date_time"] = df["date_time"].dt.strftime('%Y-%m-%dT%H:%M:%S.%f')
        
        # Drop intermediate column
        df = df.drop("timestamp", axis=1)
        df = df.drop("timestamp_int", axis=1)
        
        return df.to_dict(orient="records")
    except Exception as e:
        print(f"Error parsing CSV file {filepath}: {str(e)}")
        return None

def rows_to_csv_bytes(rows):
    """
    Convert a list of dicts (rows) to CSV bytes.
    """
    if not rows:
        return b""
    
    # Convert back to DataFrame for efficient CSV writing
    df = pd.DataFrame(rows)
    csv_data = df.to_csv(index=False).encode("utf-8")
    return csv_data