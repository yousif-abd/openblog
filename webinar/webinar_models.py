"""Pydantic models for webinar processing."""

from typing import List, Optional

from pydantic import BaseModel, Field


class TranscriptionResult(BaseModel):
    """Result from Gemini transcription of a video."""

    transcript: str = Field(default="", description="Full transcript text")
    duration_seconds: int = Field(default=0, description="Estimated video duration")
    speaker_names: List[str] = Field(default_factory=list, description="Detected speaker names")
    language: str = Field(default="de", description="Detected language")


class KeyPointExtraction(BaseModel):
    """Structured extraction from webinar content."""

    title: str = Field(default="", description="Webinar title (extracted or inferred)")
    summary: str = Field(default="", description="2-3 sentence summary for newsletter")
    key_points: List[str] = Field(default_factory=list, description="5-10 key takeaways")
    legal_references: List[str] = Field(
        default_factory=list,
        description="Referenced statutes and court decisions (e.g., § 623 BGB, BGH Az. ...)",
    )
    topics: List[str] = Field(
        default_factory=list,
        description="3-5 topic keywords for matching with content plan",
    )
    rechtsgebiet: str = Field(default="", description="Detected legal area")
    practical_tips: List[str] = Field(
        default_factory=list,
        description="Practical advice mentioned in the webinar",
    )


class WebinarResult(BaseModel):
    """Complete result from processing a webinar."""

    drive_file_id: str
    filename: str
    title: str = ""
    duration_seconds: int = 0
    transcript: str = ""
    summary: str = ""
    key_points: List[str] = Field(default_factory=list)
    legal_references: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    speaker_names: List[str] = Field(default_factory=list)
    rechtsgebiet: str = ""
    practical_tips: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    ai_calls: int = 0


class DriveFileInfo(BaseModel):
    """Google Drive file metadata."""

    id: str
    name: str
    mime_type: str = ""
    size: int = 0
    created_time: str = ""
