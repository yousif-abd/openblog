# Stage 4 AI-Only Conversion Recommendation

## Recommendation: ✅ Convert to AI-Only

### Why Convert?

1. **Consistency with Architecture**
   - User explicitly requested: "AI only - everywhere"
   - User explicitly stated: "no regex throughout the whole pipeline"
   - Current regex violates this principle

2. **Reliability**
   - AI handles edge cases better (titles with dashes, special characters, multi-line entries)
   - More robust than regex pattern matching
   - Can handle format variations gracefully

3. **Future-Proof**
   - If Stage 2 output format changes, AI adapts automatically
   - Regex would require manual pattern updates

4. **Maintainability**
   - Single approach (AI) instead of mixed regex/AI
   - Easier to debug and maintain
   - Consistent error handling

### Trade-offs

**Latency:**
- Adds ~1-2 seconds per article (one API call)
- Acceptable for production use

**Cost:**
- Minimal (~$0.0001 per article)
- Negligible impact on overall costs

**Complexity:**
- Slightly more code, but cleaner architecture
- Better error handling and validation

### Implementation Approach

**Option 1: Pure AI Parsing (Recommended)**
- Use Gemini with structured JSON schema
- Prompt: "Extract citations from Sources field. Format: [1]: Title – URL"
- Return structured CitationList JSON
- Validate and parse JSON response

**Option 2: Hybrid (Fallback)**
- Try AI parsing first
- Fallback to simple string parsing if AI fails
- Best of both worlds, but adds complexity

### Note on Stage 3

Stage 3 (`stage_03_quality_refinement.py`) also uses regex for parsing Sources field (line 1047). For full consistency, Stage 3 should also be converted to AI-only.

### Final Recommendation

**Convert Stage 4 to AI-only parsing** for consistency with user's explicit requirements. The trade-offs are minimal and the benefits (consistency, reliability, maintainability) outweigh the costs.


