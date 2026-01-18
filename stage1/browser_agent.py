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
from typing import List, Dict, Any, Optional

# Add stage1 to path for imports
stage1_path = Path(__file__).parent
if str(stage1_path) not in sys.path:
    sys.path.insert(0, str(stage1_path))

# Add project root to path for shared imports
project_root = stage1_path.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from legal_models import CourtDecision, LegalContext
from shared.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

# Import browserUse components (will be installed in requirements.txt)
try:
    from browser_use.agent.service import Agent
    from browser_use.browser import BrowserSession, BrowserProfile
    from browser_use.llm.google.chat import ChatGoogle
    BROWSER_USE_AVAILABLE = True
except ImportError as e:
    BROWSER_USE_AVAILABLE = False
    logger.warning(f"browserUse not available: {e}. Install with: pip install browser-use playwright")


# =============================================================================
# KEYWORD PREPROCESSING
# =============================================================================
# Preprocess complex keywords to extract search terms and detect rechtsgebiet.

# Schema for keyword preprocessing response
KEYWORD_PREPROCESSING_SCHEMA = {
    "type": "object",
    "properties": {
        "search_terms": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 3,
            "description": "2-3 SHORT German legal search terms (1-2 words each)"
        },
        "detected_rechtsgebiet": {
            "type": "string",
            "description": "The German legal area (e.g., Arbeitsrecht, Erbrecht, Mietrecht, Steuerrecht)"
        },
        "relevant_statutes": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Relevant German statute references (e.g., § 16 ErbStG, § 623 BGB)"
        },
        "search_strategy": {
            "type": "string",
            "description": "Brief suggestion for how to search (e.g., 'search for comparison cases')"
        }
    },
    "required": ["search_terms", "detected_rechtsgebiet"]
}


async def _preprocess_keywords_for_search(
    keywords: List[str],
    provided_rechtsgebiet: Optional[str] = None
) -> Dict[str, Any]:
    """
    Preprocess keywords to extract optimal Beck-Online search terms.

    Complex question-based keywords like "Freibetrag Erbe vs. Schenkung: Wo sind
    die Unterschiede?" need to be converted to effective search terms like
    "Freibetrag Erbschaft Schenkung" with correct rechtsgebiet detection.

    Args:
        keywords: List of raw article keywords (may be questions or complex phrases)
        provided_rechtsgebiet: Optional rechtsgebiet hint from caller

    Returns:
        Dict with:
        - search_terms: List of 2-4 German legal search terms
        - detected_rechtsgebiet: Detected or confirmed legal area
        - relevant_statutes: Optional list of relevant statute references
        - search_strategy: Brief search strategy hint

    Example:
        >>> result = await _preprocess_keywords_for_search(
        ...     ["Freibetrag Erbe vs. Schenkung: Wo sind die Unterschiede?"],
        ...     provided_rechtsgebiet="Arbeitsrecht"
        ... )
        >>> result["search_terms"]
        ["Freibetrag", "Erbschaft", "Schenkung", "§ 16 ErbStG"]
        >>> result["detected_rechtsgebiet"]
        "Erbrecht"  # Corrected from provided "Arbeitsrecht"
    """
    # Normalize keywords
    normalized_keywords = []
    for kw in keywords:
        if isinstance(kw, dict):
            normalized_keywords.append(kw.get("keyword", ""))
        else:
            normalized_keywords.append(str(kw))

    keywords_str = ", ".join(normalized_keywords)

    # Build preprocessing prompt
    prompt = f"""Analyze the following German legal article keyword(s) and extract optimal search terms for Beck-Online legal database.

KEYWORD(S): {keywords_str}
PROVIDED LEGAL AREA: {provided_rechtsgebiet or "not specified"}

YOUR TASK:
1. Extract exactly 2-3 SHORT search terms (1-2 words each) for Beck-Online
2. Detect the correct German legal area (Rechtsgebiet)
3. Identify any relevant German statute references

CRITICAL RULES FOR SEARCH TERMS:
- Keep it SIMPLE: maximum 2-3 terms, each term 1-2 words only
- NO long phrases - just core concepts
- NO statute references in search terms (put those in relevant_statutes instead)
- Good: ["Mieterhöhung", "Vergleichsmiete"] - short, simple terms
- Bad: ["Mieterhöhung Vergleichsmiete ortsüblich Mietspiegel"] - too long, too many words

Respond with JSON only."""

    try:
        gemini_client = GeminiClient()
        result = await gemini_client.generate_with_schema(
            prompt=prompt,
            response_schema=KEYWORD_PREPROCESSING_SCHEMA,
            temperature=0.2  # Low temperature for consistent extraction
        )

        logger.info(f"Preprocessed keywords: {keywords_str}")
        logger.info(f"  → Search terms: {result.get('search_terms', [])}")
        logger.info(f"  → Detected rechtsgebiet: {result.get('detected_rechtsgebiet', 'unknown')}")
        if result.get('relevant_statutes'):
            logger.info(f"  → Relevant statutes: {result.get('relevant_statutes', [])}")

        return result

    except Exception as e:
        logger.warning(f"Keyword preprocessing failed: {e}. Using raw keywords.")
        # Fallback: use raw keywords as search terms
        return {
            "search_terms": normalized_keywords,
            "detected_rechtsgebiet": provided_rechtsgebiet or "Allgemeines Recht",
            "relevant_statutes": [],
            "search_strategy": "Direct keyword search"
        }


# =============================================================================
# COMBINED TASK TEMPLATE
# =============================================================================
# Single agent handles login + search in one continuous flow.
# This prevents CDP connection issues that occur when creating multiple agents.

COMBINED_TASK_TEMPLATE = """
TASK: Login to Beck-Online and search for court decisions

=== FORBIDDEN ACTIONS - WILL CAUSE FAILURE ===
- NEVER refresh the page
- NEVER click any tabs in the header (Beck-Noxtua, Mein beck-online, etc.)
- NEVER click "Anmelden" or "Sign in" links in the TOP RIGHT CORNER - use the form instead!
- NEVER click language dropdowns or settings
- NEVER switch browser tabs - if a new tab opens, IGNORE it and stay on current tab
- NEVER click random links or elements with IDs like "pos_XX"
- NEVER click on advertisements or sponsored content
- Stay focused ONLY on: login form → search bar → search results list → one court decision

CREDENTIALS TO USE:
- USERNAME: {username}
- PASSWORD: {password}

SEARCH TERMS: {search_terms}

=== PART 1: LOGIN ===

Step 1: Go to https://beck-online.beck.de

Step 2: COOKIE CHECK (MANDATORY)
- Look for a cookie consent popup/banner
- If present, click "Alle akzeptieren" to dismiss it
- Wait for the popup to fully close
- If no popup appears, continue

Step 3: FIND THE CORRECT ANMELDEN BUTTON
- Look at the RIGHT side of the homepage (not the header/top-right!)
- Find the box labeled "Mein beck-online"
- UNDERNEATH this header, there is an "Anmelden" button
- This button is in the MAIN CONTENT area, NOT in the page header
- Click the "Anmelden" button in the "Mein beck-online" box
- WARNING: Do NOT click any "Anmelden" link in the top-right header

Step 4: HANDLE COOKIES ON LOGIN PAGE (MANDATORY)
- Wait for the login page to load
- A cookie popup WILL likely appear on the login page
- Click "Alle akzeptieren" to dismiss it
- Wait for the popup to fully close and disappear

Step 5: ENTER CREDENTIALS (IMPORTANT - use the FORM, not links!)
- Look for the LOGIN FORM in the CENTER of the page (NOT the top-right corner!)
- IGNORE any "Anmelden" or "Sign in" links in the header/top-right - these are WRONG
- The form has input fields for username and password
- Find the USERNAME input field (labeled "Benutzerkennung") and type: {username}
- Find the PASSWORD input field (labeled "Passwort") and type: {password}

Step 6: SUBMIT LOGIN (click the button INSIDE the form)
- Find the submit button that is INSIDE the login form, BELOW the input fields
- It is a BUTTON element, not a link
- DO NOT click any "Anmelden" link in the top-right header
- Click the submit button inside the form
- Wait for the page to load

Step 7: VERIFY LOGIN SUCCESS
- Look for "Abmelden" text anywhere on the page (usually top-right area)
- "Abmelden" means "Logout" - its presence confirms you are logged in
- If you do NOT see "Abmelden", report LOGIN_FAILED and stop

=== PART 2: SEARCH ===

Step 8: DISMISS COOKIE POPUP IF VISIBLE
- If a cookie popup/banner is visible, click "Alle akzeptieren"
- If no popup is visible, skip this step and go directly to Step 9
- DO NOT click on any tabs or links - only the cookie accept button

Step 9: USE THE SEARCH BAR (this is your main goal!)
- IMPORTANT: The search bar is a WHITE INPUT FIELD at the top of the page
- It has "Suche:" label on the left side
- Click INSIDE the white input field (not on any tabs or links!)
- Type: {search_terms}
- Press Enter to search
- DO NOT click on Beck-Noxtua, tabs, or any other links

Step 10: LOOK AT SEARCH RESULTS
- Wait for the search results to fully load
- Look at the results list - each result has a TITLE link
- You need to extract data from 3 DIFFERENT court decisions

Step 11: EXTRACT 3 COURT DECISIONS
For EACH of 3 different court decisions in the search results:
1. Look at the result entry (you can often see Gericht, Aktenzeichen, Datum in the result preview)
2. Click on the TITLE LINK to open the full decision
3. From the decision page, extract:
   - GERICHT: Court name (BFH, BGH, FG München, etc.)
   - AKTENZEICHEN: Case number (e.g., "II R 25/21")
   - DATUM: Date in DD.MM.YYYY format
   - LEITSATZ: The full legal principle text (look for "Leitsatz" section - copy ALL of it)
   - RELEVANTE NORMEN: Statute references (e.g., "§ 16 ErbStG")
   - URL: The page URL from browser address bar
4. Click BACK to return to search results
5. Click on a DIFFERENT result and repeat

Extract 3 total decisions, then call done with all the data.

=== OUTPUT FORMAT ===
After extracting ALL 3 decisions, call the "done" action with this format:

SEARCH_SUCCESS

Decision 1:
Gericht: [court name]
Aktenzeichen: [case number]
Datum: [date]
Leitsatz: [full legal principle text]
Relevante Normen: [statutes]
URL: [beck-online URL]

Decision 2:
Gericht: [court name]
Aktenzeichen: [case number]
Datum: [date]
Leitsatz: [full legal principle text]
Relevante Normen: [statutes]
URL: [beck-online URL]

Decision 3:
Gericht: [court name]
Aktenzeichen: [case number]
Datum: [date]
Leitsatz: [full legal principle text]
Relevante Normen: [statutes]
URL: [beck-online URL]

=== CRITICAL ===
- Extract 3 decisions before calling done
- Include the FULL Leitsatz text for each
- Call done with all the data at the end

=== IF SOMETHING FAILS ===
- If login fails: call done with "LOGIN_FAILED"
- If no search results: call done with "NO_RESULTS_FOUND"
- If less than 3 decisions found: report what you found and call done
"""


async def _execute_beck_research_single_agent(
    keywords: List[str],
    rechtsgebiet: str,
    beck_username: str,
    beck_password: str,
    gemini_api_key: str
) -> LegalContext:
    """
    Execute Beck research with a single agent handling login + search.

    Using a single agent for the entire flow prevents CDP connection issues
    that occur when creating multiple agents with the same browser session.
    The agent handles login first, then search, all in one continuous task.

    Args:
        keywords: List of article keywords
        rechtsgebiet: German legal area
        beck_username: Beck-Online username
        beck_password: Beck-Online password
        gemini_api_key: Gemini API key

    Returns:
        LegalContext with court decisions from Beck-Online

    Raises:
        ValueError: If login fails or search returns no results
        Exception: If browser automation fails
    """
    # Initialize Gemini LLM for browser-use
    llm = ChatGoogle(
        model="gemini-2.5-pro",
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

    # =========================================================================
    # PREPROCESSING: Extract search terms from complex keywords
    # =========================================================================
    logger.info("Preprocessing keywords for optimal search...")

    preprocessed = await _preprocess_keywords_for_search(
        keywords=normalized_keywords,
        provided_rechtsgebiet=rechtsgebiet
    )

    # Use preprocessed search terms and potentially corrected rechtsgebiet
    search_terms = preprocessed.get("search_terms", normalized_keywords)
    effective_rechtsgebiet = preprocessed.get("detected_rechtsgebiet", rechtsgebiet)

    # Format for search task
    search_terms_str = " ".join(search_terms)

    # Log if rechtsgebiet was corrected
    if effective_rechtsgebiet != rechtsgebiet:
        logger.info(f"Rechtsgebiet corrected: {rechtsgebiet} → {effective_rechtsgebiet}")

    # Create browser profile and session (non-headless for debugging)
    browser_profile = BrowserProfile(
        headless=False,
    )
    browser_session = BrowserSession(browser_profile=browser_profile)

    try:
        # Start the browser session
        await browser_session.start()
        logger.info("Browser session started successfully")

        # =====================================================================
        # SINGLE AGENT: Combined login + search task
        # =====================================================================
        logger.info("Starting combined login + search agent...")

        combined_task = COMBINED_TASK_TEMPLATE.format(
            username=beck_username,
            password=beck_password,
            search_terms=search_terms_str
        )

        agent = Agent(
            task=combined_task,
            llm=llm,
            browser_session=browser_session,
            use_vision=False,
            max_failures=5,            # Allow retries for the entire flow
            max_actions_per_step=25,   # Enough for login + search + extraction
        )

        result = await agent.run()

        logger.info("Combined agent completed")

        # =====================================================================
        # RESULT VALIDATION
        # =====================================================================
        # Extract output for status checking
        content = result.extracted_content() or []
        output = '\n'.join(content) if content else str(result)

        logger.info(f"Agent output preview: {output[:500]}")

        # Check for failure status codes
        failure_codes = {
            "LOGIN_FAILED": "Login failed - check credentials",
            "NOT_LOGGED_IN": "Login session issue",
            "NO_RESULTS_FOUND": "Search returned no results",
            "NO_RELEVANT_RESULTS": "No court decisions found in results",
            "PAGE_LOAD_FAILED": "Beck-Online pages failed to load",
            "EXTRACTION_FAILED": "Could not extract decision fields"
        }

        for code, description in failure_codes.items():
            if code in output:
                logger.warning(f"Agent reported failure: {code} - {description}")
                # For "no results" scenarios, return empty LegalContext instead of error
                if code in ("NO_RESULTS_FOUND", "NO_RELEVANT_RESULTS"):
                    logger.info("Returning empty LegalContext for no-results scenario")
                    return LegalContext(
                        rechtsgebiet=effective_rechtsgebiet,
                        court_decisions=[],
                        statutes=[],
                        disclaimer_template=_generate_disclaimer(effective_rechtsgebiet),
                        stand_der_rechtsprechung=datetime.now().strftime("%Y-%m-%d"),
                        keywords_researched=normalized_keywords
                    )
                # For login/page failures, raise to trigger retry
                raise ValueError(f"Agent failed: {code} - {description}")

        # Check for success indicator
        if "SEARCH_SUCCESS" not in output:
            logger.warning("SEARCH_SUCCESS not found in output, but no failure code either - proceeding with parsing")

        # Parse and return results
        court_decisions = _parse_beck_online_results(result, effective_rechtsgebiet)
        logger.info(f"Extracted {len(court_decisions)} court decisions from Beck-Online")
        disclaimer = _generate_disclaimer(effective_rechtsgebiet)

        return LegalContext(
            rechtsgebiet=effective_rechtsgebiet,
            court_decisions=court_decisions,
            statutes=[],
            disclaimer_template=disclaimer,
            stand_der_rechtsprechung=datetime.now().strftime("%Y-%m-%d"),
            keywords_researched=normalized_keywords
        )

    finally:
        # Always stop browser to prevent orphaned processes
        await browser_session.stop()
        logger.info("Browser stopped")


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

    Uses single-agent execution (combined login + search) for reliable operation.
    Login failures are not retried (require credential fix).

    Implements exponential backoff for quota errors:
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
            # Use single-agent execution for reliable CDP connection
            return await _execute_beck_research_single_agent(
                keywords=keywords,
                rechtsgebiet=rechtsgebiet,
                beck_username=beck_username,
                beck_password=beck_password,
                gemini_api_key=gemini_api_key
            )
        except Exception as e:
            error_str = str(e)

            # Login failures should not retry (need credential fix)
            is_login_error = "Login failed" in error_str or "LOGIN_FAILED" in error_str

            is_quota_error = (
                "429" in error_str or
                "RESOURCE_EXHAUSTED" in error_str or
                "quota" in error_str.lower() or
                "rate limit" in error_str.lower()
            )

            if is_login_error:
                logger.error("Login failed - check Beck credentials in .env file")
                raise

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

    Uses a single-agent approach for reliable CDP connection:
    - One agent handles login + search in a continuous flow
    - Prevents CDP connection issues from creating multiple agents

    Beck-Online provides comprehensive legal content including:
    - Court decisions from all German courts
    - Authoritative commentary (Palandt, MüKo, etc.)
    - Statute text and annotations

    Process:
    1. Preprocess keywords to extract optimal search terms
    2. Single agent: Login to Beck-Online with credentials
    3. Single agent: Search for keywords and extract 3 decisions
    4. Return structured LegalContext
    5. Auto-retry on quota errors (60s, 120s delays)

    API Quota Optimizations:
    - Uses stable model (gemini-2.0-flash, 60 RPM vs 10 RPM for -exp)
    - Vision disabled (reduces API calls by ~80%)
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


# Expanded placeholder patterns for validation (case-insensitive)
# Includes patterns that agents may echo from template instructions
PLACEHOLDER_PATTERNS = [
    # Generic placeholders
    "not available", "n/a", "na", "pending", "unknown",
    "tbd", "see above", "placeholder", "[", "]", "...",
    # Template instruction echoes (agent copying instructions instead of extracting)
    "[actual", "[value]", "actual court name", "actual case number",
    "actual date", "actual legal", "actual text", "actual statute",
    "actual beck-online", "minimum 50 characters", "minimum 50",
    # Format instruction echoes
    "dd.mm.yyyy", "court name here", "case number here",
    "legal principle text", "statute citations",
]


def _is_placeholder(value: str) -> bool:
    """
    Check if value is a placeholder or empty.

    Used to validate Beck-Online parsed results contain real data.

    Args:
        value: String value to check

    Returns:
        True if value is empty, whitespace-only, or matches placeholder patterns
    """
    if not value or not value.strip():
        return True
    lower = value.lower().strip()
    return any(p in lower for p in PLACEHOLDER_PATTERNS)


def _parse_beck_online_results(browser_output, rechtsgebiet: str) -> List[CourtDecision]:
    """
    Parse browser agent output into CourtDecision objects.

    The browser agent returns an AgentHistoryList containing extracted decisions.
    Includes strict validation to ensure only real court decisions are returned.

    Args:
        browser_output: AgentHistoryList from browser agent
        rechtsgebiet: Legal area

    Returns:
        List of validated CourtDecision objects
    """
    import re
    from datetime import datetime

    decisions = []

    logger.info("Parsing browser agent output for court decisions...")

    # Extract all content from AgentHistoryList
    output_str = ""
    try:
        content_items = browser_output.extracted_content()
        if content_items:
            # Filter to only string items (avoid ModelPrivateAttr objects)
            string_items = [str(item) for item in content_items if item is not None]
            output_str = '\n'.join(string_items)
            logger.info(f"Extracted {len(string_items)} content item(s) from browser agent")

        # Also try to get the final result/done message
        if hasattr(browser_output, 'final_result') and browser_output.final_result:
            output_str += f"\n{browser_output.final_result}"
            logger.info("Added final_result to output")

        # Try to get done message from history
        if hasattr(browser_output, 'history'):
            for item in browser_output.history:
                if hasattr(item, 'result') and item.result:
                    result_str = str(item.result)
                    if 'Gericht:' in result_str or 'SEARCH_SUCCESS' in result_str:
                        output_str += f"\n{result_str}"
                        logger.info("Found decision data in history result")

        if not output_str.strip():
            logger.warning("No extracted content from browser agent")
            return decisions

    except Exception as e:
        logger.error(f"Failed to extract content from browser output: {e}")
        # Fallback to string conversion if extraction fails
        output_str = str(browser_output)
        logger.warning("Falling back to string conversion of browser output")

    # Log the full output for debugging
    logger.debug(f"Full parsed output:\n{output_str[:2000]}")

    # Normalize the output: replace literal \n with actual newlines
    # The agent sometimes outputs escaped newlines as literal "\n" strings
    output_str = output_str.replace('\\n', '\n')
    logger.info(f"Normalized output length: {len(output_str)} chars")

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

            # Validate required fields are non-empty and not placeholders
            if _is_placeholder(gericht):
                logger.warning(f"Skipping decision with empty/placeholder Gericht: '{gericht}'")
                continue

            if _is_placeholder(aktenzeichen):
                logger.warning(f"Skipping decision with empty/placeholder Aktenzeichen: '{aktenzeichen}'")
                continue

            # URL validation - warn but don't skip if missing (agent may not have captured it)
            if not url or not url.strip():
                logger.warning(f"Decision {aktenzeichen} has no URL - using placeholder")
                url = f"https://beck-online.beck.de/search?q={aktenzeichen.replace(' ', '+')}"
            elif not url.startswith("https://beck-online.beck.de") and not url.startswith("/"):
                logger.warning(f"Decision {aktenzeichen} has non-Beck URL: {url} - using placeholder")
                url = f"https://beck-online.beck.de/search?q={aktenzeichen.replace(' ', '+')}"

            # Leitsatz validation - warn but accept shorter content
            if _is_placeholder(leitsatz):
                logger.warning(f"Decision {aktenzeichen} has placeholder Leitsatz - keeping anyway")
                leitsatz = f"Entscheidung des {gericht} vom {datum_str} - {aktenzeichen}"
            elif len(leitsatz.strip()) < 20:
                logger.warning(f"Decision {aktenzeichen} has short Leitsatz: '{leitsatz[:50]}' - keeping anyway")

            # Clean up normen_str if placeholder
            if _is_placeholder(normen_str):
                normen_str = ""

            # Parse relevante_normen (comma or pipe separated)
            relevante_normen = []
            if normen_str and isinstance(normen_str, str):
                # Split by | or , or ; and clean
                normen_list = re.split(r'[|,;]', normen_str)
                relevante_normen = [str(n).strip() for n in normen_list if n and str(n).strip()]

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
            # Log more details for debugging
            logger.warning(f"  gericht={gericht if 'gericht' in dir() else 'N/A'}")
            logger.warning(f"  aktenzeichen={aktenzeichen if 'aktenzeichen' in dir() else 'N/A'}")
            logger.warning(f"  Block preview: {block[:300] if block else 'empty'}")
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
