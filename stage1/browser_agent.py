"""
Beck-Online browser automation agent using browserUse.

Navigates beck-online.beck.de, authenticates, searches for court decisions and legal commentary,
and extracts structured data. Uses Gemini as the LLM (consistent with rest of pipeline).

This module is used when use_mock=False in legal_researcher.py.
"""

import os
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List

# Add stage1 to path for imports
stage1_path = Path(__file__).parent
if str(stage1_path) not in sys.path:
    sys.path.insert(0, str(stage1_path))

from legal_models import CourtDecision, LegalContext

logger = logging.getLogger(__name__)

# Import browserUse components (will be installed in requirements.txt)
try:
    from browser_use import Agent
    from browser_use.llm.google.chat import ChatGoogle
    BROWSER_USE_AVAILABLE = True
except ImportError:
    BROWSER_USE_AVAILABLE = False
    logger.warning("browserUse not available - install with: pip install browser-use playwright")


async def _execute_beck_research_internal(
    keywords: List[str],
    rechtsgebiet: str,
    beck_username: str,
    beck_password: str,
    gemini_api_key: str
) -> LegalContext:
    """
    Internal: Execute Beck-Online research (extracted for retry wrapper).

    This function contains the browser automation logic.
    Separated to allow retry wrapper in research_via_beck_online.

    Args:
        keywords: List of article keywords
        rechtsgebiet: German legal area
        beck_username: Beck-Online username
        beck_password: Beck-Online password
        gemini_api_key: Gemini API key

    Returns:
        LegalContext with court decisions from Beck-Online

    Raises:
        Exception: If browser automation fails
    """
    # Initialize Gemini for browserUse using browser-use's native ChatGoogle
    # Use browser-use's native ChatGoogle (not LangChain)
    # This avoids Pydantic v2 compatibility issues with ainvoke monkey-patching
    # Using stable model for higher quota: 60 RPM vs 10 RPM for -exp
    llm = ChatGoogle(
        model="gemini-2.0-flash",  # Stable model (60 RPM vs 10 RPM for -exp)
        api_key=gemini_api_key,
        temperature=0.1  # Low temperature for precise extraction
    )

    # Create planner LLM with faster model for planning phase
    planner_llm = ChatGoogle(
        model="gemini-2.5-flash-latest",  # Faster model for planning
        api_key=gemini_api_key,
        temperature=0.1
    )

    # Normalize keywords
    normalized_keywords = []
    for kw in keywords:
        if isinstance(kw, dict):
            normalized_keywords.append(kw.get("keyword", ""))
        else:
            normalized_keywords.append(str(kw))

    # Build search task for Beck-Online
    keywords_str = ", ".join(normalized_keywords)

    # Simplified task prompt - detailed login, vague search/extract
    task = f"""
RULES:
- If you see a cookie popup, click "Alle akzeptieren" immediately
- If stuck on a page, click browser back button to recover
- Do NOT type into any search bar until after login is complete

STEP 1: LOGIN TO BECK-ONLINE
-----------------------------
1. Go to https://beck-online.beck.de
2. On the RIGHT side of the page, find the "Mein beck-online" box
3. Click "Anmelden" button in that box
4. On the login page, enter:
   - Username: {beck_username}
   - Password: {beck_password}
5. Click the login button
6. Wait for login to complete (you should see "Abmelden" instead of "Anmelden")

STEP 2: SEARCH AND EXTRACT
--------------------------
After successful login:
1. Search for: {keywords_str} {rechtsgebiet}
2. Filter results to show only court decisions (Rechtsprechung/Urteile)
3. Find and extract 3 recent court decisions with these fields:
   - Gericht (court name)
   - Aktenzeichen (case reference)
   - Datum (date)
   - Leitsatz (legal principle)
   - Relevante Normen (cited statutes)
   - URL (full beck-online URL)

OUTPUT FORMAT:
Decision 1:
Gericht: [value]
Aktenzeichen: [value]
Datum: [DD.MM.YYYY]
Leitsatz: [value]
Relevante Normen: [value]
URL: [value]

Decision 2:
[same format]

Decision 3:
[same format]
    """

    logger.info("Starting browser agent...")
    agent = Agent(
        task=task,
        llm=llm,
        planner_llm=planner_llm,  # Separate LLM for planning
        use_vision=False,  # Disabled to reduce API calls by ~80%
        max_failures=3,  # Allow up to 3 retries
        max_actions_per_step=15,  # Limit actions to prevent runaway loops
        # Additional browser-use configuration
        # headless mode can be configured via browser context if needed
    )

    # Execute browser automation
    result = await agent.run()

    logger.info(f"Browser agent completed: {result}")

    # Parse extracted data into CourtDecision objects
    court_decisions = _parse_beck_online_results(result, rechtsgebiet)

    # Generate disclaimer
    disclaimer = _generate_disclaimer(rechtsgebiet)

    # Build context
    return LegalContext(
        rechtsgebiet=rechtsgebiet,
        court_decisions=court_decisions,
        statutes=[],  # Phase 2 feature
        disclaimer_template=disclaimer,
        stand_der_rechtsprechung=datetime.now().strftime("%Y-%m-%d"),
        keywords_researched=normalized_keywords
    )


async def _execute_beck_research_with_retry(
    keywords: List[str],
    rechtsgebiet: str,
    beck_username: str,
    beck_password: str,
    gemini_api_key: str,
    max_retries: int = 2
) -> LegalContext:
    """
    Execute Beck-Online research with automatic retry on quota errors.

    Implements exponential backoff:
    - Retry 1: 60s delay
    - Retry 2: 120s delay

    Falls back via exception if all retries exhausted (caller handles fallback to mock).

    Args:
        keywords: Search keywords
        rechtsgebiet: Legal area
        beck_username: Beck-Online username
        beck_password: Beck-Online password
        gemini_api_key: Gemini API key
        max_retries: Max retry attempts (default: 2)

    Returns:
        LegalContext with court decisions

    Raises:
        Exception: If all retries exhausted or non-retryable error
    """
    import asyncio

    for attempt in range(max_retries + 1):
        try:
            return await _execute_beck_research_internal(
                keywords=keywords,
                rechtsgebiet=rechtsgebiet,
                beck_username=beck_username,
                beck_password=beck_password,
                gemini_api_key=gemini_api_key
            )
        except Exception as e:
            error_str = str(e)
            is_quota_error = (
                "429" in error_str or
                "RESOURCE_EXHAUSTED" in error_str or
                "quota" in error_str.lower() or
                "rate limit" in error_str.lower()
            )

            if is_quota_error and attempt < max_retries:
                delay = 60 * (2 ** attempt)  # 60s, 120s exponential backoff
                logger.warning(
                    f"API quota exceeded (attempt {attempt + 1}/{max_retries + 1}), "
                    f"retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
            else:
                # Non-retryable error or max retries reached
                if is_quota_error:
                    logger.error(f"Max retries ({max_retries}) exceeded for quota error")
                raise


async def research_via_beck_online(
    keywords: List[str],
    rechtsgebiet: str = "Arbeitsrecht"
) -> LegalContext:
    """
    Research German court decisions on Beck-Online using browser automation.

    Automatically retries on API quota errors with exponential backoff.

    Beck-Online provides comprehensive legal content including:
    - Court decisions from all German courts
    - Authoritative commentary (Palandt, MüKo, etc.)
    - Statute text and annotations

    Process:
    1. Initialize Gemini-powered browser agent
    2. Navigate to beck-online.beck.de
    3. Authenticate with BECK_USERNAME/BECK_PASSWORD from environment
    4. For each keyword, search for recent decisions in rechtsgebiet
    5. Extract top 3-5 results per keyword (Gericht, Aktenzeichen, Datum, Leitsatz, Normen)
    6. Return structured LegalContext
    7. Auto-retry on quota errors (60s, 120s delays)

    API Quota Optimizations:
    - Uses stable model (gemini-2.0-flash, 60 RPM vs 10 RPM for -exp)
    - Vision disabled (reduces API calls by ~80%)
    - Action limiting (max_actions_per_step=15)
    - Automatic retry with exponential backoff

    Args:
        keywords: List of article keywords
        rechtsgebiet: German legal area (Arbeitsrecht, Mietrecht, etc.)

    Returns:
        LegalContext with court decisions from Beck-Online

    Raises:
        ImportError: If browserUse not installed
        ValueError: If BECK_USERNAME or BECK_PASSWORD missing from environment
        Exception: If browser automation fails (after all retries)

    Example:
        >>> context = await research_via_beck_online(
        ...     keywords=["Kündigung"],
        ...     rechtsgebiet="Arbeitsrecht"
        ... )
        >>> assert all(d.url.startswith("https://beck-online.beck.de") for d in context.court_decisions)
    """
    if not BROWSER_USE_AVAILABLE:
        raise ImportError(
            "browserUse not installed. Run: pip install browser-use playwright && playwright install chromium"
        )

    # Check credentials
    beck_username = os.getenv("BECK_USERNAME")
    beck_password = os.getenv("BECK_PASSWORD")

    if not beck_username or not beck_password:
        raise ValueError(
            "BECK_USERNAME and BECK_PASSWORD must be set in .env file for Beck-Online access"
        )

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY must be set in .env file")

    logger.info(f"Initializing browser agent for Beck-Online research: {rechtsgebiet}")

    # Execute with retry
    return await _execute_beck_research_with_retry(
        keywords=keywords,
        rechtsgebiet=rechtsgebiet,
        beck_username=beck_username,
        beck_password=beck_password,
        gemini_api_key=gemini_api_key,
        max_retries=2
    )


def _parse_beck_online_results(browser_output, rechtsgebiet: str) -> List[CourtDecision]:
    """
    Parse browser agent output into CourtDecision objects.

    The browser agent returns an AgentHistoryList containing extracted decisions.

    Args:
        browser_output: AgentHistoryList from browser agent
        rechtsgebiet: Legal area

    Returns:
        List of CourtDecision objects
    """
    import re
    from datetime import datetime

    decisions = []

    logger.info("Parsing browser agent output for court decisions...")

    # Extract all content from AgentHistoryList
    try:
        content_items = browser_output.extracted_content()
        if not content_items:
            logger.warning("No extracted content from browser agent")
            return decisions

        # Combine all extracted content chunks
        output_str = '\n'.join(content_items)
        logger.info(f"Extracted {len(content_items)} content item(s) from browser agent")
    except Exception as e:
        logger.error(f"Failed to extract content from browser output: {e}")
        # Fallback to string conversion if extraction fails
        output_str = str(browser_output)
        logger.warning("Falling back to string conversion of browser output")

    # Extract decision blocks (each starts with "Decision N:" or "Gericht:")
    # The browser agent returns text like:
    # Decision 1:
    # Gericht: LAG Düsseldorf
    # Aktenzeichen: 4 Ta 200/20
    # Datum: 02.07.2020
    # Leitsatz: ...
    # Relevante Normen: ...
    # URL: ...

    # Split by "Decision" or "Gericht:" markers
    decision_blocks = re.split(r'Decision \d+:|(?=Gericht:)', output_str)

    for block in decision_blocks:
        if not block.strip() or 'Gericht:' not in block:
            continue

        try:
            # Extract fields using regex
            gericht_match = re.search(r'Gericht:\s*([^\n]+)', block)
            aktenzeichen_match = re.search(r'Aktenzeichen:\s*([^\n]+)', block)
            datum_match = re.search(r'Datum:\s*([^\n]+)', block)
            leitsatz_match = re.search(r'Leitsatz:\s*([^\n]+)', block)
            normen_match = re.search(r'Relevante Normen:\s*([^\n]+)', block)
            url_match = re.search(r'URL:\s*([^\n]+)', block)

            if not gericht_match or not aktenzeichen_match:
                logger.warning(f"Skipping incomplete decision block: missing Gericht or Aktenzeichen")
                continue

            gericht = gericht_match.group(1).strip()
            aktenzeichen = aktenzeichen_match.group(1).strip()
            datum_str = datum_match.group(1).strip() if datum_match else ""
            leitsatz = leitsatz_match.group(1).strip() if leitsatz_match else ""
            normen_str = normen_match.group(1).strip() if normen_match else ""
            url = url_match.group(1).strip() if url_match else ""

            # Skip if marked as "Not available"
            if leitsatz.lower() in ["not available", "n/a", ""]:
                leitsatz = ""
            if normen_str.lower() in ["not available", "n/a", ""]:
                normen_str = ""

            # Parse relevante_normen (comma or pipe separated)
            relevante_normen = []
            if normen_str:
                # Split by | or , and clean
                normen_list = re.split(r'[|,]', normen_str)
                relevante_normen = [n.strip() for n in normen_list if n.strip()]

            # Fix URL (browser agent might return relative path)
            if url and not url.startswith("http"):
                url = f"https://beck-online.beck.de{url}"

            # Parse date (DD.MM.YYYY format)
            datum_parsed = None
            if datum_str:
                try:
                    datum_parsed = datetime.strptime(datum_str, "%d.%m.%Y").strftime("%Y-%m-%d")
                except ValueError:
                    logger.warning(f"Could not parse date: {datum_str}")

            # Create CourtDecision
            decision = CourtDecision(
                gericht=gericht,
                aktenzeichen=aktenzeichen,
                datum=datum_parsed or datum_str,
                leitsatz=leitsatz,
                relevante_normen=relevante_normen,
                url=url,
                rechtsgebiet=rechtsgebiet
            )

            decisions.append(decision)
            logger.info(f"Parsed decision: {gericht} {aktenzeichen} ({datum_str})")

        except Exception as e:
            logger.warning(f"Error parsing decision block: {e}")
            logger.debug(f"Block content: {block[:200]}")
            continue

    logger.info(f"Successfully parsed {len(decisions)} court decisions from browser output")
    return decisions


def _generate_disclaimer(rechtsgebiet: str) -> str:
    """
    Generate German legal disclaimer for rechtsgebiet.

    Args:
        rechtsgebiet: Legal area

    Returns:
        German legal disclaimer text
    """
    disclaimers = {
        "Arbeitsrecht": """Rechtlicher Hinweis: Dieser Artikel dient ausschließlich der allgemeinen Information und stellt keine Rechtsberatung dar. Die rechtliche Beurteilung arbeitsrechtlicher Sachverhalte hängt immer von den konkreten Umständen des Einzelfalls ab. Für eine individuelle rechtliche Beratung zu Ihrer arbeitsrechtlichen Situation wenden Sie sich bitte an einen Fachanwalt für Arbeitsrecht.""",

        "Mietrecht": """Rechtlicher Hinweis: Dieser Artikel dient ausschließlich der allgemeinen Information und stellt keine Rechtsberatung dar. Die rechtliche Beurteilung mietrechtlicher Fragen ist stark einzelfallabhängig. Für eine verbindliche rechtliche Einschätzung Ihrer mietrechtlichen Angelegenheit kontaktieren Sie bitte einen Fachanwalt für Miet- und Wohnungseigentumsrecht.""",

        "Vertragsrecht": """Rechtlicher Hinweis: Dieser Artikel dient ausschließlich der allgemeinen Information und stellt keine Rechtsberatung dar. Die vertragsrechtliche Bewertung hängt von den spezifischen Vertragsgestaltungen und Umständen ab. Für eine individuelle rechtliche Prüfung Ihrer Verträge wenden Sie sich bitte an einen Rechtsanwalt.""",

        "Familienrecht": """Rechtlicher Hinweis: Dieser Artikel dient ausschließlich der allgemeinen Information und stellt keine Rechtsberatung dar. Familienrechtliche Angelegenheiten erfordern eine individuelle Beratung unter Berücksichtigung aller persönlichen Umstände. Für eine rechtliche Beratung zu Ihrer familienrechtlichen Situation kontaktieren Sie bitte einen Fachanwalt für Familienrecht.""",

        "Erbrecht": """Rechtlicher Hinweis: Dieser Artikel dient ausschließlich der allgemeinen Information und stellt keine Rechtsberatung dar. Erbrechtliche Gestaltungen müssen immer unter Berücksichtigung der konkreten Vermögens- und Familienverhältnisse erfolgen. Für eine individuelle erbrechtliche Beratung wenden Sie sich bitte an einen Fachanwalt für Erbrecht."""
    }

    return disclaimers.get(
        rechtsgebiet,
        """Rechtlicher Hinweis: Dieser Artikel dient ausschließlich der allgemeinen Information und stellt keine Rechtsberatung dar. Für eine individuelle rechtliche Beratung wenden Sie sich bitte an einen Rechtsanwalt."""
    )
