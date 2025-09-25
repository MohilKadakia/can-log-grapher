# CAN Log Grapher - User Guide

## Quick Start

1. **Install Docker Desktop** (Required for dashboard features)
   - Download from: https://www.docker.com/products/docker-desktop
   - Install and start Docker Desktop

2. **Run the Application**
   - Double-click `CAN-Log-Grapher.exe`
   - The app will automatically check for Docker and start the dashboard (no clicking required)
   - The dashboard will open automatically in your browser

3. **Using the Dashboard**
   - The dashboard opens automatically at: http://localhost:3001
   - Login with:
     - Username: `uwfe`
     - Password: `uwfepassword`

## Features

- Upload CAN log files (CSV or TXT format)
- Filter and select specific signals
- Automatic Grafana dashboard integration
- Cloud upload and access capabilities

## Troubleshooting

**"Docker Required" message:**
- Install Docker Desktop and make sure it's running
- Restart the application after installing Docker

**Dashboard not opening:**
- Check that Docker Desktop is running
- Wait a few seconds for Grafana to start up
- Try accessing http://localhost:3001 manually
- Make sure you're logged in with username: `uwfe` and password: `uwfepassword`

**Application won't start:**
- Make sure all files are in the same folder as the .exe
- Run as administrator if needed
- Check that antivirus isn't blocking the application

## Files Included

- `CAN-Log-Grapher.exe` - Main application
- `docker-compose.yml` - Grafana configuration
- `grafana/` - Dashboard configuration files
- `public/` - Application logo files
- `README.md` - This file

## Support

If you encounter issues, please check that:
1. Docker Desktop is installed and running
2. All files are in the same directory as the .exe
3. You have sufficient permissions to run the application
