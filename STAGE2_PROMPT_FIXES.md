# Stage 2 Prompt Fixes - Deep & Smart Updates

**Date:** December 13, 2024  
**File:** `pipeline/blog_generation/stage_02_gemini_call.py`

---

## 🎯 Issues Fixed

Based on pure stage output inspection, Stage 2 was generating:
1. ❌ Citations as `<strong>` tags (should be `<a>` links)
2. ❌ Paragraphs as `<br><br>` (should be `<p>` tags)
3. ❌ Lists not properly separated from text

---

## ✅ Changes Made

### 1. HTML Structure Rules (NEW SECTION)

**Added comprehensive HTML formatting rules:**

```python
=== HTML STRUCTURE RULES (CRITICAL - FOLLOW EXACTLY) ===
- EVERY paragraph MUST be wrapped in <p> tags - NEVER use <br><br>
- Lists MUST be properly separated from preceding text with <p> tags
- Citations MUST be HTML anchor links (<a> tags), NOT <strong> tags
```

**Specific formatting examples:**
- Paragraphs: `<p>First paragraph.</p><p>Second paragraph.</p>`
- Lists: `<p>Here are the key points:</p><ul><li>Point 1</li></ul>`
- Citations: `<a href="url" class="citation">IBM research</a>`

---

### 2. Citation Formatting (ENHANCED)

**Before:**
- Citations were `<strong>` tags
- No URL linking instructions

**After:**
- Citations MUST be `<a href="url" class="citation">...</a>` tags
- URL sourcing priority:
  1. Specific URL from Google Search grounding research (preferred)
  2. Domain URL as fallback (e.g., https://www.ibm.com)
  3. Always include valid href attribute

**Example:**
```html
WRONG: <strong>IBM Cost of a Data Breach Report 2024</strong>
CORRECT: <a href="https://www.ibm.com/reports/data-breach" class="citation">IBM Cost of a Data Breach Report 2024</a>
```

---

### 3. Paragraph Formatting (ENHANCED)

**Before:**
- Instructions said "Separate paragraphs with blank lines (we add <p> tags later)"
- This caused Gemini to use `<br><br>`

**After:**
- Explicit instruction: "EVERY paragraph MUST be wrapped in <p> tags"
- Forbidden: `<br><br>` for paragraph breaks
- Required: `</p><p>` for paragraph breaks

**Example:**
```html
WRONG: "First paragraph.<br><br>Second paragraph."
CORRECT: "<p>First paragraph.</p><p>Second paragraph.</p>"
```

---

### 4. List Formatting (ENHANCED)

**Before:**
- Lists could be embedded in text flow
- No clear separation rules

**After:**
- ALWAYS close preceding paragraph with `</p>` before starting a list
- ALWAYS start new paragraph with `<p>` after closing a list
- Lists MUST be separated from surrounding text with proper `<p>` tags

**Example:**
```html
WRONG: "Here are the key points:\n<ul><li>Point 1</li></ul>"
CORRECT: "<p>Here are the key points:</p><ul><li>Point 1</li></ul><p>Following these points...</p>"
```

---

### 5. HTML Validation Checklist (NEW)

**Added comprehensive checklist:**

```python
=== HTML VALIDATION CHECKLIST (VERIFY BEFORE OUTPUT) ===
1. ✅ Every paragraph is wrapped in <p>...</p> tags
2. ✅ No <br><br> used for paragraph breaks
3. ✅ All citations are <a href="url" class="citation">...</a> tags (NOT <strong> tags)
4. ✅ Lists are separated from text with <p> tags before and after
5. ✅ No em dashes (—) or en dashes (–) anywhere
6. ✅ All HTML tags are properly closed
7. ✅ Citation links are inline within paragraphs (not standalone)
```

---

### 6. Complete Example (NEW)

**Added comprehensive example showing correct formatting:**

```html
<p>Cloud security is critical for modern organizations. <a href="https://www.ibm.com/reports/data-breach" class="citation">According to IBM research</a>, data breaches cost an average of $5.17 million per incident.</p>
<p>Here are the key practices you need to implement:</p>
<ul>
<li>Enable multi-factor authentication for all accounts</li>
<li>Implement least privilege access controls</li>
<li>Encrypt data at rest and in transit</li>
</ul>
<p>These practices form the foundation of a secure cloud environment.</p>
```

---

## 📊 Expected Impact

### Before (Current Output):
- Citations: `<strong>IBM Cost of a Data Breach Report 2024</strong>`
- Paragraphs: `Text.<br><br>More text.`
- Lists: `Text:\n<ul>...</ul>`

### After (Expected Output):
- Citations: `<a href="https://..." class="citation">IBM Cost of a Data Breach Report 2024</a>`
- Paragraphs: `<p>Text.</p><p>More text.</p>`
- Lists: `<p>Text:</p><ul>...</ul><p>Following text.</p>`

---

## 🔍 Key Improvements

1. **Explicit Instructions** - Clear, unambiguous rules
2. **Examples** - WRONG vs CORRECT examples for every rule
3. **Validation Checklist** - 7-point verification before output
4. **Complete Example** - Full HTML structure example
5. **Priority System** - URL sourcing priority (specific > domain > fallback)

---

## 🎯 Testing Required

After these changes, test:
1. ✅ Citations are `<a>` links (not `<strong>` tags)
2. ✅ Paragraphs use `<p>` tags (not `<br><br>`)
3. ✅ Lists are properly separated with `<p>` tags
4. ✅ All HTML is valid and properly structured

---

## 📝 Notes

- The renderer is now a pure viewer - it displays what Stage 2 generates
- Stage 2 must generate correct HTML structure
- These prompts are "smart, deep" - comprehensive and specific
- All rules include examples and validation criteria

