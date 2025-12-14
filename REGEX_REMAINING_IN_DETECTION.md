# Remaining Regex in Detection Methods

**Date:** December 14, 2025  
**Status:** Detection methods still use regex (not fix methods)

---

## 📊 Summary

**Stage 2b Detection Methods** still contain regex for:
- Citation pattern detection (`re.findall`, `re.search`)
- HTML tag stripping for word counting (`re.sub`)
- Academic citation detection (`re.findall`)
- Paragraph extraction (`re.search`)

**These are DETECTION methods, not FIX methods:**
- `_detect_quality_issues()` - Detects issues, doesn't fix
- `_check_first_paragraph()` - Checks length, doesn't fix
- `_check_academic_citations()` - Detects academic citations, doesn't fix

---

## 🤔 Question for User

**Should detection methods also be AI-only?**

Current approach:
- **Detection:** Uses regex to find issues (fast, deterministic)
- **Fixes:** Uses AI (Gemini) to fix issues (smart, contextual)

Alternative approach:
- **Detection:** Also use AI to detect issues
- **Fixes:** Use AI to fix issues

---

## 📋 Regex Usage in Detection Methods

### 1. Citation Pattern Detection
```python
# Line 644: citation_count = sum(len(re.findall(pattern, all_content, re.IGNORECASE)) for pattern in natural_citation_patterns)
# Line 658: has_citation_in_da = any(re.search(pattern, direct_answer_text, re.IGNORECASE) for pattern in natural_citation_patterns)
```
**Purpose:** Count citations in content for AEO scoring

### 2. HTML Tag Stripping
```python
# Line 656: direct_answer_text = re.sub(r'<[^>]+>', '', direct_answer) if direct_answer else ""
# Line 1053: text_only = re.sub(r'<[^>]+>', '', first_paragraph)
```
**Purpose:** Strip HTML tags to count words accurately

### 3. Academic Citation Detection
```python
# Line 1148: matches = re.findall(pattern, content)
```
**Purpose:** Detect `[N]` academic citations in content

### 4. Paragraph Extraction
```python
# Line 1045: first_p_match = re.search(r'<p>(.*?)</p>', first_section, re.DOTALL)
```
**Purpose:** Extract first paragraph for length checking

---

## ✅ Completed: Zero Regex in Fix Methods

- ✅ `_apply_regex_cleanup()` - REMOVED (was using regex for fixes)
- ✅ `_remove_fragment_lists()` - REMOVED (was using regex for fixes)
- ✅ All fix methods now AI-only

---

## 🎯 Recommendation

**Keep regex in detection methods** for now because:
1. Detection is fast and deterministic
2. Detection doesn't modify content (just flags issues)
3. AI is used for actual fixes (where it matters)
4. Detection methods are called frequently (performance matters)

**OR**

**Make detection AI-only** if user wants complete zero-regex:
- Use AI to detect issues (slower but more accurate)
- AI can understand context better than regex patterns

---

## 🔍 Verification

Run this to see all remaining regex:
```bash
grep -n "re\." pipeline/blog_generation/stage_02b_quality_refinement.py
```

All remaining regex is in detection methods, not fix methods.

