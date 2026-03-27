"""Beck-Online Resource Extraction Module.

Standalone module to pre-extract legal resources from Beck-Online
and store them in the SQLite database for later use during article generation.

Usage:
    python -m beck_extract.beck_extract --titles "Kündigungsschutz im Arbeitsrecht"
"""

from .beck_extractor import extract_for_keyword, extract_for_keywords
from .beck_models import BeckExtractionInput, BeckExtractionOutput

__all__ = [
    "extract_for_keyword",
    "extract_for_keywords",
    "BeckExtractionInput",
    "BeckExtractionOutput",
]
