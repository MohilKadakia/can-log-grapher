"""
Docker Manager Module - Fixed for .exe deployment
Handles automatic Docker container management for Grafana integration
Uses standard Python threading instead of QThread to prevent self-launching
"""

import subprocess
import os
import sys
import time
import webbrowser
# Threading import removed - all operations are now synchronous
from PyQt5.QtWidgets import QMessageBox, QProgressDialog
from PyQt5.QtCore import QTimer, Qt, QObject, pyqtSignal


# Threading classes removed - all Docker operations are now synchronous


class DockerManager:
    """Main Docker management class"""
    
    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.grafana_running = False
        self.docker_available = False
        
        # Determine paths for Docker Compose
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            self.app_path = os.path.dirname(sys.executable)
        else:
            # Running as Python script
            self.app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.docker_compose_path = os.path.join(self.app_path, "docker-compose.yml")
        
        # All Docker operations are now synchronous - no threading objects needed
    
    def check_docker_availability(self):
        """Check if Docker is available (synchronous)"""
        try:
            subprocess.run(["docker", "--version"], check=True, capture_output=True, timeout=10)
            subprocess.run(["docker", "info"], check=True, capture_output=True, timeout=10)
            self.on_docker_status_checked(True)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            self.on_docker_status_checked(False)
    
    def on_docker_status_checked(self, available):
        """Handle Docker status check result"""
        self.docker_available = available
        
        if not available:
            self.show_docker_installation_dialog()
        else:
            # Docker is available, offer to start Grafana
            self.offer_grafana_startup()
    
    def show_docker_installation_dialog(self):
        """Show dialog when Docker is not available"""
        msg_box = QMessageBox(self.parent)
        msg_box.setWindowTitle("Docker Required")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(
            "This application can integrate with Grafana for advanced data visualization.\n\n"
            "To enable this feature, Docker Desktop is required.\n\n"
            "Would you like to download Docker Desktop now?\n\n"
            "Note: The application will work without Docker, "
            "but Grafana features will be unavailable."
        )
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        
        if msg_box.exec_() == QMessageBox.Yes:
            webbrowser.open("https://www.docker.com/products/docker-desktop")
    
    def offer_grafana_startup(self):
        """Auto-start Grafana when Docker is available"""
        # Show brief notification that Grafana is starting
        msg_box = QMessageBox(self.parent)
        msg_box.setWindowTitle("Starting Grafana Dashboard")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(
            "Docker detected! Starting Grafana dashboard automatically...\n\n"
            "Dashboard will be available at: http://localhost:3000\n"
            "Username: uwfe\n"
            "Password: uwfepassword"
        )
        msg_box.setStandardButtons(QMessageBox.Ok)
        
        # Show message briefly then auto-close
        msg_box.show()
        QTimer.singleShot(2000, msg_box.close)  # Auto-close after 2 seconds
        
        # Automatically start Grafana
        self.start_grafana()
    
    def start_grafana(self):
        """Start Grafana container with progress dialog"""
        if not self.docker_available:
            QMessageBox.warning(
                self.parent, 
                "Docker Unavailable", 
                "Docker is not available. Please install Docker Desktop first."
            )
            return
        
        # Check if docker-compose.yml exists
        if not os.path.exists(self.docker_compose_path):
            QMessageBox.critical(
                self.parent,
                "Configuration Missing",
                f"Docker Compose file not found at:\n{self.docker_compose_path}\n\n"
                "Please ensure the application was installed correctly."
            )
            return
        
        # Create progress dialog
        self.progress_dialog = QProgressDialog(
            "Starting Grafana dashboard...", 
            "Cancel", 
            0, 0, 
            self.parent
        )
        self.progress_dialog.setWindowTitle("Starting Grafana")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.show()
        
        # Start Grafana synchronously (no threading)
        try:
            self.on_grafana_status_update("Starting Grafana container...")
            compose_dir = os.path.dirname(self.docker_compose_path)
            result = subprocess.run(["docker-compose", "up", "-d"], cwd=compose_dir, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                self.on_grafana_status_update("Grafana started successfully!")
                time.sleep(3)
                self.on_grafana_operation_complete(True)
            else:
                self.on_grafana_operation_complete(False)
        except Exception:
            self.on_grafana_operation_complete(False)
    
    def stop_grafana(self):
        """Stop Grafana container"""
        if not self.grafana_running:
            return
        
        try:
            compose_dir = os.path.dirname(self.docker_compose_path)
            result = subprocess.run(["docker-compose", "down"], cwd=compose_dir, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                self.on_grafana_stop_complete(True)
            else:
                self.on_grafana_stop_complete(False)
        except Exception:
            self.on_grafana_stop_complete(False)
    
    def on_grafana_status_update(self, message):
        """Handle status updates from Grafana manager"""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.setLabelText(message)
    
    def on_grafana_operation_complete(self, success):
        """Handle Grafana startup completion"""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        
        if success:
            self.grafana_running = True
            
            # Show success message and automatically open browser
            msg_box = QMessageBox(self.parent)
            msg_box.setWindowTitle("Grafana Started")
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setText(
                "Grafana dashboard started successfully!\n\n"
                "Opening dashboard at: http://localhost:3000\n\n"
                "Username: uwfe\n"
                "Password: uwfepassword"
            )
            msg_box.setStandardButtons(QMessageBox.Ok)
            
            # Automatically open the browser
            webbrowser.open("http://localhost:3000")
            
            # Show the message for a brief moment, then auto-close
            msg_box.show()
            QTimer.singleShot(3000, msg_box.close)  # Auto-close after 3 seconds
        else:
            QMessageBox.critical(
                self.parent,
                "Grafana Startup Failed",
                "Failed to start Grafana dashboard.\n\n"
                "Please check that Docker Desktop is running and try again."
            )
    
    def on_grafana_stop_complete(self, success):
        """Handle Grafana shutdown completion"""
        if success:
            self.grafana_running = False
    
    def cleanup(self):
        """Clean up resources and stop Grafana if running"""
        if self.grafana_running:
            # Stop Grafana silently on app exit
            try:
                compose_dir = os.path.dirname(self.docker_compose_path)
                subprocess.run(
                    ["docker-compose", "down"],
                    cwd=compose_dir,
                    capture_output=True,
                    timeout=30
                )
            except:
                pass  # Ignore errors during cleanup
