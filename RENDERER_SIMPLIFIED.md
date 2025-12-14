# HTML Renderer Simplified - Pure Viewer

## Changes Made

The HTML renderer has been simplified to be a **pure viewer** - like "html online viewer .net". It has **no functionality** - just visualization.

### Removed All Processing

1. ❌ **Citation linking** - Removed `link_natural_citations()` calls
2. ❌ **Paragraph wrapping** - Content is already HTML from Stage 2/3
3. ❌ **Citation parsing** - Removed `_parse_source_names()` and `_parse_citation_map()`
4. ❌ **Content cleanup** - No regex, no fixes, no processing

### What It Does Now

1. ✅ **Takes HTML content** from Stage 2/3 (already formatted)
2. ✅ **Wraps in page structure** (header, footer, styles)
3. ✅ **Displays as-is** - no modifications

### Code Changes

**Before:**
```python
# Link natural language citations
if source_name_map:
    content = link_natural_citations(content, source_name_map, max_links_per_source=2)

# Wrap paragraphs in <p> tags
paragraphs = content.split('\n\n')
for para in paragraphs:
    parts.append(f'<p>{para}</p>')
```

**After:**
```python
# Content is already HTML - just display it
parts.append(content)
```

### Stage 11 Updated

Stage 11 now uses `HTMLRendererSimple` instead of `HTMLRenderer`:

```python
from ..processors.html_renderer_simple import HTMLRendererSimple as HTMLRenderer
```

### Result

The renderer is now a **pure viewer** - it displays what Stage 2/3 generates, with no processing or manipulation.

---

## Next Steps

If citations need to be linked, that should happen in:
- **Stage 2** (Gemini generation) - Generate citations as links
- **Stage 2b** (Quality refinement) - Ensure citations are properly linked

The renderer trusts that content is correct when it arrives.

