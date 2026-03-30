"""
Stage 0: Humanization Research - Data Models

Pydantic models for Stage 0 input/output.
Contains research data scraped before content generation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ForumQuestion(BaseModel):
    """A real user question scraped from a legal forum."""
    source: str = Field(..., description="Forum name (e.g., juraforum.de)")
    question: str = Field(..., description="Thread title / question text")
    context: str = Field(default="", description="First 200 chars of original post")
    url: str = Field(default="", description="Thread URL")


class CompetitorPage(BaseModel):
    """Headings scraped from a competitor's ranking article."""
    url: str = Field(..., description="Competitor article URL")
    title: str = Field(default="", description="Page title")
    headings: List[str] = Field(default_factory=list, description="H2/H3 headings (prefixed with 'H2:' or 'H3:')")


class Stage0Output(BaseModel):
    """
    Output from Stage 0: Humanization Research.

    Contains real user questions, Google PAA questions, and competitor
    article structures — all used to make Stage 2 output more human.
    """
    paa_questions: List[str] = Field(
        default_factory=list,
        description="Google 'People Also Ask' / 'Ähnliche Fragen' questions"
    )
    forum_questions: List[ForumQuestion] = Field(
        default_factory=list,
        description="Real user questions from legal forums"
    )
    competitor_headings: List[CompetitorPage] = Field(
        default_factory=list,
        description="H2/H3 headings from top ranking competitor articles"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Non-fatal errors from individual scrapers"
    )
