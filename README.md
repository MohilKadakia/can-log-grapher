# CAN Log Grapher

A PyQt5-based application for parsing and visualizing CAN bus log files with Grafana integration.

## Features

- Upload and parse CSV files containing CAN log data
- Filter data by sender IDs using checkboxes
- Real-time data serving to Grafana via HTTP server
- Support for both single file and batch folder processing

## Installation

Read `docs/DeveloperGuide.md`

## Usage

The application (`main.py`) will:
1. Start a background HTTP server for Grafana integration
2. Open a GUI for file selection and data filtering
3. Allow you to upload CSV files or select entire folders

## Project Structure

- `src/` - Main application code
  - `main.py` - PyQt5 GUI application
  - `server.py` - HTTP server for Grafana integration
  - `csv_parse.py` - CSV parsing utilities
- `docs/` - Documentation files

## API Endpoints

The HTTP server provides endpoints for Grafana to consume the processed data. Read more in `API.md`