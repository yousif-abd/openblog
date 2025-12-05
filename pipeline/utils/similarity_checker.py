"""
Content Similarity Checker - SEO-level duplicate detection.

Detects content cannibalization like SEObility/Screaming Frog would flag:
- Keyword cannibalization (same target keyword)
- Title/meta overlap
- Heading similarity (H2s covering same topics)  
- Content overlap (key phrases, paragraphs)
- FAQ/PAA duplication

Usage:
    checker = ContentSimilarityChecker("fingerprints.json")
    
    # Check before generating
    issues = checker.check_keyword(new_keyword, existing_keywords)
    
    # Check after generating  
    report = checker.check_article(new_article)
    if report.is_duplicate:
        print(f"Too similar to: {report.similar_to}")
    
    # Store for future checks
    checker.store_article(article)
"""

import json
import os
import re
import logging
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Set, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class ArticleFingerprint:
    """Fingerprint of an article for similarity comparison."""
    slug: str
    primary_keyword: str
    meta_title: str
    meta_description: str
    headings: List[str]  # H2s
    key_phrases: List[str]  # Important 3-4 word phrases
    faq_questions: List[str]
    intro_hash: str  # First 200 chars normalized
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "ArticleFingerprint":
        return cls(**data)


@dataclass 
class SimilarityReport:
    """Detailed similarity report."""
    is_duplicate: bool
    overall_score: float  # 0-100
    similar_to: Optional[str] = None  # slug of most similar article
    
    # Detailed scores
    keyword_match: bool = False
    title_similarity: float = 0.0
    heading_overlap: float = 0.0
    content_overlap: float = 0.0
    faq_overlap: float = 0.0
    
    # Specific issues
    issues: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return asdict(self)


class ContentSimilarityChecker:
    """
    SEO-level content similarity checker.
    
    Thresholds (adjustable):
    - DUPLICATE_THRESHOLD: 70% overall = definite duplicate
    - WARNING_THRESHOLD: 50% overall = potential cannibalization
    - KEYWORD_EXACT_MATCH: Always flagged
    """
    
    DUPLICATE_THRESHOLD = 70.0
    WARNING_THRESHOLD = 50.0
    
    def __init__(self, storage_path: str = "content_fingerprints.json"):
        """
        Initialize checker with storage path.
        
        Args:
            storage_path: Path to JSON file storing fingerprints
        """
        self.storage_path = Path(storage_path)
        self.fingerprints: Dict[str, ArticleFingerprint] = {}
        self._load()
    
    def _load(self):
        """Load existing fingerprints from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.fingerprints = {
                        k: ArticleFingerprint.from_dict(v) 
                        for k, v in data.items()
                    }
                logger.info(f"Loaded {len(self.fingerprints)} article fingerprints")
            except Exception as e:
                logger.warning(f"Failed to load fingerprints: {e}")
                self.fingerprints = {}
    
    def _save(self):
        """Save fingerprints to storage."""
        try:
            with open(self.storage_path, 'w') as f:
                data = {k: v.to_dict() for k, v in self.fingerprints.items()}
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save fingerprints: {e}")
    
    # ========== EXTRACTION ==========
    
    def extract_fingerprint(self, article: dict, slug: str = None) -> ArticleFingerprint:
        """
        Extract fingerprint from article for comparison.
        
        Args:
            article: Article dictionary (from blog generation)
            slug: Article slug (optional, will generate if not provided)
        """
        # Get slug
        slug = slug or article.get("slug") or self._generate_slug(
            article.get("Headline") or article.get("headline", "")
        )
        
        # Primary keyword
        primary_keyword = (
            article.get("primary_keyword") or 
            article.get("keyword", "")
        ).lower().strip()
        
        # Meta
        meta_title = (article.get("Meta_Title") or article.get("meta_title", "")).lower()
        meta_description = (article.get("Meta_Description") or article.get("meta_description", "")).lower()
        
        # Headings (H2s from sections or ToC)
        headings = self._extract_headings(article)
        
        # Key phrases (important 3-4 grams)
        key_phrases = self._extract_key_phrases(article)
        
        # FAQ questions
        faq_questions = self._extract_faq_questions(article)
        
        # Intro hash
        intro = article.get("Intro") or article.get("intro", "")
        intro_hash = self._normalize_text(intro[:200])
        
        return ArticleFingerprint(
            slug=slug,
            primary_keyword=primary_keyword,
            meta_title=meta_title,
            meta_description=meta_description,
            headings=headings,
            key_phrases=key_phrases,
            faq_questions=faq_questions,
            intro_hash=intro_hash,
        )
    
    def _extract_headings(self, article: dict) -> List[str]:
        """Extract H2 headings from article."""
        headings = []
        
        # From ToC
        toc = article.get("table_of_contents") or article.get("ToC", [])
        if isinstance(toc, list):
            for item in toc:
                if isinstance(item, dict):
                    headings.append(item.get("title", "").lower())
                elif isinstance(item, str):
                    headings.append(item.lower())
        
        # From sections
        for i in range(1, 10):
            heading = article.get(f"section_{i:02d}_heading") or article.get(f"Section_{i:02d}_Heading", "")
            if heading:
                headings.append(heading.lower())
        
        return [h for h in headings if h]
    
    def _extract_key_phrases(self, article: dict) -> List[str]:
        """Extract important 3-4 word phrases from content."""
        # Combine all text content
        text_parts = []
        
        # Intro
        text_parts.append(article.get("Intro") or article.get("intro", ""))
        
        # Sections
        for i in range(1, 10):
            content = article.get(f"section_{i:02d}_content") or article.get(f"Section_{i:02d}_Content", "")
            text_parts.append(content)
        
        # Key takeaways
        for i in range(1, 4):
            takeaway = article.get(f"key_takeaway_{i:02d}") or article.get(f"Key_Takeaway_{i:02d}", "")
            text_parts.append(takeaway)
        
        full_text = " ".join(text_parts)
        return self._extract_ngrams(full_text, n=3, top_k=50)
    
    def _extract_ngrams(self, text: str, n: int = 3, top_k: int = 50) -> List[str]:
        """Extract top n-grams from text."""
        # Clean text
        text = self._normalize_text(text)
        words = text.split()
        
        # Filter stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'can', 'this', 'that', 'these', 'those', 'it', 'its', 'as',
            'if', 'when', 'where', 'how', 'what', 'which', 'who', 'not', 'no',
            'yes', 'all', 'any', 'both', 'each', 'more', 'most', 'other', 'some',
            'such', 'than', 'too', 'very', 'just', 'also', 'now', 'then', 'so',
            'your', 'you', 'they', 'their', 'our', 'we', 'i', 'my', 'me', 'us',
        }
        
        words = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Generate n-grams
        ngrams = []
        for i in range(len(words) - n + 1):
            ngram = " ".join(words[i:i+n])
            ngrams.append(ngram)
        
        # Count and return top-k
        counter = Counter(ngrams)
        return [phrase for phrase, _ in counter.most_common(top_k)]
    
    def _extract_faq_questions(self, article: dict) -> List[str]:
        """Extract FAQ questions."""
        questions = []
        
        # From FAQ
        faq = article.get("FAQ") or article.get("faq", [])
        if isinstance(faq, list):
            for item in faq:
                if isinstance(item, dict):
                    questions.append(item.get("question", "").lower())
        
        # From PAA
        paa = article.get("PAA") or article.get("paa", [])
        if isinstance(paa, list):
            for item in paa:
                if isinstance(item, dict):
                    questions.append(item.get("question", "").lower())
        
        return [q for q in questions if q]
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        if not text:
            return ""
        # Lowercase
        text = text.lower()
        # Remove HTML
        text = re.sub(r'<[^>]+>', ' ', text)
        # Remove special chars
        text = re.sub(r'[^\w\s]', ' ', text)
        # Normalize whitespace
        text = ' '.join(text.split())
        return text
    
    def _generate_slug(self, title: str) -> str:
        """Generate slug from title."""
        slug = title.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        return slug[:50]
    
    # ========== COMPARISON ==========
    
    def check_keyword(self, keyword: str) -> Tuple[bool, List[str]]:
        """
        Check if keyword is already targeted by existing content.
        
        Returns:
            (is_duplicate, list of slugs targeting same/similar keyword)
        """
        keyword = keyword.lower().strip()
        matches = []
        
        for slug, fp in self.fingerprints.items():
            # Exact match
            if fp.primary_keyword == keyword:
                matches.append(slug)
                continue
            
            # High overlap (80%+ words match)
            kw_words = set(keyword.split())
            fp_words = set(fp.primary_keyword.split())
            if kw_words and fp_words:
                overlap = len(kw_words & fp_words) / max(len(kw_words), len(fp_words))
                if overlap >= 0.8:
                    matches.append(slug)
        
        return bool(matches), matches
    
    def check_article(self, article: dict, slug: str = None) -> SimilarityReport:
        """
        Check article against all stored fingerprints.
        
        Returns:
            SimilarityReport with detailed analysis
        """
        new_fp = self.extract_fingerprint(article, slug)
        
        if not self.fingerprints:
            return SimilarityReport(is_duplicate=False, overall_score=0.0)
        
        # Compare against all existing
        best_match = None
        best_score = 0.0
        best_report = None
        
        for existing_slug, existing_fp in self.fingerprints.items():
            if existing_slug == new_fp.slug:
                continue  # Skip self
            
            report = self._compare_fingerprints(new_fp, existing_fp)
            if report.overall_score > best_score:
                best_score = report.overall_score
                best_match = existing_slug
                best_report = report
        
        if best_report is None:
            return SimilarityReport(is_duplicate=False, overall_score=0.0)
        
        best_report.similar_to = best_match
        best_report.is_duplicate = best_score >= self.DUPLICATE_THRESHOLD
        
        return best_report
    
    def _compare_fingerprints(self, new: ArticleFingerprint, existing: ArticleFingerprint) -> SimilarityReport:
        """Compare two fingerprints and return similarity report."""
        issues = []
        
        # 1. Keyword match (critical)
        keyword_match = new.primary_keyword == existing.primary_keyword
        if keyword_match:
            issues.append(f"CRITICAL: Same target keyword '{new.primary_keyword}'")
        
        # 2. Title similarity
        title_sim = self._text_similarity(new.meta_title, existing.meta_title)
        if title_sim > 0.7:
            issues.append(f"High title similarity ({title_sim:.0%})")
        
        # 3. Heading overlap
        heading_overlap = self._list_overlap(new.headings, existing.headings)
        if heading_overlap > 0.5:
            issues.append(f"Overlapping headings ({heading_overlap:.0%})")
        
        # 4. Content overlap (key phrases)
        content_overlap = self._list_overlap(new.key_phrases, existing.key_phrases)
        if content_overlap > 0.3:
            issues.append(f"Content phrase overlap ({content_overlap:.0%})")
        
        # 5. FAQ overlap
        faq_overlap = self._list_overlap(new.faq_questions, existing.faq_questions)
        if faq_overlap > 0.5:
            issues.append(f"FAQ question overlap ({faq_overlap:.0%})")
        
        # 6. Intro similarity
        intro_sim = self._text_similarity(new.intro_hash, existing.intro_hash)
        if intro_sim > 0.6:
            issues.append(f"Similar intro ({intro_sim:.0%})")
        
        # Calculate overall score (weighted)
        overall = (
            (30 if keyword_match else 0) +  # Keyword match is heavily weighted
            (title_sim * 20) +
            (heading_overlap * 20) +
            (content_overlap * 20) +
            (faq_overlap * 5) +
            (intro_sim * 5)
        )
        
        return SimilarityReport(
            is_duplicate=False,  # Set by caller
            overall_score=min(overall, 100),
            keyword_match=keyword_match,
            title_similarity=title_sim * 100,
            heading_overlap=heading_overlap * 100,
            content_overlap=content_overlap * 100,
            faq_overlap=faq_overlap * 100,
            issues=issues,
        )
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (0-1)."""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _list_overlap(self, list1: List[str], list2: List[str]) -> float:
        """Calculate overlap between two lists (0-1)."""
        if not list1 or not list2:
            return 0.0
        
        set1 = set(list1)
        set2 = set(list2)
        
        intersection = len(set1 & set2)
        smaller = min(len(set1), len(set2))
        
        return intersection / smaller if smaller > 0 else 0.0
    
    # ========== STORAGE ==========
    
    def store_article(self, article: dict, slug: str = None):
        """
        Store article fingerprint for future comparisons.
        
        Args:
            article: Article dictionary
            slug: Optional slug (will generate if not provided)
        """
        fp = self.extract_fingerprint(article, slug)
        self.fingerprints[fp.slug] = fp
        self._save()
        logger.info(f"Stored fingerprint for '{fp.slug}'")
    
    def remove_article(self, slug: str):
        """Remove article from storage."""
        if slug in self.fingerprints:
            del self.fingerprints[slug]
            self._save()
            logger.info(f"Removed fingerprint for '{slug}'")
    
    def list_articles(self) -> List[str]:
        """List all stored article slugs."""
        return list(self.fingerprints.keys())
    
    def clear(self):
        """Clear all stored fingerprints."""
        self.fingerprints = {}
        self._save()


# Convenience functions
def check_for_duplicates(
    article: dict,
    storage_path: str = "content_fingerprints.json"
) -> SimilarityReport:
    """
    Quick check if article is duplicate of existing content.
    
    Args:
        article: Article dictionary to check
        storage_path: Path to fingerprints storage
        
    Returns:
        SimilarityReport with analysis
    """
    checker = ContentSimilarityChecker(storage_path)
    return checker.check_article(article)


def store_article_fingerprint(
    article: dict,
    slug: str = None,
    storage_path: str = "content_fingerprints.json"
):
    """
    Store article fingerprint for future duplicate detection.
    
    Args:
        article: Article dictionary
        slug: Optional slug
        storage_path: Path to fingerprints storage
    """
    checker = ContentSimilarityChecker(storage_path)
    checker.store_article(article, slug)

