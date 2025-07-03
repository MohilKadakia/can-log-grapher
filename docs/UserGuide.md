# User Guide

## Getting Started

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd can-log-grapher
   ```

2. **Create and activate virtual environment**
   ```bash
   # Using venv
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   # Windows
   pip install -r .\src\requirements.txt
   
   # Linux/macOS
   pip install -r ./src/requirements.txt
   ```

4. **Run the application**
   ```bash
   # Start the GUI application
   python src/main.py
   ```

5. **Starting the Grafana Dashboard**
   ```bash
   docker-compose up -d
   ```

### Deactivation Steps
Docker doesn't close when you close the terminal. To ensure that the container shuts down you must run this command in the `src` folder:

**Shutdown Grafana Container**
```bash
docker-compose down
```

## Uploading Files

### Single File Upload
Use the file selection dialog to choose a CSV file containing CAN log data.

### Batch Upload
Select a folder containing multiple CSV files for batch processing.

## Data Filtering

Use the checkbox interface to filter data by CAN sender IDs.

## Grafana Integration

The application serves data via HTTP endpoints that can be consumed by Grafana dashboards.