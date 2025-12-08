"""
Ultimate Citation Validator

Combines the best features from multiple OpenBlog repositories:
- OpenDraft: DOI validation via CrossRef API + metadata quality checks
- Blog-Writer: Async URL validation with caching + alternative URL search
- Isaac Security: Clean structured approach with V4.0 architecture

Features:
- Comprehensive DOI validation via CrossRef API
- Async URL status validation with intelligent caching
- Alternative URL search using Gemini + GoogleSearch for 404s
- Metadata quality analysis (author sanity, title validation, etc.)
- Performance optimized with parallel processing
- Maintains citation count requirement
- Zero tolerance for fake/placeholder URLs
"""

import asyncio
import json
import logging
import re
import time
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass
from urllib.parse import urlparse
import httpx
import requests

from ..models.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

# Performance caches
_URL_STATUS_CACHE: Dict[str, Tuple[bool, str, float]] = {}
_DOI_VALIDATION_CACHE: Dict[str, Tuple[bool, float]] = {}
_CACHE_TTL = 300  # 5 minutes

# Forbidden hosts and domains
FORBIDDEN_HOSTS: Set[str] = {
    "vertexaisearch.cloud.google.com",
    "cloud.google.com",
    "example.com",
    "example.org",
    "placeholder.com"
}


@dataclass
class ValidationResult:
    """Result of citation validation"""
    is_valid: bool
    url: str
    title: str
    issues: List[str]
    validation_type: str  # 'original', 'alternative', 'doi_only'


@dataclass
class CitationValidationIssue:
    """Citation validation issue"""
    citation_id: str
    severity: str  # 'critical', 'warning', 'info'
    issue_type: str
    message: str
    citation_text: str


class UltimateCitationValidator:
    """
    Ultimate citation validator combining best features from all repositories.
    
    Provides comprehensive validation including:
    - DOI verification via CrossRef API
    - URL status validation with caching
    - Alternative URL search for invalid URLs
    - Metadata quality analysis
    - Author sanity checks
    """

    def __init__(
        self,
        gemini_client: Optional[GeminiClient] = None,
        timeout: float = 10.0,
        max_search_attempts: int = 5
    ):
        """
        Initialize ultimate citation validator.
        
        Args:
            gemini_client: Optional Gemini client for alternative URL search
            timeout: HTTP request timeout in seconds
            max_search_attempts: Maximum attempts to find alternative URLs
        """
        self.gemini_client = gemini_client
        self.timeout = timeout
        self.max_search_attempts = max_search_attempts
        self.crossref_api_base = "https://api.crossref.org/works/"
        
        # Async HTTP client for URL validation
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=3.0, read=timeout),
            follow_redirects=True,
            max_redirects=3
        )

    async def validate_citations_comprehensive(
        self,
        citations: List[Dict[str, Any]],
        company_url: str = "",
        competitors: List[str] = None,
        language: str = "en"
    ) -> List[ValidationResult]:
        """
        Comprehensive validation of multiple citations in parallel.
        
        Args:
            citations: List of citation dictionaries
            company_url: Company URL for fallback
            competitors: List of competitor domains to avoid
            language: Language for alternative searches
            
        Returns:
            List of ValidationResult objects
        """
        if not citations:
            return []

        competitors = competitors or []
        
        logger.info(f"🔍 Starting comprehensive validation of {len(citations)} citations")
        
        # Validate all citations in parallel for performance
        validation_tasks = [
            self.validate_single_citation(
                citation, company_url, competitors, language
            )
            for citation in citations
        ]
        
        results = await asyncio.gather(*validation_tasks, return_exceptions=True)
        
        # Handle any exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Citation {i} validation failed: {result}")
                # Create failed validation result
                citation = citations[i]
                valid_results.append(ValidationResult(
                    is_valid=False,
                    url=citation.get('url', ''),
                    title=citation.get('title', ''),
                    issues=[f"Validation failed: {str(result)}"],
                    validation_type='failed'
                ))
            else:
                valid_results.append(result)
        
        # Log validation summary
        valid_count = sum(1 for r in valid_results if r.is_valid)
        logger.info(f"✅ Citation validation complete: {valid_count}/{len(citations)} valid")
        
        return valid_results

    async def validate_single_citation(
        self,
        citation: Dict[str, Any],
        company_url: str,
        competitors: List[str],
        language: str
    ) -> ValidationResult:
        """
        Validate a single citation comprehensively.
        
        Process:
        1. Extract and validate DOI if present
        2. Validate URL status
        3. Check metadata quality
        4. Search for alternatives if needed
        5. Return best available result
        """
        url = citation.get('url', '').strip()
        title = citation.get('title', '').strip()
        authors = citation.get('authors', [])
        doi = citation.get('doi', '').strip()
        
        issues = []
        
        # Step 1: DOI validation (if present)
        if doi:
            doi_valid = await self.validate_doi_async(doi)
            if doi_valid:
                logger.info(f"✅ DOI validated: {doi}")
                # For DOI citations, we can be more lenient with URL issues
                return ValidationResult(
                    is_valid=True,
                    url=url or f"https://doi.org/{doi}",
                    title=title,
                    issues=issues,
                    validation_type='doi_verified'
                )
            else:
                issues.append(f"DOI validation failed: {doi}")
        
        # Step 2: Metadata quality checks
        metadata_issues = self.check_metadata_quality(citation)
        issues.extend(metadata_issues)
        
        # Step 3: Author sanity checks
        if authors:
            author_issues = self.check_author_sanity(authors)
            issues.extend(author_issues)
        
        # Step 4: URL validation
        if url:
            url_valid, final_url, url_issues = await self.validate_url_comprehensive(url)
            issues.extend(url_issues)
            
            if url_valid and not self._is_forbidden_or_competitor(final_url, competitors):
                return ValidationResult(
                    is_valid=True,
                    url=final_url,
                    title=title,
                    issues=issues,
                    validation_type='original_url'
                )
        
        # Step 5: Search for alternative URL if original failed
        if self.gemini_client and title:
            alternative = await self._find_alternative_url_enhanced(
                title, company_url, competitors, language
            )
            
            if alternative:
                return ValidationResult(
                    is_valid=True,
                    url=alternative[0],
                    title=alternative[1],
                    issues=issues + ["Used alternative URL"],
                    validation_type='alternative_found'
                )
        
        # Step 6: Final fallback - mark as invalid but preserve data
        return ValidationResult(
            is_valid=False,
            url=url or company_url,
            title=title or "Source unavailable",
            issues=issues + ["No valid URL or alternative found"],
            validation_type='fallback'
        )

    async def validate_doi_async(self, doi: str) -> bool:
        """
        Validate DOI via CrossRef API (async version).
        
        Args:
            doi: DOI to validate
            
        Returns:
            True if DOI exists, False otherwise
        """
        if not doi:
            return False
        
        # Clean DOI
        doi_clean = doi.replace('https://doi.org/', '').replace('http://doi.org/', '')
        
        # Check cache
        cache_key = doi_clean
        if cache_key in _DOI_VALIDATION_CACHE:
            is_valid, timestamp = _DOI_VALIDATION_CACHE[cache_key]
            if time.time() - timestamp < _CACHE_TTL:
                return is_valid
        
        try:
            async with self.http_client as client:
                response = await client.get(
                    f"{self.crossref_api_base}{doi_clean}",
                    headers={'User-Agent': 'OpenBlog/1.0 Citation Validator'}
                )
                is_valid = response.status_code == 200
                
                # Cache result
                _DOI_VALIDATION_CACHE[cache_key] = (is_valid, time.time())
                
                return is_valid
                
        except Exception as e:
            logger.warning(f"DOI validation failed for {doi}: {e}")
            return False

    async def validate_url_comprehensive(self, url: str) -> Tuple[bool, str, List[str]]:
        """
        Comprehensive URL validation with caching.
        
        Returns:
            Tuple of (is_valid, final_url, issues_list)
        """
        if not url:
            return False, "", ["No URL provided"]
        
        # Check cache
        cache_key = url
        if cache_key in _URL_STATUS_CACHE:
            is_valid, final_url, timestamp = _URL_STATUS_CACHE[cache_key]
            if time.time() - timestamp < _CACHE_TTL:
                return is_valid, final_url, []
        
        issues = []
        
        try:
            async with self.http_client as client:
                response = await client.head(url)
                
                # Some servers block HEAD requests, try GET
                if response.status_code == 405:
                    response = await client.get(url)
                
                is_valid = 200 <= response.status_code < 400
                final_url = str(response.url)
                
                if not is_valid:
                    issues.append(f"HTTP {response.status_code}")
                
                # Cache result
                _URL_STATUS_CACHE[cache_key] = (is_valid, final_url, time.time())
                
                return is_valid, final_url, issues
                
        except httpx.TimeoutException:
            issues.append("Request timeout")
            _URL_STATUS_CACHE[cache_key] = (False, url, time.time())
            return False, url, issues
            
        except Exception as e:
            issues.append(f"Request failed: {str(e)[:50]}")
            _URL_STATUS_CACHE[cache_key] = (False, url, time.time())
            return False, url, issues

    def check_metadata_quality(self, citation: Dict[str, Any]) -> List[str]:
        """
        Check citation metadata quality (from OpenDraft).
        
        Returns:
            List of quality issues found
        """
        issues = []
        title = citation.get('title', '')
        authors = citation.get('authors', [])
        url = citation.get('url', '')
        year = citation.get('year', 0)
        
        # Check 1: Title is domain name
        domain_pattern = r'^[a-zA-Z0-9.-]+\.(com|org|gov|edu|net|io|ai|co\.uk)(:443)?$'
        if re.match(domain_pattern, title, re.IGNORECASE):
            issues.append(f"Domain name as title: '{title}'")
        
        # Check 2: Author is same as title
        if authors and title and len(authors) > 0:
            if authors[0].strip().lower() == title.strip().lower():
                issues.append(f"Author duplicates title: '{authors[0]}'")
        
        # Check 3: URL contains error keywords
        error_keywords = ['error', '403', '404', '500', '503', 'not-found', 'forbidden']
        if url and any(keyword in url.lower() for keyword in error_keywords):
            issues.append(f"URL contains error keyword: '{url}'")
        
        # Check 4: Year validation
        if year and (year < 1990 or year > 2026):
            issues.append(f"Year out of range: {year}")
        
        # Check 5: Placeholder titles
        placeholder_titles = [
            'untitled', 'no title', 'unknown', '[title]', 'n/a', 'article', 'document'
        ]
        if title.lower().strip() in placeholder_titles:
            issues.append(f"Placeholder title: '{title}'")
        
        return issues

    def check_author_sanity(self, authors: List[str]) -> List[str]:
        """
        Check for suspicious author patterns (from OpenDraft).
        
        Returns:
            List of author-related issues
        """
        issues = []
        
        # Check for excessive authors
        MAX_REASONABLE_AUTHORS = 30
        if len(authors) > MAX_REASONABLE_AUTHORS:
            issues.append(f"Excessive authors ({len(authors)}) - likely malformed data")
            return issues
        
        for author in authors:
            # Repetitive initials pattern
            if re.match(r'^([A-Z]\.\s*){6,}$', author):
                issues.append(f"Repetitive initials pattern: '{author}'")
            
            # Domain name as author
            domain_pattern = r'^[a-zA-Z0-9.-]+\.(com|org|gov|edu|net|io|ai|co\.uk)$'
            if re.match(domain_pattern, author, re.IGNORECASE):
                issues.append(f"Domain name as author: '{author}'")
        
        return issues

    async def _find_alternative_url_enhanced(
        self,
        title: str,
        company_url: str,
        competitors: List[str],
        language: str
    ) -> Optional[Tuple[str, str]]:
        """
        Enhanced alternative URL search using Gemini + GoogleSearch.
        
        Returns:
            Tuple of (url, title) if found, None otherwise
        """
        if not self.gemini_client or not title:
            return None
        
        try:
            # Construct search query
            search_query = f"authoritative source: {title}"
            
            logger.info(f"🔍 Searching for alternative URL: {search_query}")
            
            # Use Gemini with GoogleSearch tool
            prompt = f"""
            Find an authoritative, accessible URL for this topic: "{title}"
            
            Requirements:
            - Must be from a reputable source (academic, government, established organization)
            - Must be publicly accessible (not behind paywall)
            - Must be relevant to the topic
            - Avoid these competitors: {', '.join(competitors)}
            - Avoid these forbidden domains: {', '.join(FORBIDDEN_HOSTS)}
            
            Return format:
            URL: [the URL]
            Title: [the page title]
            """
            
            response = await self.gemini_client.generate_content_async(
                prompt,
                tools=['googleSearch']
            )
            
            if response and 'URL:' in response:
                # Parse response
                lines = response.split('\n')
                url_line = next((line for line in lines if line.startswith('URL:')), None)
                title_line = next((line for line in lines if line.startswith('Title:')), None)
                
                if url_line:
                    url = url_line.replace('URL:', '').strip()
                    new_title = title_line.replace('Title:', '').strip() if title_line else title
                    
                    # Validate the alternative URL
                    if not self._is_forbidden_or_competitor(url, competitors):
                        url_valid, final_url, _ = await self.validate_url_comprehensive(url)
                        if url_valid:
                            logger.info(f"✅ Alternative URL found: {final_url}")
                            return final_url, new_title
            
            return None
            
        except Exception as e:
            logger.warning(f"Alternative URL search failed: {e}")
            return None

    def _is_forbidden_or_competitor(self, url: str, competitors: List[str]) -> bool:
        """
        Check if URL is forbidden or from a competitor.
        
        Args:
            url: URL to check
            competitors: List of competitor domains
            
        Returns:
            True if URL should be avoided
        """
        if not url:
            return True
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Check forbidden hosts
            if domain in FORBIDDEN_HOSTS:
                return True
            
            # Check competitors
            for competitor in competitors:
                if competitor.lower() in domain:
                    return True
            
            return False
            
        except Exception:
            return True

    async def close(self):
        """Close HTTP client."""
        if hasattr(self, 'http_client'):
            await self.http_client.aclose()


# Utility functions for backwards compatibility
def validate_citation_url_legacy(url: str, timeout: int = 10) -> Tuple[Optional[int], str]:
    """
    Legacy URL validation function for backwards compatibility.
    
    Returns:
        Tuple of (status_code, error_message)
    """
    if not url:
        return None, "No URL provided"
    
    try:
        response = requests.head(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={'User-Agent': 'OpenBlog Citation Validator'}
        )
        
        # Try GET if HEAD fails
        if response.status_code == 405:
            response = requests.get(url, timeout=timeout, allow_redirects=True)
        
        return response.status_code, ""
        
    except requests.exceptions.Timeout:
        return None, "Timeout"
    except requests.exceptions.ConnectionError:
        return None, "Connection failed"
    except requests.exceptions.RequestException as e:
        return None, f"Request error: {str(e)[:50]}"