"""Pydantic models for Beck-Online resource extraction."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class BeckExtractionInput(BaseModel):
    """Input for Beck-Online resource extraction."""

    titles: List[str] = Field(
        ...,
        min_length=1,
        description="Article titles/keywords to extract resources for",
    )
    rechtsgebiet: Optional[str] = Field(
        default=None,
        description="German legal area (auto-detected if not provided)",
    )
    use_mock: bool = Field(
        default=False,
        description="Use mock data instead of live Beck-Online",
    )


class BeckResourceResult(BaseModel):
    """Result for a single keyword extraction."""

    keyword: str
    rechtsgebiet: str = ""
    resources_count: int = 0
    resources: List[Dict] = Field(default_factory=list)
    error: Optional[str] = None


class BeckExtractionOutput(BaseModel):
    """Output from Beck-Online resource extraction."""

    results: List[BeckResourceResult] = Field(default_factory=list)
    total_resources: int = 0
    total_keywords: int = 0
    errors: List[str] = Field(default_factory=list)
