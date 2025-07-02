import pandas as pd
from datetime import timedelta, datetime
from io import StringIO
import csv

def parse_csv(filepath):
    """
    Parses a CSV file with format: Timestamp, SignalName, Value
    Populates self.rows with dicts: [{'timestamp': ..., 'signal': ..., 'value': ...}, ...]
    """
    rows = []
    BASE_TIME = datetime(2025, 1, 1, 0, 0, 0)
    for df in pd.read_csv(filepath, chunksize=100_000, names=["timestamp", "sender", "value"]):
        df["date_time"] = df["timestamp"].apply(lambda x: BASE_TIME + timedelta(milliseconds=int(x, 16)))
        rows.extend(df.to_dict(orient="records"))
    return rows

def rows_to_csv_bytes(rows):
    """
    Convert a list of dicts (rows) to CSV bytes.
    Handles pandas Timestamp in 'date_time' by converting to ISO string.
    """
    if not rows:
        return b""

    # Ensure all keys are present in every row
    fieldnames = list(rows[0].keys())

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        row_copy = row.copy()
        # Convert pandas Timestamp to string if needed
        if "date_time" in row_copy and hasattr(row_copy["date_time"], "isoformat"):
            row_copy["date_time"] = row_copy["date_time"].isoformat()
        writer.writerow(row_copy)
    return output.getvalue().encode("utf-8")