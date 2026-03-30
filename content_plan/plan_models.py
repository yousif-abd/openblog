"""Pydantic models for content plan."""

from typing import Optional

from pydantic import BaseModel, Field


class ContentPlanEntry(BaseModel):
    """A single entry in the content plan."""

    title: str = Field(..., description="Article title")
    keyword: str = Field(default="", description="SEO keyword (defaults to title)")
    rechtsgebiet: str = Field(default="", description="German legal area")
    target_date: str = Field(default="", description="Target publication date")
    priority: str = Field(default="", description="Priority level")
    author: str = Field(default="", description="Assigned author")
    word_count: int = Field(default=2000, description="Target word count")
    notes: str = Field(default="", description="Additional notes")
    instructions: str = Field(default="", description="Generation instructions")
    status: str = Field(default="planned", description="planned | in_progress | completed")
