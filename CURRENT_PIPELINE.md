# Current Pipeline Structure

**Last Updated:** December 16, 2024

## Quick Overview

**10 stages (0-9)** that generate blog articles from job config to HTML export.

```
Data → Prompt → Generate → Refine → Citations → Links → [Image||Similarity] → Merge → Export
```

## Detailed Flow

### Stage 0: Data Fetch
**File:** `stage_00_data_fetch.py`  
**Purpose:** Load configuration and data  
**Inputs:** Job config (from API/file)  
**Outputs:** Company data, sitemap URLs, job config  
**Type:** Sequential

---

### Stage 1: Prompt Build
**File:** `stage_01_prompt_build.py`  
**Purpose:** Create prompt with variables  
**Inputs:** Job config, company data  
**Outputs:** Final prompt for Gemini  
**Type:** Sequential

---

### Stage 2: Content Generation
**File:** `stage_02_gemini_call.py`  
**Purpose:** Generate article content  
**What it does:**
- Calls Gemini API with prompt
- Generates full article content
- Extracts structured data (Headline, Intro, sections, etc.)
- Generates ToC labels
- Calculates metadata (word count, reading time, etc.)

**Inputs:** Prompt from Stage 1  
**Outputs:** `structured_data` (ArticleOutput)  
**Type:** Sequential  
**API Calls:** 1 (main generation)

---

### Stage 3: Quality Refinement ✨
**File:** `stage_03_quality_refinement.py`  
**Purpose:** AI-based quality refinement  
**Status:** **ALWAYS RUNS** (not conditional)

**What it does:**
- Quality refinement via AI
- Natural language generation
- Proper structure & formatting
- Citation placement optimization
- FAQ/PAA validation
- **ALL content quality checks** ← This is the key!

**Inputs:** `structured_data` from Stage 2  
**Outputs:** Refined `structured_data`  
**Type:** Sequential  
**API Calls:** 1-3 (quality checks)

**Important:** All content manipulation happens here via AI. No regex, no post-processing.

---

### Stage 4: Citations Validation
**File:** `stage_04_citations.py`  
**Purpose:** Validate sources and update citations  
**What it does:**
- Parse and validate citation sources (AI-only parsing)
- Check URL validity (HTTP 200)
- Update body content with validated citations
- Generate citations HTML for display

**Inputs:** `structured_data` from Stage 3  
**Outputs:** Updated `structured_data` with validated citations  
**Type:** Sequential  
**API Calls:** 1 (citation parsing)

---

### Stage 5: Internal Links
**File:** `stage_05_internal_links.py`  
**Purpose:** Generate and embed internal links  
**What it does:**
- Find related blog posts
- Generate contextual internal links
- Embed links in body content
- Generate internal links HTML for display

**Inputs:** `structured_data` from Stage 4  
**Outputs:** Updated `structured_data` with internal links  
**Type:** Sequential

---

### Stage 6: Image Generation (Parallel)
**File:** `stage_06_image.py`  
**Purpose:** Generate article images  
**What it does:**
- Generate featured image
- Generate mid-article image (optional)
- Generate bottom image (optional)
- Upload to storage

**Inputs:** `structured_data` from Stage 5  
**Outputs:** Image URLs and alt text  
**Type:** **Parallel** (runs simultaneously with Stage 7)

---

### Stage 7: Similarity Check (Parallel)
**File:** `stage_07_similarity_check.py`  
**Purpose:** Check for content cannibalization  
**What it does:**
- Compare article with existing content
- Detect duplicate sections
- Flag similar content for review

**Inputs:** `structured_data` from Stage 5  
**Outputs:** Similarity report  
**Type:** **Parallel** (runs simultaneously with Stage 6)

---

### Stage 8: Merge & Link ✨
**File:** `stage_08_cleanup.py`  
**Purpose:** Merge parallel results and link citations  
**Status:** **SIMPLIFIED** (from 1,727 → 330 lines)

**What it does:**
1. Merge parallel results (images from Stage 6, similarity from Stage 7)
2. Link citations (convert `[1]` to clickable `<a href>` tags with URL validation)
3. Flatten data structure (for export compatibility)

**What it does NOT do:**
- ❌ No HTML cleaning (Stage 3 outputs clean HTML)
- ❌ No humanization (Stage 3 writes naturally)
- ❌ No AEO enforcement (Stage 3 generates proper structure)
- ❌ No quality validation (Stage 3 ensures quality)
- ❌ No content manipulation (all handled by Stage 3)

**Inputs:** `structured_data` + `parallel_results`  
**Outputs:** `validated_article` (flat dict)  
**Type:** Sequential

**Important:** Only technical operations (merge + link), no content manipulation.

---

### Stage 9: Storage & Export
**File:** `stage_09_storage.py`  
**Purpose:** Generate HTML and export in multiple formats  
**What it does:**
- Generate final HTML from validated article
- Export in multiple formats:
  - **HTML** (rendered article)
  - **Markdown** (converted from HTML)
  - **PDF** (via PDF service)
  - **JSON** (structured data)
  - **CSV** (flat table)
  - **XLSX** (Excel with multiple sheets)
- Store to Supabase
- Final validation and reporting

**Inputs:** `validated_article` from Stage 8  
**Outputs:** Storage result, exported files  
**Type:** Sequential

---

## Execution Order

```
┌─────────────┐
│ Sequential  │
└─────────────┘
    Stage 0: Data Fetch
    Stage 1: Prompt Build
    Stage 2: Content Generation (Gemini + ToC + Metadata)
    Stage 3: Quality Refinement (AI) ← ALWAYS RUNS
    Stage 4: Citations Validation (AI-only parsing)
    Stage 5: Internal Links

┌─────────────┐
│  Parallel   │
└─────────────┘
    Stage 6: Image Generation
         |
         ├──── Runs simultaneously ────┐
         |                             ↓
    Stage 7: Similarity Check

┌─────────────┐
│ Sequential  │
└─────────────┘
    Stage 8: Merge & Link (merge results + link citations)
    Stage 9: Storage & Export (HTML, PDF, Markdown, CSV, XLSX, JSON)
```

## Key Stages

### 🌟 Stage 3: Quality Refinement
**The Content Quality Engine**

- **Always runs** (not conditional)
- **All content manipulation** happens here via AI
- **No regex** for content
- Ensures natural language, proper structure, correct formatting

### 🔧 Stage 8: Merge & Link
**The Technical Merger**

- **Only technical operations** (no content manipulation)
- Merges parallel results (images, similarity check)
- Links citations (`[1]` → `<a href>`)
- Flattens data for export

### 📦 Stage 9: Storage & Export
**The Multi-Format Exporter**

- Generates final HTML
- Exports to 6 formats: HTML, Markdown, PDF, JSON, CSV, XLSX
- Stores to Supabase

## AI-First Principles

### Content Manipulation = AI (Stage 3)
- Quality refinement
- Natural language generation
- Proper structure
- Citation placement
- FAQ/PAA validation

### Technical Operations = Stage 8
- Merge parallel results
- Link citations (HTML generation)
- Flatten data (export compatibility)

### No Regex for Content
- Content manipulation = AI only (Stage 3)
- Technical operations = Stage 8 (URL validation, data merging)

## Performance

| Stage | Type | API Calls | Approx Time |
|-------|------|-----------|-------------|
| 0 | Sequential | 0 | <1s |
| 1 | Sequential | 0 | <1s |
| 2 | Sequential | 1 | 10-30s |
| 3 | Sequential | 1-3 | 5-15s |
| 4 | Sequential | 1 | 2-5s |
| 5 | Sequential | 0 | 1-3s |
| 6 | **Parallel** | 1-3 | 5-10s |
| 7 | **Parallel** | 1 | 5-10s |
| 8 | Sequential | 0 | <1s |
| 9 | Sequential | 0 | 2-5s |

**Total:** ~30-80s per article (stages 6-7 run in parallel)

## Files

| Stage | File | Lines | Status |
|-------|------|-------|--------|
| 0 | `stage_00_data_fetch.py` | ~200 | ✅ |
| 1 | `stage_01_prompt_build.py` | ~300 | ✅ |
| 2 | `stage_02_gemini_call.py` | ~400 | ✅ |
| 3 | `stage_03_quality_refinement.py` | ~500 | ✅ Always runs |
| 4 | `stage_04_citations.py` | ~600 | ✅ AI-only |
| 5 | `stage_05_internal_links.py` | ~400 | ✅ |
| 6 | `stage_06_image.py` | ~300 | ✅ |
| 7 | `stage_07_similarity_check.py` | ~400 | ✅ |
| 8 | `stage_08_cleanup.py` | **330** | ✅ Simplified |
| 9 | `stage_09_storage.py` | ~500 | ✅ |

**Total:** ~3,930 lines (down from ~5,330 with old Stage 8)

## Testing

```bash
cd /Users/federicodeponte/openblog

# Verify stage imports
python3 -c "
from pipeline.core.stage_factory import ProductionStageFactory
factory = ProductionStageFactory()
stages = factory.create_all_stages()
print(f'✅ Successfully created {len(stages)} stages')
"

# Run tests (if available)
python3 -m pytest tests/
```

---

**Status:** ✅ Production Ready  
**Architecture:** AI-First  
**Last Verified:** December 16, 2024

