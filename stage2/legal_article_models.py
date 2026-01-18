"""
Legal Article Models for Decision-Centric Generation.

This module defines the two-phase generation models:
- Phase 1: Generate structured outline mapping sections to court decisions
- Phase 2: Generate section content with type-specific constraints

Section Types:
- decision_anchor: Content built around a specific Leitsatz (MUST cite the assigned decision)
- context: General statutory references only (no legal claims requiring court backing)
- practical_advice: Actionable tips for readers (no legal claims)
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class SectionOutline(BaseModel):
    """
    Outline for a single article section.

    Each section is categorized by type:
    - decision_anchor: Must cite and explain its assigned court decision
    - context: Only statutory references (§ XYZ BGB), no interpretive claims
    - practical_advice: Tips and recommendations, no legal claims
    """

    section_id: str = Field(
        ...,
        description="Section identifier (e.g., 'section_01', 'section_02')"
    )

    title: str = Field(
        ...,
        description="Section heading/title"
    )

    section_type: Literal["decision_anchor", "context", "practical_advice"] = Field(
        ...,
        description="Type determines content constraints"
    )

    anchored_decision_aktenzeichen: Optional[str] = Field(
        default=None,
        description="Aktenzeichen of the court decision this section explains (required if decision_anchor)"
    )

    content_brief: str = Field(
        ...,
        description="Brief description of what this section should cover (2-3 sentences)"
    )

    relevant_statutes: List[str] = Field(
        default_factory=list,
        description="Statutes to reference (e.g., ['§ 623 BGB', '§ 1 KSchG'])"
    )

    @field_validator('section_id')
    @classmethod
    def validate_section_id(cls, v):
        """Ensure section_id follows expected format."""
        if not v.startswith('section_'):
            raise ValueError(f"section_id must start with 'section_', got: {v}")
        return v

    @field_validator('title')
    @classmethod
    def validate_title_not_empty(cls, v):
        """Ensure title is not empty."""
        if not v or not v.strip():
            raise ValueError("Section title cannot be empty")
        return v.strip()


class ArticleOutline(BaseModel):
    """
    Complete article outline for decision-centric generation.

    Generated in Phase 1, used to guide Phase 2 section generation.
    Maps each content section to a specific court decision or section type.
    """

    headline: str = Field(
        ...,
        description="Article headline with primary keyword"
    )

    teaser: str = Field(
        ...,
        description="2-3 sentence hook (pain point or benefit)"
    )

    direct_answer: str = Field(
        ...,
        description="40-60 word direct answer to the keyword question"
    )

    intro_brief: str = Field(
        ...,
        description="Brief description of what the intro should cover"
    )

    target_sections: List[SectionOutline] = Field(
        ...,
        description="Ordered list of sections with their types and assignments"
    )

    faq_topics: List[str] = Field(
        default_factory=list,
        description="4-6 FAQ question topics to cover"
    )

    key_takeaway_topics: List[str] = Field(
        default_factory=list,
        description="3 key takeaway topics"
    )

    @field_validator('headline')
    @classmethod
    def validate_headline(cls, v):
        """Ensure headline is not empty."""
        if not v or not v.strip():
            raise ValueError("Headline cannot be empty")
        return v.strip()

    @field_validator('target_sections')
    @classmethod
    def validate_sections_count(cls, v):
        """Ensure we have 4-6 sections."""
        if len(v) < 4:
            raise ValueError(f"Need at least 4 sections, got {len(v)}")
        if len(v) > 7:
            raise ValueError(f"Maximum 7 sections, got {len(v)}")
        return v

    def get_decision_anchor_sections(self) -> List[SectionOutline]:
        """Get all sections anchored to court decisions."""
        return [s for s in self.target_sections if s.section_type == "decision_anchor"]

    def get_context_sections(self) -> List[SectionOutline]:
        """Get all context-only sections."""
        return [s for s in self.target_sections if s.section_type == "context"]

    def get_practical_sections(self) -> List[SectionOutline]:
        """Get all practical advice sections."""
        return [s for s in self.target_sections if s.section_type == "practical_advice"]

    def validate_decision_coverage(self, available_decisions: List[str]) -> List[str]:
        """
        Check that all anchored decisions exist in available decisions.

        Args:
            available_decisions: List of Aktenzeichen from legal context

        Returns:
            List of missing Aktenzeichen (empty if all valid)
        """
        missing = []
        for section in self.get_decision_anchor_sections():
            if section.anchored_decision_aktenzeichen:
                if section.anchored_decision_aktenzeichen not in available_decisions:
                    missing.append(section.anchored_decision_aktenzeichen)
        return missing


class GeneratedSection(BaseModel):
    """
    Output from Phase 2 section generation.

    Contains the generated content and metadata for verification.
    """

    section_id: str = Field(
        ...,
        description="Section identifier matching the outline"
    )

    title: str = Field(
        ...,
        description="Section heading"
    )

    content: str = Field(
        ...,
        description="HTML content for the section"
    )

    section_type: Literal["decision_anchor", "context", "practical_advice"] = Field(
        ...,
        description="Type from the outline"
    )

    cited_decision: Optional[str] = Field(
        default=None,
        description="Aktenzeichen of cited decision (for decision_anchor sections)"
    )

    cited_statutes: List[str] = Field(
        default_factory=list,
        description="Statutes cited in this section"
    )

    @field_validator('content')
    @classmethod
    def validate_content_not_empty(cls, v):
        """Ensure content is not empty."""
        if not v or not v.strip():
            raise ValueError("Section content cannot be empty")
        return v.strip()


def calculate_section_allocation(num_decisions: int) -> dict:
    """
    Calculate optimal section allocation based on available court decisions.

    Rules:
    - 2 decisions → 2 decision_anchor, 2 context, 1 practical
    - 4 decisions → 4 decision_anchor, 1 context, 1 practical
    - 6+ decisions → 5 decision_anchor (pick most relevant), 1 context, 1 practical

    Args:
        num_decisions: Number of available court decisions

    Returns:
        Dict with counts for each section type
    """
    if num_decisions <= 2:
        return {
            "decision_anchor": min(num_decisions, 2),
            "context": 2,
            "practical_advice": 1
        }
    elif num_decisions <= 4:
        return {
            "decision_anchor": num_decisions,
            "context": 1,
            "practical_advice": 1
        }
    else:  # 5+ decisions
        return {
            "decision_anchor": 5,  # Pick top 5 most relevant
            "context": 1,
            "practical_advice": 1
        }
