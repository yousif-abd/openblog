"""
Legal Claim Verification Logic

Extracts legal claims from article content and matches them against
provided court decisions from Stage 1 research.

Supports two verification modes:
1. Decision-centric mode: For articles generated with two-phase approach
   - Verifies section types match expected content
   - 0-1 AI calls (vs 7+ in legacy mode)

2. Legacy mode: Full claim extraction and verification
   - Extracts all legal claims using Gemini
   - Matches against court decisions
   - Regenerates sections with unsupported claims

When unsupported claims are found, affected sections are regenerated
using Gemini to ensure natural flow (not just sentence deletion).
"""

import logging
import re
from collections import defaultdict
from typing import Dict, Any, List, Tuple, Optional
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.gemini_client import GeminiClient
from shared.prompt_loader import load_prompt
from stage2_5.stage2_5_models import LegalClaim

logger = logging.getLogger(__name__)


async def verify_legal_claims(
    article: Dict[str, Any],
    legal_context: Optional[Dict[str, Any]]
) -> Tuple[Dict[str, Any], List[LegalClaim], int]:
    """
    Extract legal claims from article and verify against LegalContext.

    Supports two modes:
    1. Decision-centric: If article has section_types_metadata metadata, uses fast verification
    2. Legacy: Full claim extraction and verification with Gemini

    Process (decision-centric mode):
    1. Check section types from section_types_metadata metadata
    2. For decision_anchor sections: verify cited decision exists
    3. For context sections: verify no unsupported legal claims
    4. For practical_advice sections: skip (no legal claims expected)

    Process (legacy mode):
    1. Extract all legal claims from content sections using Gemini
    2. Match claims to court decisions in LegalContext
    3. Flag unsupported claims in article.legal_issues
    4. Update article.legal_verification_status

    Args:
        article: ArticleOutput dict from Stage 2
        legal_context: LegalContext dict from Stage 1 (or None)

    Returns:
        Tuple of (modified_article, legal_claims_list, ai_calls)
        - modified_article has legal_verification_status updated
        - legal_claims_list contains all extracted claims with verification results
        - ai_calls is 0-1 for decision-centric, 1+ for legacy

    Example:
        >>> article, claims, ai_calls = await verify_legal_claims(
        ...     article={"Headline": "...", "section_01_content": "..."},
        ...     legal_context={"court_decisions": [...], "rechtsgebiet": "Arbeitsrecht"}
        ... )
        >>> article["legal_verification_status"]
        'verified'
        >>> len([c for c in claims if not c.supported])
        0
    """
    # Skip verification if no legal context
    if not legal_context:
        logger.info("No legal context provided - skipping verification")
        article["legal_verification_status"] = "skipped"
        return article, [], 0

    # Check for decision-centric generation metadata
    section_types = article.get("section_types_metadata", {})

    if section_types:
        logger.info("Decision-centric article detected - using fast verification")
        return await _verify_decision_centric(article, legal_context, section_types)

    # Legacy verification path
    logger.info("Starting legacy legal claim verification...")

    # Extract article content for verification
    content = _extract_article_content(article)

    # Format court decisions for prompt
    court_decisions = legal_context.get("court_decisions", [])
    decisions_summary = _format_decisions_for_verification(court_decisions)

    # Build verification prompt
    prompt_template = load_prompt("stage2_5", "legal_verification")
    prompt = prompt_template.format(
        content=content,
        court_decisions=decisions_summary
    )

    # Define verification schema
    verification_schema = {
        "type": "object",
        "properties": {
            "legal_claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "claim_text": {"type": "string"},
                        "field": {"type": "string"},
                        "cited_source": {"type": "string"},
                        "supported": {"type": "boolean"},
                        "matching_decision": {"type": "string"},
                        "confidence": {"type": "string", "enum": ["high", "medium", "low"]}
                    },
                    "required": ["claim_text", "field", "supported"]
                }
            }
        },
        "required": ["legal_claims"]
    }

    # Call Gemini with schema (no grounding needed - pure analysis)
    try:
        gemini_client = GeminiClient()
        result = await gemini_client.generate_with_schema(
            prompt=prompt,
            response_schema=verification_schema,
            temperature=0.2  # Low temperature for consistent verification
        )

        # Parse claims
        claims_data = result.get("legal_claims", [])
        claims = [LegalClaim(**claim) for claim in claims_data]

        logger.info(f"Extracted {len(claims)} legal claims")

        # Analyze results
        unsupported = [c for c in claims if not c.supported]
        supported = [c for c in claims if c.supported]

        logger.info(f"  Supported: {len(supported)}")
        logger.info(f"  Unsupported: {len(unsupported)}")

        # Update article metadata
        article["legal_issues"] = [c.claim_text for c in unsupported]
        article["legal_verification_status"] = "verified" if not unsupported else "issues_found"

        # Update rechtliche_grundlagen with matched decisions
        matched_decisions = [c.matching_decision for c in claims if c.matching_decision]
        if matched_decisions:
            article["rechtliche_grundlagen"] = list(set(matched_decisions))

        # Regenerate sections to remove unsupported claims
        ai_calls_for_removal = 0
        if unsupported:
            logger.info(f"Regenerating sections to remove {len(unsupported)} unsupported claims...")
            article, ai_calls_for_removal = await _regenerate_without_claims(
                article, unsupported
            )
            logger.info(f"Regeneration complete: {ai_calls_for_removal} AI calls used")

        total_ai_calls = 1 + ai_calls_for_removal  # 1 for verification + N for regeneration
        logger.info(f"Verification complete: status={article['legal_verification_status']}, total_ai_calls={total_ai_calls}")

        return article, claims, total_ai_calls

    except Exception as e:
        logger.error(f"Legal verification failed: {e}")
        article["legal_verification_status"] = "error"
        article["legal_issues"] = [f"Verification failed: {str(e)}"]
        return article, [], 0


# =============================================================================
# Decision-Centric Verification (Fast Path)
# =============================================================================

async def _verify_decision_centric(
    article: Dict[str, Any],
    legal_context: Dict[str, Any],
    section_types: Dict[str, str]
) -> Tuple[Dict[str, Any], List[LegalClaim], int]:
    """
    Fast verification for decision-centric generated articles.

    This verification is much faster (0-1 AI calls vs 7+) because:
    1. decision_anchor sections are DESIGNED to cite specific decisions
    2. context sections only have statutory references (no legal claims)
    3. practical_advice sections have no legal claims by design

    Verification process:
    - decision_anchor: Verify the assigned decision was cited
    - context: Check for prohibited legal claim patterns
    - practical_advice: Skip (no legal claims expected)

    Args:
        article: ArticleOutput dict with section_types_metadata metadata
        legal_context: LegalContext dict from Stage 1
        section_types: Dict mapping section_id to section_type

    Returns:
        Tuple of (modified_article, legal_claims_list, ai_calls)
    """
    logger.info("=" * 60)
    logger.info("DECISION-CENTRIC VERIFICATION")
    logger.info("=" * 60)

    court_decisions = legal_context.get("court_decisions", [])
    available_aktenzeichen = {d.get("aktenzeichen") for d in court_decisions}

    issues = []
    claims = []
    ai_calls = 0

    # Track statistics
    stats = {
        "decision_anchor": {"total": 0, "verified": 0},
        "thematic_synthesis": {"total": 0, "verified": 0},
        "context": {"total": 0, "verified": 0},
        "practical_advice": {"total": 0, "skipped": 0},
    }

    # Collect thematic_synthesis sections for batched verification
    thematic_sections_to_verify = []

    for section_id, section_type in section_types.items():
        content_field = f"{section_id}_content"
        content = article.get(content_field, "")

        if not content:
            continue

        logger.info(f"  Verifying {section_id} ({section_type})...")

        if section_type == "decision_anchor":
            stats["decision_anchor"]["total"] += 1

            # Verify the section cites a court decision
            has_citation = _content_has_decision_citation(content, available_aktenzeichen)

            if has_citation:
                stats["decision_anchor"]["verified"] += 1
                logger.info(f"    ✓ Decision citation found")

                # Extract the claim for tracking
                claims.append(LegalClaim(
                    claim_text=f"Section anchored to court decision",
                    field=content_field,
                    supported=True,
                    matching_decision=has_citation,
                    confidence="high"
                ))
            else:
                logger.warning(f"    ✗ No decision citation found in decision_anchor section")
                issues.append(f"{section_id}: Missing decision citation")

                claims.append(LegalClaim(
                    claim_text=f"Section should cite a court decision but doesn't",
                    field=content_field,
                    supported=False,
                    confidence="high"
                ))

        elif section_type == "context":
            stats["context"]["total"] += 1

            # Check for prohibited patterns (legal claims without citations)
            prohibited_patterns = _check_prohibited_patterns(content)

            if not prohibited_patterns:
                stats["context"]["verified"] += 1
                logger.info(f"    ✓ No prohibited patterns found")
            else:
                logger.warning(f"    ✗ Found prohibited patterns: {prohibited_patterns}")
                for pattern in prohibited_patterns:
                    issues.append(f"{section_id}: {pattern}")
                    claims.append(LegalClaim(
                        claim_text=pattern,
                        field=content_field,
                        supported=False,
                        confidence="medium"
                    ))

        elif section_type == "thematic_synthesis":
            stats["thematic_synthesis"]["total"] += 1

            # Extract all cited Aktenzeichen and their surrounding propositions
            cited_az = _extract_citations_with_context(content, available_aktenzeichen)

            if not cited_az:
                logger.warning(f"    ✗ No decision citations found in thematic_synthesis section")
                issues.append(f"{section_id}: No decision citations in thematic_synthesis section")
            else:
                # Collect for batched AI verification
                for az, proposition in cited_az:
                    # Find the matching decision's Leitsatz
                    decision_data = next(
                        (d for d in court_decisions if d.get("aktenzeichen") == az), None
                    )
                    if decision_data:
                        thematic_sections_to_verify.append({
                            "section_id": section_id,
                            "content_field": content_field,
                            "aktenzeichen": az,
                            "proposition": proposition,
                            "leitsatz": decision_data.get("leitsatz", ""),
                            "volltext_auszug": decision_data.get("volltext_auszug", ""),
                            "relevante_normen": decision_data.get("relevante_normen", []),
                        })
                    else:
                        logger.warning(f"    ✗ Cited decision {az} not in provided list")
                        issues.append(f"{section_id}: Cites unknown decision {az}")
                        claims.append(LegalClaim(
                            claim_text=f"Cites decision {az} which is not in the provided court decisions",
                            field=content_field,
                            supported=False,
                            confidence="high"
                        ))

                logger.info(f"    → {len(cited_az)} citations queued for proposition-level verification")

        elif section_type == "practical_advice":
            stats["practical_advice"]["total"] += 1
            stats["practical_advice"]["skipped"] += 1
            logger.info(f"    ○ Skipped (practical advice - no legal claims expected)")

    # Batch-verify all thematic_synthesis proposition-citation pairs
    if thematic_sections_to_verify:
        logger.info(f"  Verifying {len(thematic_sections_to_verify)} thematic proposition-citation pairs...")
        thematic_claims, thematic_issues, thematic_ai_calls = await _verify_thematic_propositions(
            thematic_sections_to_verify, court_decisions
        )
        claims.extend(thematic_claims)
        issues.extend(thematic_issues)
        ai_calls += thematic_ai_calls

        # Count verified thematic sections
        verified_sections = set()
        for claim in thematic_claims:
            if claim.supported:
                verified_sections.add(claim.field)
        stats["thematic_synthesis"]["verified"] = len(verified_sections)

    # Log summary
    logger.info("-" * 60)
    logger.info("VERIFICATION SUMMARY:")
    logger.info(f"  decision_anchor: {stats['decision_anchor']['verified']}/{stats['decision_anchor']['total']} verified")
    logger.info(f"  thematic_synthesis: {stats['thematic_synthesis']['verified']}/{stats['thematic_synthesis']['total']} verified")
    logger.info(f"  context: {stats['context']['verified']}/{stats['context']['total']} verified")
    logger.info(f"  practical_advice: {stats['practical_advice']['skipped']}/{stats['practical_advice']['total']} skipped")
    logger.info(f"  Issues found: {len(issues)}")
    logger.info(f"  AI calls used: {ai_calls}")
    logger.info("=" * 60)

    # Update article metadata
    article["legal_issues"] = issues
    article["legal_verification_status"] = "verified" if not issues else "issues_found"

    # Clean up internal metadata (not needed in final output)
    # Keep section_types_metadata for debugging but could remove in production

    unsupported_count = len([c for c in claims if not c.supported])

    logger.info(f"Decision-centric verification complete: {len(claims)} claims, {unsupported_count} unsupported")

    return article, claims, ai_calls


def _content_has_decision_citation(content: str, available_aktenzeichen: set) -> Optional[str]:
    """
    Check if content contains a citation to one of the available court decisions.

    Looks for patterns like:
    - "Az. 6 AZR 123/23"
    - "II R 25/21" (BFH with Roman numerals)
    - "3 K 210/21" (FG with K)
    - "XII ZR 456/22"

    Args:
        content: Section content (HTML)
        available_aktenzeichen: Set of valid Aktenzeichen

    Returns:
        The matched Aktenzeichen if found, None otherwise
    """
    # German court case reference patterns
    # Pattern 1: Numeric prefix (e.g., 6 AZR 123/23)
    # Pattern 2: Roman numeral prefix (e.g., II R 25/21, XII ZR 456/22)
    # Pattern 3: FG pattern with K (e.g., 3 K 210/21)
    az_patterns = [
        r'\b(\d+\s*(?:AZR|ZR|AR|StR|BVR|B|K|S|O|U|L|T|V|W)\s*\d+/\d+)\b',  # Numeric prefix
        r'\b([IVXLC]+\s*(?:R|ZR|AR|B|BVR)\s*\d+/\d+)\b',  # Roman numeral prefix (BFH style)
    ]

    all_matches = []
    for pattern in az_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        all_matches.extend(matches)

    for match in all_matches:
        # Normalize the match (remove extra spaces)
        normalized = re.sub(r'\s+', ' ', match.upper())

        for az in available_aktenzeichen:
            if az:
                # Normalize the available Az too
                normalized_az = re.sub(r'\s+', ' ', az.upper())
                if normalized == normalized_az or normalized in normalized_az or normalized_az in normalized:
                    return az

    return None


def _check_prohibited_patterns(content: str) -> List[str]:
    """
    Check context section for prohibited legal claim patterns.

    Context sections should only have statutory references, not legal interpretations.

    Prohibited patterns:
    - "Die Rechtsprechung hat entschieden..."
    - "Nach ständiger Rechtsprechung..."
    - "Das BAG/BGH hat festgestellt..."
    - Specific legal consequences without citation

    Args:
        content: Section content (HTML)

    Returns:
        List of prohibited pattern descriptions found
    """
    prohibited = []

    # Patterns that suggest legal interpretation without citation
    patterns = [
        (r'(?:Die|Nach)\s+(?:ständiger?\s+)?Rechtsprechung\s+(?:hat|des|ist)', 'Rechtsprechungsverweis ohne Zitat'),
        (r'(?:Das\s+)?(?:BAG|BGH|OLG|LAG|ArbG)\s+hat\s+(?:entschieden|festgestellt|geurteilt)', 'Gerichtsverweis ohne Aktenzeichen'),
        (r'Sie\s+haben\s+(?:Anspruch|Recht)\s+auf', 'Rechtsanspruch ohne Quellenangabe'),
        (r'Der\s+Arbeitgeber\s+(?:muss|ist\s+verpflichtet)', 'Arbeitgeberpflicht ohne Quellenangabe'),
        (r'ist\s+(?:unwirksam|nichtig|rechtswidrig)', 'Rechtsfolge ohne Quellenangabe'),
    ]

    for pattern, description in patterns:
        if re.search(pattern, content, re.IGNORECASE):
            prohibited.append(description)

    return prohibited


def _extract_citations_with_context(
    content: str, available_aktenzeichen: set
) -> List[Tuple[str, str]]:
    """
    Extract all cited Aktenzeichen from content along with the surrounding proposition.

    For each citation found, extracts the sentence or paragraph that contains it,
    which represents the legal proposition the citation is supposed to support.

    Args:
        content: Section content (HTML)
        available_aktenzeichen: Set of valid Aktenzeichen

    Returns:
        List of (aktenzeichen, proposition_text) tuples
    """
    # Strip HTML tags for text extraction
    text = re.sub(r'<[^>]+>', ' ', content)
    text = re.sub(r'\s+', ' ', text).strip()

    results = []

    az_patterns = [
        r'\b(\d+\s*(?:AZR|ZR|AR|StR|BVR|B|K|S|O|U|L|T|V|W)\s*\d+/\d+)\b',
        r'\b([IVXLC]+\s*(?:R|ZR|AR|B|BVR)\s*\d+/\d+)\b',
    ]

    for pattern in az_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            az_text = match.group(1)
            normalized = re.sub(r'\s+', ' ', az_text.upper())

            # Find the matching available Aktenzeichen
            matched_az = None
            for az in available_aktenzeichen:
                if az:
                    normalized_az = re.sub(r'\s+', ' ', az.upper())
                    if normalized == normalized_az or normalized in normalized_az or normalized_az in normalized:
                        matched_az = az
                        break

            if matched_az:
                # Extract surrounding context (the sentence containing this citation)
                start = max(0, match.start() - 300)
                end = min(len(text), match.end() + 300)
                context_text = text[start:end].strip()

                # Try to extract just the sentence
                sentences = re.split(r'(?<=[.!?])\s+', context_text)
                proposition = context_text  # fallback to full context
                for sentence in sentences:
                    if az_text in sentence or normalized.lower() in sentence.lower():
                        proposition = sentence.strip()
                        break

                results.append((matched_az, proposition))

    return results


async def _verify_thematic_propositions(
    pairs: List[Dict[str, Any]],
    court_decisions: List[Dict[str, Any]],
) -> Tuple[List[LegalClaim], List[str], int]:
    """
    Batch-verify proposition-citation pairs for thematic_synthesis sections.

    Sends all pairs to Gemini in ONE call and checks whether each cited
    decision's Leitsatz actually supports the specific legal proposition.

    Args:
        pairs: List of dicts with section_id, content_field, aktenzeichen,
               proposition, leitsatz, volltext_auszug, relevante_normen
        court_decisions: Full list of court decisions for context

    Returns:
        Tuple of (claims_list, issues_list, ai_calls_count)
    """
    if not pairs:
        return [], [], 0

    # Format proposition pairs for the prompt
    pair_texts = []
    for i, pair in enumerate(pairs, 1):
        normen_str = ", ".join(pair["relevante_normen"]) if pair["relevante_normen"] else "keine"
        volltext_snippet = pair.get("volltext_auszug", "")
        if volltext_snippet:
            volltext_snippet = " ".join(volltext_snippet.split()[:150])
            volltext_line = f"\n   Entscheidungsgründe (Auszug): {volltext_snippet}"
        else:
            volltext_line = ""

        pair_texts.append(
            f"Zuordnung {i}:\n"
            f"   Abschnitt: {pair['section_id']}\n"
            f"   Rechtliche Aussage im Artikel: \"{pair['proposition']}\"\n"
            f"   Zitierte Entscheidung: {pair['aktenzeichen']}\n"
            f"   Leitsatz der Entscheidung: {pair['leitsatz']}\n"
            f"   Relevante Normen: {normen_str}"
            f"{volltext_line}"
        )

    proposition_pairs_text = "\n\n".join(pair_texts)

    # Load and format the verification prompt
    prompt_template = load_prompt("stage2_5", "thematic_verification")
    prompt = prompt_template.format(proposition_pairs=proposition_pairs_text)

    # Schema for structured response
    verification_schema = {
        "type": "object",
        "properties": {
            "verifications": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "zuordnung_nr": {"type": "integer"},
                        "supported": {"type": "boolean"},
                        "reason": {"type": "string"},
                        "correction": {"type": "string"}
                    },
                    "required": ["zuordnung_nr", "supported", "reason"]
                }
            }
        },
        "required": ["verifications"]
    }

    claims = []
    issues_list = []
    ai_calls = 0

    try:
        gemini_client = GeminiClient()
        result = await gemini_client.generate_with_schema(
            prompt=prompt,
            response_schema=verification_schema,
            temperature=0.2,
        )
        ai_calls = 1

        verifications = result.get("verifications", [])
        logger.info(f"  Thematic verification returned {len(verifications)} results")

        for v in verifications:
            idx = v.get("zuordnung_nr", 0) - 1
            if 0 <= idx < len(pairs):
                pair = pairs[idx]
                supported = v.get("supported", False)
                reason = v.get("reason", "")
                correction = v.get("correction", "")

                claims.append(LegalClaim(
                    claim_text=pair["proposition"][:200],
                    field=pair["content_field"],
                    cited_source=pair["aktenzeichen"],
                    supported=supported,
                    matching_decision=pair["aktenzeichen"] if supported else None,
                    confidence="high" if supported else "low"
                ))

                if not supported:
                    issue_msg = f"{pair['section_id']}: Citation {pair['aktenzeichen']} does not support claim — {reason}"
                    if correction:
                        issue_msg += f" (Correction: {correction})"
                    issues_list.append(issue_msg)
                    logger.warning(f"    ✗ {issue_msg}")
                else:
                    logger.info(f"    ✓ {pair['section_id']}: {pair['aktenzeichen']} supports claim — {reason}")

    except Exception as e:
        logger.error(f"Thematic proposition verification failed: {e}")
        # On failure, mark all as unverified rather than silently passing
        for pair in pairs:
            claims.append(LegalClaim(
                claim_text=pair["proposition"][:200],
                field=pair["content_field"],
                cited_source=pair["aktenzeichen"],
                supported=False,
                confidence="low"
            ))
            issues_list.append(f"{pair['section_id']}: Verification failed for {pair['aktenzeichen']}: {e}")

    return claims, issues_list, ai_calls


def _extract_article_content(article: Dict[str, Any]) -> str:
    """
    Extract all text content from article for verification.

    Args:
        article: ArticleOutput dict

    Returns:
        Combined text from all content fields
    """
    content_fields = [
        "Headline", "Teaser", "Direct_Answer", "Intro",
        "section_01_title", "section_01_content",
        "section_02_title", "section_02_content",
        "section_03_title", "section_03_content",
        "section_04_title", "section_04_content",
        "section_05_title", "section_05_content",
        "section_06_title", "section_06_content",
        "section_07_title", "section_07_content",
    ]

    parts = []
    for field in content_fields:
        value = article.get(field, "")
        if value and value.strip():
            parts.append(f"[{field}]\n{value}\n")

    return "\n".join(parts)


def _format_decisions_for_verification(court_decisions: List[Dict[str, Any]]) -> str:
    """
    Format court decisions for verification prompt.

    Args:
        court_decisions: List of CourtDecision dicts

    Returns:
        Formatted string with all decisions for verification prompt
    """
    if not court_decisions:
        return "Keine Gerichtsentscheidungen verfügbar."

    parts = []
    for i, decision in enumerate(court_decisions, 1):
        # Extract fields with defaults
        gericht = decision.get("gericht", "Unbekannt")
        aktenzeichen = decision.get("aktenzeichen", "")
        datum = decision.get("datum", "")
        leitsatz = decision.get("leitsatz", "")
        normen = decision.get("relevante_normen", [])
        rechtsgebiet = decision.get("rechtsgebiet", "")

        # Format date to German format (DD.MM.YYYY)
        if datum and len(datum) == 10:  # ISO format YYYY-MM-DD
            try:
                year, month, day = datum.split("-")
                datum = f"{day}.{month}.{year}"
            except:
                pass  # Keep original if parsing fails

        normen_str = ", ".join(normen) if normen else "keine Normen angegeben"

        entry = (
            f"Entscheidung {i}:\n"
            f"  Gericht: {gericht}\n"
            f"  Aktenzeichen: {aktenzeichen}\n"
            f"  Datum: {datum}\n"
            f"  Leitsatz: {leitsatz}\n"
            f"  Relevante Normen: {normen_str}\n"
            f"  Rechtsgebiet: {rechtsgebiet}"
        )

        # Include richer decision context when available
        orientierung = decision.get("orientierungssatz", "")
        if orientierung:
            entry += f"\n  Orientierungssatz: {orientierung}"

        volltext = decision.get("volltext_auszug", "")
        if volltext:
            truncated = " ".join(volltext.split()[:300])
            entry += f"\n  Entscheidungsgründe (Auszug): {truncated}"

        parts.append(entry)

    return "\n\n".join(parts)


async def _regenerate_without_claims(
    article: Dict[str, Any],
    unsupported_claims: List[LegalClaim]
) -> Tuple[Dict[str, Any], int]:
    """
    Regenerate article sections that contain unsupported claims.

    Simply deleting sentences can break flow (orphaned transitions like
    "Furthermore...", dangling references). Instead, this function regenerates
    affected sections using Gemini to ensure coherent text.

    Args:
        article: ArticleOutput dict with unsupported claims
        unsupported_claims: List of LegalClaim objects that are not supported

    Returns:
        Tuple of (modified_article, ai_calls_used)

    Example:
        >>> article, calls = await _regenerate_without_claims(
        ...     article={"section_02_content": "...claim text..."},
        ...     unsupported_claims=[LegalClaim(claim_text="...", field="section_02_content", ...)]
        ... )
        >>> calls
        1
    """
    # Group claims by field
    claims_by_field = defaultdict(list)
    for claim in unsupported_claims:
        claims_by_field[claim.field].append(claim.claim_text)

    if not claims_by_field:
        return article, 0

    ai_calls = 0
    gemini_client = GeminiClient()

    for field, claim_texts in claims_by_field.items():
        if field not in article or not article[field]:
            continue

        original_content = article[field]

        # Build regeneration prompt
        prompt = f"""Rewrite the following article section, but REMOVE these specific legal claims that are not supported by court decisions:

CLAIMS TO REMOVE:
{chr(10).join(f"- {claim}" for claim in claim_texts)}

ORIGINAL SECTION:
{original_content}

INSTRUCTIONS:
1. Remove the sentences containing the unsupported claims listed above
2. Rewrite surrounding text so it flows naturally (fix transitions, remove dangling references)
3. Keep all OTHER content intact - only remove/modify what's necessary
4. Maintain the same HTML formatting (<p>, <ul>, <li>, <strong>, etc.)
5. Do NOT add new legal claims or facts
6. Output ONLY the rewritten section, no explanations

REWRITTEN SECTION:"""

        try:
            result = await gemini_client.generate(
                prompt=prompt,
                use_url_context=False,
                use_google_search=False,
                json_output=False,
                temperature=0.2,  # Low temp for consistency
                max_tokens=4096
            )

            # Update article with regenerated content
            article[field] = result.strip()
            ai_calls += 1
            logger.info(f"Regenerated {field} without {len(claim_texts)} unsupported claims")

        except Exception as e:
            logger.error(f"Failed to regenerate {field}: {e}")
            # Fallback: simple sentence removal if regeneration fails
            for claim_text in claim_texts:
                article[field] = _remove_sentence_containing(article[field], claim_text)
            logger.warning(f"Used fallback sentence removal for {field}")

    return article, ai_calls


def _remove_sentence_containing(content: str, claim_text: str) -> str:
    """
    Fallback: Remove sentence containing claim text using regex.

    Used when Gemini regeneration fails. May leave awkward flow,
    but ensures unsupported claims are removed.

    Args:
        content: HTML content string
        claim_text: The unsupported claim text to remove

    Returns:
        Content with sentence removed
    """
    # Use first 50 chars for matching (claims can be long)
    search_text = claim_text[:50] if len(claim_text) > 50 else claim_text
    # Escape special regex chars
    escaped = re.escape(search_text)
    # Match sentence containing the claim (ends with . ! or ?)
    pattern = rf'[^.!?]*{escaped}[^.!?]*[.!?]\s*'
    return re.sub(pattern, '', content, flags=re.IGNORECASE)
