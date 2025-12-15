# Stage 4 Citation Validation Fixes

## Issues Identified

1. **Broken citations kept**: When URLs returned 404/500 errors and no alternative was found, citations were still kept in the final output (lines 695-701 in `stage_04_citations.py`).

2. **Alternative search not extracting URLs**: The alternative source search was calling Gemini but not properly extracting URLs from the response text (lines 470-477 in `ultimate_citation_validator.py`).

## Fixes Applied

### Fix 1: Remove Broken Citations (No Alternative Found)

**File**: `pipeline/blog_generation/stage_04_citations.py` (lines 683-701)

**Before**: Citations with HTTP errors (404, 500, etc.) were kept even if no alternative was found.

**After**: Citations are now filtered out if:
- HTTP errors (403, 404, 500, 503, 504) AND no alternative found
- No valid URL found
- Spam/malicious/phishing (existing behavior)

**Logic**:
```python
# Filter out if HTTP error AND no alternative found
if has_http_error and ('no alternative source found' in issues):
    should_filter = True

# Filter out if no valid URL found
if 'no valid url found' in issues:
    should_filter = True
```

### Fix 2: Improved Alternative URL Extraction

**File**: `pipeline/processors/ultimate_citation_validator.py` (lines 464-477)

**Before**: Only checked if response text started with `http://` or `https://`.

**After**: Three methods to extract URLs:
1. **Direct URL**: If response starts with URL, extract first URL using regex
2. **Embedded URL**: Extract URLs from anywhere in the response text using regex
3. **Grounding URLs**: Use Gemini's grounding URLs (from Google Search) as fallback

**Code**:
```python
# Method 1: Direct URL
if response_stripped.startswith(('http://', 'https://')):
    url_match = re.search(r'https?://[^\s<>"\'\)]+', response_stripped)
    if url_match:
        return url_match.group(0)

# Method 2: Extract URL from text
urls = re.findall(url_pattern, response)
if urls:
    return urls[0]

# Method 3: Use grounding URLs
grounding_urls = self.gemini_client.get_last_grounding_urls()
if grounding_urls:
    return grounding_urls[0].get('url', '')
```

## Expected Behavior After Fixes

1. **404 detected** → Alternative search triggered
2. **Alternative found** → Citation replaced with alternative URL
3. **No alternative found** → Citation **removed** from final output
4. **Valid URL** → Citation kept

## Testing

Run `test_stage4_citations.py` to verify:
- Broken citations (404s) are removed if no alternative found
- Alternative URLs are properly extracted from Gemini responses
- Valid citations are preserved


