"""
Webinar Processor

Orchestrates the full webinar processing pipeline:
1. Download from Google Drive
2. Transcribe with Gemini
3. Extract key points
4. Store in SQLite
5. Auto-link to content plan keywords
"""

import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional

_PROJECT_ROOT = Path(__file__).parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from shared.database import OpenBlogDB

from .drive_client import DriveClient
from .transcriber import GeminiTranscriber
from .webinar_models import WebinarResult

logger = logging.getLogger(__name__)

# Max file size for Gemini File API upload (2 GB)
_GEMINI_MAX_UPLOAD_BYTES = 2 * 1024 * 1024 * 1024


def extract_audio(video_path: Path, output_dir: Path) -> Path:
    """
    Extract audio track from a video file using ffmpeg.

    Converts to AAC .m4a which is compact and well-supported by Gemini.
    A 3 GB video typically becomes ~50-80 MB audio.

    Args:
        video_path: Path to the video file
        output_dir: Directory to save the audio file

    Returns:
        Path to the extracted audio file
    """
    audio_path = output_dir / f"{video_path.stem}.m4a"

    logger.info(
        f"Extracting audio from {video_path.name} "
        f"({video_path.stat().st_size / 1024 / 1024:.0f} MB)..."
    )

    result = subprocess.run(
        [
            "ffmpeg", "-i", str(video_path),
            "-vn",              # no video
            "-acodec", "aac",   # AAC codec
            "-b:a", "128k",     # 128kbps bitrate (good enough for speech)
            "-y",               # overwrite
            str(audio_path),
        ],
        capture_output=True,
        text=True,
        timeout=600,  # 10 min max
    )

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr[-500:]}")

    audio_size_mb = audio_path.stat().st_size / 1024 / 1024
    logger.info(f"Audio extracted: {audio_path.name} ({audio_size_mb:.1f} MB)")
    return audio_path


async def process_webinar(
    drive_file_id: str,
    filename: str,
    drive_client: Optional[DriveClient] = None,
    transcriber: Optional[GeminiTranscriber] = None,
    db: Optional[OpenBlogDB] = None,
    local_path: Optional[Path] = None,
) -> WebinarResult:
    """
    Process a single webinar: download → transcribe → extract → store.

    Args:
        drive_file_id: Google Drive file ID
        filename: Original filename
        drive_client: Reusable Drive client (created if None)
        transcriber: Reusable transcriber (created if None)
        db: Database instance (created if None)
        local_path: If provided, skip download and use this local file

    Returns:
        WebinarResult with all extracted data
    """
    if db is None:
        db = OpenBlogDB()

    # Check if already processed
    if db.is_webinar_processed(drive_file_id):
        logger.info(f"Webinar already processed: {filename} (id={drive_file_id})")
        # Return existing data
        webinars = db.get_all_webinars()
        for w in webinars:
            if w.get("drive_file_id") == drive_file_id:
                return WebinarResult(
                    drive_file_id=drive_file_id,
                    filename=filename,
                    title=w.get("title", ""),
                    summary=w.get("summary", ""),
                    key_points=w.get("key_points", []),
                    legal_references=w.get("legal_references", []),
                    topics=w.get("topics", []),
                    rechtsgebiet=w.get("rechtsgebiet", ""),
                )
        # Fallback if not found in DB query
        return WebinarResult(drive_file_id=drive_file_id, filename=filename)

    result = WebinarResult(drive_file_id=drive_file_id, filename=filename)
    tmp_dir = None

    try:
        # Step 1: Get file locally
        if local_path and local_path.exists():
            video_path = local_path
            logger.info(f"Using local file: {video_path}")
        else:
            if drive_client is None:
                drive_client = DriveClient()

            tmp_dir = Path(tempfile.mkdtemp(prefix="openblog_webinar_"))
            video_path = drive_client.download_file(drive_file_id, tmp_dir)

        # Step 2: Extract audio if file is too large for Gemini File API
        file_to_transcribe = video_path
        if video_path.stat().st_size > _GEMINI_MAX_UPLOAD_BYTES:
            audio_dir = tmp_dir or Path(tempfile.mkdtemp(prefix="openblog_audio_"))
            if tmp_dir is None:
                tmp_dir = audio_dir  # ensure cleanup
            file_to_transcribe = extract_audio(video_path, audio_dir)

        # Step 3: Transcribe
        if transcriber is None:
            transcriber = GeminiTranscriber()

        logger.info(f"Transcribing: {file_to_transcribe.name}")
        transcription = await transcriber.transcribe(file_to_transcribe)
        result.transcript = transcription.transcript
        result.duration_seconds = transcription.duration_seconds
        result.speaker_names = transcription.speaker_names
        result.ai_calls += 1

        # Step 4: Extract key points
        logger.info(f"Extracting key points: {filename}")
        extraction = await transcriber.extract_key_points(transcription.transcript)
        result.title = extraction.title
        result.summary = extraction.summary
        result.key_points = extraction.key_points
        result.legal_references = extraction.legal_references
        result.topics = extraction.topics
        result.rechtsgebiet = extraction.rechtsgebiet
        result.practical_tips = extraction.practical_tips
        result.ai_calls += 1

        # Step 5: Store in database
        webinar_id = db.store_webinar(result.model_dump())

        # Step 6: Auto-link to content plan keywords
        db.auto_link_webinars_to_keywords()

        logger.info(
            f"Webinar processed: {result.title} "
            f"({result.duration_seconds // 60} min, "
            f"{len(result.key_points)} key points, "
            f"{result.ai_calls} AI calls)"
        )

    except Exception as e:
        logger.error(f"Failed to process webinar {filename}: {type(e).__name__}: {e}")
        result.error = str(e)

    finally:
        # Clean up temp files
        if tmp_dir and tmp_dir.exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)

    return result


async def process_folder(
    folder_id: Optional[str] = None,
) -> List[WebinarResult]:
    """
    Process all new webinar recordings in a Google Drive folder.

    Args:
        folder_id: Google Drive folder ID. Defaults to GOOGLE_DRIVE_WEBINAR_FOLDER env var.

    Returns:
        List of WebinarResult for each processed video
    """
    folder_id = folder_id or os.getenv("GOOGLE_DRIVE_WEBINAR_FOLDER", "")
    if not folder_id:
        raise ValueError(
            "No folder ID provided. Set GOOGLE_DRIVE_WEBINAR_FOLDER in .env "
            "or pass --folder-id"
        )

    db = OpenBlogDB()
    drive_client = DriveClient()
    transcriber = GeminiTranscriber()

    # List files
    files = drive_client.list_files(folder_id)
    logger.info(f"Found {len(files)} video/audio files in folder")

    # Filter already processed
    new_files = [f for f in files if not db.is_webinar_processed(f.id)]
    logger.info(f"New files to process: {len(new_files)} (skipping {len(files) - len(new_files)} already processed)")

    if not new_files:
        logger.info("No new webinars to process")
        return []

    # Process sequentially to avoid API rate limits
    results = []
    for i, file_info in enumerate(new_files, 1):
        logger.info(f"\nProcessing [{i}/{len(new_files)}]: {file_info.name}")
        result = await process_webinar(
            drive_file_id=file_info.id,
            filename=file_info.name,
            drive_client=drive_client,
            transcriber=transcriber,
            db=db,
        )
        results.append(result)

    return results


async def process_local_file(
    file_path: str,
    drive_file_id: Optional[str] = None,
) -> WebinarResult:
    """
    Process a local video/audio file (no Drive download needed).

    Useful for testing or when files are already downloaded.

    Args:
        file_path: Path to local video/audio file
        drive_file_id: Optional ID for tracking (defaults to filename hash)

    Returns:
        WebinarResult
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Generate a stable ID from the filename if none provided
    if not drive_file_id:
        import hashlib
        drive_file_id = f"local_{hashlib.sha256(path.name.encode()).hexdigest()[:16]}"

    return await process_webinar(
        drive_file_id=drive_file_id,
        filename=path.name,
        local_path=path,
    )
