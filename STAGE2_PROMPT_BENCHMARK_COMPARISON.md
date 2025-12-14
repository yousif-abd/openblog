# Stage 2 Prompt Benchmark Comparison

**Date:** December 14, 2025  
**Comparing:** Our Stage 2 System Instruction vs Benchmark Prompt

---

## 📊 Side-by-Side Comparison

| Aspect | Benchmark Prompt | Our Stage 2 Prompt | Difference |
|--------|------------------|-------------------|------------|
| **Word Count** | ~1,200-1,800 (flexible) | 2,500-4,000 (dynamic) | **Ours: 2x longer** |
| **Paragraph Length** | ≤25 words each | 40-60 words average (mix 20-30 and 60-80) | **Ours: Longer paragraphs** |
| **Active Voice** | ≥90% active voice | Not specified | **Benchmark: More explicit** |
| **Paragraph Requirements** | Must contain number/KPI/example | Not explicitly required | **Benchmark: More specific** |
| **Section Length** | New H2/H3 every 150-200 words | SHORT (200-300), MEDIUM (400-600), LONG (700-900) | **Ours: More variety** |
| **Section Structure** | Not specified | 5 patterns, must use 4 different | **Ours: More structured** |
| **Lists** | 2-4 sections with lists, 4-8 items | 3-5 lists required, mix <ul>/<ol> | **Similar** |
| **Citations Format** | `[1]`, `[2]` academic format | `<a href="url" class="citation">` HTML links | **Different approaches** |
| **Citation Count** | MAX 20 sources, max 3 per section | Target 12-15 citations | **Benchmark: More sources** |
| **Internal Links** | At least one per H2 block | Not specified in Stage 2 | **Benchmark: More explicit** |
| **Strong Tags** | 1-2 insights per section | Not specified | **Benchmark: More explicit** |
| **Narrative Flow** | Bridging sentences between sections | Not specified | **Benchmark: More explicit** |
| **Competitors** | NEVER mention competitors | Not addressed | **Benchmark: Explicit rule** |
| **PAA/FAQ** | NEVER embed in sections | Not addressed | **Benchmark: Explicit rule** |
| **Output Language** | Must match company_language | Uses job_config.language | **Different approach** |
| **Conversational Tone** | Not specified | "you" and "your" in every paragraph | **Ours: More explicit** |
| **E-E-A-T** | Not specified | Explicit requirements | **Ours: More explicit** |
| **Sources URLs** | Canonical URLs only | Full specific URLs required | **Ours: More specific** |
| **Em/En Dashes** | Not addressed | Explicitly forbidden | **Ours: More explicit** |
| **HTML Validation** | Keep HTML tags intact | Detailed HTML validation checklist | **Ours: More comprehensive** |

---

## 🔍 Detailed Analysis

### 1. **Word Count & Length**

**Benchmark:**
- ~1,200-1,800 words (flexible)
- "Keep storyline tight, info-dense"

**Ours:**
- 2,500-4,000 words (dynamic based on word_count)
- "Minimum: 2,500 words total"

**Analysis:**
- **Benchmark:** Shorter, tighter content
- **Ours:** Longer, more comprehensive content
- **Trade-off:** Benchmark prioritizes brevity, ours prioritizes depth

---

### 2. **Paragraph Structure**

**Benchmark:**
- ≤25 words per paragraph
- ≥90% active voice
- **Must contain** number, KPI, or real example

**Ours:**
- 40-60 words average
- Mix: Short (20-30) and long (60-80)
- 3-5 sentences per paragraph

**Analysis:**
- **Benchmark:** Very short paragraphs, data-driven
- **Ours:** Longer paragraphs, more narrative
- **Trade-off:** Benchmark is more scannable, ours is more readable

---

### 3. **Section Structure**

**Benchmark:**
- New H2/H3 every 150-200 words
- No specific variety requirements

**Ours:**
- SHORT (200-300), MEDIUM (400-600), LONG (700-900)
- 5 structure patterns (must use 4 different)
- Mandatory distribution: 2 SHORT, 3 MEDIUM, 2 LONG, 1 Conclusion

**Analysis:**
- **Benchmark:** Consistent section length
- **Ours:** Mandatory variety in length and structure
- **Trade-off:** Benchmark is more uniform, ours is more varied

---

### 4. **Citations**

**Benchmark:**
- Academic format: `[1]`, `[2]` in text
- MAX 20 sources
- Max 3 citations per section
- Canonical URLs only

**Ours:**
- HTML format: `<a href="url" class="citation">text</a>`
- Target 12-15 citations
- Every paragraph needs citation
- Full specific URLs required

**Analysis:**
- **Benchmark:** Academic citation style, more sources
- **Ours:** HTML links, fewer but more integrated citations
- **Trade-off:** Benchmark is more academic, ours is more web-friendly

---

### 5. **Lists**

**Benchmark:**
- 2-4 sections with lists
- 4-8 items per list
- Introduced by one short lead-in sentence

**Ours:**
- 3-5 lists required
- Mix of `<ul>` and `<ol>`
- Separated with `<p>` tags

**Analysis:**
- **Similar requirements** - both require lists
- **Benchmark:** More specific about list introduction
- **Ours:** More specific about HTML structure

---

### 6. **Internal Links**

**Benchmark:**
- At least one per H2 block
- Woven seamlessly into sentence
- ≤6 words anchor text, varied

**Ours:**
- Not specified in Stage 2 system instruction
- Handled in Stage 5 (Internal Links)

**Analysis:**
- **Benchmark:** Explicit requirement in prompt
- **Ours:** Handled in separate stage
- **Trade-off:** Benchmark integrates into generation, ours post-processes

---

### 7. **Content Rules**

**Benchmark:**
- Strong tags: 1-2 insights per section
- Narrative flow: Bridging sentences between sections
- NEVER mention competitors
- NEVER embed PAA/FAQ in sections
- NEVER overuse <p> tags (one per sentence)

**Ours:**
- Conversational tone: "you" and "your" in every paragraph
- E-E-A-T requirements
- Section variety requirements
- HTML validation checklist

**Analysis:**
- **Benchmark:** More specific content rules (strong tags, bridging sentences)
- **Ours:** More comprehensive quality requirements (E-E-A-T, variety)
- **Trade-off:** Benchmark focuses on structure, ours focuses on quality

---

### 8. **Output Language**

**Benchmark:**
- Must match `company_language`
- Explicitly stated: "Whole textual Output language = company_language"

**Ours:**
- Uses `job_config.language` with fallback priority
- Priority: `job_config.language` > `company_data.language` > `"en"`

**Analysis:**
- **Benchmark:** Strictly follows company language
- **Ours:** Allows override via job_config
- **Trade-off:** Benchmark is more rigid, ours is more flexible

---

## ✅ What We Do Better

1. **Section Variety** - Mandatory variety in length and structure patterns
2. **E-E-A-T Requirements** - Explicit expertise, experience, authority, trust
3. **HTML Structure** - Comprehensive HTML validation checklist
4. **Conversational Tone** - Explicit "you" and "your" requirements
5. **Citation Format** - HTML links instead of academic format (better for web)
6. **Sources URLs** - Full specific URLs vs canonical URLs
7. **Em/En Dashes** - Explicitly forbidden
8. **Dynamic Word Count** - Adapts to job_config.word_count

---

## ⚠️ What Benchmark Does Better

1. **Paragraph Requirements** - Explicit "must contain number/KPI/example"
2. **Active Voice** - ≥90% active voice requirement
3. **Internal Links** - Explicit requirement in generation prompt
4. **Strong Tags** - 1-2 insights per section requirement
5. **Narrative Flow** - Bridging sentences between sections
6. **Competitors** - Explicit "NEVER mention competitors" rule
7. **PAA/FAQ Separation** - Explicit "NEVER embed" rule
8. **Paragraph Length** - Shorter paragraphs (≤25 words) for scannability
9. **Output Language** - Strictly follows company language

---

## 🎯 Key Differences Summary

### Philosophy:
- **Benchmark:** Tight, info-dense, scannable content (1,200-1,800 words)
- **Ours:** Comprehensive, deep, readable content (2,500-4,000 words)

### Citation Style:
- **Benchmark:** Academic format `[1]`, `[2]` (more sources)
- **Ours:** HTML links `<a>` tags (fewer but integrated)

### Section Structure:
- **Benchmark:** Uniform sections (150-200 words each)
- **Ours:** Varied sections (SHORT/MEDIUM/LONG with patterns)

### Content Rules:
- **Benchmark:** More specific structural rules (strong tags, bridging sentences)
- **Ours:** More comprehensive quality rules (E-E-A-T, variety, HTML)

---

## 💡 Recommendations (Analysis Only - No Changes)

### Consider Adding from Benchmark:
1. ✅ **Paragraph requirements:** "Must contain number/KPI/example"
2. ✅ **Active voice:** ≥90% active voice requirement
3. ✅ **Internal links:** Explicit requirement in Stage 2 prompt
4. ✅ **Strong tags:** 1-2 insights per section
5. ✅ **Narrative flow:** Bridging sentences between sections
6. ✅ **Competitors rule:** NEVER mention competitors
7. ✅ **PAA/FAQ rule:** NEVER embed in sections

### Keep from Ours:
1. ✅ **Section variety** - Our mandatory variety is better
2. ✅ **E-E-A-T requirements** - More comprehensive
3. ✅ **HTML citation format** - Better for web
4. ✅ **Conversational tone** - More explicit
5. ✅ **Dynamic word count** - More flexible

### Consider Adjusting:
1. ⚠️ **Paragraph length:** Benchmark's ≤25 words might be too short, but our 40-60 average might be too long
2. ⚠️ **Word count:** Benchmark's 1,200-1,800 vs our 2,500-4,000 - different use cases?
3. ⚠️ **Citation count:** Benchmark's MAX 20 vs our 12-15 - benchmark allows more

---

## 📋 Missing from Our Prompt

1. ❌ **Paragraph must contain number/KPI/example** - Benchmark has this
2. ❌ **≥90% active voice** - Benchmark has this
3. ❌ **Internal links requirement** - Benchmark has this in prompt
4. ❌ **Strong tags requirement** - Benchmark has this
5. ❌ **Bridging sentences** - Benchmark has this
6. ❌ **NEVER mention competitors** - Benchmark has this
7. ❌ **NEVER embed PAA/FAQ** - Benchmark has this
8. ❌ **NEVER overuse <p> tags** - Benchmark has this

---

## 🎯 Conclusion

**Benchmark Strengths:**
- More specific structural requirements
- Better integration of internal links
- Explicit content rules (strong tags, bridging sentences)
- Stricter language control

**Our Strengths:**
- Better section variety
- More comprehensive quality requirements (E-E-A-T)
- Better HTML structure validation
- More flexible word count

**Potential Improvements:**
- Add benchmark's specific content rules (numbers/KPIs, active voice, bridging sentences)
- Add benchmark's explicit prohibitions (competitors, PAA/FAQ embedding)
- Consider adding internal links requirement to Stage 2 prompt
- Consider adding strong tags requirement

