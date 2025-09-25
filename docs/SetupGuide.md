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
# The dashboard can be accessed from localhost:3001
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

To access a graph of this, you must run the docker-compose command (as shown above in step 5 of the installation), and go to `localhost:3001`. It will prompt you to sign in, the sign in information is:

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

## Running the Application from Terminal

### Method 1: Direct Python Execution

1. **Navigate to the source directory**
   ```bash
   cd can-log-grapher/src
   ```

2. **Install dependencies** (if not already installed)
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

### Method 2: From Project Root

If you're in the project root directory:

```bash
# Install dependencies
pip install -r src/requirements.txt

# Run the application
python src/main.py
```

### Starting with Grafana Dashboard

To run both the application and Grafana dashboard:

1. **Start Grafana first** (from the `src` directory):
   ```bash
   cd src
   docker-compose up -d
   ```

2. **Run the application** (in a new terminal or same terminal):
   ```bash
   python main.py
   ```

3. **Access the dashboard** at `http://localhost:3001`
   - Username: `uwfe`
   - Password: `uwfepassword`

## Building the Executable

### Prerequisites for Building

Before building the executable, ensure you have:

- Python 3.8 or higher
- PyInstaller (will be installed automatically)
- All project dependencies installed

### Building Process

1. **Navigate to the project root directory**
   ```bash
   cd can-log-grapher
   ```

2. **Install build dependencies**
   ```bash
   pip install pyinstaller
   pip install -r src/requirements.txt
   ```

3. **Run the build script**
   ```bash
   python build_exe.py
   ```

### Build Script Features

The `build_exe.py` script automatically:

- ✅ Cleans previous build artifacts
- ✅ Checks for required files
- ✅ Creates a single executable file
- ✅ Includes all necessary data files (CSS, images, Grafana configs)
- ✅ Optimizes file size
- ✅ Creates a distribution-ready folder (`final-sharable-app`)
- ✅ Generates user documentation

### Build Output

After successful build, you'll find:

```
final-sharable-app/
├── CAN-Log-Grapher.exe    # Main executable
├── docker-compose.yml      # Grafana configuration
├── grafana/               # Dashboard configuration
├── public/                # Application assets
└── README.md             # User guide
```

### Manual Build (Alternative)

If you prefer to build manually using PyInstaller directly:

```bash
# From project root
pyinstaller --onefile \
  --name=CAN-Log-Grapher \
  --add-data="src/docker-compose.yml;." \
  --add-data="src/grafana;grafana" \
  --add-data="src/app/styles.css;app" \
  --add-data="public/UWFElogo.png;public" \
  --add-data="src/parsing;parsing" \
  --hidden-import=PyQt5.QtWebEngineWidgets \
  --hidden-import=PyQt5.sip \
  --hidden-import=pandas \
  --hidden-import=cantools \
  --icon="public/UWFElogo.ico" \
  src/main.py
```

### Troubleshooting Build Issues

**Missing dependencies:**
```bash
pip install --upgrade pyinstaller
pip install -r src/requirements.txt
```

**Build fails with import errors:**
- Ensure all hidden imports are specified
- Check that all required files exist
- Try building in a clean virtual environment

**Large executable size:**
- The executable may be 100+ MB due to included Python runtime and dependencies
- This is normal for PyInstaller builds

### Distributing the Application

The `final-sharable-app` folder contains everything needed to run the application:

1. **Requirements for end users:**
   - Docker Desktop (for Grafana dashboard)
   - Windows 10/11 (if built on Windows)

2. **Distribution:**
   - Zip the entire `final-sharable-app` folder
   - Users only need to extract and run `CAN-Log-Grapher.exe`

3. **No Python installation required** for end users