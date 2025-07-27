"""Firebase Cloud integration for the application."""
import os
import firebase_admin
from firebase_admin import credentials, storage, firestore
import pyrebase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class FirebaseClient:
    """Client for interacting with Firebase services."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Singleton pattern to ensure only one Firebase client exists."""
        if cls._instance is None:
            cls._instance = FirebaseClient()
        return cls._instance
    
    def __init__(self):
        """Initialize Firebase services."""
        # Path to your Firebase service account key JSON file
        service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        
        # Firebase configuration
        self.config = {
            "apiKey": os.getenv("FIREBASE_API_KEY"),
            "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
            "projectId": os.getenv("FIREBASE_PROJECT_ID"),
            "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
            "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
            "appId": os.getenv("FIREBASE_APP_ID"),
            "databaseURL": os.getenv("FIREBASE_DATABASE_URL", "")
        }
        self.database_name = os.getenv("FIREBASE_DATABASE_NAME", "(default)")
        # Initialize Firebase Admin SDK (for server-side operations)
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_path)
            self.admin_app = firebase_admin.initialize_app(cred, {
                'storageBucket': self.config["storageBucket"]
            })
        
        # Initialize Pyrebase (for client operations including auth)
        self.firebase = pyrebase.initialize_app(self.config)
        self.auth = self.firebase.auth()
        self.db = firestore.client(
            app=self.admin_app,
            database_id=self.database_name
        )
        self.storage = self.firebase.storage()
     
    def check_internet_connection(self):
        """
        Check if there is an active internet connection.
        
        Returns:
            bool: True if internet is available, False otherwise
        """
        import socket
        try:
            # Try to connect to Google's DNS server
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False    
    def upload_file(self, file_path, cloud_path=None):
        """
        Upload a file to Firebase Storage.
        
        Args:
            file_path (str): Path to the local file
            cloud_path (str, optional): Path in cloud storage. If None, uses filename
            
        Returns:
            str: Public URL of the uploaded file
        """
        if not self.check_internet_connection():
            raise ConnectionError("No internet connection available. Please connect to the internet and try again.")
        
        # Check if the file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check if the file is a valid file
        if not os.path.isfile(file_path):
            raise ValueError(f"Invalid file: {file_path}")
        
        # Check if the file is empty
        if os.path.getsize(file_path) == 0:
            raise ValueError(f"File is empty: {file_path}")
        
        if cloud_path is None:
            cloud_path = os.path.basename(file_path)
            
        # Upload the file
        self.storage.child(cloud_path).put(file_path)
        
        # Get the download URL
        url = self.storage.child(cloud_path).get_url(None)
        
        # Store metadata in Firestore
        file_metadata = {
            "filename": os.path.basename(file_path),
            "path": cloud_path,
            "url": url,
            "uploaded_at": firestore.SERVER_TIMESTAMP
        }
        self.db.collection("uploads").add(file_metadata)
        
        return url
        
    def upload_folder(self, folder_path, cloud_base_path=None):
        """
        Upload all files in a folder to Firebase Storage.
        
        Args:
            folder_path (str): Path to the local folder
            cloud_base_path (str, optional): Base path in cloud storage
            
        Returns:
            list: List of public URLs for uploaded files
        """
        if cloud_base_path is None:
            cloud_base_path = os.path.basename(folder_path)
            
        urls = []
        
        for root, _, files in os.walk(folder_path):
            for file in files:
                local_path = os.path.join(root, file)
                
                # Determine relative path from the base folder
                rel_path = os.path.relpath(local_path, folder_path)
                cloud_path = os.path.join(cloud_base_path, rel_path)
                
                # Upload the file
                url = self.upload_file(local_path, cloud_path)
                urls.append(url)
                
        return urls