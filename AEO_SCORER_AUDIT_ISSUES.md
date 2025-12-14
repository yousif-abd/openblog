# AEO Scorer Self-Audit - Critical Issues Found

## 🔴 CRITICAL ISSUES

### 1. Double-Counting: Question Patterns
**Problem:**
- Conversational phrases list includes: `"what is", "why does", "when should", "where can", "how can", "what are"`
- Question patterns list includes: `r"\bwhat is\b", r"\bhow do\b", r"\bwhy does\b", r"\bwhen should\b", r"\bwhere can\b", r"\bhow can\b", r"\bwhat are\b"`
- **These are the SAME patterns!** They're counted twice:
  - Once in conversational phrases (6 points)
  - Once in question patterns (4 points)
- **Impact:** Articles get inflated scores for the same thing

**Fix:** Remove question patterns from conversational phrases list

### 2. Inconsistent Citation Checking
**Problem:**
- Direct Answer: Checks `output.Direct_Answer` (original field, before HTML renderer strips `[N]`)
- Citation Clarity: Checks `all_content` (rendered HTML, after HTML renderer strips `[N]`)
- **Impact:** Direct Answer might find academic citations that Citation Clarity won't find (inconsistent scoring)

**Fix:** Both should check the same source (original ArticleOutput fields, not rendered HTML)

### 3. Academic Citations Comment is Misleading
**Problem:**
- Comment says "Academic citations [N] are stripped in HTML renderer, so we only count natural citations here"
- But `academic_citations = re.findall(r'\[\d+\]', all_content)` still runs!
- If citations are stripped, this will always be 0, making the check pointless
- **Impact:** Academic citations are counted but will always be 0 (wasted computation)

**Fix:** Either don't strip academic citations, or don't check for them in Citation Clarity

## ⚠️ MEDIUM ISSUES

### 4. Question Patterns in Headers vs Content
**Problem:**
- Q&A Format checks question patterns in section titles (headers)
- Natural Language checks question patterns in content
- **This is OK** - they're different things (headers vs body)
- But the patterns are the same, so if a section title is "What is X?" and content says "What is Y?", both count
- **Impact:** Might be intentional (headers + content both should have questions), but could be double-counting

**Fix:** Keep as-is (headers and content are different), but document this

### 5. Thresholds Might Be Too Strict
**Problem:**
- 8+ citations for full points (5 points)
- FAQ 5-6 items for full points (10 points)
- **Impact:** Shorter articles or articles that don't need many FAQs might be penalized

**Fix:** Consider making thresholds relative to article length

### 6. Missing Factors
**Problem:**
- No keyword density check
- No internal links check
- No image alt text check
- **Impact:** Missing important AEO factors

**Fix:** Consider adding these (but might make scoring too complex)

## ✅ FIXED ISSUES

### 7. Direct Statements Check Too Lenient ✅ FIXED
**Problem:**
- Even with word boundaries, `\bis\b` and `\bare\b` are very common
- Almost every article will have many "is" and "are" statements
- **Impact:** Might still score 5 points too easily

**Fix Applied:** ✅ Removed "is", "are", "does" from direct patterns. Focused on action verbs. Adjusted thresholds.

### 8. Section Titles Double-Counting ✅ VERIFIED NOT AN ISSUE
**Problem:**
- Section titles are counted as H2 in Structured Data
- Section titles are checked for questions in Q&A Format
- If section titles are rendered as `<h2>` tags, they might be counted twice
- **Impact:** Might inflate Structured Data score

**Analysis:** ✅ Section titles are stored in separate fields, not in content. They're counted as H2 equivalents separately from explicit `<h2>` tags in content. No double-counting occurs.


