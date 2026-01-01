"""
Shared constants for openblog-neo pipeline.
"""

import os

# Gemini model with URL Context + Google Search + JSON output support
# Can be overridden via GEMINI_MODEL environment variable
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")

# Sitemap crawler limit
MAX_SITEMAP_URLS = int(os.getenv("MAX_SITEMAP_URLS", "10000"))
