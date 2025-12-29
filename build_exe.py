"""
Build script for creating CAN Log Grapher executable
Converts the Python application into a standalone .exe file
"""

import PyInstaller.__main__
import os
import shutil
import sys
import re

def clean_previous_builds():
    """Clean up previous build artifacts"""
    print("🧹 Cleaning previous builds...")
    
    # Remove previous build directories
    directories_to_clean = ['dist', 'build', '__pycache__']
    
    for directory in directories_to_clean:
        if os.path.exists(directory):
            shutil.rmtree(directory)
            print(f"   ✓ Removed {directory}/")
    
    # Clean pycache in subdirectories
    for root, dirs, files in os.walk('.'):
        for directory in dirs:
            if directory == '__pycache__':
                pycache_path = os.path.join(root, directory)
                shutil.rmtree(pycache_path)
                print(f"   ✓ Removed {pycache_path}")

def check_required_files():
    """Check if all required files exist before building"""
    print("📋 Checking required files...")
    
    required_files = [
        'src/main.py',
        'src/docker-compose.yml',
        'src/app/styles.css',
        'public/UWFElogo.png',
        'src/grafana/etc/provisioning/dashboards/dashboard.yml',
        'src/grafana/etc/provisioning/dashboards/general.json',
        'src/grafana/etc/provisioning/datasources/infinity.yml'
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✓ Found {file_path}")
        else:
            print(f"   ❌ Missing {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Build cannot proceed. Missing files: {missing_files}")
        return False
    
    return True

def create_final_sharable_folder():
    """Create the final-sharable-app directory if it doesn't exist"""
    if not os.path.exists('final-sharable-app'):
        os.makedirs('final-sharable-app')
        print("📁 Created final-sharable-app directory")

def build_executable():
    """Build the executable using PyInstaller"""
    print("🏗️  Building executable with PyInstaller...")
    
    # PyInstaller arguments for CAN Log Grapher
    args = [
        'src/main.py',                              # Entry point
        '--onefile',                                # Single executable file                               # No console window (GUI app)
        '--name=CAN-Log-Grapher',                  # Executable name
        
        # Include additional data files that the app needs
        '--add-data=src/docker-compose.yml;.',     # Docker compose file
        '--add-data=src/grafana;grafana',          # Grafana configuration
        '--add-data=src/app/styles.css;app',       # CSS stylesheet
        '--add-data=public/UWFElogo.png;public',   # Logo image
        '--add-data=src/parsing;parsing',          # Parsing modules
        
        # Hidden imports for modules that PyInstaller might miss
        '--hidden-import=PyQt5.QtWebEngineWidgets',
        '--hidden-import=PyQt5.sip',
        '--hidden-import=pandas',
        '--hidden-import=cantools',
        '--hidden-import=firebase-admin',
        '--hidden-import=pyrebase4',
        
        # Exclude unnecessary modules to reduce file size
        '--exclude-module=matplotlib.tests',
        '--exclude-module=numpy.tests',
        '--exclude-module=pandas.tests',
        
        # Performance and build options
        '--clean',                                  # Clean cache before building
        '--noconfirm',                             # Don't ask for confirmation
        
        # Output directory - put exe in final-sharable-app
        '--distpath=final-sharable-app',
        
        # Optimize for size and performance
        '--optimize=2',                            # Python optimization level
    ]
    
    # Add icon if it exists
    icon_path = 'public/UWFElogo.ico'
    if os.path.exists(icon_path):
        args.extend(['--icon=' + icon_path])
        print(f"   ✓ Using icon: {icon_path}")
    else:
        print(f"   ⚠️  Icon not found: {icon_path} (executable will use default icon)")
    
    # Run PyInstaller
    try:
        PyInstaller.__main__.run(args)
        return True
    except Exception as e:
        print(f"❌ PyInstaller failed: {e}")
        return False

def copy_additional_files():
    """Copy additional files needed for distribution"""
    print("📄 Copying additional files...")
    
    files_to_copy = [
        # Copy docker-compose.yml to root of final-sharable-app
        ('src/docker-compose.yml', 'final-sharable-app/docker-compose.yml'),
        # Copy grafana folder
        ('src/grafana', 'final-sharable-app/grafana'),
        # Copy logo file so it appears in the application
        ('public/UWFElogo.png', 'final-sharable-app/public/UWFElogo.png'),
        # Copy .env file for Firebase credentials
        ('.env', 'final-sharable-app/.env'),
        # Copy Firebase service account JSON file
        ('uwfe-test-firebase.json', 'final-sharable-app/uwfe-test-firebase.json'),
    ]
    
    for src, dst in files_to_copy:
        try:
            if os.path.isfile(src):
                # Copy file
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                print(f"   ✓ Copied {src} → {dst}")
            elif os.path.isdir(src):
                # Copy directory
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                print(f"   ✓ Copied {src}/ → {dst}/")
        except Exception as e:
            print(f"   ⚠️  Failed to copy {src}: {e}")
    
    # Update .env file path to use relative path
    env_path = 'final-sharable-app/.env'
    if os.path.exists(env_path):
        try:
            # Read the .env file
            with open(env_path, 'r', encoding='utf-8') as f:
                env_content = f.read()
            
            # Replace absolute path with relative path
            # Update the FIREBASE_SERVICE_ACCOUNT_PATH to use relative path
            # Handle both quoted and unquoted paths
            env_content = re.sub(
                r'FIREBASE_SERVICE_ACCOUNT_PATH=["\']?[^"\'\n]*["\']?',
                'FIREBASE_SERVICE_ACCOUNT_PATH=./uwfe-test-firebase.json',
                env_content
            )
            
            # Write back the updated content
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            print(f"   ✓ Updated .env file paths to be relative")
        except Exception as e:
            print(f"   ⚠️  Failed to update .env file: {e}")

def create_user_readme():
    """Create a simple README for end users"""
    print("📝 Creating user README...")
    
    readme_content = """# CAN Log Grapher - User Guide

## Quick Start

1. **Install Docker Desktop** (Required for dashboard features)
   - Download from: https://www.docker.com/products/docker-desktop
   - Install and start Docker Desktop

2. **Run the Application**
   - Double-click `CAN-Log-Grapher.exe`
   - The app will automatically check for Docker and offer to start the dashboard

3. **Using the Dashboard**
   - When prompted, click "Yes" to start Grafana
   - The dashboard will open automatically in your browser at: http://localhost:3000
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
- Try accessing http://localhost:3000 manually

**Application won't start:**
- Make sure all files are in the same folder as the .exe
- Run as administrator if needed
- Check that antivirus isn't blocking the application

## Files Included

- `CAN-Log-Grapher.exe` - Main application
- `docker-compose.yml` - Grafana configuration
- `grafana/` - Dashboard configuration files
- `README.md` - This file

## Support

If you encounter issues, please check that:
1. Docker Desktop is installed and running
2. All files are in the same directory as the .exe
3. You have sufficient permissions to run the application
"""
    
    readme_path = 'final-sharable-app/README.md'
    try:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print(f"   ✓ Created {readme_path}")
    except Exception as e:
        print(f"   ⚠️  Failed to create README: {e}")

def print_build_summary():
    """Print summary of build results"""
    print("\n" + "="*60)
    print("🎉 BUILD COMPLETE!")
    print("="*60)
    
    exe_path = 'final-sharable-app/CAN-Log-Grapher.exe'
    if os.path.exists(exe_path):
        # Get file size
        size_bytes = os.path.getsize(exe_path)
        size_mb = size_bytes / (1024 * 1024)
        
        print(f"✅ Executable created: {exe_path}")
        print(f"📦 File size: {size_mb:.1f} MB")
        print(f"📁 Distribution folder: final-sharable-app/")
        
        # List contents of final-sharable-app
        print(f"\n📋 Contents of final-sharable-app/:")
        for item in os.listdir('final-sharable-app'):
            item_path = os.path.join('final-sharable-app', item)
            if os.path.isdir(item_path):
                print(f"   📁 {item}/")
            else:
                print(f"   📄 {item}")
        
        print(f"\n🚀 Ready to distribute!")
        print(f"   Users only need to:")
        print(f"   1. Install Docker Desktop")
        print(f"   2. Double-click CAN-Log-Grapher.exe")
        
    else:
        print("❌ Build failed - executable not found")
        print("   Check the error messages above")

def main():
    """Main build process"""
    print("🏗️  CAN Log Grapher - Build Script")
    print("="*50)
    
    # Step 1: Clean previous builds
    clean_previous_builds()
    
    # Step 2: Check required files
    if not check_required_files():
        sys.exit(1)
    
    # Step 3: Create output directory
    create_final_sharable_folder()
    
    # Step 4: Build executable
    if not build_executable():
        print("❌ Build failed!")
        sys.exit(1)
    
    # Step 5: Copy additional files
    copy_additional_files()
    
    # Step 6: Create user documentation
    create_user_readme()
    
    # Step 7: Print summary
    print_build_summary()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Build cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
