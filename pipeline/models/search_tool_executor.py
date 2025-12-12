# ABOUTME: Unified search tool executor with Google Search + DataForSEO fallback support
# ABOUTME: Handles search operations with automatic fallback when Google Search quota is exhausted

import logging
import os
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class SearchToolExecutor:
    """Unified search tool executor with fallback support.
    
    Primary: Google Search (free, built into Gemini)
    Fallback: DataForSEO (paid, $0.50/1k queries)
    """

    def __init__(self):
        """Initialize search executor with DataForSEO fallback."""
        self.dataforseo_provider = None
        
        # Initialize DataForSEO provider if credentials available
        try:
            from .dataforseo_provider import DataForSeoProvider
            
            login = os.getenv("DATAFORSEO_LOGIN")
            password = os.getenv("DATAFORSEO_PASSWORD")
            
            if login and password:
                self.dataforseo_provider = DataForSeoProvider(login, password)
                logger.info("✅ DataForSEO fallback initialized")
            else:
                logger.warning("⚠️  DataForSEO credentials not found - fallback disabled")
        except ImportError:
            logger.warning("⚠️  DataForSEO provider not available")

    async def execute_search_with_fallback(
        self, 
        query: str, 
        primary_error: Optional[Exception] = None,
        max_results: int = 5,
        country: str = "us",
        language: str = "en"
    ) -> str:
        """Execute search with DataForSEO fallback when Google Search fails.

        Args:
            query: Search query string
            primary_error: Error from primary Google Search (if any)
            max_results: Maximum number of results to return
            country: Country code for localization
            language: Language code

        Returns:
            Formatted search results string for LLM consumption
        """
        # Check if we should use fallback
        should_use_fallback = False
        
        if primary_error:
            error_str = str(primary_error).lower()
            quota_exhausted = any(keyword in error_str for keyword in [
                "rate limit", "quota", "resource_exhausted", "429", 
                "too many requests", "usage limit", "billing"
            ])
            
            if quota_exhausted:
                should_use_fallback = True
                logger.warning(f"🚨 Google Search quota exhausted, activating DataForSEO fallback")

        if should_use_fallback and self.dataforseo_provider:
            return await self._execute_dataforseo_search(
                query, max_results, country, language
            )
        elif primary_error:
            # No fallback available or error is not quota-related
            logger.error(f"❌ Search failed and no fallback available: {primary_error}")
            return f"Search failed: {str(primary_error)}"
        else:
            # This shouldn't happen - we're only called when there's an error
            logger.warning("⚠️  SearchToolExecutor called without error")
            return f"Search unavailable for: {query}"

    async def _execute_dataforseo_search(
        self, 
        query: str, 
        max_results: int,
        country: str,
        language: str
    ) -> str:
        """Execute search using DataForSEO provider.

        Args:
            query: Search query string
            max_results: Maximum number of results
            country: Country code
            language: Language code

        Returns:
            Formatted search results string
        """
        try:
            logger.info(f"🔍 Executing DataForSEO search: '{query}' ({country}, {language})")
            
            response = await self.dataforseo_provider.search(
                query=query,
                num_results=max_results * 2,  # Get more results, format fewer
                language=language,
                country=country
            )

            if not response.success:
                error_msg = f"DataForSEO search failed: {response.error}"
                logger.error(f"❌ {error_msg}")
                return error_msg

            # Format results for LLM consumption
            formatted_results = self.dataforseo_provider.format_for_llm(
                response, max_results=max_results
            )

            # Log success metrics
            logger.info(
                f"✅ DataForSEO fallback successful: {len(response.results)} results, "
                f"~${response.cost_credits:.4f} cost"
            )
            
            return formatted_results

        except Exception as e:
            error_msg = f"DataForSEO fallback error: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return error_msg

    def is_fallback_available(self) -> bool:
        """Check if DataForSEO fallback is available."""
        return self.dataforseo_provider is not None and self.dataforseo_provider.is_configured()

    def get_fallback_info(self) -> Dict[str, Any]:
        """Get information about fallback configuration."""
        if not self.dataforseo_provider:
            return {
                "available": False,
                "reason": "DataForSEO provider not initialized"
            }

        if not self.dataforseo_provider.is_configured():
            return {
                "available": False,
                "reason": "DataForSEO credentials not configured"
            }

        return {
            "available": True,
            "provider": self.dataforseo_provider.name,
            "cost_per_1k": self.dataforseo_provider.cost_per_1k,
            "credentials_set": bool(self.dataforseo_provider.api_login)
        }


# Global instance for reuse across requests
_search_executor = None


def get_search_executor() -> SearchToolExecutor:
    """Get global search executor instance."""
    global _search_executor
    if _search_executor is None:
        _search_executor = SearchToolExecutor()
    return _search_executor


