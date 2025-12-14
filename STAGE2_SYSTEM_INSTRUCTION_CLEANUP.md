# Stage 2 System Instruction Cleanup

## Problem
Having two system instructions (`_get_detailed_system_instruction` and `_get_light_system_instruction`) controlled by an environment variable was:
- **Unclear** - No clear guidance on when to use which
- **Messy** - Extra complexity with env var switching
- **Confusing** - Two different prompts doing the same thing

## Solution
Consolidated to a **single, production-quality system instruction**.

## Changes Made

### Before:
```python
# Two methods
def _get_detailed_system_instruction(self, word_count: int = None) -> str:
    """Detailed system instruction with comprehensive rules and examples."""
    # ~3,500 chars

def _get_light_system_instruction(self, word_count: int = None) -> str:
    """Lightweight system instruction - minimal, focused rules."""
    # ~500 chars

# Env var switching
prompt_style = os.getenv("STAGE2_PROMPT_STYLE", "detailed").lower()
if prompt_style == "light":
    system_instruction = self._get_light_system_instruction(word_count=word_count)
else:
    system_instruction = self._get_detailed_system_instruction(word_count=word_count)
```

### After:
```python
# Single method
def _get_system_instruction(self, word_count: int = None) -> str:
    """System instruction with comprehensive rules for production-quality content."""
    # ~3,500 chars (the better one)

# Simple call
system_instruction = self._get_system_instruction(word_count=word_count)
```

## Why Keep the Detailed Version?

Based on `CONTENT_QUALITY_DEEP_ANALYSIS.md`:
- ✅ **Better citation formatting** - Proper `<a>` links vs `<strong>` tags
- ✅ **Better citation quality** - More authoritative sources
- ✅ **Deeper content** - More actionable, detailed explanations
- ✅ **Better flow** - More coherent structure
- ✅ **Production quality** - Meets all requirements

## What Was Removed

1. ❌ `_get_light_system_instruction()` method (removed)
2. ❌ `STAGE2_PROMPT_STYLE` environment variable logic (removed)
3. ❌ Conditional prompt selection (removed)

## Result

✅ **Single, clear system instruction**
✅ **No env var switching**
✅ **Production-quality by default**
✅ **Simpler codebase**

## System Instruction Contents

The consolidated instruction includes:
- HTML structure rules (paragraphs, lists, citations)
- Citation formatting (must be `<a>` links)
- Conversational tone requirements
- E-E-A-T requirements
- Sources field requirements (full URLs)
- Punctuation rules (no em/en dashes)
- Section length and structure variety
- List requirements (3-5 lists)
- HTML validation checklist

All rules are comprehensive and production-ready.

