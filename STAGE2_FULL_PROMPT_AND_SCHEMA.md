# Stage 2 Full Prompt & JSON Output Schema

**Date:** December 14, 2025  
**Purpose:** Complete documentation of Stage 2 prompt (system instruction + main prompt) and JSON output schema

---

## 📋 Table of Contents

1. [System Instruction](#system-instruction)
2. [Main Prompt (from Stage 1)](#main-prompt)
3. [JSON Output Schema](#json-output-schema)
4. [Examples Included](#examples-included)
5. [Missing: JSON Output Example](#missing-json-output-example)

---

## 🔧 System Instruction

**Location:** `pipeline/blog_generation/stage_02_gemini_call.py` → `_get_system_instruction()`

**Length:** ~4,500 characters  
**Purpose:** High-priority rules for HTML structure, citations, tone, E-E-A-T, formatting

### Key Sections:

1. **HTML STRUCTURE RULES** - Paragraphs, lists, citations formatting
2. **FORMAT RULES** - HTML only, no markdown, strong tags usage
3. **CITATION RULES** - Every paragraph needs citation, 12-15 total, authoritative sources
4. **CONVERSATIONAL TONE** - Direct address with "you" and "your"
5. **WRITING STYLE** - Active voice (70-80%), paragraph content (70%+ with data)
6. **E-E-A-T REQUIREMENTS** - Expertise, experience, authority, trust
7. **BRAND PROTECTION** - NEVER mention competitors
8. **SOURCES FIELD** - Full URLs required, specific paths
9. **PUNCTUATION RULES** - No em/en dashes
10. **LISTS** - 3-5 lists required, mix of <ul> and <ol>
11. **SECTION VARIETY** - SHORT/MEDIUM/LONG sections, 5 structure patterns
12. **SECTION TRANSITIONS** - Bridging sentences (flexible)

### Examples Included in System Instruction:

✅ **HTML Formatting Examples:**
- WRONG vs CORRECT for paragraphs, lists, citations
- Full HTML structure example with citations
- Numbered list example
- Bullet list example

✅ **Citation Pattern Examples:**
- 5 citation patterns as <a> tags
- Sources field examples (WRONG vs CORRECT URLs)

✅ **Transition Examples:**
- 4 varied bridging sentence examples

✅ **Strong Tags Example:**
- Example with <strong> tag usage

---

## 📝 Main Prompt (from Stage 1)

**Location:** `pipeline/prompts/simple_article_prompt.py` → `build_article_prompt()`

**Structure:**
```
Write a comprehensive, high-quality blog article about "{primary_keyword}".

TOPIC FOCUS:
[Focus on primary keyword]

COMPANY CONTEXT:
[Company name, URL, industry, description, products, tone, etc.]

[Optional sections: pain points, value propositions, use cases, content themes, competitors]

[System instructions, batch instructions, knowledge base, content instructions]

TARGET MARKET:
[Country-specific context if provided]

ADDITIONAL CONTENT INSTRUCTIONS:
[Article-specific instructions if provided]

ARTICLE REQUIREMENTS:
- Target language: {language}
- Write in {tone} tone
- Target word count: {word_count_range}
- [Other requirements]

CRITICAL CITATION REQUIREMENTS:
- MANDATORY: Include citations in 70%+ of paragraphs
- [Citation rules]

SECTION HEADER REQUIREMENTS:
- MANDATORY: Include 2+ question-format section headers
- Examples: "What is...", "How does...", "Why should..."

CONVERSATIONAL TONE REQUIREMENTS:
- Use conversational language throughout
- [Tone rules]

IMPORTANT GUIDELINES:
- [General guidelines]

Please write the complete article now.
```

### Examples Included in Main Prompt:

✅ **Section Header Examples:**
- "What is...", "How does...", "Why should...", "When can..."

❌ **No JSON Output Example** - The main prompt doesn't show what the JSON structure should look like

---

## 📐 JSON Output Schema

**Location:** `pipeline/models/output_schema.py` → `ArticleOutput` class

**Schema Definition:** Pydantic model with 30+ fields

### Required Fields:
- `Headline` (str)
- `Subtitle` (Optional[str], default="")
- `Teaser` (str)
- `Direct_Answer` (str)
- `Intro` (str)
- `Meta_Title` (str, ≤60 chars)
- `Meta_Description` (str, ≤160 chars)
- `section_01_title` (str)
- `section_01_content` (str)

### Optional Fields:
- `Lead_Survey_Title` (Optional[str])
- `Lead_Survey_Button` (Optional[str])
- `section_02_title` through `section_09_title` (Optional[str])
- `section_02_content` through `section_09_content` (Optional[str])
- `key_takeaway_01` through `key_takeaway_03` (Optional[str])
- `paa_01_question` through `paa_04_question` (Optional[str])
- `paa_01_answer` through `paa_04_answer` (Optional[str])
- `faq_01_question` through `faq_06_question` (Optional[str])
- `faq_01_answer` through `faq_06_answer` (Optional[str])
- `image_url` (Optional[str])
- `image_alt_text` (Optional[str])
- `Sources` (Optional[str])
- `Search_Queries` (Optional[str])
- `tables` (Optional[List[ComparisonTable]])

### Schema Example (in `json_schema_extra`):

```json
{
  "Headline": "Complete Guide to Python Blog Writing in 2024",
  "Subtitle": "Master the art of writing engaging technical content",
  "Teaser": "Writing about Python can be challenging. This guide shows exactly how to craft engaging, SEO-optimized blog posts that rank.",
  "Direct_Answer": "Blog writing about Python requires balancing technical depth with accessibility, consistent research, and SEO optimization for discovery.",
  "Intro": "Python is one of the most discussed programming languages online...",
  "Meta_Title": "Python Blog Writing Guide 2024 | SCAILE",
  "Meta_Description": "Learn professional Python blog writing techniques for maximum reach and engagement.",
  "section_01_title": "Why Python Blog Writing Matters",
  "section_01_content": "<p>Python content serves multiple audiences...</p>",
  "Sources": "[1]: https://example.com – Research on Python trends"
}
```

**Note:** This example is in the Pydantic model's `json_schema_extra`, but it's not explicitly shown to Gemini in the prompt.

---

## ✅ Examples Included

### System Instruction Examples:
- ✅ HTML formatting (WRONG vs CORRECT)
- ✅ Citation patterns (5 examples)
- ✅ Sources field (WRONG vs CORRECT URLs)
- ✅ List formatting (numbered and bullet examples)
- ✅ Strong tags usage
- ✅ Bridging sentences (4 examples)
- ✅ Section structure patterns (5 patterns with examples)

### Main Prompt Examples:
- ✅ Section header formats ("What is...", "How does...")

### JSON Schema:
- ✅ Example in `json_schema_extra` (but not shown to Gemini)

---

## ❌ Missing: JSON Output Example

**Issue:** The prompt doesn't explicitly show Gemini what the JSON output structure should look like.

**Current Approach:**
- Gemini receives `response_schema` (built from `ArticleOutput` Pydantic model)
- The schema defines the structure automatically
- But no concrete JSON example is shown in the prompt

**Question:** Should we add a JSON output example to the system instruction or main prompt?

**Recommendation:** ✅ **YES** - Add a complete JSON example showing:
- All required fields
- Example section content with proper HTML
- Example Sources format
- Example FAQ/PAA format

This would help Gemini understand:
1. The exact JSON structure expected
2. How HTML should be formatted within JSON fields
3. How Sources should be formatted
4. How sections should be structured

---

## 🎯 Recommendation

**Add to System Instruction:**

```python
=== OUTPUT FORMAT (CRITICAL - JSON STRUCTURE) ===
You MUST output a valid JSON object matching this exact structure:

{{
  "Headline": "Main article headline with primary keyword",
  "Subtitle": "Optional sub-headline for context",
  "Teaser": "2-3 sentence hook highlighting pain point or benefit",
  "Direct_Answer": "40-60 word direct answer to primary question",
  "Intro": "<p>Opening paragraph (80-120 words) framing the problem with citations.</p>",
  "Meta_Title": "≤55 character SEO title with primary keyword",
  "Meta_Description": "≤130 character SEO description with CTA",
  "section_01_title": "Section 1 heading",
  "section_01_content": "<p>Section content with <a href=\"url\" class=\"citation\">citations</a>.</p><ul><li>List item</li></ul><p>More content.</p>",
  "section_02_title": "Section 2 heading",
  "section_02_content": "<p>Content...</p>",
  "key_takeaway_01": "Key insight #1",
  "key_takeaway_02": "Key insight #2",
  "key_takeaway_03": "Key insight #3",
  "paa_01_question": "People Also Ask question #1",
  "paa_01_answer": "Answer to PAA question #1",
  "faq_01_question": "FAQ question #1",
  "faq_01_answer": "Answer to FAQ question #1",
  "Sources": "[1]: Gartner Top Cybersecurity Trends 2025 – https://www.gartner.com/en/articles/top-cybersecurity-trends-for-2025\\n[2]: IBM Cost of a Data Breach 2024 – https://www.ibm.com/reports/data-breach",
  "Search_Queries": "Q1: cybersecurity trends 2025\\nQ2: data breach costs\\nQ3: cloud security best practices"
}}

CRITICAL JSON RULES:
- ALL section content MUST be valid HTML (use <p>, <ul>, <ol>, <a> tags)
- Sources format: "[N]: Title – URL" (one per line, separated by \\n)
- Search_Queries format: "Q1: keyword\\nQ2: keyword" (one per line)
- Empty optional fields should be "" (empty string), not null
- JSON must be valid and parseable
```

---

## 📊 Summary

| Component | Examples Included? | Status |
|-----------|-------------------|--------|
| **System Instruction** | ✅ Yes (HTML, citations, lists, transitions) | Complete |
| **Main Prompt** | ✅ Yes (section headers) | Complete |
| **JSON Schema** | ✅ Yes (in Pydantic model) | Complete |
| **JSON Output Example in Prompt** | ❌ No | **MISSING** |

**Action Required:** Add JSON output example to system instruction to help Gemini understand the expected structure.

