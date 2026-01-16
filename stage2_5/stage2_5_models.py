"""
Stage 2.5 Input/Output Models

Defines the data structures for legal verification.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class LegalClaim(BaseModel):
    """
    Represents a single legal claim extracted from article content.

    A legal claim is any statement about legal rights, obligations,
    procedures, or consequences that should be supported by court decisions.
    """
    claim_text: str = Field(
        ...,
        description="The exact legal claim text from the article"
    )
    field: str = Field(
        ...,
        description="ArticleOutput field where claim appears (e.g., 'section_02_content')"
    )
    cited_source: Optional[str] = Field(
        default=None,
        description="Legal source cited in the claim (e.g., '§ 623 BGB', 'BAG, Urt. v. 12.05.2024 – 6 AZR 123/23')"
    )
    supported: bool = Field(
        default=False,
        description="Whether this claim is supported by provided court decisions"
    )
    matching_decision: Optional[str] = Field(
        default=None,
        description="Aktenzeichen of supporting decision if found (e.g., '6 AZR 123/23')"
    )
    confidence: Optional[str] = Field(
        default=None,
        description="Confidence level: 'high', 'medium', 'low'"
    )


class Stage25Input(BaseModel):
    """
    Input for Stage 2.5 Legal Verification.

    Receives an article from Stage 2 and the legal context from Stage 1
    to verify legal claims.
    """
    article: Dict[str, Any] = Field(
        ...,
        description="ArticleOutput dict from Stage 2 (with all content fields)"
    )
    legal_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="LegalContext dict from Stage 1 (with court_decisions)"
    )


class Stage25Output(BaseModel):
    """
    Output from Stage 2.5 Legal Verification.

    Returns the article with updated legal verification fields and
    detailed verification metrics.
    """
    article: Dict[str, Any] = Field(
        ...,
        description="Article with legal_verification_status and legal_issues updated"
    )
    claims_extracted: int = Field(
        default=0,
        description="Total number of legal claims extracted from article"
    )
    claims_supported: int = Field(
        default=0,
        description="Number of claims supported by provided court decisions"
    )
    claims_unsupported: int = Field(
        default=0,
        description="Number of claims lacking support in provided decisions"
    )
    legal_claims: List[LegalClaim] = Field(
        default_factory=list,
        description="Detailed list of all extracted claims with verification results"
    )
    ai_calls: int = Field(
        default=0,
        description="Number of AI API calls made (1 for verification)"
    )
    verification_skipped: bool = Field(
        default=False,
        description="True if verification was skipped (no legal context provided)"
    )

    class Config:
        extra = "ignore"
