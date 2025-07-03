# Developer Guide

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