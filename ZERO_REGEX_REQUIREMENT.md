# ZERO REGEX REQUIREMENT

**User Requirement:** NO regex throughout the entire pipeline.

## Files That Need Regex Removal:

1. ✅ `pipeline/processors/html_renderer_simple.py` - DONE (replaced with string methods)
2. ❌ `pipeline/blog_generation/stage_02b_quality_refinement.py` - HAS 38+ regex operations
3. ❌ `pipeline/blog_generation/stage_04_citations.py` - HAS 6 regex operations

## Strategy:

- **Stage 2b:** Remove ALL regex cleanup. Use ONLY AI (Gemini) to fix issues.
- **Stage 4:** Replace regex citation parsing with simple string methods (find, split, etc.)
- **HTML Renderer:** Already done - uses simple string replace and manual parsing

## What Stage 2b Should Do:

- ONLY use Gemini AI to review and fix content
- NO regex-based cleanup
- NO pattern matching
- AI should handle all quality fixes

## What Stage 4 Should Do:

- Parse citations using simple string methods:
  - Find `[N]:` using `.find()`
  - Extract URL using `.find('http')`
  - Extract title using string slicing
  - NO regex matching

