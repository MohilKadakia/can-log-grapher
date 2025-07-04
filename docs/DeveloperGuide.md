# Developer Guide

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
# At this point you should be in the /src folder of the repository

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

########################
# Shutting down
# Close the app closing the window
# Turn off the Grafana dashboard by running:
docker-compose down
```

## Architecture Overview

The application consists of three main components:

1. **GUI Application** ([`src/main.py`](../src/main.py))
   - PyQt5-based interface
   - File selection and data filtering

2. **HTTP Server** ([`src/server.py`](../src/server.py))
   - Background server for Grafana integration
   - Data serving (CSV) endpoints

3. **CSV Parser** ([`src/csv_parse.py`](../src/csv_parse.py))
   - Handles CSV file parsing and processing

## Setup Development Environment

### Prerequisites

- Docker
- Git
- Python 3.8 or higher

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd can-log-grapher
   cd ./src
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
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   # Start the application
   python main.py
   ```

5. Starting the Grafana Dashboard
   ```bash
   docker-compose up -d
   ```

### Accessing the Dashboard

The main.py file should open up an application for you to upload parsed CAN files to.

To access a graph of this, you must run the docker-compose command, and go to `localhost:3000`. From the page you can access a Grafana dashboard that will graph the datapoints given.

### Deactivation Steps
Docker doesn't close when you close the terminal. To ensure that the container shuts down you must run this command in the `src` folder:

```bash
docker-compose down
```

### Project Structure
```
can-log-grapher/
├── src/
│   ├── main.py          # GUI application entry point
│   ├── server.py        # HTTP server for Grafana
│   ├── requirements.txt # Python dependencies
│   └── csv_parse.py     # CSV parsing utilities
└── docs/                # Documentation
```