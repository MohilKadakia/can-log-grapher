# CAN Log Grapher

A PyQt5-based application for parsing and visualizing CAN bus log files with Grafana integration.

## Features

- Upload and parse TXT or CSV files containing raw or parsed CAN log data respectively
- Filter data by sender IDs using checkboxes
- Real-time data serving to Grafana via HTTP server
- Support for both single file and batch folder processing

## Installation

Read `docs/DeveloperGuide.md`

## Usage

For more information read `docs/SetupGuide.md`

The application (`main.py`) will:
1. Start a background HTTP server for Grafana integration
2. Open a GUI for file selection and data filtering
3. Allow you to upload CSV files or select entire folders

### Project Structure
```bash
can-log-grapher/
├── src/
│   ├── main.py               # Application entry point
│   │
│   ├── /app                  # PyQT Application & HTTP Server
│   ├──── /threading_scripts  # Important threading scripts
│   │
│   ├── /parsing              # Log parsing scripts
│   ├──── /csv_reading        # Scripts to parse CSV (parsed) logs
│   ├──── /raw_parsing        # Scripts to parse TXT (raw) logs
│   │
│   ├── /grafana/etc          # Grafana initilization files
│   └── docker-compose.yml    # Docker compose file
└── docs/                     # Documentation
```
## API Endpoints

The HTTP server provides endpoints for Grafana to consume the processed data. Read more in `API.md`