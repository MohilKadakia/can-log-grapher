import threading
from typing import Dict, List, Any
import uuid

class SharedDataManager:
    """Manages shared data between threads using references instead of copying."""
    
    def __init__(self):
        self._data_store: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def store_data(self, data: List[Dict]) -> str:
        """Store data and return a unique identifier."""
        data_id = str(uuid.uuid4())
        with self._lock:
            self._data_store[data_id] = data
        return data_id
    
    def get_data(self, data_id: str) -> List[Dict]:
        """Retrieve data by identifier."""
        with self._lock:
            return self._data_store.get(data_id)
    
    def remove_data(self, data_id: str):
        """Remove data from store to free memory."""
        with self._lock:
            self._data_store.pop(data_id, None)
    
    def get_data_size(self, data_id: str) -> int:
        """Get the number of rows for a data_id."""
        with self._lock:
            data = self._data_store.get(data_id)
            return len(data) if data else 0

# Global shared data manager
shared_data_manager = SharedDataManager()