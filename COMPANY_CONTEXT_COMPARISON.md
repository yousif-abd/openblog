# Company Context Field Comparison

**Date:** December 14, 2025  
**Comparing:** `openblog` vs `opencontext` (federicodeponte/opencontext)

---

## 📊 Field Comparison

| Field | openblog | opencontext | Match? |
|-------|----------|-------------|--------|
| `company_name` | ✅ Optional | ✅ Required | ✅ Same |
| `company_url` | ✅ **Required** | ✅ Required | ✅ Same |
| `industry` | ✅ Optional | ✅ Required | ⚠️ Different requirement |
| `description` | ✅ Optional | ✅ Required | ⚠️ Different requirement |
| `products` | ❌ `products_services` | ✅ `products` | ❌ **Different name** |
| `target_audience` | ✅ Optional | ✅ Required | ⚠️ Different requirement |
| `competitors` | ✅ Optional (List) | ✅ Required (List) | ⚠️ Different requirement |
| `tone` | ❌ `brand_tone` | ✅ `tone` | ❌ **Different name** |
| `pain_points` | ✅ Optional (List) | ✅ Required (List) | ⚠️ Different requirement |
| `value_propositions` | ✅ Optional (List) | ✅ Required (List) | ⚠️ Different requirement |
| `use_cases` | ✅ Optional (List) | ✅ Required (List) | ⚠️ Different requirement |
| `content_themes` | ✅ Optional (List) | ✅ Required (List) | ⚠️ Different requirement |
| `system_instructions` | ✅ Optional | ❌ Not in schema | ❌ **Extra field** |
| `client_knowledge_base` | ✅ Optional (List) | ❌ Not in schema | ❌ **Extra field** |
| `content_instructions` | ✅ Optional | ❌ Not in schema | ❌ **Extra field** |

---

## 🔍 OpenContext Schema (from types.ts)

```typescript
export interface AnalysisResponse {
  company_name: string          // Required
  company_url: string           // Required
  industry: string              // Required
  description: string           // Required
  products: string[]            // Required (array)
  target_audience: string       // Required
  competitors: string[]         // Required (array)
  tone: string                 // Required
  pain_points: string[]        // Required (array)
  value_propositions: string[]  // Required (array)
  use_cases: string[]         // Required (array)
  content_themes: string[]     // Required (array)
}
```

---

## 🔍 OpenBlog Schema (from company_context.py)

```python
@dataclass
class CompanyContext:
    # REQUIRED
    company_url: str
    
    # OPTIONAL - Company Information
    company_name: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    
    # OPTIONAL - Products & Services
    products_services: Optional[List[str]] = field(default_factory=list)  # ⚠️ Different name
    target_audience: Optional[str] = None
    
    # OPTIONAL - Competitive Context
    competitors: Optional[List[str]] = field(default_factory=list)
    brand_tone: Optional[str] = None  # ⚠️ Different name
    
    # OPTIONAL - Business Context
    pain_points: Optional[List[str]] = field(default_factory=list)
    value_propositions: Optional[List[str]] = field(default_factory=list)
    use_cases: Optional[List[str]] = field(default_factory=list)
    content_themes: Optional[List[str]] = field(default_factory=list)
    
    # OPTIONAL - Content Guidelines (NOT in opencontext)
    system_instructions: Optional[str] = None
    client_knowledge_base: Optional[List[str]] = field(default_factory=list)
    content_instructions: Optional[str] = None
```

---

## ⚠️ Key Differences

### 1. **Field Name Mismatches**
- ❌ `products` (opencontext) vs `products_services` (openblog)
- ❌ `tone` (opencontext) vs `brand_tone` (openblog)

### 2. **Required vs Optional**
- **opencontext:** Most fields are required (except URL normalization)
- **openblog:** Only `company_url` is required, everything else is optional

### 3. **Extra Fields in openblog**
- ✅ `system_instructions` - Not in opencontext
- ✅ `client_knowledge_base` - Not in opencontext
- ✅ `content_instructions` - Not in opencontext

---

## 🎯 Recommendations

### Option 1: Align with opencontext (Recommended)
**Pros:**
- Consistent schema across projects
- Easy integration with opencontext API
- Standardized field names

**Changes needed:**
1. Rename `products_services` → `products`
2. Rename `brand_tone` → `tone`
3. Keep extra fields (`system_instructions`, `client_knowledge_base`, `content_instructions`) as optional additions

### Option 2: Keep current schema
**Pros:**
- More flexible (all optional except URL)
- Additional fields for content generation
- No breaking changes

**Cons:**
- Field name mismatch with opencontext
- Potential confusion when integrating

---

## 📝 Migration Path (if aligning)

1. **Add aliases** for backward compatibility:
   ```python
   @property
   def products(self) -> List[str]:
       return self.products_services
   
   @property
   def tone(self) -> Optional[str]:
       return self.brand_tone
   ```

2. **Update prompt builder** to use new field names

3. **Update all references** throughout codebase

4. **Keep extra fields** as optional additions

---

## ✅ Current Status

**openblog** can accept opencontext output with minor mapping:
- `products` → `products_services`
- `tone` → `brand_tone`
- Extra fields (`system_instructions`, etc.) are ignored if not present

**Question:** Should we align field names with opencontext for consistency?

