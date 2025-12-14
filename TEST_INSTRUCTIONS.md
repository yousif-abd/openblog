# Test Generation Instructions

## Running the Test

A test article generation has been started in the background. It will take several minutes to complete (especially Stage 2b).

## Once Generation Completes

### Option 1: Automatic Verification
Run the verification script:
```bash
python3 verify_fixes.py
```

This will automatically find the latest test output and verify all fixes.

### Option 2: Manual Verification
1. Find the latest test output:
   ```bash
   ls -lt output/ | grep test-fixes
   ```

2. Open the HTML file in your browser:
   ```bash
   open output/test-fixes-YYYYMMDD-HHMMSS/index.html
   ```

3. Or verify a specific file:
   ```bash
   python3 verify_fixes.py output/test-fixes-YYYYMMDD-HHMMSS/index.html
   ```

## What the Verification Checks

The verification script checks:

1. ✅ **Meta Description** - Present and populated
2. ✅ **Teaser Paragraph** - Present and populated  
3. ✅ **Section Variety** - Different section lengths (not all uniform)
4. ✅ **Sources Formatting** - Titles with URLs (not bare URLs)
5. ✅ **TOC Formatting** - Line breaks between items
6. ✅ **Paragraph Spacing** - Newlines for readability
7. ✅ **Schema Markup** - JSON-LD schemas present
8. ✅ **Em/En Dashes** - Zero tolerance (none found)
9. ✅ **Paragraph Structure** - No broken patterns
10. ✅ **Internal Links** - Rendered correctly (if available)
11. ✅ **Paragraph Tags** - Balanced opening/closing tags

## Expected Results

- **Section Variety**: Should see sections with 2-3 paragraphs (short), 4-6 paragraphs (medium), and 7-10 paragraphs (long)
- **Sources**: Should have titles like "IBM Cost of a Data Breach Report 2024" not just URLs
- **TOC**: Should have proper line breaks
- **HTML**: Should be readable with proper spacing
- **No Issues**: All checks should pass

## If Issues Found

Check the verification output for specific issues. Most fixes are in:
- `pipeline/processors/html_renderer_simple.py` - HTML rendering
- `pipeline/blog_generation/stage_02_gemini_call.py` - Section variety instructions
- `pipeline/blog_generation/stage_02b_quality_refinement.py` - Paragraph structure fixes

