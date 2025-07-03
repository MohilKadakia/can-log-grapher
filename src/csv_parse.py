import pandas as pd
from datetime import datetime

def parse_csv(filepath):
    """
    Parses a CSV file with format: Timestamp, SignalName, Value
    Populates self.rows with dicts: [{'timestamp': ..., 'signal': ..., 'value': ...}, ...]
    """
    BASE_TIME = datetime(2025, 1, 1, 0, 0, 0)
    
    # Read entire file at once if memory allows, or use larger chunks
    df = pd.read_csv(filepath, names=["timestamp", "sender", "value"])
    
    # Vectorized conversion - much faster than apply()
    df["timestamp_int"] = df["timestamp"].apply(lambda x: int(x, 16))
    df["date_time"] = pd.to_datetime(BASE_TIME) + pd.to_timedelta(df["timestamp_int"], unit='ms')

    # Convert datetime to string immediately
    df["date_time"] = df["date_time"].dt.strftime('%Y-%m-%dT%H:%M:%S.%f')
    
    # Drop intermediate column
    df = df.drop("timestamp_int", axis=1)
    
    return df.to_dict(orient="records")

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