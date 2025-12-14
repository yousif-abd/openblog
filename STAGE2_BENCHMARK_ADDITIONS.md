# Stage 2 Prompt - Benchmark Additions to Consider

**Date:** December 14, 2025  
**Purpose:** List of benchmark features to add to our Stage 2 system instruction

---

## ✅ High Priority Additions

### 1. **Paragraph Content Requirement**
**Benchmark:** "Every paragraph ≤ 25 words & ≥ 90% active voice, and **must contain** a number, KPI or real example."

**What to Add:**
- Every paragraph MUST contain at least one: number, KPI, percentage, dollar amount, timeframe, or real example
- This ensures data-driven, concrete content
- Aligns with our E-E-A-T requirements (expertise/experience)

**Priority:** ⭐⭐⭐ HIGH - Ensures every paragraph has substance

---

### 2. **Active Voice Requirement**
**Benchmark:** "≥90% active voice"

**What to Add:**
- Use active voice in ≥90% of sentences
- Prefer: "Organizations implement X" over "X is implemented by organizations"
- Makes content more direct and engaging

**Priority:** ⭐⭐⭐ HIGH - Improves readability and engagement

---

### 3. **Internal Links Requirement**
**Benchmark:** "At least one per H2 block, woven seamlessly into the surrounding sentence. Example: `<a href="/target-slug">Descriptive Anchor</a>` (≤ 6 words, varied)."

**What to Add:**
- Include at least one internal link per section (H2 block)
- Links must be woven seamlessly into sentences (not standalone)
- Anchor text: ≤6 words, varied phrasing
- Use company's internal URLs from sitemap/internal links pool

**Priority:** ⭐⭐⭐ HIGH - Currently handled in Stage 5, but should be in Stage 2 prompt for better integration

---

### 4. **Bridging Sentences**
**Benchmark:** "**Narrative flow**: end every section with one bridging sentence that naturally sets up the next section."

**What to Add:**
- End every section with a bridging sentence that connects to the next section
- Creates smooth narrative flow
- Example: "Now that you understand X, let's explore how Y works..."

**Priority:** ⭐⭐ MEDIUM - Improves readability and flow

---

### 5. **Competitors Rule**
**Benchmark:** "**NEVER** mention or link to competing companies(Competitors) in the article."

**What to Add:**
- NEVER mention competitor names in the article content
- NEVER link to competitor websites
- Focus on your company's solutions, not competitors
- (Competitors list is for differentiation context only, not for mentioning)

**Priority:** ⭐⭐⭐ HIGH - Important for brand protection

---

### 6. **Strong Tags Requirement**
**Benchmark:** "Highlight 1–2 insights per section with `<strong>…</strong>` (never `**…**`)."

**What to Add:**
- Include 1-2 key insights per section wrapped in `<strong>` tags
- Use for important takeaways, key statistics, or critical points
- Never use markdown `**bold**` - always HTML `<strong>`

**Priority:** ⭐⭐ MEDIUM - Helps with scannability and emphasis

---

## ⚠️ Medium Priority Additions

### 7. **PAA/FAQ Separation Rule**
**Benchmark:** "**NEVER** embed PAA, FAQ or Key Takeaways inside sections or section titles, intro or teaser; they live in separate JSON keys."

**What to Add:**
- NEVER embed PAA questions/answers in section content
- NEVER embed FAQ items in section content
- NEVER embed Key Takeaways in section content
- These belong in separate JSON fields only

**Priority:** ⭐⭐ MEDIUM - Already handled by JSON schema, but good to reinforce

---

### 8. **Paragraph Length Warning**
**Benchmark:** "NEVER create the article sections using this kind of text structure using <p>, this text looks terrible in rendered html (overuse of <p> for each sentence)"

**What to Add:**
- Avoid overusing `<p>` tags (one per sentence)
- Group related sentences into paragraphs
- Target: 3-5 sentences per paragraph (we already have this, but reinforce)

**Priority:** ⭐ LOW - Already covered in our "3-5 sentences per paragraph" rule

---

### 9. **Citation Format Clarification**
**Benchmark:** "Citations in-text as [1], [2]… matching the **Sources** list. MAX 20 sources. STRICT citation format in text [1],[2],[4][9]."

**What to Add:**
- Clarify that citations in Sources field use `[1]: URL – Description` format
- Maximum 20 sources
- Citation numbers in Sources must match in-text citations (if we add academic format support)

**Priority:** ⭐ LOW - We use HTML links, not academic format, so less relevant

---

## 🔄 Consider Adjusting (Not Adding)

### 10. **Word Count Range**
**Benchmark:** ~1,200-1,800 words  
**Ours:** 2,500-4,000 words

**Consideration:** 
- Benchmark is shorter, more scannable
- Ours is longer, more comprehensive
- **Decision:** Keep ours (different use case - comprehensive vs scannable)

---

### 11. **Paragraph Length**
**Benchmark:** ≤25 words per paragraph  
**Ours:** 40-60 words average (mix 20-30 and 60-80)

**Consideration:**
- Benchmark's ≤25 words might be too short for depth
- Our 40-60 average might be too long for scannability
- **Decision:** Consider adjusting to 30-50 words average (middle ground)

---

## 📋 Recommended Addition Order

### Phase 1 (Critical):
1. ✅ **Paragraph Content Requirement** (number/KPI/example)
2. ✅ **Active Voice Requirement** (≥90%)
3. ✅ **Competitors Rule** (NEVER mention)
4. ✅ **Internal Links Requirement** (at least one per section)

### Phase 2 (Important):
5. ✅ **Bridging Sentences** (between sections)
6. ✅ **Strong Tags Requirement** (1-2 per section)

### Phase 3 (Reinforcement):
7. ✅ **PAA/FAQ Separation Rule** (reinforce existing schema)
8. ✅ **Paragraph Length Warning** (reinforce existing rule)

---

## 🎯 Implementation Notes

### Where to Add:
- **Paragraph Content Requirement** → Add to "PARAGRAPH LENGTH REQUIREMENTS" section
- **Active Voice Requirement** → Add to "CONVERSATIONAL TONE" section
- **Internal Links Requirement** → Add new section or to "CONTENT RULES"
- **Bridging Sentences** → Add to "SECTION STRUCTURE PATTERNS" or "NARRATIVE FLOW"
- **Competitors Rule** → Add to "HARD RULES" or "CRITICAL RULES"
- **Strong Tags Requirement** → Add to "FORMAT RULES" section

### Integration:
- These additions should complement (not replace) our existing requirements
- Maintain our section variety requirements (they're better than benchmark)
- Keep our HTML citation format (better than academic format)
- Keep our E-E-A-T requirements (more comprehensive)

---

## ✅ Summary

**Must Add (High Priority):**
1. Paragraph must contain number/KPI/example
2. ≥90% active voice
3. Internal links requirement (one per section)
4. NEVER mention competitors
5. Bridging sentences between sections
6. Strong tags (1-2 per section)

**Should Add (Medium Priority):**
7. PAA/FAQ separation rule (reinforcement)
8. Paragraph length warning (reinforcement)

**Consider Adjusting:**
- Paragraph length: 30-50 words average (vs current 40-60)

