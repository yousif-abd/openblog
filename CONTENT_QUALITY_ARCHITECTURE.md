# Content Quality Architecture

## 🚨 The Problem

The current codebase has **regex cleanup scattered everywhere**:

| File | Lines | Regex/Cleanup Operations |
|------|-------|--------------------------|
| `html_renderer.py` | 2,693 | 221 regex, 53 "CRITICAL FIX" |
| `stage_02b_quality_refinement.py` | 1,636 | ~100 regex patterns |
| `citation_linker.py` | ~500 | Pattern matching |
| `content_cleanup_pipeline.py` | ~300 | More cleanup |

**Total: ~5,000+ lines of cleanup code**

This approach:
- Creates fragile, unmaintainable code
- Often **breaks** content (as we saw in the output)
- Is redundant — same issues "fixed" in multiple places
- Should be unnecessary if AI generates correct content

---

## ✅ The Correct Architecture

### Principle: AI Should Fix AI Problems

Content issues should be fixed by AI (Gemini), not regex.

```
┌─────────────────────────────────────────────────────────────────┐
│                     CONTENT GENERATION FLOW                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  STAGE 2: Content Generation                                   │
│  ───────────────────────────                                   │
│  • Gemini with comprehensive system instruction                 │
│  • Proper HTML output                                          │
│  • Natural language citations                                   │
│  • Lists when appropriate                                       │
│  • NO cleanup needed (get it right first time)                 │
│                                                                 │
│                          ▼                                      │
│                                                                 │
│  STAGE 2B: AI Quality Review (if issues detected)              │
│  ─────────────────────────────────────────────────             │
│  • Gemini reviews content with quality checklist               │
│  • Fixes structural issues (broken HTML, fragments)            │
│  • Fixes grammar and capitalization                            │
│  • Removes AI markers (em dashes, robotic phrases)             │
│  • Returns FIXED content                                        │
│  • NO regex - AI does ALL the work                             │
│                                                                 │
│                          ▼                                      │
│                                                                 │
│  HTML RENDERER: Simple Output (~400 lines)                     │
│  ─────────────────────────────────────────                     │
│  • Takes validated content                                      │
│  • Renders to semantic HTML5                                   │
│  • Links citations                                              │
│  • NO content manipulation                                      │
│  • NO regex cleanup                                            │
│  • Trusts content is correct                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Required Changes

### 1. Stage 2: Better System Instruction

Improve the system instruction to prevent issues:
- Clear HTML format rules
- Examples of correct vs wrong patterns
- Explicit list usage guidance
- Natural citation patterns

### 2. Stage 2b: AI-Only Quality Review

Remove all regex from Stage 2b. Let AI do the work:
- Give AI the quality checklist
- AI reads content and returns fixed version
- NO regex fallback (if AI can't fix it, it stays)

### 3. HTML Renderer: Minimal Implementation

Replace `html_renderer.py` (2,693 lines) with `html_renderer_simple.py` (454 lines):
- Just rendering
- No cleanup
- No regex
- Trusts content

---

## 📋 Stage 2b Checklist (For AI)

```
=== STRUCTURAL ISSUES ===
□ Truncated list items (ending mid-word)
□ Fragment lists (single-item lists from broken sentences)
□ Duplicate summary lists (paragraph + list with same content)
□ Malformed HTML (<ul> inside <p>, </p> inside <li>)
□ Empty paragraphs
□ Broken sentences split across tags

=== FORMAT ISSUES ===
□ Em dashes (—) → replace with comma or " - "
□ En dashes (–) → replace with "-"
□ Academic citations [N] → remove from body
□ Robotic phrases → rewrite naturally
□ Double question prefixes ("What is What is")

=== GRAMMAR ISSUES ===
□ Lowercase after period
□ Missing punctuation
□ Incomplete sentences
□ Wrong capitalization of brands

=== CONTENT QUALITY ===
□ Citation distribution (40%+ paragraphs cited)
□ Conversational tone ("you", "your")
□ Lists when appropriate (3-5 per article)
□ Question patterns for AEO
```

---

## 🎯 Implementation Priority

### Phase 1: Use Simple Renderer
1. Replace `html_renderer.py` usage with `html_renderer_simple.py`
2. Test output quality

### Phase 2: Improve Stage 2 Instruction
1. Add more examples of correct formatting
2. Add explicit guidance for edge cases
3. Test until generation quality improves

### Phase 3: Simplify Stage 2b
1. Remove regex from Stage 2b
2. Keep only AI quality review
3. Let AI do all the fixing

### Phase 4: Remove Old Code
1. Delete `html_renderer.py` (the 2,693 line monster)
2. Delete `content_cleanup_pipeline.py`
3. Simplify `citation_linker.py`

---

## ✅ Benefits

1. **Simpler code** — 80% less cleanup code
2. **Better quality** — AI fixes are more intelligent than regex
3. **Maintainable** — Changes go in system instruction, not regex
4. **Predictable** — No regex surprises breaking content
5. **Faster** — Less post-processing overhead

---

## 📝 Current Status

Created:
- `html_renderer_simple.py` — 454 lines, clean implementation

Next Steps:
1. Test simple renderer with current content
2. Improve Stage 2 system instruction
3. Reduce regex in Stage 2b

