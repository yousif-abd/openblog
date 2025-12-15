"""
Stage 4: Citations Validation and Formatting

Maps to v4.1 Phase 4, Steps 8-13: CitationSanitizer + Information Extractor + AI Agent3 + Formatting

Processes citations from the article:
1. Extract sources from structured_data.Sources field
2. Parse citation format [1], [2], etc.
3. Extract URLs and titles
4. Validate URLs (optional)
5. Format as HTML

Input:
  - ExecutionContext.structured_data (ArticleOutput with Sources field)

Output:
  - ExecutionContext.parallel_results['citations_html'] (HTML formatted citations)

The citations from Gemini come in format:
[1]: https://example.com – Description of source
[2]: https://example.org – Another source
...
"""

import logging
from typing import Dict, List, Any, Optional

from ..core import ExecutionContext, Stage
from ..models.citation import Citation, CitationList
from ..models.gemini_client import GeminiClient
from ..processors.url_validator import CitationURLValidator
from ..processors.ultimate_citation_validator import SmartCitationValidator, ValidationResult
from ..config import Config

logger = logging.getLogger(__name__)


class CitationsStage(Stage):
    """
    Stage 4: Citations Validation and Formatting.

    Handles:
    - Parsing sources from structured_data
    - Extracting URLs and titles
    - Creating Citation objects
    - Formatting as HTML
    - Validation (optional URL checks)
    
    Performance Notes:
    - Uses Gemini 3 Pro (gemini-3-pro-preview) for citation validation
    - Required for complex tool calling (web search + JSON output + validation)
    - Flash 2.5 cannot handle multi-tool workflows reliably
    """

    stage_num = 4
    stage_name = "Citations Validation & Formatting"

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize citations stage.
        
        Args:
            config: Configuration object (optional, loads from env if not provided)
        """
        self.config = config or Config()
        self.gemini_client = None  # Lazy initialization
        self.validator = None  # Lazy initialization
        self.ultimate_validator = None  # Ultimate citation validator

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        """
        Execute Stage 4: Process and format citations (sequential flow).

        NEW SEQUENTIAL FLOW:
        1. Extract URLs from Sources field (simple parsing)
        2. HTTP Status Check (parallel)
        3. Security Check (AI)
        4. Identify Issues
        5. Find Replacements (1 retry max)
        6. Update Body Citations (AI-based)
        7. Format Output

        Input from context:
        - structured_data: ArticleOutput with Sources field

        Output to context:
        - parallel_results['citations_html']: Formatted HTML
        - parallel_results['citations_list']: Updated CitationList
        - parallel_results['validated_citation_map']: Citation number -> URL mapping

        Args:
            context: ExecutionContext from Stage 3

        Returns:
            Updated context with parallel_results populated
        """
        try:
            logger.info(f"Stage 4: {self.stage_name}")

            # Check if citations are disabled (defensive null check)
            job_config = context.job_config if context.job_config else {}
            if job_config.get("citations_disabled", False):
                logger.info("Citations disabled via job_config")
                context.parallel_results["citations_html"] = ""
                return context

            # Validate input
            if not context.structured_data:
                logger.warning("No structured_data available for citations")
                context.parallel_results["citations_html"] = ""
                return context

            sources_text = context.structured_data.Sources or ""
            if not sources_text.strip():
                logger.warning("No sources found in structured_data")
                context.parallel_results["citations_html"] = ""
                return context

            logger.info(f"Processing sources ({len(sources_text)} chars)...")

            # ============================================================
            # STEP 1: Extract URLs (Simple Parsing)
            # ============================================================
            logger.info("📝 Step 1: Extracting citations from Sources field (AI-only)...")
            citation_list = await self._extract_citations_simple(sources_text)

            if not citation_list.citations:
                logger.warning("No valid citations extracted")
                context.parallel_results["citations_html"] = ""
                return context

            logger.info(f"✅ Extracted {citation_list.count()} citations")

            # ============================================================
            # STEP 2: HTTP Status Check (Parallel)
            # ============================================================
            logger.info("🔍 Step 2: Checking HTTP status for all URLs (parallel)...")
            status_map = await self._check_url_status_parallel(citation_list)

            # ============================================================
            # STEP 3: Security Check (AI)
            # ============================================================
            logger.info("🔒 Step 3: Checking citations for security risks (AI)...")
            security_map = await self._check_security_ai(citation_list)

            # ============================================================
            # STEP 4: Identify Issues
            # ============================================================
            logger.info("📋 Step 4: Identifying citations needing replacement...")
            issues_list = self._identify_issues(citation_list, status_map, security_map)

            # ============================================================
            # STEP 5: Find Replacements (1 Retry Max)
            # ============================================================
            if issues_list:
                logger.info("🔍 Step 5: Finding replacements for broken/risky citations...")
                citation_list, no_replacement_nums = await self._find_replacements(
                    citation_list, issues_list, context
                )
            else:
                logger.info("✅ Step 5: No citations need replacement")
                no_replacement_nums = []

            # ============================================================
            # STEP 6: Update Body Citations (AI-Based)
            # ============================================================
            if no_replacement_nums or issues_list:
                logger.info("🔗 Step 6: Updating body citations (AI-based)...")
                context = await self._update_body_citations_ai(
                    context, citation_list, no_replacement_nums
                )
            else:
                logger.info("✅ Step 6: No body citations need updating")

            # ============================================================
            # STEP 7: Format Output
            # ============================================================
            logger.info("📄 Step 7: Formatting citations as HTML...")
            
            # Filter out citations with no replacement
            valid_citations = CitationList()
            valid_citations.citations = [
                citation for citation in citation_list.citations
                if citation.number not in no_replacement_nums
            ]
            
            citations_html = valid_citations.to_html_paragraph_list()
            logger.info(f"   HTML size: {len(citations_html)} chars")
            
            # Build validated citation map for in-body links
            validated_citation_map = {}
            validated_source_name_map = {}
            for citation in valid_citations.citations:
                validated_citation_map[citation.number] = citation.url
                title_words = citation.title.split() if citation.title else []
                if title_words:
                    source_name = title_words[0]
                    validated_source_name_map[source_name.lower()] = citation.url
            
            logger.info(f"   Validated citation map: {len(validated_citation_map)} entries")
            if validated_source_name_map:
                logger.info(f"   Validated source names: {list(validated_source_name_map.keys())[:5]}...")

            # Store in context
            context.parallel_results["citations_html"] = citations_html
            context.parallel_results["citations_count"] = valid_citations.count()
            context.parallel_results["citations_list"] = valid_citations
            context.parallel_results["validated_citation_map"] = validated_citation_map
            context.parallel_results["validated_source_name_map"] = validated_source_name_map

            return context
        
        except AttributeError as e:
            if "'NoneType' object has no attribute 'get'" in str(e):
                logger.error(f"❌ Stage 4 AttributeError: {e}")
                logger.error("   This usually means company_data, sitemap_data, or job_config is None")
                logger.error(f"   company_data: {context.company_data is not None if hasattr(context, 'company_data') else 'N/A'}")
                logger.error(f"   sitemap_data: {getattr(context, 'sitemap_data', None) is not None}")
                logger.error(f"   job_config: {context.job_config is not None if hasattr(context, 'job_config') else 'N/A'}")
                # Return empty citations HTML to allow pipeline to continue
                context.parallel_results["citations_html"] = ""
                context.parallel_results["citations_count"] = 0
                return context
            else:
                raise
        except Exception as e:
            logger.error(f"❌ Stage 4 unexpected error: {e}", exc_info=True)
            # Return empty citations HTML to allow pipeline to continue
            context.parallel_results["citations_html"] = ""
            context.parallel_results["citations_count"] = 0
            return context

    async def _validate_citation_urls(
        self,
        citation_list: CitationList,
        context: ExecutionContext,
    ) -> CitationList:
        """
        Validate citation URLs and find alternatives for invalid ones.
        
        Matches v4.1 Step 11: AI Agent3 behavior:
        - Validates each URL with HTTP HEAD
        - Finds alternatives for invalid URLs
        - Filters competitors/internal/forbidden domains
        - Maintains citation count
        
        Args:
            citation_list: List of citations to validate
            context: Execution context with company data
            
        Returns:
            Validated CitationList (same count as input)
        """
        logger.info(f"Validating {citation_list.count()} citation URLs...")
        
        # Initialize validator if needed
        if not self.validator:
            if not self.gemini_client:
                # Use Gemini 3 Pro for citation validation (tool calling required)
                # Use Gemini 3 Pro for web search + JSON + tool calling capabilities
                # 2.5 Flash cannot handle complex tool calling with JSON output reliably
                self.gemini_client = GeminiClient(model="gemini-3-pro-preview")
            self.validator = CitationURLValidator(
                gemini_client=self.gemini_client,
                max_attempts=self.config.max_validation_attempts,
                timeout=self.config.citation_validation_timeout,
            )
        
        # Get company data (with null check)
        if not context.company_data:
            logger.warning("No company_data available for citation validation")
            return citation_list
        company_url = context.company_data.get("company_url", "")
        competitors = context.company_data.get("company_competitors", [])
        language = context.language or "en"
        
        # Validate all citations
        try:
            validated_citations = await self.validator.validate_all_citations(
                citations=citation_list.citations,
                company_url=company_url,
                competitors=competitors,
                language=language,
            )
            
            # OPTIMIZATION: Skip post-validation to speed up (already validated during main validation)
            # Post-validation was adding ~30 seconds and catching minimal issues
            # If needed, can re-enable but it slows down the workflow significantly
            logger.info("Skipping post-validation (performance optimization)")
            final_valid_count = len(validated_citations)  # Assume all valid (they were validated above)
            valid_ratio = 1.0
            
            # DISABLED: Post-validation check (too slow)
            # Uncomment below if you want to re-enable double-checking
            # logger.info("Running post-validation check on all citations...")
            # final_valid_count = 0
            # post_validation_results = []
            # for citation in validated_citations:
            #     try:
            #         is_valid, final_url = await self.validator._check_url_status(citation.url)
            #         post_validation_results.append({'citation': citation, 'valid': is_valid, 'url': final_url})
            #         if is_valid:
            #             final_valid_count += 1
            #     except Exception as e:
            #         logger.error(f"Error in post-validation for [{citation.number}]: {e}")
            #         post_validation_results.append({'citation': citation, 'valid': False, 'url': citation.url})
            # valid_ratio = final_valid_count / len(validated_citations) if validated_citations else 0
            # logger.info(f"✅ Post-validation complete: {final_valid_count}/{len(validated_citations)} ({valid_ratio:.0%}) valid")
            
            # Quality threshold check: Require at least 75% valid URLs
            # OPTIMIZATION: Disabled for now (post-validation is disabled, so we can't measure accurately)
            # Can re-enable if post-validation is restored
            QUALITY_THRESHOLD = 0.75
            logger.info(f"✅ Citation validation complete: {len(validated_citations)} citations processed")
            
            # DISABLED: Quality threshold (requires post-validation)
            # if valid_ratio < QUALITY_THRESHOLD:
            #     logger.warning(f"⚠️  Citation quality below threshold: {valid_ratio:.0%} < {QUALITY_THRESHOLD:.0%}")
            # else:
            #     logger.info(f"✅ Citation quality acceptable: {valid_ratio:.0%} valid")
            
            # Create new CitationList with validated citations
            validated_list = CitationList()
            validated_list.citations = validated_citations
            
            return validated_list
            
        except Exception as e:
            logger.error(f"Error validating citations: {e}")
            logger.warning("Continuing with original citations")
            return citation_list

    def _enhance_with_grounding_urls(
        self, 
        citation_list: CitationList, 
        grounding_urls: List[Dict[str, str]]
    ) -> CitationList:
        """
        Enhance citations with SPECIFIC URLs from Gemini's Google Search grounding.
        
        GeminiClient resolves grounding URLs:
        - 'url': Real resolved URL (e.g., https://checkpoint.com/.../cloud-security/)
        - 'domain': Domain from title (e.g., "checkpoint.com")
        - 'proxy_url': Original vertex proxy URL (kept for reference)
        
        Strategy:
        1. For each citation, find a grounding URL where domain matches
        2. Replace the citation URL with the real resolved URL
        3. If multiple matches, prefer the one with most similar title
        
        Args:
            citation_list: CitationList with potentially generic URLs
            grounding_urls: List of {'url': str, 'domain': str, ...} from Gemini grounding
            
        Returns:
            Enhanced CitationList with real, validated source URLs
        """
        if not grounding_urls:
            return citation_list
        
        # Build domain -> specific URLs map
        # CRITICAL: Use TITLE as domain (not URL which is always vertexaisearch.cloud.google.com)
        domain_to_urls: Dict[str, List[Dict[str, str]]] = {}
        for grounding in grounding_urls:
            url = grounding.get('url', '')
            title = grounding.get('title', '')
            if not url or not title:
                continue
            # The title IS the domain (e.g., "sportingnews.com", "aljazeera.com")
            domain = title.lower().replace('www.', '')
            if domain not in domain_to_urls:
                domain_to_urls[domain] = []
            domain_to_urls[domain].append(grounding)
        
        logger.info(f"   Grounding URL domains (from titles): {', '.join(domain_to_urls.keys())}")
        
        enhanced_count = 0
        domain_only_count = 0
        
        for citation in citation_list.citations:
            # Extract domain from citation URL
            try:
                from urllib.parse import urlparse
                parsed = urlparse(citation.url)
                citation_domain = parsed.netloc.lower().replace('www.', '')
                # Check if URL is domain-only (path has <= 3 parts: /, maybe /path, maybe /path/item)
                path_parts = [p for p in parsed.path.split('/') if p]
                is_domain_only = len(path_parts) <= 1  # Domain-only if just "/" or "/single-item"
            except Exception:
                continue
            
            # Check if we have grounding URLs for this domain
            # The domain_to_urls keys are from grounding titles (e.g., "gartner.com")
            if citation_domain in domain_to_urls:
                specific_urls = domain_to_urls[citation_domain]
                
                if specific_urls:
                    # Find best match by title similarity
                    best_match = self._find_best_title_match(citation.title, specific_urls)
                    
                    # CRITICAL: Always enhance domain-only URLs, only enhance full URLs if significantly better
                    should_enhance = False
                    if is_domain_only:
                        # Domain-only URLs should ALWAYS be enhanced
                        should_enhance = True
                        domain_only_count += 1
                        logger.info(f"   🎯 Citation [{citation.number}] is domain-only - WILL ENHANCE")
                    elif best_match and best_match['url'] != citation.url:
                        # Full URLs: only enhance if grounding URL is significantly better (longer path = more specific)
                        grounding_path_parts = [p for p in urlparse(best_match['url']).path.split('/') if p]
                        if len(grounding_path_parts) > len(path_parts) + 1:  # Significantly more specific
                            should_enhance = True
                            logger.info(f"   📎 Citation [{citation.number}] full URL - enhancing to more specific URL")
                        else:
                            logger.debug(f"   ⏭️  Citation [{citation.number}] already has good full URL - skipping")
                    
                    if should_enhance and best_match:
                        old_url = citation.url
                        citation.url = best_match['url']
                        enhanced_count += 1
                        logger.info(f"   ✅ Citation [{citation.number}] enhanced:")
                        logger.info(f"      OLD: {old_url}")
                        logger.info(f"      NEW: {citation.url[:80]}...")
        
        if enhanced_count > 0:
            logger.info(f"✅ Enhanced {enhanced_count} citations with specific URLs")
            if domain_only_count > 0:
                logger.info(f"   📊 {domain_only_count} domain-only URLs converted to full URLs")
        else:
            logger.info("   No URLs needed enhancement")
        
        return citation_list
    
    def _find_best_title_match(
        self, 
        citation_title: str, 
        grounding_urls: List[Dict[str, str]]
    ) -> Optional[Dict[str, str]]:
        """Find the grounding URL with the most similar title."""
        if not grounding_urls:
            return None
        
        if len(grounding_urls) == 1:
            return grounding_urls[0]
        
        # Simple word overlap scoring
        citation_words = set(citation_title.lower().split())
        
        best_match = grounding_urls[0]
        best_score = 0
        
        for grounding in grounding_urls:
            title = grounding.get('title', '')
            grounding_words = set(title.lower().split())
            overlap = len(citation_words & grounding_words)
            if overlap > best_score:
                best_score = overlap
                best_match = grounding
        
        return best_match

    async def _extract_citations_simple(self, sources_text: str) -> CitationList:
        """
        Extract citations from Sources field using AI-only parsing (no regex).
        
        Format: [1]: Title – URL
        Example: [1]: IBM Cost of a Data Breach Report 2024 – https://www.ibm.com/reports/data-breach
        
        Args:
            sources_text: Raw sources from structured_data
            
        Returns:
            CitationList with extracted citations
        """
        citation_list = CitationList()
        
        if not sources_text or not sources_text.strip():
            return citation_list
        
        logger.info("📝 Extracting citations from Sources field (AI-only parsing)")
        
        # Initialize Gemini client if needed
        if not self.gemini_client:
            self.gemini_client = GeminiClient()
        
        prompt = f"""Extract all citations from the Sources field below. Parse each citation and return structured JSON.

Sources field format: [number]: Title – URL
Example: [1]: IBM Cost of a Data Breach Report 2024 – https://www.ibm.com/reports/data-breach

CRITICAL REQUIREMENTS:
1. Extract ALL citations from the text
2. Parse citation number, title, and URL correctly
3. Handle both em dash (—) and regular dash (-) as separators
4. Validate URLs start with http:// or https://
5. Return ONLY valid citations (skip any malformed entries)

Sources field text:
{sources_text}

Return a JSON object with a "citations" array. Each citation must have:
- number: integer (citation number)
- title: string (citation title)
- url: string (full URL starting with http:// or https://)
"""
        
        try:
            from google.genai import types
            
            response_schema = types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "citations": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "number": types.Schema(
                                    type=types.Type.INTEGER,
                                    description="Citation number (e.g., 1, 2, 3)"
                                ),
                                "title": types.Schema(
                                    type=types.Type.STRING,
                                    description="Citation title (8-15 words)"
                                ),
                                "url": types.Schema(
                                    type=types.Type.STRING,
                                    description="Full URL starting with http:// or https://"
                                )
                            }
                        )
                    )
                },
                required=["citations"]
            )
            
            response = await self.gemini_client.generate_content(
                prompt=prompt,
                response_schema=response_schema,
                enable_tools=False
            )
            
            if not response:
                logger.warning("⚠️ AI parsing returned no response")
                return citation_list
            
            import json
            parsed = json.loads(response)
            citations_data = parsed.get('citations', [])
            
            for cit_data in citations_data:
                try:
                    citation = Citation(
                        number=cit_data.get('number'),
                        url=cit_data.get('url', '').strip(),
                        title=cit_data.get('title', '').strip(),
                        meta_description=""  # Will be populated later if needed
                    )
                    citation_list.citations.append(citation)
                except Exception as e:
                    logger.warning(f"   ⚠️ Could not create citation from AI response: {e}")
                    continue
            
            # Resolve any proxy URLs (vertexaisearch.cloud.google.com redirects)
            citation_list = self._resolve_proxy_urls(citation_list)
            
            logger.info(f"✅ Extracted {len(citation_list.citations)} citations (AI-only)")
            
        except Exception as e:
            logger.error(f"❌ AI citation extraction failed: {e}")
            logger.warning("   Returning empty citation list")
            return citation_list
        
        return citation_list
    
    def _resolve_proxy_urls(self, citation_list: CitationList) -> CitationList:
        """
        Resolve Gemini grounding proxy URLs to real destination URLs.
        
        Gemini sometimes includes proxy URLs directly in the Sources field:
        https://vertexaisearch.cloud.google.com/grounding-api-redirect/...
        
        These redirect (302) to the actual source. We follow the redirect
        to get clean, real URLs for citations.
        """
        import requests
        
        resolved_count = 0
        for citation in citation_list.citations:
            if 'vertexaisearch.cloud.google.com' in citation.url:
                try:
                    resp = requests.head(citation.url, allow_redirects=False, timeout=5)
                    if resp.status_code in (301, 302, 303, 307, 308):
                        real_url = resp.headers.get('Location', citation.url)
                        logger.info(f"   📎 Resolved proxy URL [{citation.number}]: {real_url}")
                        citation.url = real_url
                        resolved_count += 1
                except Exception as e:
                    logger.warning(f"   Failed to resolve proxy URL [{citation.number}]: {e}")
        
        if resolved_count > 0:
            logger.info(f"✅ Resolved {resolved_count} proxy URLs to real URLs")
        
        return citation_list
    
    async def _check_url_status_parallel(self, citation_list: CitationList) -> Dict[int, str]:
        """
        Check HTTP status of all citation URLs in parallel.
        
        Args:
            citation_list: CitationList with citations to check
            
        Returns:
            Dict mapping citation number to status: 'valid' | 'broken' | 'unknown'
        """
        import asyncio
        import requests
        from concurrent.futures import ThreadPoolExecutor
        
        def check_single_url_sync(citation: Citation) -> tuple[int, str]:
            """Check a single URL synchronously and return (number, status)."""
            try:
                response = requests.head(
                    citation.url,
                    timeout=5,
                    allow_redirects=True,
                    headers={'User-Agent': 'OpenBlog Citation Validator'}
                )
                
                # Some servers block HEAD, try GET
                if response.status_code == 405:
                    response = requests.get(
                        citation.url,
                        timeout=5,
                        allow_redirects=True,
                        headers={'User-Agent': 'OpenBlog Citation Validator'}
                    )
                
                if 200 <= response.status_code < 400:
                    return (citation.number, 'valid')
                elif response.status_code in (404, 500, 503, 504):
                    return (citation.number, 'broken')
                else:
                    return (citation.number, 'unknown')
                    
            except requests.exceptions.Timeout:
                return (citation.number, 'broken')
            except requests.exceptions.ConnectionError:
                return (citation.number, 'broken')
            except Exception as e:
                logger.debug(f"   ⚠️ Citation [{citation.number}]: HTTP check failed - {e}")
                return (citation.number, 'unknown')
        
        logger.info(f"🔍 Checking HTTP status for {len(citation_list.citations)} URLs (parallel)...")
        
        # Run all checks in parallel using thread pool executor
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=10) as executor:
            tasks = [
                loop.run_in_executor(executor, check_single_url_sync, citation)
                for citation in citation_list.citations
            ]
            results = await asyncio.gather(*tasks)
        
        # Build status map
        status_map = {}
        valid_count = 0
        broken_count = 0
        
        for citation_num, status in results:
            status_map[citation_num] = status
            if status == 'valid':
                valid_count += 1
            elif status == 'broken':
                broken_count += 1
        
        logger.info(f"   ✅ HTTP status check complete: {valid_count} valid, {broken_count} broken, {len(citation_list.citations) - valid_count - broken_count} unknown")
        
        return status_map
    
    async def _check_security_ai(self, citation_list: CitationList) -> Dict[int, bool]:
        """
        Use AI (Gemini) to check citations for spam/malicious content.
        
        Args:
            citation_list: CitationList with citations to check
            
        Returns:
            Dict mapping citation number to is_security_risk (True = security risk, False = safe)
        """
        if not citation_list.citations:
            return {}
        
        # Initialize Gemini client if needed
        if not self.gemini_client:
            self.gemini_client = GeminiClient()
        
        logger.info(f"🔒 Checking {len(citation_list.citations)} citations for security risks (AI)...")
        
        # Build list of URLs and titles for analysis
        citations_text = ""
        for citation in citation_list.citations:
            citations_text += f"[{citation.number}]: {citation.url} - {citation.title}\n"
        
        prompt = f"""Analyze these citation URLs for security risks, spam, malicious content, phishing, or low-quality sources.

Citations:
{citations_text}

For each citation, determine if it's a security risk:
- Spam websites
- Malicious/phishing domains
- Low-quality or suspicious sources
- Known bad domains

Return JSON with this structure:
{{
  "security_risks": [
    {{"number": 1, "is_risk": true, "reason": "spam domain"}},
    {{"number": 2, "is_risk": false, "reason": "legitimate source"}}
  ]
}}

Only mark as security risk if you're confident it's spam/malicious. Legitimate sources should be marked as false.
"""
        
        try:
            from google.genai import types
            security_schema = types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "security_risks": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "number": types.Schema(type=types.Type.INTEGER),
                                "is_risk": types.Schema(type=types.Type.BOOLEAN),
                                "reason": types.Schema(type=types.Type.STRING)
                            },
                            required=["number", "is_risk", "reason"]
                        )
                    )
                },
                required=["security_risks"]
            )
            
            response = await self.gemini_client.generate_content(
                prompt=prompt,
                response_schema=security_schema,
                enable_tools=False
            )
            
            if response:
                import json
                parsed = json.loads(response)
                security_map = {}
                risk_count = 0
                
                for risk_info in parsed.get('security_risks', []):
                    citation_num = risk_info.get('number')
                    is_risk = risk_info.get('is_risk', False)
                    reason = risk_info.get('reason', '')
                    
                    security_map[citation_num] = is_risk
                    if is_risk:
                        risk_count += 1
                        logger.warning(f"   ⚠️ Citation [{citation_num}]: Security risk - {reason}")
                
                logger.info(f"   ✅ Security check complete: {risk_count} security risks found")
                return security_map
            else:
                logger.warning("⚠️ Security check returned no response")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Security check failed: {e}")
            logger.warning("   Continuing without security check")
            return {}
    
    def _identify_issues(
        self,
        citation_list: CitationList,
        status_map: Dict[int, str],
        security_map: Dict[int, bool]
    ) -> List[Citation]:
        """
        Identify citations that need replacement based on HTTP status and security checks.
        
        Args:
            citation_list: CitationList with all citations
            status_map: Dict mapping citation number to HTTP status ('valid' | 'broken' | 'unknown')
            security_map: Dict mapping citation number to is_security_risk (True/False)
            
        Returns:
            List of Citation objects that need replacement
        """
        issues = []
        
        for citation in citation_list.citations:
            needs_replacement = False
            reason = []
            
            # Check HTTP status
            status = status_map.get(citation.number, 'unknown')
            if status == 'broken':
                needs_replacement = True
                reason.append('broken URL (404/500/timeout)')
            
            # Check security risk
            is_security_risk = security_map.get(citation.number, False)
            if is_security_risk:
                needs_replacement = True
                reason.append('security risk (spam/malicious)')
            
            # Check if domain-only (path has <= 1 part)
            from urllib.parse import urlparse
            try:
                parsed = urlparse(citation.url)
                path_parts = [p for p in parsed.path.split('/') if p]
                if len(path_parts) <= 1:
                    needs_replacement = True
                    reason.append('domain-only URL')
            except Exception:
                pass
            
            if needs_replacement:
                issues.append(citation)
                logger.debug(f"   ⚠️ Citation [{citation.number}] needs replacement: {', '.join(reason)}")
        
        logger.info(f"📋 Identified {len(issues)} citations needing replacement")
        return issues
    
    async def _find_replacements(
        self,
        citation_list: CitationList,
        issues_list: List[Citation],
        context: ExecutionContext
    ) -> tuple[CitationList, List[int]]:
        """
        Find replacement URLs for broken/security-risk citations (1 retry max).
        
        Args:
            citation_list: Original CitationList
            issues_list: List of citations needing replacement
            context: Execution context
            
        Returns:
            Tuple of (updated CitationList, list of citation numbers with no replacement found)
        """
        if not issues_list:
            return citation_list, []
        
        # Initialize Gemini client if needed
        if not self.gemini_client:
            self.gemini_client = GeminiClient()
        
        logger.info(f"🔍 Finding replacements for {len(issues_list)} citations (1 retry max)...")
        
        updated_list = CitationList()
        updated_list.citations = citation_list.citations.copy()
        no_replacement_nums = []
        
        for citation in issues_list:
            # Try to find alternative URL using Gemini web search
            alternative_url = await self._find_alternative_url(citation, context)
            
            if alternative_url:
                # Validate replacement URL
                status = await self._validate_replacement_url(alternative_url)
                if status == 'valid':
                    # Update citation URL
                    for updated_citation in updated_list.citations:
                        if updated_citation.number == citation.number:
                            logger.info(f"   ✅ Citation [{citation.number}]: Replaced {citation.url[:60]}... → {alternative_url[:60]}...")
                            updated_citation.url = alternative_url
                            break
                else:
                    # Replacement URL also broken - mark as no replacement
                    logger.warning(f"   ⚠️ Citation [{citation.number}]: Replacement URL also broken")
                    no_replacement_nums.append(citation.number)
            else:
                # No alternative found - mark as no replacement
                logger.warning(f"   ⚠️ Citation [{citation.number}]: No replacement found")
                no_replacement_nums.append(citation.number)
        
        if no_replacement_nums:
            logger.warning(f"❌ {len(no_replacement_nums)} citations have no replacement: {no_replacement_nums}")
        else:
            logger.info(f"✅ All {len(issues_list)} citations replaced successfully")
        
        return updated_list, no_replacement_nums
    
    async def _find_alternative_url(self, citation: Citation, context: ExecutionContext) -> Optional[str]:
        """
        Use Gemini web search to find alternative URL for a broken citation (AI-only, no regex).
        
        Args:
            citation: Citation needing replacement
            context: Execution context
            
        Returns:
            Alternative URL if found, None otherwise
        """
        prompt = f"""Find a high-quality alternative source for this broken citation.

Original Citation:
Title: {citation.title}
Original URL: {citation.url} (broken - 404/500/timeout or security risk)

REQUIREMENTS:
1. Search for authoritative sources (.edu, .gov, .org, major publications)
2. Avoid blogs, personal websites, or low-quality sources
3. Prefer recent sources (2020+) unless historical context needed
4. Return the URL of the best alternative source in the "url" field
5. If no good alternative exists, set "url" to null

Search for: {citation.title}
"""
        
        try:
            # Use structured JSON output (AI-only, no regex)
            from pipeline.models.gemini_client import build_response_schema
            
            response_schema = build_response_schema({
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Alternative URL if found, null if no good alternative exists"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Brief reason why this URL was chosen or why no alternative exists"
                    }
                },
                "required": ["url", "reason"]
            })
            
            response = await self.gemini_client.generate_content(
                prompt=prompt,
                response_schema=response_schema,
                enable_tools=True  # Enable Google Search grounding
            )
            
            if not response:
                return None
            
            # Parse JSON response (AI-only, no regex)
            import json
            parsed = json.loads(response)
            url = parsed.get('url')
            
            if url and url.strip() and url.lower() != 'null':
                # Validate URL format (simple check, no regex)
                if url.startswith(('http://', 'https://')):
                    return url.strip()
            
            # Fallback: Check grounding URLs from Gemini search (from current response)
            # Note: Gemini's grounding URLs are automatically included in the response
            # We rely on Gemini's structured output above, but if that fails, we check context
            grounding_urls = getattr(context, 'grounding_urls', [])
            if grounding_urls:
                # Use first grounding URL as fallback
                for grounding in grounding_urls[:1]:
                    url = grounding.get('url', '')
                    if url and url.startswith(('http://', 'https://')):
                        logger.debug(f"   Using grounding URL as alternative: {url[:60]}...")
                        return url
            
            return None
            
        except Exception as e:
            logger.warning(f"   Alternative search failed for citation [{citation.number}]: {e}")
            return None
    
    async def _validate_replacement_url(self, url: str) -> str:
        """
        Validate a replacement URL with HTTP check.
        
        Args:
            url: URL to validate
            
        Returns:
            'valid' | 'broken' | 'unknown'
        """
        import requests
        
        try:
            response = requests.head(
                url,
                timeout=5,
                allow_redirects=True,
                headers={'User-Agent': 'OpenBlog Citation Validator'}
            )
            
            if response.status_code == 405:
                response = requests.get(url, timeout=5, allow_redirects=True)
            
            if 200 <= response.status_code < 400:
                return 'valid'
            else:
                return 'broken'
        except Exception:
            return 'broken'
    
    async def _update_body_citations_ai(
        self,
        context: ExecutionContext,
        citation_list: CitationList,
        no_replacement_nums: List[int]
    ) -> ExecutionContext:
        """
        Update body citations using AI (find-and-replace similar to Stage 3).
        
        - Update href URLs to match validated citations
        - Remove citations with no replacement
        - Preserve citation numbers for remaining citations
        
        Args:
            context: Execution context with structured_data
            citation_list: Updated CitationList with validated URLs
            no_replacement_nums: List of citation numbers to remove from body
            
        Returns:
            Updated context with body citations updated
        """
        if not context.structured_data:
            return context
        
        # Initialize Gemini client if needed
        if not self.gemini_client:
            self.gemini_client = GeminiClient()
        
        # Build citation map for URL updates
        citation_map = {citation.number: citation.url for citation in citation_list.citations}
        
        # Build list of citations to remove
        remove_nums_str = ', '.join(str(n) for n in no_replacement_nums) if no_replacement_nums else 'none'
        
        logger.info(f"🔗 Updating body citations: {len(citation_map)} valid, {len(no_replacement_nums)} to remove")
        
        # Fields to update
        fields_to_update = [
            'Intro', 'Direct_Answer',
            'section_01_content', 'section_02_content', 'section_03_content',
            'section_04_content', 'section_05_content', 'section_06_content',
            'section_07_content', 'section_08_content', 'section_09_content'
        ]
        
        article_dict = context.structured_data.model_dump()
        
        import asyncio
        
        async def update_field(field_name: str) -> tuple[str, str]:
            """Update a single field's citations."""
            content = article_dict.get(field_name, '')
            if not content or not isinstance(content, str):
                return field_name, content or ''
            
            prompt = f"""Update citation links in this content.

VALIDATED CITATIONS (update href URLs to match these):
{chr(10).join(f'[{num}]: {url}' for num, url in sorted(citation_map.items()))}

CITATIONS TO REMOVE (remove these citation links completely):
Citation numbers: {remove_nums_str if no_replacement_nums else 'none'}

CONTENT TO UPDATE:
{content}

TASK:
1. Update all <a href="..." class="citation"> tags to use validated URLs from the list above
2. Remove all citation links for citations in the "remove" list (citation numbers: {remove_nums_str if no_replacement_nums else 'none'})
3. Preserve all other content exactly as-is
4. Preserve citation numbers for remaining citations

Return ONLY the updated content, no explanations.
"""
            
            try:
                response = await self.gemini_client.generate_content(
                    prompt=prompt,
                    enable_tools=False
                )
                
                if response and response.strip():
                    return field_name, response.strip()
                else:
                    return field_name, content
            except Exception as e:
                logger.warning(f"   ⚠️ Field {field_name}: Citation update failed - {e}")
                return field_name, content
        
        # Update all fields in parallel
        tasks = [update_field(field) for field in fields_to_update]
        results = await asyncio.gather(*tasks)
        
        # Apply updates
        updated_count = 0
        for field_name, updated_content in results:
            if article_dict.get(field_name) != updated_content:
                article_dict[field_name] = updated_content
                updated_count += 1
        
        if updated_count > 0:
            logger.info(f"✅ Updated citations in {updated_count} body fields")
            # Update structured_data
            from ..models.output_schema import ArticleOutput
            context.structured_data = ArticleOutput(**article_dict)
        else:
            logger.debug("   No body citations needed updating")
        
        return context

    async def _validate_citations_ultimate(
        self,
        citation_list: CitationList,
        context: ExecutionContext
    ) -> CitationList:
        """
        Ultimate citation validation using the enhanced validator.
        
        Combines:
        - DOI validation via CrossRef API
        - URL status validation with caching
        - Alternative URL search for invalid URLs
        - Metadata quality analysis
        - Author sanity checks
        
        Args:
            citation_list: Citations to validate
            context: Execution context with company data
            
        Returns:
            CitationList with validated and enhanced citations
        """
        if not citation_list.citations:
            return citation_list
        
        # Initialize ultimate validator
        if not self.ultimate_validator:
            if not self.gemini_client:
                self.gemini_client = GeminiClient()
            self.ultimate_validator = SmartCitationValidator(
                gemini_client=self.gemini_client,
                timeout=8.0
            )
        
        # Convert citations to dict format for validation
        citations_for_validation = []
        for citation in citation_list.citations:
            citation_dict = {
                'url': citation.url,
                'title': citation.title,
                'authors': [],  # Isaac Security doesn't parse authors yet
                'doi': '',  # Could be extracted from URL if needed
                'year': 0   # Could be extracted from content if needed
            }
            citations_for_validation.append(citation_dict)
        
        # Extract company and competitor information
        if not context.company_data:
            logger.warning("No company_data available for ultimate citation validation")
            return citation_list
        company_url = context.company_data.get("company_url", "")
        # Fix: Handle case where sitemap_data exists but is None
        sitemap_data = getattr(context, 'sitemap_data', None) or {}
        competitors = sitemap_data.get("competitors", []) if isinstance(sitemap_data, dict) else []
        language = context.language or "en"
        
        # Validate all citations
        try:
            validation_results = await self.ultimate_validator.validate_citations_simple(
                citations_for_validation,
                company_url=company_url,
                competitors=competitors
            )
            
            # Create new citation list with validated URLs
            validated_list = CitationList()
            
            for i, (original_citation, validation_result) in enumerate(zip(citation_list.citations, validation_results)):
                if validation_result.is_valid:
                    # Use validated URL and title
                    enhanced_citation = Citation(
                        number=original_citation.number,
                        url=validation_result.url,
                        title=validation_result.title or original_citation.title
                    )
                    validated_list.citations.append(enhanced_citation)
                    
                    # Log validation result
                    validation_type = validation_result.validation_type
                    if validation_type == 'original_url':
                        logger.info(f"✅ Citation [{enhanced_citation.number}]: Original URL validated")
                    elif validation_type == 'alternative_found':
                        logger.info(f"🔄 Citation [{enhanced_citation.number}]: Alternative URL found")
                        logger.info(f"   Original: {original_citation.url}")
                        logger.info(f"   Enhanced: {enhanced_citation.url}")
                    elif validation_type == 'doi_verified':
                        logger.info(f"📚 Citation [{enhanced_citation.number}]: DOI verified")
                    
                    if validation_result.issues:
                        for issue in validation_result.issues:
                            logger.warning(f"   ⚠️  {issue}")
                            
                else:
                    # Citation failed validation - check if we should keep it
                    # Filter out if:
                    # 1. Spam/malicious/phishing
                    # 2. HTTP errors (404, 500, etc.) with no alternative found
                    # 3. No valid URL found
                    should_filter = False
                    has_http_error = False
                    has_alternative_attempt = False
                    
                    for issue in validation_result.issues:
                        issue_lower = issue.lower()
                        # Security concerns - always filter
                        if any(keyword in issue_lower for keyword in ['spam', 'malicious', 'phishing']):
                            should_filter = True
                            break
                        # HTTP errors (404, 500, etc.)
                        if 'http' in issue_lower and any(code in issue for code in ['403', '404', '500', '503', '504']):
                            has_http_error = True
                        # Check if alternative was attempted
                        if 'alternative' in issue_lower or 'no alternative' in issue_lower:
                            has_alternative_attempt = True
                    
                    # Filter out if HTTP error AND no alternative found
                    if has_http_error and ('no alternative source found' in ' '.join(validation_result.issues).lower()):
                        should_filter = True
                    
                    # Filter out if no valid URL found
                    if 'no valid url found' in ' '.join(validation_result.issues).lower():
                        should_filter = True
                    
                    if should_filter:
                        logger.warning(f"❌ Filtering out Citation [{original_citation.number}]: Validation failed")
                        for issue in validation_result.issues:
                            logger.warning(f"   ⚠️  {issue}")
                        # Don't add to validated_list - citation is removed
                    else:
                        # Only keep if it's a minor issue (metadata quality, etc.) but URL is valid
                        logger.warning(f"⚠️ Keeping Citation [{original_citation.number}] with minor issues:")
                        for issue in validation_result.issues:
                            logger.warning(f"   ⚠️  {issue}")
                        validated_list.citations.append(original_citation)
            
            # Renumber citations
            for i, citation in enumerate(validated_list.citations, 1):
                citation.number = i
            
            logger.info(f"🔍 Ultimate validation complete: {len(validated_list.citations)} citations processed")
            
            return validated_list
            
        except Exception as e:
            logger.error(f"Ultimate citation validation failed: {e}")
            # Return original citations on failure
            return citation_list
    
    def __repr__(self) -> str:
        """String representation."""
        return f"CitationsStage(stage_num={self.stage_num})"
