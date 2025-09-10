"""Firebase Cloud integration for the application."""
import os
import firebase_admin
from firebase_admin import credentials, storage, firestore
import pyrebase
from dotenv import load_dotenv
import datetime
import uuid

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
    def upload_file(self, file_path, cloud_path=None, folder_id=None):
        """
        Upload a file to Firebase Storage.
        
        Args:
            file_path (str): Path to the local file
            cloud_path (str, optional): Path in cloud storage. If None, uses filename
            folder_id (str, optional): ID of the folder to upload to
            
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
        
        # Store metadata in Firestore in the "files" collection
        file_metadata = {
            "filename": os.path.basename(file_path),
            "path": cloud_path,
            "url": url,
            "uploaded_at": datetime.datetime.now().isoformat(),
            "folder_id": folder_id  # Add folder_id reference if provided
        }
        
        # Create a document ID based on the file path
        if folder_id:
            doc_id = f"{folder_id}_{cloud_path.replace('/', '_')}"
        else:
            doc_id = cloud_path.replace('/', '_')
        
        # Add the file to Firestore with the path-based ID
        self.db.collection("files").document(doc_id).set(file_metadata)
        
        # If folder_id is provided, update the folder's file list
        if folder_id:
            # Get the folder document
            folder_doc = self.db.collection("folders").document(folder_id).get()
            if folder_doc.exists:
                folder_data = folder_doc.to_dict()
                
                # Update the folder's file list
                files = folder_data.get("files", [])
                files.append(file_metadata)
                
                # Update the folder document
                self.db.collection("folders").document(folder_id).update({
                    "files": files,
                    "file_count": len(files)
                })
        
        return url
        
    def upload_folder(self, folder_path, cloud_base_path=None, check_cancel_func=None):
        """
        Upload all files in a folder to Firebase Storage, maintaining folder structure.
        
        Args:
            folder_path (str): Path to the local folder
            cloud_base_path (str, optional): Base path in cloud storage
            check_cancel_func (callable, optional): Function to call to check if upload should be cancelled
                
        Returns:
            dict: Dictionary with folder metadata and URLs of uploaded files
        """
        if not self.check_internet_connection():
            raise ConnectionError("No internet connection available. Please connect to the internet and try again.")
            
        # Check if the folder exists
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Folder not found: {folder_path}")
            
        # Check if the path is a directory
        if not os.path.isdir(folder_path):
            raise ValueError(f"Not a folder: {folder_path}")
            
        if cloud_base_path is None:
            cloud_base_path = os.path.basename(folder_path)
        
        # Generate a folder ID that includes parent directory structure
        folder_name = os.path.basename(folder_path)
        parent_dir = os.path.basename(os.path.dirname(folder_path))
        
        # If parent directory exists and isn't the root, include it in the ID
        if parent_dir and parent_dir != os.path.dirname(os.path.abspath(os.sep)):
            folder_id = f"{parent_dir}_{folder_name}"
        else:
            folder_id = folder_name
            
        # Create a folder metadata document in Firestore first
        folder_metadata = {
            "name": folder_name,
            "path": cloud_base_path,
            "type": "folder",
            "created_at": datetime.datetime.now().isoformat(),
            "parent_dir": parent_dir if parent_dir else None
        }
        
        # Add the folder to Firestore with custom ID in the "folders" collection
        self.db.collection("folders").document(folder_id).set(folder_metadata)
        
        urls = []
        file_metadata_list = []
        subfolder_paths = []
        created_subfolders = set()  # Track which subfolders we've already created
        subfolder_id_map = {}  # Map subfolder relative paths to their IDs
        subfolder_files = {}  # Track files for each subfolder
        parent_map = {}  # Track parent-child relationships between subfolders
        
        # First pass: identify all subfolders and create their documents
        for root, dirs, files in os.walk(folder_path):
            # Check for cancellation if function provided
            if check_cancel_func and check_cancel_func():
                return {"folder_id": folder_id, "urls": urls}
                
            # Check internet connection periodically
            if not self.check_internet_connection():
                raise ConnectionError("Internet connection lost during upload")
            
            # Track subfolder paths and create individual folder documents for each
            for dir_name in dirs:
                subfolder_path = os.path.join(root, dir_name)
                rel_path = os.path.relpath(subfolder_path, folder_path)
                subfolder_paths.append(rel_path)
                
                # Create individual folder document for each subfolder
                if rel_path not in created_subfolders:
                    subfolder_id = f"{folder_id}_{rel_path.replace(os.sep, '_')}"
                    
                    # Determine the parent folder of this subfolder
                    parent_rel_path = os.path.dirname(rel_path)
                    parent_folder_id = None
                    
                    if parent_rel_path and parent_rel_path != '.':
                        # This is a nested subfolder, set its parent to be the parent subfolder
                        parent_folder_id = f"{folder_id}_{parent_rel_path.replace(os.sep, '_')}"
                        # Track this parent-child relationship
                        if parent_folder_id not in parent_map:
                            parent_map[parent_folder_id] = []
                        parent_map[parent_folder_id].append(subfolder_id)
                    else:
                        # This is a top-level subfolder, set its parent to be the main folder
                        parent_folder_id = folder_id
                        # Track this parent-child relationship
                        if folder_id not in parent_map:
                            parent_map[folder_id] = []
                        parent_map[folder_id].append(subfolder_id)
                    
                    subfolder_metadata = {
                        "name": os.path.basename(rel_path),
                        "path": os.path.join(cloud_base_path, rel_path).replace(os.sep, '/'),
                        "type": "folder",
                        "created_at": datetime.datetime.now().isoformat(),
                        "parent_dir": os.path.dirname(rel_path) if os.path.dirname(rel_path) else folder_name,
                        "parent_folder_id": parent_folder_id,
                        "relative_path": rel_path,
                        "files": [],  # Initialize empty file list
                        "file_count": 0,
                        "is_subfolder": True
                    }
                    
                    # Add the subfolder to Firestore
                    self.db.collection("folders").document(subfolder_id).set(subfolder_metadata)
                    created_subfolders.add(rel_path)
                    
                    # Map the relative path to the subfolder ID for file assignment
                    subfolder_id_map[rel_path] = subfolder_id
                    # Initialize file list for this subfolder
                    subfolder_files[subfolder_id] = []
        
        # Second pass: upload files and assign them to the correct folders
        for root, dirs, files in os.walk(folder_path):
            # Process each file in the current directory
            for file in files:
                local_path = os.path.join(root, file)
                
                # Determine relative path from the base folder
                rel_path = os.path.relpath(local_path, folder_path)
                cloud_path = os.path.join(cloud_base_path, rel_path).replace(os.sep, '/')
                
                # Determine which folder this file belongs to
                file_dir_rel_path = os.path.dirname(rel_path)
                if file_dir_rel_path and file_dir_rel_path != '.' and file_dir_rel_path in subfolder_id_map:
                    # File is in a subfolder
                    file_folder_id = subfolder_id_map[file_dir_rel_path]
                else:
                    # File is in the root folder
                    file_folder_id = folder_id
                
                # Upload the file
                self.storage.child(cloud_path).put(local_path)
                download_url = self.storage.child(cloud_path).get_url(None)
                urls.append(download_url)
                
                # Create file metadata
                file_metadata = {
                    "filename": file,
                    "path": cloud_path,
                    "url": download_url,
                    "relative_path": rel_path,
                    "uploaded_at": datetime.datetime.now().isoformat(),
                    "folder_id": file_folder_id  # Assign to correct folder (root or subfolder)
                }
                
                # Create a document ID based on the folder and file path
                doc_id = f"{file_folder_id}/{rel_path}".replace('/', '_')
                
                # Add individual file to "files" collection with path-based ID
                self.db.collection("files").document(doc_id).set(file_metadata)
                
                # Track files for their respective folders
                if file_folder_id == folder_id:
                    # File is in the root folder
                    file_metadata_list.append(file_metadata)
                else:
                    # File is in a subfolder
                    subfolder_files[file_folder_id].append(file_metadata)
        
        # Update the main folder document with root-level file information and parent-child relationships
        self.db.collection("folders").document(folder_id).update({
            "files": file_metadata_list,
            "file_count": len(file_metadata_list),
            "subfolders": subfolder_paths,
            "child_folders": parent_map.get(folder_id, [])
        })
        
        # Update each subfolder document with its files and child folders
        for subfolder_id, files_in_subfolder in subfolder_files.items():
            update_data = {
                "files": files_in_subfolder,
                "file_count": len(files_in_subfolder)
            }
            
            # Add child folders information if this subfolder has children
            if subfolder_id in parent_map:
                update_data["child_folders"] = parent_map[subfolder_id]
                
            self.db.collection("folders").document(subfolder_id).update(update_data)
        
        return {
            "folder_id": folder_id,
            "folder_name": folder_name,
            "urls": urls,
            "file_count": len(file_metadata_list)
        }
        
    def download_folder_recursive(self, folder_id, destination=None, _current_path=None):
        """
        Recursively download a folder and all its subfolders with their files.
        
        Args:
            folder_id (str): ID of the folder to download
            destination (str, optional): Local destination directory. If None, creates a folder in Downloads
            _current_path (str, optional): Internal parameter for recursion - current path being built
            
        Returns:
            str: Path to the downloaded folder
        """
        if not self.check_internet_connection():
            raise ConnectionError("No internet connection available. Please connect to the internet and try again.")
        
        try:
            # Get folder document from "folders" collection
            folder_doc = self.db.collection("folders").document(folder_id).get()
            
            if not folder_doc.exists:
                raise ValueError(f"Folder with ID {folder_id} not found")
                
            folder_data = folder_doc.to_dict()
            folder_name = folder_data.get("name", "downloaded_folder")
            
            # Determine the destination path
            if destination is None:
                # This is the root call, create base destination
                destination = os.path.join(os.path.expanduser("~"), "Downloads", folder_name)
                current_destination = destination
            else:
                # This is a recursive call, append folder name to current path
                current_destination = os.path.join(destination, folder_name)
            
            # Ensure the directory exists
            os.makedirs(current_destination, exist_ok=True)
            
            # Download all files directly in this folder
            files = self.list_files(limit=1000, folder_id=folder_id)
            
            for file in files:
                file_path = file.get("path")
                filename = file.get("filename")
                relative_path = file.get("relative_path", filename)
                
                if file_path:
                    # For files in subfolders, we only want the filename since we're already in the correct folder
                    # The relative_path contains the full path from the root, but we're already in the subfolder
                    file_destination = os.path.join(current_destination, filename)
                    
                    # Ensure the file's directory exists
                    file_dir = os.path.dirname(file_destination)
                    if file_dir:
                        os.makedirs(file_dir, exist_ok=True)
                    
                    # Download the file
                    self.storage.child(file_path).download(path=file_path, filename=file_destination)
            
            # Find and recursively download all subfolders
            # Get all folders that have this folder as parent
            subfolder_query = self.db.collection("folders").where("parent_folder_id", "==", folder_id)
            
            for subfolder_doc in subfolder_query.stream():
                subfolder_id = subfolder_doc.id
                # Recursively download the subfolder
                self.download_folder_recursive(subfolder_id, current_destination)
            
            # Return the root destination path
            return destination if _current_path is None else current_destination
            
        except Exception as e:
            raise Exception(f"Error downloading folder recursively: {str(e)}")
            
    def download_folder(self, folder_id, destination=None):
        """
        Download all files in a folder to a local directory.
        
        Args:
            folder_id (str): ID of the folder to download
            destination (str, optional): Local destination directory. If None, creates a folder in Downloads
            
        Returns:
            str: Path to the downloaded folder
        """
        if not self.check_internet_connection():
            raise ConnectionError("No internet connection available. Please connect to the internet and try again.")
        
        try:
            # Get folder document from "folders" collection
            folder_doc = self.db.collection("folders").document(folder_id).get()
            
            if not folder_doc.exists:
                raise ValueError(f"Folder with ID {folder_id} not found")
                
            folder_data = folder_doc.to_dict()
            folder_name = folder_data.get("name", "downloaded_folder")
            
            # Create destination folder
            if destination is None:
                destination = os.path.join(os.path.expanduser("~"), "Downloads", folder_name)
            
            # Ensure the directory exists
            os.makedirs(destination, exist_ok=True)
            
            # Get all files in the folder
            files = self.list_files(limit=1000, folder_id=folder_id)
            
            if not files:
                return destination  # Return early if no files to download
            
            # Download each file
            for file in files:
                file_path = file.get("path")
                filename = file.get("filename")
                if file_path:
                    file_destination = os.path.join(destination, filename)
                    self.storage.child(file_path).download(path=file_path, filename=file_destination)
            
            return destination
        except Exception as e:
            raise Exception(f"Error downloading folder: {str(e)}")
        
    def list_folders(self, limit=100):
        """
        List recent folders.
        
        Args:
            limit (int): Maximum number of folders to return
            
        Returns:
            list: List of folder metadata
        """
        if not self.check_internet_connection():
            raise ConnectionError("No internet connection available. Please connect to the internet and try again.")
            
        folders = []
        query = self.db.collection("folders").order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit)
        
        for doc in query.stream():
            data = doc.to_dict()
            data["id"] = doc.id
            folders.append(data)
            
        return folders
        
    def create_folder(self, folder_name):
        """
        Create a new folder in Firebase.
        
        Args:
            folder_name (str): Name of the folder to create
            
        Returns:
            str: ID of the created folder
        """
        if not self.check_internet_connection():
            raise ConnectionError("No internet connection available. Please connect to the internet and try again.")
            
        # Generate a unique folder ID
        folder_id = f"{folder_name}_{uuid.uuid4().hex[:8]}"
        
        # Create folder metadata
        folder_metadata = {
            "name": folder_name,
            "path": folder_name,
            "type": "folder",
            "created_at": datetime.datetime.now().isoformat(),
            "parent_dir": None,
            "files": [],
            "file_count": 0,
            "subfolders": []
        }
        
        # Add the folder to Firestore
        self.db.collection("folders").document(folder_id).set(folder_metadata)
        
        return folder_id
        
    def list_files(self, limit=100, folder_id=None):
        """
        List recent files, optionally filtered by folder.
        
        Args:
            limit (int): Maximum number of files to return
            folder_id (str, optional): If provided, only return files from this folder
            
        Returns:
            list: List of file metadata
        """
        if not self.check_internet_connection():
            raise ConnectionError("No internet connection available. Please connect to the internet and try again.")
            
        files = []
        
        if folder_id:
            query = self.db.collection("files").where("folder_id", "==", folder_id).limit(limit)
        else:
            query = self.db.collection("files").order_by("uploaded_at", direction=firestore.Query.DESCENDING).limit(limit)
        
        for doc in query.stream():
            data = doc.to_dict()
            data["id"] = doc.id
            files.append(data)
            
        return files
        
    def get_cloud_structure(self, limit=200):
        """
        Get both folders and files from Firebase to display in the cloud access panel.
        
        Args:
            limit (int): Maximum number of items to return per type
            
        Returns:
            dict: Dictionary with separate lists for folders and files
        """
        if not self.check_internet_connection():
            raise ConnectionError("No internet connection available. Please connect to the internet and try again.")
        
        try:
            # Get folders
            folders = self.list_folders(limit)
            
            # Get standalone files (not in folders)
            standalone_files = []
            query = self.db.collection("files").where("folder_id", "==", None).order_by("uploaded_at", direction=firestore.Query.DESCENDING).limit(limit)
            
            for doc in query.stream():
                data = doc.to_dict()
                data["id"] = doc.id
                standalone_files.append(data)
            
            # Get recent files regardless of folder for "Recent" tab
            recent_files = self.list_files(limit)
            
            return {
                "folders": folders,
                "standalone_files": standalone_files,
                "recent_files": recent_files
            }
            
        except Exception as e:
            raise Exception(f"Error retrieving cloud structure: {str(e)}")
            
    def download_file(self, file_path, destination=None):
        """
        Download a file from Firebase Storage.
        
        Args:
            file_path (str): Path of the file in Firebase Storage
            destination (str, optional): Local destination path. If None, uses temp directory
            
        Returns:
            str: Path to the downloaded file
        """
        if not self.check_internet_connection():
            raise ConnectionError("No internet connection available. Please connect to the internet and try again.")
            
        try:
            if destination is None:
                # Create a temporary file with the same extension
                filename = os.path.basename(file_path)
                destination = os.path.join(os.path.expanduser("~"), "Downloads", filename)
                
            # Ensure the directory exists
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            # Download the file - passing both required parameters
            # The path parameter is the path in Firebase Storage where the file is stored
            # The filename parameter is the local path where the file will be saved
            self.storage.child(file_path).download(path=file_path, filename=destination)
            
            return destination
        except Exception as e:
            raise Exception(f"Error downloading file: {str(e)}")