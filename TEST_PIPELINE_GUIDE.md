# Interactive Pipeline Test Guide

## Overview

The `test_pipeline_interactive.py` script runs the full pipeline stage-by-stage, pausing after each stage for inspection and verification. This allows you to:

- ✅ Verify each stage's output before proceeding
- ✅ Inspect context data at any point
- ✅ Catch issues early
- ✅ Understand the data flow through the pipeline

## Prerequisites

1. **Environment Variables:**
   ```bash
   export GEMINI_API_KEY='your-api-key-here'
   ```

2. **Python Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

```bash
python3 test_pipeline_interactive.py
```

Or make it executable and run directly:

```bash
chmod +x test_pipeline_interactive.py
./test_pipeline_interactive.py
```

## How It Works

The script runs all 10 stages sequentially:

1. **Stage 0:** Data Fetch
2. **Stage 1:** Prompt Build
3. **Stage 2:** Content Generation (Gemini)
4. **Stage 3:** Quality Refinement ← **Always runs now!**
5. **Stage 4:** Citations Validation
6. **Stage 5:** Internal Links
7. **Stage 6:** Image Generation (normally parallel with Stage 7)
8. **Stage 7:** Similarity Check (normally parallel with Stage 6)
9. **Stage 8:** Merge & Link ← **Simplified!**
10. **Stage 9:** Storage & Export

After each stage, you'll see:
- ✅ Stage completion status
- 📊 Context summary
- 📝 Data previews (structured_data, validated_article, etc.)
- ⏱️ Execution times

## Interactive Commands

After each stage completes, you can choose:

- **[Enter]** - Continue to next stage
- **[i]** - Inspect full context data (see all fields)
- **[s]** - Skip remaining stages (stop after current)
- **[q]** - Quit test immediately
- **[r]** - Retry current stage

### Inspect Mode

When you press `[i]`, you can view:
- `structured_data` - Full article structure from Stage 2-3
- `validated_article` - Flattened article from Stage 8
- `parallel_results` - Results from Stages 6-7
- `storage_result` - Export results from Stage 9

## Example Session

```
================================================================================
  Interactive Pipeline Test
================================================================================

✅ GEMINI_API_KEY: AIzaSyBxxxxxxxxxxxxx...

Job ID: interactive-test-20241216-123456
Primary Keyword: AI-powered customer service automation
Language: en

Press Enter to start the pipeline...

================================================================================
  Stage 0: Data Fetch
================================================================================

Executing Data Fetch...

✅ Stage 0 completed in 0.15s

────────────────────────────────────────────────────────────────────────────────
  Context Summary After Stage 0
────────────────────────────────────────────────────────────────────────────────

  job_id                        : interactive-test-20241216-123456
  has_structured_data           : False
  has_validated_article         : False
  has_parallel_results          : False
  ...

================================================================================
  Stage 0: Data Fetch - COMPLETE
================================================================================

Options:
  [Enter] - Continue to next stage
  [i]     - Inspect full context data
  [s]     - Skip remaining stages
  [q]     - Quit test
  [r]     - Retry this stage

Your choice: [Enter]
```

## What to Verify at Each Stage

### Stage 0: Data Fetch
- ✅ Job config loaded
- ✅ Company data loaded
- ✅ Sitemap data loaded (if available)

### Stage 1: Prompt Build
- ✅ Prompt created successfully
- ✅ All variables substituted

### Stage 2: Content Generation
- ✅ Structured data created
- ✅ Headline, Intro, sections present
- ✅ Sources field populated
- ✅ ToC labels generated

### Stage 3: Quality Refinement ⭐
- ✅ Structured data refined
- ✅ Quality improvements applied
- ✅ FAQ/PAA validated (if present)

### Stage 4: Citations Validation
- ✅ Citations parsed correctly
- ✅ URLs validated
- ✅ Body citations updated

### Stage 5: Internal Links
- ✅ Internal links generated
- ✅ Links embedded in content

### Stage 6: Image Generation
- ✅ Image URLs generated
- ✅ Alt text created

### Stage 7: Similarity Check
- ✅ Similarity check completed
- ✅ No duplicate content (or flagged if found)

### Stage 8: Merge & Link ⭐
- ✅ Parallel results merged
- ✅ Citations linked (`[1]` → `<a href>`)
- ✅ Validated article created (flat structure)

### Stage 9: Storage & Export
- ✅ HTML generated
- ✅ Files exported (HTML, PDF, Markdown, CSV, XLSX, JSON)
- ✅ Storage result available

## Troubleshooting

### Stage Fails

If a stage fails:
1. Check the error message
2. Choose `[i]` to inspect context
3. Choose `[r]` to retry, or `[q]` to quit

### Missing Data

If data is missing:
- Check previous stages completed successfully
- Inspect context to see what's available
- Verify job_config and company_data are set correctly

### API Errors

If you see API errors:
- Verify `GEMINI_API_KEY` is set correctly
- Check API quota/limits
- Verify network connectivity

## Customization

You can modify the test script to:

1. **Change test data:**
   ```python
   context.job_config = {
       "primary_keyword": "your-topic",
       "language": "en",
       # ... your config
   }
   ```

2. **Add more inspection points:**
   ```python
   # Add custom preview functions
   def print_custom_preview(context):
       # Your custom inspection code
       pass
   ```

3. **Skip certain stages:**
   ```python
   # Modify stages list
   stages = [
       (0, "Data Fetch"),
       (2, "Content Generation"),  # Skip Stage 1
       # ...
   ]
   ```

## Tips

1. **Start with Stage 0-2** to verify basic flow
2. **Pay attention to Stage 3** - it's now always running!
3. **Check Stage 8** - verify merge & link works correctly
4. **Inspect data** frequently to understand the pipeline flow
5. **Use `[s]` to skip** if you only want to test specific stages

## Expected Outputs

### After Stage 2 (Content Generation)
- `structured_data` should have:
  - Headline, Subtitle, Meta fields
  - Intro, Direct_Answer, Key_Takeaways
  - section_01_content through section_09_content
  - Sources field with citations

### After Stage 3 (Quality Refinement)
- `structured_data` should be refined:
  - Better quality content
  - Proper structure
  - Validated FAQ/PAA (if present)

### After Stage 8 (Merge & Link)
- `validated_article` should be:
  - Flat structure (no nested dicts)
  - Citations linked (`<a href>` tags)
  - Images merged from Stage 6
  - ToC merged from Stage 2

### After Stage 9 (Storage)
- `storage_result` should have:
  - `success: true`
  - `exported_files` with paths to:
    - HTML
    - PDF
    - Markdown
    - CSV
    - XLSX
    - JSON

---

**Happy Testing!** 🚀

For questions or issues, check:
- `PIPELINE_SIMPLIFICATION_COMPLETE.md` - Recent changes
- `CURRENT_PIPELINE.md` - Pipeline structure
- `STAGE_8_BEFORE_AFTER.md` - Stage 8 simplification details

