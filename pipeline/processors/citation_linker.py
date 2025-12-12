"""
Citation Linker - Natural Language Citation Linking

Converts natural language source attributions to clickable hyperlinks.

Design Principles:
- Single Responsibility: Only handles citation→link conversion
- Open/Closed: Pattern list is configurable without code changes
- DRY: Centralized citation detection logic

Examples:
- "According to IBM" → <a href="ibm.com">According to IBM</a>
- "Gartner reports that" → <a href="gartner.com">Gartner</a> reports that
- "research by McKinsey" → research by <a href="mckinsey.com">McKinsey</a>

This module works WITH the citation_map from Stage 4, matching source names
to their validated URLs.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CitationPattern:
    """Defines a pattern for finding natural language citations."""
    pattern: str  # Regex pattern
    source_group: int  # Which group contains the source name
    link_format: str  # How to format the link (use {source} and {url})


class CitationLinker:
    """
    Link natural language citations to their source URLs.
    
    Uses a citation_map (source_name → URL) to find and link
    phrases like "according to IBM" or "Gartner predicts".
    """
    
    # Common patterns for source attribution in professional content
    # These are ordered by specificity (more specific patterns first)
    CITATION_PATTERNS = [
        # "According to [Source]" - most common
        CitationPattern(
            pattern=r'(?i)\baccording to\s+([A-Z][A-Za-z\s&]+?)(?=[,\.\s]|\'s|\s+research|\s+report|\s+study|\s+data)',
            source_group=1,
            link_format='according to <a href="{url}" target="_blank" rel="noopener noreferrer" class="citation">{source}</a>'
        ),
        # "[Source] reports/states/notes/predicts/estimates/indicates"
        CitationPattern(
            pattern=r'(?i)\b([A-Z][A-Za-z\s&]+?)\s+(reports?|states?|notes?|predicts?|estimates?|indicates?|found|shows?|reveals?|highlights?)\s+that\b',
            source_group=1,
            link_format='<a href="{url}" target="_blank" rel="noopener noreferrer" class="citation">{source}</a> {verb} that'
        ),
        # "research/report/study by [Source]"
        CitationPattern(
            pattern=r'(?i)\b(research|report|study|survey|analysis)\s+(?:by|from)\s+([A-Z][A-Za-z\s&]+?)(?=[,\.\s])',
            source_group=2,
            link_format='{prefix} by <a href="{url}" target="_blank" rel="noopener noreferrer" class="citation">{source}</a>'
        ),
        # "[Source]'s research/report/study/data"
        CitationPattern(
            pattern=r'(?i)\b([A-Z][A-Za-z\s&]+?)\'s\s+(research|report|study|survey|analysis|data|findings)\b',
            source_group=1,
            link_format='<a href="{url}" target="_blank" rel="noopener noreferrer" class="citation">{source}</a>\'s {suffix}'
        ),
        # "data from [Source]"
        CitationPattern(
            pattern=r'(?i)\b(data|statistics|figures|numbers)\s+from\s+([A-Z][A-Za-z\s&]+?)(?=[,\.\s])',
            source_group=2,
            link_format='{prefix} from <a href="{url}" target="_blank" rel="noopener noreferrer" class="citation">{source}</a>'
        ),
    ]
    
    # Known source name mappings (handles variations)
    SOURCE_ALIASES = {
        'ibm': ['ibm', 'ibm security', 'ibm research'],
        'gartner': ['gartner', 'gartner research', 'gartner inc'],
        'mckinsey': ['mckinsey', 'mckinsey & company', 'mckinsey and company'],
        'forrester': ['forrester', 'forrester research'],
        'palo alto': ['palo alto', 'palo alto networks'],
        'crowdstrike': ['crowdstrike'],
        'splunk': ['splunk'],
        'darktrace': ['darktrace'],
        'sans': ['sans', 'sans institute'],
        'isc2': ['isc2', 'isc²', '(isc)²'],
        'owasp': ['owasp'],
        'nist': ['nist'],
        'cisa': ['cisa'],
    }
    
    def __init__(self, citation_map: Optional[Dict[str, str]] = None, max_links_per_source: int = 2):
        """
        Initialize the citation linker.
        
        Args:
            citation_map: Dict mapping source names/numbers to URLs
            max_links_per_source: Maximum times to link each source (avoid over-linking)
        """
        self.citation_map = citation_map or {}
        self.max_links_per_source = max_links_per_source
        self.link_counts: Dict[str, int] = {}  # Track links per URL
        
        # Build a normalized source→URL lookup
        self.source_lookup = self._build_source_lookup()
    
    def _build_source_lookup(self) -> Dict[str, str]:
        """
        Build a normalized lookup from source names to URLs.
        
        Handles:
        - Citation numbers (1, 2, 3) mapped to their sources
        - Source names mapped to URLs
        - Common aliases (IBM → ibm research, etc.)
        """
        lookup = {}
        
        for key, url in self.citation_map.items():
            # Skip if not a valid URL
            if not url or not url.startswith('http'):
                continue
            
            # Extract domain/source name from URL
            domain = self._extract_source_from_url(url)
            if domain:
                lookup[domain.lower()] = url
                # Also add the full key if it's a string name
                if isinstance(key, str) and not key.isdigit():
                    lookup[key.lower()] = url
        
        logger.debug(f"Built source lookup with {len(lookup)} entries")
        return lookup
    
    def _extract_source_from_url(self, url: str) -> Optional[str]:
        """Extract source name from URL domain."""
        try:
            # Extract domain from URL
            domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
            if domain_match:
                domain = domain_match.group(1)
                # Get the main part (e.g., 'ibm' from 'ibm.com')
                parts = domain.split('.')
                if len(parts) >= 2:
                    return parts[-2]  # 'ibm' from 'ibm.com'
        except Exception:
            pass
        return None
    
    def _find_matching_url(self, source_name: str) -> Optional[str]:
        """
        Find URL for a source name, handling aliases and fuzzy matching.
        
        Args:
            source_name: The source name to look up (e.g., "IBM", "Gartner Research")
            
        Returns:
            URL if found, None otherwise
        """
        normalized = source_name.lower().strip()
        
        # Direct lookup
        if normalized in self.source_lookup:
            return self.source_lookup[normalized]
        
        # Check aliases
        for base_name, aliases in self.SOURCE_ALIASES.items():
            if normalized in aliases or base_name in normalized:
                # Look for this base name in the lookup
                for key, url in self.source_lookup.items():
                    if base_name in key:
                        return url
        
        # Fuzzy match - check if any lookup key is contained in source_name
        for key, url in self.source_lookup.items():
            if key in normalized or normalized in key:
                return url
        
        return None
    
    def link_citations(self, content: str) -> str:
        """
        Convert natural language citations to hyperlinks.
        
        Args:
            content: HTML content with natural language citations
            
        Returns:
            Content with citations converted to <a> links
        """
        if not content or not self.source_lookup:
            logger.debug("No content or no source lookup - skipping citation linking")
            return content
        
        linked_count = 0
        
        # Process each pattern
        for pattern_def in self.CITATION_PATTERNS:
            matches = list(re.finditer(pattern_def.pattern, content))
            
            # Process matches in reverse order to preserve positions
            for match in reversed(matches):
                source_name = match.group(pattern_def.source_group).strip()
                url = self._find_matching_url(source_name)
                
                if not url:
                    logger.debug(f"No URL found for source: {source_name}")
                    continue
                
                # Check link count limit
                current_count = self.link_counts.get(url, 0)
                if current_count >= self.max_links_per_source:
                    logger.debug(f"URL {url} already linked {current_count} times, skipping")
                    continue
                
                # Build replacement
                replacement = self._build_replacement(match, pattern_def, source_name, url)
                if replacement:
                    # Replace in content
                    content = content[:match.start()] + replacement + content[match.end():]
                    self.link_counts[url] = current_count + 1
                    linked_count += 1
        
        if linked_count > 0:
            logger.info(f"✅ Linked {linked_count} natural language citations")
        else:
            logger.debug("No natural language citations linked")
        
        return content
    
    def _build_replacement(self, match: re.Match, pattern_def: CitationPattern, 
                          source_name: str, url: str) -> Optional[str]:
        """Build the replacement string for a matched citation."""
        try:
            # Get the full matched text
            full_match = match.group(0)
            
            # Simple replacement - wrap source name in link
            # This handles most cases
            linked_source = f'<a href="{url}" target="_blank" rel="noopener noreferrer" class="citation">{source_name}</a>'
            
            # Replace source name with linked version
            replacement = full_match.replace(source_name, linked_source, 1)
            
            return replacement
            
        except Exception as e:
            logger.warning(f"Error building citation replacement: {e}")
            return None


def link_natural_citations(content: str, citation_map: Dict[str, str], 
                          max_links_per_source: int = 2) -> str:
    """
    Link natural language citations to their source URLs.
    
    This is the main entry point for citation linking.
    
    Args:
        content: HTML content with citations
        citation_map: Dict mapping source identifiers to URLs
        max_links_per_source: Maximum times to link each URL
        
    Returns:
        Content with linked citations
    """
    linker = CitationLinker(citation_map, max_links_per_source)
    return linker.link_citations(content)
