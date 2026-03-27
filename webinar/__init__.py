"""Webinar Processing Module.

Transcribes webinar recordings from Google Drive using Gemini,
extracts key points, and stores results for newsletter and article generation.

Usage:
    python -m webinar.process_webinars --folder-id FOLDER_ID
    python -m webinar.process_webinars --newsletter 2026-03
"""

from .webinar_processor import process_webinar, process_folder
from .webinar_models import WebinarResult, TranscriptionResult

__all__ = [
    "process_webinar",
    "process_folder",
    "WebinarResult",
    "TranscriptionResult",
]
