# CAN Log CSV Parser

This folder contains code for parsing "parsed" CAN log CSV files and uploading the data to an InfluxDB database. It is designed to work with CSV files where each row represents a CAN message, for example:

````
00000077, VCU_wheelSpeed_RL, 0.0  
00000077, VCU_wheelSpeed_RR, 0.0  
0000009A, RLSpeedKPH, 0.0  
0000009A, RRSpeedKPH, 0.0  
0000009A, FLSpeedKPH, 0.0  
0000009A, FRSpeedKPH, 0.0  
0000009A, TCTorqueMax, 3.392  
````

## Features

- **CSV Parsing:** Reads and parses CAN log data from a CSV file.
- **InfluxDB Integration:**  
  - Deletes (drops) the target InfluxDB bucket and recreates it, clearing all previous data.
  - Uploads all parsed CSV data to the specified InfluxDB bucket.

## Usage

1. **Prepare your CSV file**  
   Ensure your CSV file is formatted as shown above, with each row containing a timestamp, signal name, and value.

2. **Configure InfluxDB Connection**
   Update the code or configuration (in `./app/config.py`) with your InfluxDB URL, token, organization, and bucket name.

3. **Run the Parser**
   Execute the script to parse the CSV and upload the data to InfluxDB.  
   (See the main script or function for usage details.)

## Requirements

- Python 3.x
- `influxdb-client` Python package

Install dependencies with:
````
pip install -r requirements.txt
````

## Notes

- **Data Loss Warning:** The script will delete all data in the specified InfluxDB bucket before uploading new data.
- Designed for use with already-parsed CAN log CSVs, not raw CAN log files.

---

For more details, see the source code in this folder.
