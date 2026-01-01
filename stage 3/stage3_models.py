"""
Stage 3: Quality Check - Data Models

Pydantic models for input/output JSON schemas.
"""

from typing import Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field


class QualityFix(BaseModel):
    """Single surgical fix: find and replace."""

    model_config = ConfigDict(extra="ignore")

    field: str = Field(..., description="Field name where fix applies")
    find: str = Field(..., description="Exact text to find")
    replace: str = Field(..., description="Replacement text")
    reason: str = Field(default="", description="Why this fix was made")

    def __repr__(self) -> str:
        find_preview = self.find[:30] + "..." if len(self.find) > 30 else self.find
        replace_preview = self.replace[:30] + "..." if len(self.replace) > 30 else self.replace
        return f"QualityFix(field={self.field!r}, find={find_preview!r}, replace={replace_preview!r})"


class Stage3Input(BaseModel):
    """Input for Stage 3: Quality Check."""

    model_config = ConfigDict(extra="ignore")

    article: Dict[str, Any] = Field(..., description="ArticleOutput dict from Stage 2")
    keyword: str = Field(default="", description="Primary keyword for context")
    language: str = Field(default="en", description="Target language (en, de, fr, etc.)")
    enabled: bool = Field(default=True, description="Set to False to skip quality check")


class Stage3Output(BaseModel):
    """Output from Stage 3: Quality Check."""

    model_config = ConfigDict(extra="ignore")

    article: Dict[str, Any] = Field(..., description="ArticleOutput with fixes applied")
    fixes_applied: int = Field(default=0, description="Number of fixes applied")
    fixes: List[QualityFix] = Field(default_factory=list, description="List of fixes made")
    ai_calls: int = Field(default=0, description="Number of AI calls made")
    skipped: bool = Field(default=False, description="True if stage was skipped")
