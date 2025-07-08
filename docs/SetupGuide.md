# User Guide

## TLDR Setup

### Prerequisites

- Docker
- Git
- Python 3.8 or higher

### Commands
```bash
git clone <repository-url>
cd can-log-grapher
cd ./src 
# At this point you should be in the src folder of the repository

########################
# Optional: using venv
python -m venv venv

# Windows
.\venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

########################
# Running the Application
# In the /src folder
pip install -r requirements.txt

# Start the application
python main.py

# Start the Grafana Dashboard
docker-compose up -d 
# The dashboard can be accessed from localhost:3000
# Username: uwfe
# Password: uwfepassword
```

## Getting Started

### Requirements
To run this application you will need:

- Docker
- Python 3.8 or higher
- Git

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

### Accessing the Dashboard

The main.py file should open up an application for you to upload parsed CAN files to.

To access a graph of this, you must run the docker-compose command (as shown above in step 5 of the installation), and go to `localhost:3000`. It will prompt you to sign in, the sign in information is:

**Username:** uwfe 

**Password:** uwfepassword

From the page you can access a Grafana dashboard that will graph the datapoints.

### Deactivation Steps
Docker doesn't close when you close the terminal. To ensure that the container shuts down you must run this command in the `src` folder:

**Shutdown Grafana Container**
```bash
docker-compose down
```

## Uploading Files

### Single File Upload
Use the file selection dialog to choose a CSV/TXT file containing CAN log data.

### Batch Upload
Select a folder containing multiple CSV/TXT files for batch processing.

## Data Filtering

Use the checkbox interface to filter data by CAN sender IDs.

You can also use the Regex filter textbox above the checkboxes. After typing in your Regex string, click the "Select Filtered" button to select the appropriate signals.

## Grafana Integration

The application serves data via HTTP endpoints that can be consumed by Grafana dashboards.