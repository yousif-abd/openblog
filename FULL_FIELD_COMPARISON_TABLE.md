# Full Field Comparison Table: openblog vs opencontext

**Date:** December 14, 2025  
**Comparing:** `openblog` (pipeline/core/company_context.py) vs `opencontext` (federicodeponte/opencontext)

---

## 📊 Complete Field Comparison

| # | Field Name | openblog | opencontext | Type | Required | Notes |
|---|------------|----------|-------------|------|----------|-------|
| 1 | `company_name` | ✅ `company_name` | ✅ `company_name` | `str` | ❌ Optional | ✅ Same name |
| 2 | `company_url` | ✅ `company_url` | ✅ `company_url` | `str` | ✅ **Required** | ✅ Same name |
| 3 | `industry` | ✅ `industry` | ✅ `industry` | `str` | ❌ Optional | ✅ Same name |
| 4 | `description` | ✅ `description` | ✅ `description` | `str` | ❌ Optional | ✅ Same name |
| 5 | `products` | ❌ `products_services` | ✅ `products` | `List[str]` | ❌ Optional | ❌ **Different name** |
| 6 | `target_audience` | ✅ `target_audience` | ✅ `target_audience` | `str` | ❌ Optional | ✅ Same name |
| 7 | `competitors` | ✅ `competitors` | ✅ `competitors` | `List[str]` | ❌ Optional | ✅ Same name |
| 8 | `tone` | ❌ `brand_tone` | ✅ `tone` | `str` | ❌ Optional | ❌ **Different name** |
| 9 | `pain_points` | ✅ `pain_points` | ✅ `pain_points` | `List[str]` | ❌ Optional | ✅ Same name |
| 10 | `value_propositions` | ✅ `value_propositions` | ✅ `value_propositions` | `List[str]` | ❌ Optional | ✅ Same name |
| 11 | `use_cases` | ✅ `use_cases` | ✅ `use_cases` | `List[str]` | ❌ Optional | ✅ Same name |
| 12 | `content_themes` | ✅ `content_themes` | ✅ `content_themes` | `List[str]` | ❌ Optional | ✅ Same name |
| 13 | `system_instructions` | ✅ `system_instructions` | ❌ **Not in schema** | `str` | ❌ Optional | ❌ **Extra field** |
| 14 | `client_knowledge_base` | ✅ `client_knowledge_base` | ❌ **Not in schema** | `List[str]` | ❌ Optional | ❌ **Extra field** |
| 15 | `content_instructions` | ✅ `content_instructions` | ❌ **Not in schema** | `str` | ❌ Optional | ❌ **Extra field** |

---

## 📋 Detailed Field Specifications

### Field 1: `company_name`
| Property | openblog | opencontext |
|----------|----------|-------------|
| **Name** | `company_name` | `company_name` |
| **Type** | `Optional[str]` | `string` |
| **Required** | ❌ No | ✅ Yes |
| **Default** | `None` | N/A |
| **Description** | Company name | Official company name |
| **Match** | ✅ **SAME** | |

### Field 2: `company_url`
| Property | openblog | opencontext |
|----------|----------|-------------|
| **Name** | `company_url` | `company_url` |
| **Type** | `str` | `string` |
| **Required** | ✅ **YES** | ✅ Yes |
| **Default** | N/A | N/A |
| **Description** | Company website URL | Normalized company website URL |
| **Match** | ✅ **SAME** | |

### Field 3: `industry`
| Property | openblog | opencontext |
|----------|----------|-------------|
| **Name** | `industry` | `industry` |
| **Type** | `Optional[str]` | `string` |
| **Required** | ❌ No | ✅ Yes |
| **Default** | `None` | N/A |
| **Description** | Industry category | Primary industry category |
| **Match** | ✅ **SAME** (different requirement) | |

### Field 4: `description`
| Property | openblog | opencontext |
|----------|-------------|
| **Name** | `description` | `description` |
| **Type** | `Optional[str]` | `string` |
| **Required** | ❌ No | ✅ Yes |
| **Default** | `None` | N/A |
| **Description** | Company description | Clear 2-3 sentence company description |
| **Match** | ✅ **SAME** (different requirement) | |

### Field 5: Products
| Property | openblog | opencontext |
|----------|----------|-------------|
| **Name** | `products_services` | `products` |
| **Type** | `Optional[List[str]]` | `string[]` |
| **Required** | ❌ No | ✅ Yes |
| **Default** | `[]` (empty list) | N/A |
| **Description** | Products/services offered | Products/services offered |
| **Match** | ❌ **DIFFERENT NAME** | |

### Field 6: `target_audience`
| Property | openblog | opencontext |
|----------|----------|-------------|
| **Name** | `target_audience` | `target_audience` |
| **Type** | `Optional[str]` | `string` |
| **Required** | ❌ No | ✅ Yes |
| **Default** | `None` | N/A |
| **Description** | Target audience | Ideal customer profile description |
| **Match** | ✅ **SAME** (different requirement) | |

### Field 7: `competitors`
| Property | openblog | opencontext |
|----------|----------|-------------|
| **Name** | `competitors` | `competitors` |
| **Type** | `Optional[List[str]]` | `string[]` |
| **Required** | ❌ No | ✅ Yes |
| **Default** | `[]` (empty list) | N/A |
| **Description** | Main competitors | Main competitors (based on industry and offerings) |
| **Match** | ✅ **SAME** (different requirement) | |

### Field 8: Tone
| Property | openblog | opencontext |
|----------|----------|-------------|
| **Name** | `brand_tone` | `tone` |
| **Type** | `Optional[str]` | `string` |
| **Required** | ❌ No | ✅ Yes |
| **Default** | `None` | N/A |
| **Description** | Brand tone/voice | Brand voice description |
| **Match** | ❌ **DIFFERENT NAME** | |

### Field 9: `pain_points`
| Property | openblog | opencontext |
|----------|----------|-------------|
| **Name** | `pain_points` | `pain_points` |
| **Type** | `Optional[List[str]]` | `string[]` |
| **Required** | ❌ No | ✅ Yes |
| **Default** | `[]` (empty list) | N/A |
| **Description** | Customer pain points | Customer pain points they address |
| **Match** | ✅ **SAME** (different requirement) | |

### Field 10: `value_propositions`
| Property | openblog | opencontext |
|----------|----------|-------------|
| **Name** | `value_propositions` | `value_propositions` |
| **Type** | `Optional[List[str]]` | `string[]` |
| **Required** | ❌ No | ✅ Yes |
| **Default** | `[]` (empty list) | N/A |
| **Description** | Value propositions | Key value propositions |
| **Match** | ✅ **SAME** (different requirement) | |

### Field 11: `use_cases`
| Property | openblog | opencontext |
|----------|----------|-------------|
| **Name** | `use_cases` | `use_cases` |
| **Type** | `Optional[List[str]]` | `string[]` |
| **Required** | ❌ No | ✅ Yes |
| **Default** | `[]` (empty list) | N/A |
| **Description** | Use cases | Common use cases |
| **Match** | ✅ **SAME** (different requirement) | |

### Field 12: `content_themes`
| Property | openblog | opencontext |
|----------|----------|-------------|
| **Name** | `content_themes` | `content_themes` |
| **Type** | `Optional[List[str]]` | `string[]` |
| **Required** | ❌ No | ✅ Yes |
| **Default** | `[]` (empty list) | N/A |
| **Description** | Content themes | Content themes they focus on |
| **Match** | ✅ **SAME** (different requirement) | |

### Field 13: `system_instructions`
| Property | openblog | opencontext |
|----------|----------|-------------|
| **Name** | `system_instructions` | ❌ **Not in schema** |
| **Type** | `Optional[str]` | N/A |
| **Required** | ❌ No | N/A |
| **Default** | `None` | N/A |
| **Description** | Reusable prompts for all content | N/A |
| **Match** | ❌ **EXTRA FIELD** (only in openblog) | |

### Field 14: `client_knowledge_base`
| Property | openblog | opencontext |
|----------|----------|-------------|
| **Name** | `client_knowledge_base` | ❌ **Not in schema** |
| **Type** | `Optional[List[str]]` | N/A |
| **Required** | ❌ No | N/A |
| **Default** | `[]` (empty list) | N/A |
| **Description** | Facts about company | N/A |
| **Match** | ❌ **EXTRA FIELD** (only in openblog) | |

### Field 15: `content_instructions`
| Property | openblog | opencontext |
|----------|----------|-------------|
| **Name** | `content_instructions` | ❌ **Not in schema** |
| **Type** | `Optional[str]` | N/A |
| **Required** | ❌ No | N/A |
| **Default** | `None` | N/A |
| **Description** | Style, format, requirements | N/A |
| **Match** | ❌ **EXTRA FIELD** (only in openblog) | |

---

## 📊 Summary Statistics

### Matching Fields
- **✅ Same name, same type:** 10 fields
- **❌ Different name, same purpose:** 2 fields (`products_services` vs `products`, `brand_tone` vs `tone`)
- **❌ Extra fields in openblog:** 3 fields (`system_instructions`, `client_knowledge_base`, `content_instructions`)

### Field Count
- **openblog total:** 15 fields
- **opencontext total:** 12 fields
- **Common fields:** 12 fields (with 2 name differences)
- **Unique to openblog:** 3 fields

### Required Fields
- **openblog:** 1 required (`company_url`)
- **opencontext:** 12 required (all fields except URL normalization)

---

## 🔄 Field Mapping (opencontext → openblog)

When receiving data from opencontext API:

```python
# opencontext output
{
  "company_name": "...",
  "company_url": "...",
  "industry": "...",
  "description": "...",
  "products": ["..."],           # ⚠️ Need to map to products_services
  "target_audience": "...",
  "competitors": ["..."],
  "tone": "...",                 # ⚠️ Need to map to brand_tone
  "pain_points": ["..."],
  "value_propositions": ["..."],
  "use_cases": ["..."],
  "content_themes": ["..."]
}

# Mapping to openblog CompanyContext
CompanyContext(
    company_url=data["company_url"],
    company_name=data["company_name"],
    industry=data["industry"],
    description=data["description"],
    products_services=data["products"],      # Map products → products_services
    target_audience=data["target_audience"],
    competitors=data["competitors"],
    brand_tone=data["tone"],                 # Map tone → brand_tone
    pain_points=data["pain_points"],
    value_propositions=data["value_propositions"],
    use_cases=data["use_cases"],
    content_themes=data["content_themes"],
    # Extra fields (not in opencontext) remain None/empty
    system_instructions=None,
    client_knowledge_base=[],
    content_instructions=None
)
```

---

## 🎯 Recommendations

### Option 1: Align Field Names (Recommended)
**Rename in openblog:**
- `products_services` → `products`
- `brand_tone` → `tone`

**Benefits:**
- Direct compatibility with opencontext output
- No mapping needed
- Consistent naming across projects

### Option 2: Add Aliases
**Keep both names for backward compatibility:**
```python
@property
def products(self) -> List[str]:
    return self.products_services

@property  
def tone(self) -> Optional[str]:
    return self.brand_tone
```

**Benefits:**
- No breaking changes
- Supports both naming conventions
- Gradual migration possible

### Option 3: Keep Current Schema
**No changes, manual mapping when needed**

**Benefits:**
- No code changes
- More descriptive names (`products_services`, `brand_tone`)

---

## ✅ Current Compatibility

**openblog can accept opencontext output** with 2 field name mappings:
1. `products` → `products_services`
2. `tone` → `brand_tone`

**Extra fields** (`system_instructions`, `client_knowledge_base`, `content_instructions`) are optional and can remain empty when using opencontext data.

