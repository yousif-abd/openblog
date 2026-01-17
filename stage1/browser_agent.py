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

    # CRITICAL: Pass the password directly in the task since browser-use needs it
    task = f"""
    CRITICAL WARNING: There is a large search bar in the CENTER of the homepage.
    DO NOT USE IT until Step 4. You must LOGIN FIRST using the small "Anmelden" link.

    STEP 1: NAVIGATE AND HANDLE COOKIE POPUP
    -----------------------------------------
    1. Navigate to https://beck-online.beck.de
    2. Wait 2 seconds for the page to fully load
    3. You will see a large search bar in the middle - IGNORE IT FOR NOW
    4. Look for a cookie consent popup or banner
    5. If you see a cookie popup, click "Akzeptieren", "Alle akzeptieren", or "OK" to dismiss it
    6. Wait 1 second after dismissing the cookie popup

    STEP 2: FIND AND CLICK THE LOGIN LINK (NOT THE SEARCH BAR!)
    ------------------------------------------------------------
    7. IGNORE the large search bar in the center of the page
    8. Look at the TOP RIGHT CORNER of the page header (near the edge)
    9. Find the text "Mein beck-online" - it's a small link, NOT the big search bar
    10. Click on "Mein beck-online" or look for "Anmelden" near it
    11. If you see a dropdown menu, click "Anmelden" (Login) in that menu
    12. If "Anmelden" is directly visible as a link, click it
    13. This will take you to a SEPARATE LOGIN PAGE with a login form
    14. Wait for the login page to fully load

    STEP 3: ENTER CREDENTIALS IN THE LOGIN FORM
    --------------------------------------------
    15. You are now on the LOGIN PAGE (URL should contain "login" or "anmelden")
    16. This page has a LOGIN FORM with username and password fields
    17. DO NOT type in any search bar - use ONLY the login form fields
    18. Find the input field labeled "Benutzername", "E-Mail", or "Benutzerkennung"
    19. Click inside this username/email field
    20. Type this username exactly: {beck_username}
    21. Press Tab to move to the password field
    22. Find the input field labeled "Passwort" or "Kennwort"
    23. Click inside the password field
    24. Type this password exactly: {beck_password}
    25. Find the submit button labeled "Anmelden", "Login", or "Einloggen"
    26. Click the submit button to log in
    27. Wait 3 seconds for login to complete
    28. Verify login success: look for your username or "Abmelden" (Logout) in top right

    STEP 4: SEARCH FOR COURT DECISIONS (ONLY AFTER SUCCESSFUL LOGIN)
    -----------------------------------------------------------------
    For each of these keywords: {keywords_str}

    1. Only proceed if you confirmed login in step 28 above
    2. NOW you can use the search bar at beck-online.beck.de
    3. Find the main search bar and click in it
    4. Type: [keyword] {rechtsgebiet}
       For example: "Kündigung Arbeitsrecht"
    5. Press Enter or click the search button
    6. Wait for search results to load
    7. Look for a filter for "Rechtsprechung" or "Urteile" (court decisions)
    8. Click to filter results to court decisions only
    9. Sort by date (newest first / "Datum absteigend") if possible
    10. Click on the top 3 most recent results to view details
    11. For each decision, extract:
        - Gericht (court name, e.g., BGH, BAG, OLG München)
        - Aktenzeichen (case reference, e.g., 6 AZR 123/23)
        - Datum (decision date in DD.MM.YYYY format)
        - Leitsatz (core legal principle - usually the first bold paragraph)
        - Relevante Normen (cited statutes, e.g., § 623 BGB, § 626 BGB)
        - URL (copy the full beck-online.beck.de URL from the address bar)

    STEP 5: OUTPUT FORMAT
    ---------------------
    For each decision found, output in this exact format:

    Decision 1:
    Gericht: [court name]
    Aktenzeichen: [case reference]
    Datum: [DD.MM.YYYY]
    Leitsatz: [main legal principle]
    Relevante Normen: [statute citations separated by commas]
    URL: [full URL]

    Decision 2:
    [same format]

    Extract up to 3 decisions per keyword (maximum 15 total across all keywords).
    Focus on decisions from the last 2 years (2024-2026).

    CRITICAL RULES:
    1. The homepage has a big search bar in the CENTER - DO NOT USE IT before logging in
    2. "Mein beck-online" and "Anmelden" are small links in the TOP RIGHT corner
    3. You MUST click "Anmelden" to go to the login page FIRST
    4. Enter credentials ONLY in the login form, NEVER in any search bar
    5. Only search AFTER you see "Abmelden" confirming successful login
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
