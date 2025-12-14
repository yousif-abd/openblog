# Job Config Parameters - Complete Reference

## Overview
This document lists all `job_config` parameters that can be used to control blog generation, their priorities, defaults, and usage.

## ✅ Currently Used in Stage 1 Prompt

### 1. **primary_keyword** (Required)
- **Type:** `str`
- **Default:** None (required)
- **Usage:** Main topic/keyword for the article
- **Priority:** Direct use
- **Example:** `"AI visibility engine"`

### 2. **language** (Optional)
- **Type:** `str`
- **Default:** `"en"`
- **Usage:** Target language for the blog
- **Priority:** `job_config.language` > `company_data.language` > `company_data.company_language` > `"en"`
- **Example:** `"en"`, `"de"`, `"fr"`
- **In Prompt:** `"Target language: {language}"`

### 3. **word_count** (Optional)
- **Type:** `int`
- **Default:** `None` (uses 1,500-2,500 words)
- **Usage:** Target word count for the article
- **Priority:** Direct use
- **Dynamic Range Calculation:**
  - `< 1,500 words`: `{word_count - 200}-{word_count + 200} words`
  - `1,500-2,500 words`: `{word_count - 300}-{word_count + 300} words`
  - `> 2,500 words`: `{word_count - 500}-{word_count + 500} words`
- **Example:** `3000` → `"Target word count: 2500-3500 words"`
- **In Prompt:** `"Target word count: {word_count_range}"`

### 4. **country** (Optional)
- **Type:** `str`
- **Default:** `None`
- **Usage:** Target market country for localization
- **Priority:** Direct use
- **Example:** `"DE"`, `"US"`, `"FR"`
- **In Prompt:** Adds `TARGET MARKET` section with:
  - Primary country name
  - Market adaptation instructions
  - Local context guidance

### 5. **tone** (Optional)
- **Type:** `str`
- **Default:** `None` (uses `company_context.tone` or `"professional"`)
- **Usage:** Override company tone
- **Priority:** `job_config.tone` > `company_context.tone` > `"professional"`
- **Example:** `"casual"`, `"professional"`, `"technical"`
- **In Prompt:** `"Write in {tone} tone"`

### 6. **content_generation_instruction** (Optional)
- **Type:** `str`
- **Default:** `None`
- **Usage:** Custom instructions for content generation
- **Priority:** Direct use
- **Example:** `"Focus on B2B use cases and ROI metrics. Include case studies from European companies."`
- **In Prompt:** Adds `ADDITIONAL CONTENT INSTRUCTIONS` section

## 📋 Other Available Parameters (Not Used in Stage 1)

### Used in Other Stages:
- **sitemap_urls** - Used in Stage 5 (Internal Links)
- **existing_blog_slugs** - Used in Stage 5 (Internal Links)
- **batch_siblings** - Used in Stage 5 (Internal Links)
- **batch_id** - Used for batch tracking
- **slug** - Used in Stage 11 (Storage)
- **index** - Used in Stage 11 (Storage)
- **system_prompts** - Used in Stage 12 (Review Iteration)
- **review_prompts** - Used in Stage 12 (Review Iteration)
- **use_graphics** - Used in Stage 9 (Image Generation)
- **citations_disabled** - Used in Stage 4 (Citations)

## 🔄 Priority Rules Summary

### Language Priority:
```
job_config.language 
  → company_data.language 
  → company_data.company_language 
  → "en"
```

### Tone Priority:
```
job_config.tone 
  → company_context.tone 
  → "professional"
```

## 📝 Example Usage

```python
job_config = {
    "primary_keyword": "AI visibility engine",
    "language": "en",  # Overrides company language if provided
    "country": "DE",  # Adds market-specific context
    "word_count": 3000,  # Dynamic word count range
    "tone": "casual",  # Overrides company tone
    "content_generation_instruction": "Focus on B2B use cases and ROI metrics."
}
```

## 🎯 Prompt Structure with All Configs

```
Write a comprehensive, high-quality blog article about "{primary_keyword}".

TOPIC FOCUS:
[Topic-specific instructions]

COMPANY CONTEXT:
[Company information]

TARGET MARKET: (if country provided)
- Primary country: {country_name} ({country_code})
- Market adaptation instructions

ADDITIONAL CONTENT INSTRUCTIONS: (if content_generation_instruction provided)
{custom_instructions}

ARTICLE REQUIREMENTS:
- Target language: {language}
- Write in {tone} tone
- Target word count: {word_count_range}
[...]
```

## ✅ Summary

**All key configs are now used:**
- ✅ `primary_keyword` - Required, main topic
- ✅ `language` - With fallback priority
- ✅ `word_count` - Dynamic range calculation
- ✅ `country` - Market-specific context
- ✅ `tone` - Override company tone
- ✅ `content_generation_instruction` - Custom instructions

**Result:** Fully dynamic, configurable prompt generation with proper fallbacks and overrides.

