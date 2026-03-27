"""
Google Drive Client

Downloads webinar recordings from a shared Google Drive folder
using a service account.

Setup:
    1. Create a service account in Google Cloud Console
    2. Enable Google Drive API
    3. Share the Drive folder with the service account email
    4. Save credentials JSON to credentials/service_account.json
    5. Set GOOGLE_DRIVE_CREDENTIALS in .env
"""

import io
import logging
import os
from pathlib import Path
from typing import List, Optional

from .webinar_models import DriveFileInfo

logger = logging.getLogger(__name__)

# Video MIME types we process
VIDEO_MIME_TYPES = {
    "video/mp4",
    "video/webm",
    "video/quicktime",    # .mov
    "video/x-msvideo",    # .avi
    "video/x-matroska",   # .mkv
    "video/mpeg",
    "audio/mpeg",         # .mp3 (audio-only webinars)
    "audio/wav",
    "audio/x-wav",
    "audio/mp4",          # .m4a
    "audio/ogg",
}

# Also match by file extension as fallback
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv", ".mpeg", ".mp3", ".wav", ".m4a", ".ogg"}


class DriveClient:
    """Google Drive API client for downloading webinar recordings."""

    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Drive client with service account credentials.

        Args:
            credentials_path: Path to service account JSON. Defaults to
                              GOOGLE_DRIVE_CREDENTIALS env var.
        """
        self.credentials_path = credentials_path or os.getenv("GOOGLE_DRIVE_CREDENTIALS", "")

        if not self.credentials_path:
            raise ValueError(
                "Google Drive credentials not configured. Set GOOGLE_DRIVE_CREDENTIALS "
                "in .env or pass credentials_path."
            )

        creds_path = Path(self.credentials_path)
        if not creds_path.exists():
            raise FileNotFoundError(
                f"Credentials file not found: {self.credentials_path}. "
                f"Create a service account and save the JSON credentials."
            )

        self._service = None

    def _get_service(self):
        """Lazy-init the Drive API service."""
        if self._service is None:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            creds = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=["https://www.googleapis.com/auth/drive.readonly"],
            )
            self._service = build("drive", "v3", credentials=creds)
            logger.info("Google Drive API client initialized")

        return self._service

    def list_files(self, folder_id: str) -> List[DriveFileInfo]:
        """
        List video/audio files in a Google Drive folder.

        Args:
            folder_id: Google Drive folder ID

        Returns:
            List of DriveFileInfo for video/audio files
        """
        service = self._get_service()

        # Query for files in folder
        query = f"'{folder_id}' in parents and trashed = false"
        results = []
        page_token = None

        while True:
            response = service.files().list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType, size, createdTime)",
                pageSize=100,
                pageToken=page_token,
                orderBy="createdTime desc",
            ).execute()

            for file_data in response.get("files", []):
                # Filter for video/audio files
                mime_type = file_data.get("mimeType", "")
                name = file_data.get("name", "")
                ext = Path(name).suffix.lower()

                if mime_type in VIDEO_MIME_TYPES or ext in VIDEO_EXTENSIONS:
                    results.append(DriveFileInfo(
                        id=file_data["id"],
                        name=name,
                        mime_type=mime_type,
                        size=int(file_data.get("size", 0)),
                        created_time=file_data.get("createdTime", ""),
                    ))

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        logger.info(f"Found {len(results)} video/audio files in folder {folder_id}")
        return results

    def download_file(self, file_id: str, dest_dir: Path) -> Path:
        """
        Download a file from Google Drive.

        Args:
            file_id: Google Drive file ID
            dest_dir: Directory to save the file

        Returns:
            Path to the downloaded file
        """
        service = self._get_service()

        # Get file metadata for the filename
        meta = service.files().get(fileId=file_id, fields="name, size").execute()
        filename = meta.get("name", f"{file_id}.mp4")
        size_bytes = int(meta.get("size", 0))

        dest_path = dest_dir / filename
        dest_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Downloading {filename} ({size_bytes / 1024 / 1024:.1f} MB)...")

        from googleapiclient.http import MediaIoBaseDownload

        request = service.files().get_media(fileId=file_id)
        with open(dest_path, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    if progress % 25 == 0:
                        logger.info(f"  Download progress: {progress}%")

        logger.info(f"Downloaded: {dest_path} ({dest_path.stat().st_size / 1024 / 1024:.1f} MB)")
        return dest_path
