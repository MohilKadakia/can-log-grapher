from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import WriteOptions
from time import sleep
from datetime import datetime, timezone, timedelta

from config import INFLUX_URL, INFLUX_BUCKET, INFLUX_TOKEN, INFLUX_ORG

token = INFLUX_TOKEN
org = INFLUX_ORG
url = INFLUX_URL
bucket = INFLUX_BUCKET

write_client = InfluxDBClient(url=url, token=token, org=org)
write_api = write_client.write_api(write_options=WriteOptions(batch_size=5000))

def write_rows(rows):
    """
    Accepts a list of dicts with keys: 'timestamp', 'signal', 'value'.
    Writes all rows to InfluxDB in a batch, mapping hex timestamps to real times.
    """
    drop_and_recreate_bucket()
    sleep(1)
    points = []
    # Use the current UTC time as the base time
    base_time = datetime.now(timezone.utc)
    for row in rows:
        try:
            # Convert hex timestamp to int (counter)
            hex_ts = row.get("timestamp", "0")
            ts_offset = int(hex_ts, 16)
            # Add offset as milliseconds to base_time
            point_time = base_time + timedelta(milliseconds=ts_offset)
            point = (
                Point(row.get("signal", "Unknown"))
                .tag("sender", row.get("signal", "Unknown"))
                .field("value", float(row.get("value", 0)))
                .time(point_time, WritePrecision.MS)
            )
            points.append(point)
        except Exception as e:
            print(f"Error creating point: {e}, row: {row}")
    if points:
        write_api.write(bucket=bucket, org=INFLUX_ORG, record=points)
        print(f"Wrote {len(points)} points to InfluxDB")
        sleep(5)  # Ensure all points are flushed before closing
        write_api.flush()

def drop_and_recreate_bucket():
    """
    Drops and recreates the InfluxDB bucket for a fast, complete flush.
    """
    buckets_api = write_client.buckets_api()
    bucket_obj = buckets_api.find_bucket_by_name(bucket)
    if bucket_obj:
        buckets_api.delete_bucket(bucket_obj)
        print(f"Bucket '{bucket}' deleted.")
    buckets_api.create_bucket(bucket_name=bucket, org=org)
    print(f"Bucket '{bucket}' recreated.")