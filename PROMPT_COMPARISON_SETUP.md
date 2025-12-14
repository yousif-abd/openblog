# Stage 2 Prompt Comparison Setup

**Date:** December 13, 2024

## Summary

Created a dual-prompt system for Stage 2 to compare:
- **Detailed prompt** (current, comprehensive) - ~3,500 chars
- **Light prompt** (minimal, focused) - ~500 chars

## Implementation

### Code Changes

**File:** `pipeline/blog_generation/stage_02_gemini_call.py`

1. Added prompt style selection via environment variable:
   ```python
   prompt_style = os.getenv("STAGE2_PROMPT_STYLE", "detailed").lower()
   ```

2. Created two methods:
   - `_get_detailed_system_instruction()` - Full comprehensive prompt
   - `_get_light_system_instruction()` - Minimal focused prompt

### Light Prompt Content

The light prompt focuses on essentials:
- HTML format rules (paragraphs, citations, lists)
- Citation requirements
- List requirements
- Tone guidelines
- Source URL requirements
- No em/en dashes

**Length:** ~500 characters vs ~3,500 for detailed

## Testing

**Test Script:** `test_prompt_comparison.py`

This script:
1. Runs pipeline with detailed prompt (default)
2. Runs pipeline with light prompt (`STAGE2_PROMPT_STYLE=light`)
3. Compares outputs side-by-side
4. Generates comparison report

## Usage

### Run with detailed prompt (default):
```bash
python3 test_prompt_comparison.py
```

### Run with light prompt:
```bash
STAGE2_PROMPT_STYLE=light python3 test_prompt_comparison.py
```

### Run comparison test:
```bash
python3 test_prompt_comparison.py
```

## Expected Comparison Metrics

The test will compare:
- Citations as `<a>` links (count)
- `<p>` tags usage (count)
- Lists present (count)
- `<br><br>` tags (fewer is better)
- Content quality (manual inspection)

## Next Steps

1. Run the comparison test
2. Inspect pure outputs from both versions
3. Compare quality metrics
4. Decide which prompt style performs better

