# helpers/blob_utils.py
import os
import io
from datetime import datetime, timedelta
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions

# ==========================================================
#  Azure Blob Utilities for iLending POC
# ==========================================================
#  • Manages file listing / downloading / uploading
#  • Generates SAS URLs for Streamlit previews
#  • Handles structured log file uploads for each STIPS ID
# ==========================================================

load_dotenv()


class BlobHelper:
    """Handles Azure Blob operations for input, output, and logs containers."""

    def __init__(self):
        conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not conn_str:
            raise ValueError(
                "AZURE_STORAGE_CONNECTION_STRING missing in environment. "
                "Ensure .env file exists and contains the required key."
            )

        self.blob_service = BlobServiceClient.from_connection_string(conn_str)
        self.input_container = os.getenv("AZURE_INPUT_CONTAINER")
        self.output_container = os.getenv("AZURE_OUTPUT_CONTAINER")
        self.logs_container = os.getenv("AZURE_LOGS_CONTAINER", "stipsportal-logs")

        if not self.input_container or not self.output_container:
            raise ValueError(
                "AZURE_INPUT_CONTAINER or AZURE_OUTPUT_CONTAINER missing in .env"
            )

    # ------------------------------------------------------
    # 1️. List all folders (top-level)
    # ------------------------------------------------------
    def list_folders(self):
        """Returns a sorted list of top-level folders in the input container."""
        container = self.blob_service.get_container_client(self.input_container)
        folders = set()

        for blob in container.list_blobs():
            parts = blob.name.split("/")
            if len(parts) > 1:
                folders.add(parts[0])

        return sorted(list(folders))

    # ------------------------------------------------------
    # 2️. List files inside a folder
    # ------------------------------------------------------
    def list_files_in_folder(self, folder_prefix: str):
        """List all files under a specific folder prefix."""
        container = self.blob_service.get_container_client(self.input_container)
        blobs = container.list_blobs(name_starts_with=folder_prefix)
        return [b.name for b in blobs if not b.name.endswith("/")]

    # ------------------------------------------------------
    # 3️. Download blob bytes
    # ------------------------------------------------------
    def download_blob(self, blob_path: str) -> bytes:
        """Downloads a blob as bytes for local processing."""
        try:
            container = self.blob_service.get_container_client(self.input_container)
            blob_client = container.get_blob_client(blob_path)
            data = blob_client.download_blob().readall()
            print(f"⬇️  Downloaded: {blob_path}")
            return data
        except Exception as e:
            print(f" Blob download failed: {e}")
            raise

    # ------------------------------------------------------
    # 4️. Upload JSON to output container
    # ------------------------------------------------------
    def upload_json(self, blob_path: str, json_bytes: bytes):
        """Uploads a JSON output file, maintaining mirrored folder structure."""
        try:
            output_path = os.path.splitext(blob_path)[0] + ".json"
            container = self.blob_service.get_container_client(self.output_container)
            blob_client = container.get_blob_client(output_path)
            blob_client.upload_blob(io.BytesIO(json_bytes), overwrite=True)
            print(f"Uploaded JSON → {output_path}")
        except Exception as e:
            print(f"JSON upload failed for {blob_path}: {e}")
            raise

    # ------------------------------------------------------
    # 5️. Generate temporary SAS URL for preview
    # ------------------------------------------------------
    def get_image_url(self, blob_path: str, expiry_minutes: int = 30) -> str:
        """Generates a temporary SAS URL for displaying images in Streamlit."""
        try:
            blob_client = self.blob_service.get_blob_client(self.input_container, blob_path)
            sas_token = generate_blob_sas(
                account_name=self.blob_service.account_name,
                container_name=self.input_container,
                blob_name=blob_path,
                account_key=self.blob_service.credential.account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(minutes=expiry_minutes),
            )
            return f"{blob_client.url}?{sas_token}"
        except Exception as e:
            print(f" SAS generation failed: {e}")
            return ""

    # ------------------------------------------------------
    # 6️. Connection verification (debug only)
    # ------------------------------------------------------
    def verify_connection(self):
        """Verifies blob connectivity and lists all containers."""
        try:
            print(f"Connected to storage account: {self.blob_service.account_name}")
            print("Available containers:")
            for c in self.blob_service.list_containers():
                print(" -", c["name"])
        except Exception as e:
            print(f"Connection verification failed: {e}")

    # ======================================================
    #  EXTENSIONS FOR LOGGING SUPPORT
    # ======================================================

    def download_blob_from_container(self, container_name: str, blob_path: str) -> bytes:
        """Download blob bytes from a specified container (e.g., stipsportal-logs)."""
        try:
            container = self.blob_service.get_container_client(container_name)
            blob_client = container.get_blob_client(blob_path)
            return blob_client.download_blob().readall()
        except Exception:
            # Return empty if not found
            return b""

    def upload_blob_to_container(self, container_name: str, blob_path: str, data_bytes: bytes):
        """Upload or overwrite a blob in the specified container."""
        try:
            container = self.blob_service.get_container_client(container_name)
            blob_client = container.get_blob_client(blob_path)
            blob_client.upload_blob(io.BytesIO(data_bytes), overwrite=True)
        except Exception as e:
            print(f"Log upload failed for {blob_path}: {e}")

    def blob_exists(self, container_name: str, blob_path: str) -> bool:
        """Check if a blob exists in the given container."""
        try:
            container = self.blob_service.get_container_client(container_name)
            blob_client = container.get_blob_client(blob_path)
            return blob_client.exists()
        except Exception:
            return False
