# Batch vs Article-Level Instructions

## Overview
Instructions can be provided at two levels:
1. **Article-level** - Specific to a single article
2. **Batch-level** - Applies to all articles in a batch

Both levels are merged in Stage 1 prompt generation.

## Instruction Types

### 1. System Instructions / System Prompts

**Article-level:**
- **Field:** `company_data.system_instructions` (from CompanyContext)
- **Usage:** Reusable prompts for all content from this company
- **Example:** `"Focus on practical, actionable advice. Include real-world examples."`
- **In Prompt:** `SYSTEM INSTRUCTIONS (Article-level):`

**Batch-level:**
- **Field:** `job_config.system_prompts` (List[str])
- **Usage:** Instructions that apply to all articles in a batch
- **Example:** `["Focus on B2B use cases", "Include ROI metrics", "Use European examples"]`
- **In Prompt:** `BATCH INSTRUCTIONS (Applies to all articles in this batch):`
- **Priority:** Merged with article-level (both appear in prompt)

### 2. Knowledge Base

**Article-level:**
- **Field:** `company_data.client_knowledge_base` (List[str])
- **Usage:** Facts about the company
- **Example:** `["Founded in 2015", "Serves Fortune 500 companies", "ISO 27001 certified"]`
- **In Prompt:** `COMPANY KNOWLEDGE BASE:`

**Batch-level:**
- **Not currently supported** (could be added if needed)

### 3. Content Instructions

**Article-level:**
- **Field:** `company_data.content_instructions` (from CompanyContext)
- **Usage:** Style, format, requirements for this company
- **Example:** `"Use conversational tone. Include statistics. Add case studies."`
- **In Prompt:** `CONTENT WRITING INSTRUCTIONS (Article-level):`

**Article-level (alternative):**
- **Field:** `job_config.content_generation_instruction` (str)
- **Usage:** Additional instructions for this specific article
- **Example:** `"Focus on B2B use cases and ROI metrics. Include case studies from European companies."`
- **In Prompt:** `ADDITIONAL CONTENT INSTRUCTIONS:`
- **Priority:** Merged with article-level content_instructions

## Priority and Merging

### Merging Rules:
1. **System Instructions:**
   - Article-level (`system_instructions`) + Batch-level (`system_prompts`) = Both appear
   - Both are shown in separate sections

2. **Content Instructions:**
   - Article-level (`content_instructions`) + Article-specific (`content_generation_instruction`) = Both appear
   - Both are shown in separate sections

3. **Knowledge Base:**
   - Only article-level (`client_knowledge_base`)

## Example Usage

### Article-Level Only:
```python
company_data = {
    "system_instructions": "Focus on practical, actionable advice.",
    "client_knowledge_base": ["Founded in 2015", "ISO 27001 certified"],
    "content_instructions": "Use conversational tone. Include statistics."
}

job_config = {
    "primary_keyword": "AI visibility engine",
    "content_generation_instruction": "Focus on B2B use cases."
}
```

**Result:** Article-level instructions + article-specific instruction

### Batch-Level + Article-Level:
```python
# Batch config (applies to all articles)
batch_config = {
    "system_prompts": [
        "Focus on B2B use cases",
        "Include ROI metrics",
        "Use European examples"
    ]
}

# Article 1 config
article1_config = {
    "primary_keyword": "AI visibility engine",
    "system_prompts": batch_config["system_prompts"],  # Inherit from batch
    "content_generation_instruction": "Focus on enterprise security."
}

# Article 2 config
article2_config = {
    "primary_keyword": "Cloud security best practices",
    "system_prompts": batch_config["system_prompts"],  # Inherit from batch
    "content_generation_instruction": "Focus on compliance."
}
```

**Result:** Both articles get batch-level `system_prompts` + their own article-specific instructions

## Prompt Structure

```
SYSTEM INSTRUCTIONS (Article-level):
[From company_data.system_instructions]

BATCH INSTRUCTIONS (Applies to all articles in this batch):
- [From job_config.system_prompts[0]]
- [From job_config.system_prompts[1]]
...

COMPANY KNOWLEDGE BASE:
- [From company_data.client_knowledge_base[0]]
- [From company_data.client_knowledge_base[1]]
...

CONTENT WRITING INSTRUCTIONS (Article-level):
[From company_data.content_instructions]

ADDITIONAL CONTENT INSTRUCTIONS:
[From job_config.content_generation_instruction]
```

## Implementation

### Stage 1 Merging:
- `system_prompts` from `job_config` are merged with `system_instructions` from `company_context`
- Both appear in separate sections
- Article-specific `content_generation_instruction` is added separately

### Stage 12 Usage:
- `system_prompts` are also used in Stage 12 (Review Iteration) for quality checks
- `review_prompts` are used for revision instructions

## Summary

✅ **Article-level:** `system_instructions`, `client_knowledge_base`, `content_instructions` (from CompanyContext)
✅ **Batch-level:** `system_prompts` (from job_config, applies to all articles)
✅ **Article-specific:** `content_generation_instruction` (from job_config, per article)
✅ **Merging:** All levels are merged and appear in prompt

