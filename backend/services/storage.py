from typing import Optional
from io import BytesIO
import uuid
import hashlib

# Local application imports
from core.config import settings
from services.supabase import get_supabase

# This class handles interaction with Supabase Storage.
class StorageService:
    """A service for uploading files to Supabase Storage."""
    def __init__(self):
        """
        Initializes the service by getting the Supabase client and bucket name.
        This is called only once due to the lazy loading pattern below.
        """
        self.supabase_client = get_supabase()
        self.bucket_name = settings.SUPABASE_BUCKET_NAME
        if not self.bucket_name:
            raise ValueError("SUPABASE_BUCKET_NAME is not set in the environment settings.")
        print("Supabase Storage Service Initialized.")

    def save_file(self, file_stream: BytesIO, original_filename: str, file_type: str) -> dict:
        """
        Uploads a file to Supabase Storage and returns its metadata.

        Args:
            file_stream: A BytesIO object containing the file content.
            original_filename: The original name of the file being uploaded.
            file_type: The category of the file (e.g., 'image', 'pdf').

        Returns:
            A dictionary containing metadata about the stored file.
        """
        # Read content for hashing and uploading
        content = file_stream.getvalue()
        
        # Generate a unique file ID and a hash of the content
        file_id = str(uuid.uuid4())
        file_hash = hashlib.sha256(content).hexdigest()
        
        # Get the file extension from the original filename
        file_extension = original_filename.split('.')[-1] if '.' in original_filename else ''
        storage_filename = f"{file_id}.{file_extension}" if file_extension else file_id
        
        # Create a structured path for storage (e.g., 'image/uuid.png')
        storage_path = f"{file_type}/{storage_filename}"

        # Upload the file to the specified Supabase bucket
        # Supabase client expects bytes for the file content.
        response = self.supabase_client.storage.from_(self.bucket_name).upload(
            path=storage_path,
            file=content,
            file_options={"content-type": "application/octet-stream"} # A generic type is fine
        )
        
        # Check for upload errors
        if response.status_code != 200:
            raise Exception(f"Failed to upload to Supabase Storage. Status: {response.status_code}, Response: {response.text}")

        # Return a dictionary of metadata, as expected by the caller (upload router)
        return {
            "file_id": file_id,
            "filename": storage_filename,
            "original_filename": original_filename,
            "file_type": file_type,
            "file_hash": file_hash,
            "storage_path": storage_path,
            "storage_type": "supabase"
        }

# --- The Fix for Lazy Loading (No changes needed here) ---

# 1. Create a variable to hold the instance, initialized to None
_storage_service_instance: Optional[StorageService] = None

# 2. Create a "getter" function to manage the singleton instance
def get_storage_service() -> StorageService:
    """
    Initializes and returns a singleton instance of the StorageService.
    This ensures the StorageService is only instantiated when first needed.
    """
    global _storage_service_instance
    # 3. If the instance doesn't exist yet, create it
    if _storage_service_instance is None:
        _storage_service_instance = StorageService()
    # 4. Return the now-guaranteed-to-exist instance
    return _storage_service_instance

