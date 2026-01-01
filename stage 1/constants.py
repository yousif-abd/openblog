"""
Stage 1: Constants

Re-exports from shared/ for standalone compatibility.
When running as part of the pipeline, shared/ is the source of truth.
"""

import sys
from pathlib import Path

# Add parent to path for shared imports
_parent = Path(__file__).parent.parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

try:
    from shared.constants import GEMINI_MODEL, MAX_SITEMAP_URLS
except ImportError:
    # Fallback for standalone execution without shared/
    GEMINI_MODEL = "gemini-3-flash-preview"
    MAX_SITEMAP_URLS = 10000
