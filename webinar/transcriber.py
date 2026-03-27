"""
Gemini Transcriber

Transcribes video/audio files using Gemini 2.5 Pro's native multimodal capabilities.
Uses the Gemini File API for upload and processing.

No additional dependencies beyond google-genai (already in requirements).
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

from .webinar_models import TranscriptionResult, KeyPointExtraction

logger = logging.getLogger(__name__)

# Transcription model — use the same model as the pipeline
_TRANSCRIPTION_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")

# Prompts
_TRANSCRIPTION_PROMPT = """Transcribe this video/audio recording completely and accurately.

This is a legal webinar recording in German. Provide:

1. **Full transcript**: Write out everything said, preserving the original language (German).
   - Include speaker changes when detectable (e.g., "Sprecher 1:", "Moderator:")
   - Preserve legal terminology exactly as spoken
   - Include timestamps approximately every 5 minutes if possible

2. **Speaker names**: If speakers introduce themselves or are introduced, list their names.

3. **Duration**: Estimate the total duration in seconds.

4. **Language**: Confirm the primary language.

Return the result as JSON:
{
    "transcript": "Full transcript text here...",
    "duration_seconds": 2700,
    "speaker_names": ["Dr. Schmidt", "Rechtsanwalt Müller"],
    "language": "de"
}
"""

_EXTRACTION_PROMPT = """Analyze the following transcript from a legal webinar and extract structured information.

TRANSCRIPT:
{transcript}

Extract the following:

1. **title**: A concise title for this webinar (max 80 chars)
2. **summary**: A 2-3 sentence summary suitable for a newsletter. Should be informative and engaging.
3. **key_points**: 5-10 key takeaways from the webinar. Each should be a complete, standalone sentence.
4. **legal_references**: All statutes (§ XYZ BGB/KSchG/etc.) and court decisions (BGH Az. ..., BAG Az. ...) mentioned.
5. **topics**: 3-5 topic keywords for categorization (e.g., "Kündigungsschutz", "Abfindung", "Betriebsrat")
6. **rechtsgebiet**: The primary legal area (Arbeitsrecht, Mietrecht, Erbrecht, Familienrecht, Vertragsrecht, Steuerrecht, or other)
7. **practical_tips**: Any practical advice or actionable recommendations mentioned.

Return as JSON:
{{
    "title": "...",
    "summary": "...",
    "key_points": ["...", "..."],
    "legal_references": ["§ 1 KSchG", "BAG Az. 2 AZR 123/22"],
    "topics": ["Kündigungsschutz", "..."],
    "rechtsgebiet": "Arbeitsrecht",
    "practical_tips": ["...", "..."]
}}
"""


class GeminiTranscriber:
    """Transcribes video/audio using Gemini's native multimodal capabilities."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be set")

        from google import genai as _genai
        from google.genai import types as _types
        self._genai = _genai
        self._types = _types
        self.client = _genai.Client(api_key=self.api_key)

    async def transcribe(self, video_path: Path) -> TranscriptionResult:
        """
        Transcribe a video/audio file using Gemini File API.

        Process:
        1. Upload file to Gemini File API
        2. Wait for processing to complete
        3. Send to Gemini with transcription prompt
        4. Parse structured response

        Args:
            video_path: Path to the video/audio file

        Returns:
            TranscriptionResult with transcript and metadata
        """
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        file_size_mb = video_path.stat().st_size / 1024 / 1024
        logger.info(f"Uploading {video_path.name} ({file_size_mb:.1f} MB) to Gemini File API...")

        # Step 1: Upload file
        uploaded_file = self.client.files.upload(file=str(video_path))
        logger.info(f"File uploaded: {uploaded_file.name} (state: {uploaded_file.state})")

        # Step 2: Wait for processing
        while uploaded_file.state == "PROCESSING":
            logger.info("  Waiting for file processing...")
            time.sleep(5)
            uploaded_file = self.client.files.get(name=uploaded_file.name)

        if uploaded_file.state == "FAILED":
            raise RuntimeError(f"File processing failed: {uploaded_file.name}")

        logger.info(f"File ready: {uploaded_file.name}")

        # Step 3: Transcribe with Gemini
        try:
            response = self.client.models.generate_content(
                model=_TRANSCRIPTION_MODEL,
                contents=[
                    self._types.Content(
                        role="user",
                        parts=[
                            self._types.Part.from_uri(
                                file_uri=uploaded_file.uri,
                                mime_type=uploaded_file.mime_type,
                            ),
                            self._types.Part.from_text(text=_TRANSCRIPTION_PROMPT),
                        ],
                    )
                ],
                config=self._types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )

            text = response.text.strip()
            # Remove markdown code fences if present
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            data = json.loads(text)

            result = TranscriptionResult(
                transcript=data.get("transcript", ""),
                duration_seconds=data.get("duration_seconds", 0),
                speaker_names=data.get("speaker_names", []),
                language=data.get("language", "de"),
            )

            logger.info(
                f"Transcription complete: {len(result.transcript)} chars, "
                f"~{result.duration_seconds // 60} min"
            )
            return result

        finally:
            # Clean up uploaded file
            try:
                self.client.files.delete(name=uploaded_file.name)
                logger.debug(f"Cleaned up uploaded file: {uploaded_file.name}")
            except Exception as e:
                logger.warning(f"Failed to clean up file {uploaded_file.name}: {e}")

    async def extract_key_points(self, transcript: str) -> KeyPointExtraction:
        """
        Extract structured key points from a transcript using Gemini.

        Args:
            transcript: Full transcript text

        Returns:
            KeyPointExtraction with title, summary, key_points, etc.
        """
        if not transcript:
            return KeyPointExtraction()

        # Truncate very long transcripts to fit context
        max_chars = 500_000
        if len(transcript) > max_chars:
            transcript = transcript[:max_chars] + "\n\n[... transcript truncated ...]"

        prompt = _EXTRACTION_PROMPT.format(transcript=transcript)

        response = self.client.models.generate_content(
            model=_TRANSCRIPTION_MODEL,
            contents=prompt,
            config=self._types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )

        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        data = json.loads(text)

        result = KeyPointExtraction(
            title=data.get("title", ""),
            summary=data.get("summary", ""),
            key_points=data.get("key_points", []),
            legal_references=data.get("legal_references", []),
            topics=data.get("topics", []),
            rechtsgebiet=data.get("rechtsgebiet", ""),
            practical_tips=data.get("practical_tips", []),
        )

        logger.info(
            f"Extraction complete: {len(result.key_points)} key points, "
            f"{len(result.legal_references)} legal refs, "
            f"rechtsgebiet: {result.rechtsgebiet}"
        )
        return result
