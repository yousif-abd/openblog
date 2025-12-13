# Stage 2b AEO Enhancement Plan

## Problem

**Current State:**
- Stage 2b fixes content quality (grammar, formatting, structure)
- AEO score: 83/100
- Stage 10 (`_enforce_aeo_requirements`) does AEO optimization, but it's too late

**Gap Analysis:**
Stage 2b is NOT checking/fixing AEO score components:
1. ❌ Direct Answer quality (length, keyword, citation)
2. ❌ Citation distribution (ensuring citations per paragraph)
3. ❌ Conversational phrases count (target: 8+)
4. ❌ Question headers count (target: 2+)
5. ❌ FAQ/PAA count (FAQ: 5-6, PAA: 3-4)
6. ❌ Sources list completeness (target: 5+ sources)

## Solution: Supercharge Stage 2b with AEO Optimization

### Phase 1: Add AEO Component Checks

**New AEO Checklist Section:**
```
=== AEO OPTIMIZATION (CRITICAL FOR SCORE 95+) ===
□ Direct Answer: 40-60 words, contains keyword, has citation
□ Citation distribution: 40%+ paragraphs have citations (natural language)
□ Conversational phrases: 8+ instances ("you can", "here's", "let's", etc.)
□ Question headers: 2+ section titles are questions
□ FAQ count: 5-6 items (if <5, enhance existing or add)
□ PAA count: 3-4 items (if <3, enhance existing or add)
□ Sources list: 5+ sources with full URLs
```

### Phase 2: Add AEO Fix Methods

**New Methods in Stage 2b:**
1. `_check_and_fix_direct_answer()` - Ensure Direct Answer meets AEO criteria
2. `_check_and_fix_citation_distribution()` - Add citations to paragraphs missing them
3. `_check_and_fix_conversational_phrases()` - Add conversational phrases if <8
4. `_check_and_fix_question_headers()` - Convert titles to questions if <2
5. `_check_and_fix_faq_paa()` - Enhance FAQ/PAA if counts are low
6. `_check_and_fix_sources_list()` - Ensure Sources field has 5+ entries

### Phase 3: Integration

**Execution Flow:**
```
Stage 2b:
1. Regex cleanup (existing)
2. Gemini quality review (existing)
3. NEW: AEO component checks
4. NEW: AEO fixes (Gemini-powered)
5. Return enhanced article
```

## Expected Impact

**Before:**
- AEO Score: 83/100
- Direct Answer: May be missing or incomplete
- Citations: May be unevenly distributed
- Conversational phrases: May be <8
- Question headers: May be <2

**After:**
- AEO Score: 95+/100
- Direct Answer: Perfect (40-60 words, keyword, citation)
- Citations: Well-distributed (40%+ paragraphs)
- Conversational phrases: 8+ instances
- Question headers: 2+ questions
- FAQ/PAA: Optimal counts

## Implementation Priority

1. **High Priority** (immediate impact):
   - Citation distribution fix
   - Conversational phrases fix
   - Question headers fix

2. **Medium Priority**:
   - Direct Answer enhancement
   - FAQ/PAA enhancement

3. **Low Priority**:
   - Sources list completeness (handled in Stage 4)

## Code Changes Required

### File: `stage_02b_quality_refinement.py`

**Add new methods:**
- `_check_aeo_components()` - Check all AEO components
- `_fix_aeo_citations()` - Add citations to paragraphs missing them
- `_fix_aeo_conversational_phrases()` - Add conversational phrases
- `_fix_aeo_question_headers()` - Convert titles to questions
- `_fix_aeo_direct_answer()` - Enhance Direct Answer

**Update Gemini checklist:**
- Add AEO optimization section
- Include specific targets (8+ phrases, 2+ questions, etc.)

**Update execute method:**
- Call AEO checks after quality review
- Apply AEO fixes if needed

## Testing

**Test Cases:**
1. Article with 0 conversational phrases → Should add 8+
2. Article with 0 question headers → Should convert 2+ titles
3. Article with uneven citations → Should distribute evenly
4. Article with incomplete Direct Answer → Should enhance

**Success Criteria:**
- AEO score increases from 83 → 95+
- All AEO components meet targets
- No regression in content quality

