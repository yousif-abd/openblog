# Root-Level Fix Plan: Citation Style & Em Dash Issues

## Problem Statement

Despite v4.0 structured JSON output eliminating hallucinations, two minor formatting issues persist:
1. **Academic citations** `[1], [2]` still appear in ~80% of blogs (should be 0%)
2. **Em dashes** `—` appear in ~20% of blogs (should be 0%)

**Current approach**: Regex cleanup in `html_renderer.py` (reactive, last-resort)  
**Target approach**: Multi-layered prevention (proactive, sustainable)

---

## Root Cause Analysis

### Issue 1: Academic Citations `[1], [2]`

**Current State:**
- Gemini generates numbered citations despite instructions
- Regex in `html_renderer.py` attempts cleanup but misses edge cases
- Pattern: `[1], [2]` or `[2][3]` or mid-sentence `text [1] more text`

**Root Causes:**
1. **Prompt ambiguity** (Stage 1): Instructions say "inline contextual" but don't explicitly forbid `[N]`
2. **Schema permissiveness** (Stage 2): Pydantic `ArticleOutput` doesn't validate citation format
3. **Quality gate gap** (Stage 2b): Doesn't check for citation style violations
4. **Regex limitations** (Cleanup): Only catches common patterns, misses edge cases

### Issue 2: Em Dashes `—`, `&mdash;`, `&#8212;`

**Current State:**
- Gemini occasionally uses em dashes for emphasis or parenthetical clauses
- Regex replacement exists but may miss HTML entity variants

**Root Causes:**
1. **Prompt silence**: No explicit instruction against em dashes
2. **Quality gate gap**: Stage 2b doesn't check for em dashes
3. **Regex incompleteness**: May not catch all 3 variants (Unicode, HTML entity, numeric entity)

---

## Multi-Layered Defense Strategy

### Layer 1: Prevention at Source (Prompt Engineering) - **P0**
**Goal**: Gemini never generates these patterns  
**Effectiveness**: 90%+ reduction  
**Maintenance**: Low (one-time prompt update)

### Layer 2: Validation (Schema + Quality Gate) - **P0**
**Goal**: Detect violations before HTML rendering  
**Effectiveness**: 8-9% additional coverage  
**Maintenance**: Medium (schema + quality checker updates)

### Layer 3: Cleanup (Regex Hardening) - **P1**
**Goal**: Catch the remaining 1-2% edge cases  
**Effectiveness**: Final safety net  
**Maintenance**: Low (comprehensive regex patterns)

---

## Implementation Plan

## Phase 1: Prompt Engineering (P0) 🎯

### 1.1 Update Main Content Prompt

**File**: `services/blog-writer/pipeline/prompts/main_prompt.py`

**Changes Required:**

```python
# Add explicit citation style enforcement section
CITATION_STYLE_RULES = """
CRITICAL CITATION RULES (ZERO TOLERANCE):
- NEVER use academic numbered citations like [1], [2], [3]
- NEVER use bracket notation for sources: [source], [ref], [citation]
- ALWAYS use inline contextual anchor text: "according to GitHub's 2024 report"
- Link anchor text must be descriptive: "as demonstrated in Amazon's case study"
- Citation numbers are FORBIDDEN in all content fields

Examples of FORBIDDEN patterns:
❌ "Studies show [1] that AI improves productivity [2][3]"
❌ "According to research [1], developers prefer..."
❌ "[Source] indicates that..."

Examples of CORRECT patterns:
✅ "Studies from MIT's 2024 AI Research Lab show that AI improves productivity"
✅ "According to GitHub's Developer Survey, developers prefer..."
✅ "Amazon's 2024 case study indicates that..."
"""

# Add to main prompt template (after tone/style section)
```

**Action Items:**
- [ ] Locate current citation instructions in prompt
- [ ] Replace/enhance with explicit FORBIDDEN patterns
- [ ] Add visual examples (❌ vs ✅)
- [ ] Position prominently in prompt (not buried in middle)

### 1.2 Add Em Dash Prevention

**File**: Same as above

**Changes Required:**

```python
# Add punctuation rules section
PUNCTUATION_RULES = """
PUNCTUATION STANDARDS:
- NEVER use em dashes (—) or their HTML entities (&mdash;, &#8212;)
- Use regular hyphens (-) for ranges: "2024-2025", "cost-effective"
- Use commas, parentheses, or separate sentences for parenthetical clauses
- Use colons (:) for introducing lists or explanations

Examples of FORBIDDEN patterns:
❌ "The tool — despite its cost — improves productivity"
❌ "Organizations are adopting AI&mdash;with mixed results"
❌ "The market is growing&#8212;projected to reach $30B"

Examples of CORRECT patterns:
✅ "The tool, despite its cost, improves productivity"
✅ "Organizations are adopting AI (with mixed results)"
✅ "The market is growing: projected to reach $30B"
"""
```

**Action Items:**
- [ ] Add punctuation rules section to prompt
- [ ] Include all 3 em dash variants in forbidden list
- [ ] Provide alternative punctuation guidance

---

## Phase 2: Schema-Level Validation (P0) 🛡️

### 2.1 Add Content Validators to Pydantic Schema

**File**: `services/blog-writer/pipeline/models/article_schema.py`

**Changes Required:**

```python
from pydantic import BaseModel, Field, field_validator, ValidationError
import re

class ArticleOutput(BaseModel):
    """Article schema with citation and punctuation validation."""
    
    Headline: str = Field(..., description="Article headline")
    # ... other fields ...
    
    @field_validator('Headline', 'Subtitle', 'Teaser', 'Intro', 'Direct_Answer')
    @classmethod
    def validate_no_academic_citations(cls, v: str) -> str:
        """Reject content with academic citation patterns [N]."""
        if re.search(r'\[\d+\]', v):
            raise ValueError(
                f"Academic citations [N] are forbidden. Found in: {v[:100]}... "
                "Use inline contextual links instead."
            )
        return v
    
    @field_validator('Headline', 'Subtitle', 'Teaser', 'Intro', 'Direct_Answer')
    @classmethod
    def validate_no_em_dashes(cls, v: str) -> str:
        """Reject content with em dashes."""
        if re.search(r'—|&mdash;|&#8212;', v):
            raise ValueError(
                f"Em dashes are forbidden. Found in: {v[:100]}... "
                "Use commas, parentheses, or colons instead."
            )
        return v
    
    @field_validator('section_01_content', 'section_02_content', ..., mode='before')
    @classmethod
    def validate_section_content(cls, v: str) -> str:
        """Validate section content for citations and em dashes."""
        if re.search(r'\[\d+\]', v):
            raise ValueError("Academic citations [N] found in section content")
        if re.search(r'—|&mdash;|&#8212;', v):
            raise ValueError("Em dashes found in section content")
        return v
```

**Action Items:**
- [ ] Add `field_validator` decorators for all text fields
- [ ] Create comprehensive regex patterns for both issues
- [ ] Test validation with known bad examples
- [ ] Ensure validation runs BEFORE extraction stage

**Trade-off**: This will cause Gemini calls to fail if violations exist, triggering retry. This is GOOD - forces Gemini to comply.

### 2.2 Update Quality Checker

**File**: `services/blog-writer/pipeline/core/quality_checker.py`

**Changes Required:**

```python
def check_citation_style(article_data: Dict[str, Any]) -> List[str]:
    """Check for academic citation violations."""
    issues = []
    citation_pattern = re.compile(r'\[\d+\]')
    
    # Check all text fields
    for key, value in article_data.items():
        if isinstance(value, str) and citation_pattern.search(value):
            issues.append(f"Academic citation [N] found in {key}: {value[:50]}...")
    
    return issues

def check_em_dashes(article_data: Dict[str, Any]) -> List[str]:
    """Check for em dash violations."""
    issues = []
    em_dash_pattern = re.compile(r'—|&mdash;|&#8212;')
    
    for key, value in article_data.items():
        if isinstance(value, str) and em_dash_pattern.search(value):
            issues.append(f"Em dash found in {key}: {value[:50]}...")
    
    return issues

# Add to overall quality check
def validate_article(article_data: Dict[str, Any]) -> Dict[str, Any]:
    """Run all quality checks."""
    issues = {
        'citation_style_violations': check_citation_style(article_data),
        'em_dash_violations': check_em_dashes(article_data),
        # ... other checks
    }
    return issues
```

**Action Items:**
- [ ] Add citation style checker
- [ ] Add em dash checker
- [ ] Integrate into Stage 10 quality validation
- [ ] Return violations in quality report

---

## Phase 3: Quality Refinement Enhancement (P0) 🔧

### 3.1 Add Citation Style to Stage 2b Checks

**File**: `services/blog-writer/pipeline/blog_generation/stage_02b_quality_refinement.py`

**Changes Required:**

```python
def _check_citation_style(self, article_data: Dict[str, Any]) -> List[QualityIssue]:
    """Detect academic citation patterns."""
    issues = []
    citation_pattern = re.compile(r'\[\d+\]')
    
    for key, value in article_data.items():
        if isinstance(value, str):
            matches = citation_pattern.findall(value)
            if matches:
                issues.append(QualityIssue(
                    type="citation_style",
                    severity="high",
                    field=key,
                    issue=f"Academic citations {matches} found - must use inline contextual links",
                    fix_instruction="Replace [N] with descriptive anchor text like 'according to X study'"
                ))
    
    return issues

def _check_em_dashes(self, article_data: Dict[str, Any]) -> List[QualityIssue]:
    """Detect em dash usage."""
    issues = []
    em_dash_pattern = re.compile(r'—|&mdash;|&#8212;')
    
    for key, value in article_data.items():
        if isinstance(value, str) and em_dash_pattern.search(value):
            issues.append(QualityIssue(
                type="punctuation",
                severity="medium",
                field=key,
                issue="Em dash found - use comma, parentheses, or colon instead",
                fix_instruction="Replace em dash with comma or split into separate sentences"
            ))
    
    return issues

# Add to detect_issues() method
def detect_issues(self, article_data: Dict[str, Any]) -> List[QualityIssue]:
    """Run all quality checks."""
    all_issues = []
    all_issues.extend(self._check_keyword_density(article_data))
    all_issues.extend(self._check_paragraph_length(article_data))
    all_issues.extend(self._check_ai_markers(article_data))
    all_issues.extend(self._check_citation_style(article_data))  # NEW
    all_issues.extend(self._check_em_dashes(article_data))        # NEW
    return all_issues
```

**Action Items:**
- [ ] Add citation style detector to Stage 2b
- [ ] Add em dash detector to Stage 2b
- [ ] Create fix instructions for RewriteEngine
- [ ] Test with known violations
- [ ] Verify rewrite quality

**Expected Behavior**: If violations detected, Stage 2b will trigger RewriteEngine to fix them using Gemini's rewrite mode.

---

## Phase 4: Regex Hardening (P1) 🧹

### 4.1 Comprehensive Citation Regex

**File**: `services/blog-writer/pipeline/processors/html_renderer.py`

**Current Regex** (likely incomplete):
```python
# Probably something like:
content = re.sub(r'\[\d+\]', '', content)
```

**Enhanced Regex** (catches all edge cases):
```python
def strip_academic_citations(html: str) -> str:
    """
    Remove all academic citation patterns comprehensively.
    Handles: [1], [2], [1,2], [1-3], [1][2], mid-sentence [N], etc.
    """
    # Pattern 1: Basic numbered citations [N]
    html = re.sub(r'\[\d+\]', '', html)
    
    # Pattern 2: Range citations [1-3]
    html = re.sub(r'\[\d+\s*-\s*\d+\]', '', html)
    
    # Pattern 3: Comma-separated citations [1,2] or [1, 2]
    html = re.sub(r'\[\d+(?:\s*,\s*\d+)+\]', '', html)
    
    # Pattern 4: Multiple adjacent citations [1][2][3]
    html = re.sub(r'(?:\[\d+\])+', '', html)
    
    # Pattern 5: Citations with spaces [ 1 ]
    html = re.sub(r'\[\s*\d+\s*\]', '', html)
    
    # Pattern 6: Superscript citations <sup>[1]</sup>
    html = re.sub(r'<sup>\s*\[\d+\]\s*</sup>', '', html)
    
    # Cleanup: Remove double spaces left behind
    html = re.sub(r'\s{2,}', ' ', html)
    
    # Cleanup: Fix punctuation after citation removal
    html = re.sub(r'\s+([.,;:!?])', r'\1', html)
    
    return html
```

### 4.2 Comprehensive Em Dash Regex

**Enhanced Regex**:
```python
def replace_em_dashes(html: str) -> str:
    """
    Replace all em dash variants with appropriate punctuation.
    Handles: —, &mdash;, &#8212;, &#x2014;
    """
    # Pattern 1: Unicode em dash
    html = re.sub(r'\s*—\s*', ', ', html)
    
    # Pattern 2: HTML entity &mdash;
    html = re.sub(r'\s*&mdash;\s*', ', ', html)
    
    # Pattern 3: Numeric entity &#8212;
    html = re.sub(r'\s*&#8212;\s*', ', ', html)
    
    # Pattern 4: Hex entity &#x2014;
    html = re.sub(r'\s*&#x2014;\s*', ', ', html)
    
    # Cleanup: Fix spacing around commas
    html = re.sub(r'\s*,\s*', ', ', html)
    
    return html
```

**Action Items:**
- [ ] Replace existing regex with comprehensive patterns
- [ ] Test against known edge cases
- [ ] Add logging when replacements occur
- [ ] Track replacement counts in metrics

---

## Phase 5: Testing Strategy 🧪

### 5.1 Unit Tests for Validators

**File**: `services/blog-writer/tests/test_validators.py` (NEW)

```python
import pytest
from pipeline.models.article_schema import ArticleOutput
from pydantic import ValidationError

class TestCitationValidation:
    def test_reject_basic_citation(self):
        """Should reject [1] pattern."""
        with pytest.raises(ValidationError, match="Academic citations"):
            ArticleOutput(
                Headline="AI Tools [1] Are Great",
                # ... other required fields
            )
    
    def test_reject_multiple_citations(self):
        """Should reject [1][2] pattern."""
        with pytest.raises(ValidationError):
            ArticleOutput(
                Intro="Studies show [1][2] that AI helps",
                # ...
            )
    
    def test_accept_inline_citations(self):
        """Should accept inline contextual links."""
        article = ArticleOutput(
            Headline="AI Tools Are Great",
            Intro="According to GitHub's study, AI helps",
            # ...
        )
        assert article.Intro == "According to GitHub's study, AI helps"

class TestEmDashValidation:
    def test_reject_unicode_em_dash(self):
        """Should reject — character."""
        with pytest.raises(ValidationError, match="Em dashes"):
            ArticleOutput(
                Headline="AI Tools — The Future",
                # ...
            )
    
    def test_reject_html_entity(self):
        """Should reject &mdash; entity."""
        with pytest.raises(ValidationError):
            ArticleOutput(
                Intro="AI is growing&mdash;fast",
                # ...
            )
```

### 5.2 Integration Tests for Stage 2b

**File**: `services/blog-writer/tests/test_stage_02b.py`

```python
@pytest.mark.asyncio
async def test_citation_style_detection():
    """Stage 2b should detect citation violations."""
    article_data = {
        "Headline": "Test Article",
        "Intro": "Research shows [1] that AI helps [2].",
    }
    
    stage = QualityRefinementStage()
    issues = stage.detect_issues(article_data)
    
    citation_issues = [i for i in issues if i.type == "citation_style"]
    assert len(citation_issues) > 0
    assert "[1]" in str(citation_issues)
```

### 5.3 End-to-End Regression Tests

**File**: `services/blog-writer/tests/test_generation_e2e.py`

```python
@pytest.mark.asyncio
async def test_no_academic_citations_in_output():
    """Generated blogs must not contain [N] citations."""
    result = await generate_blog(keyword="test keyword")
    
    html = result.html_content
    assert not re.search(r'\[\d+\]', html), "Academic citations found in output"

@pytest.mark.asyncio
async def test_no_em_dashes_in_output():
    """Generated blogs must not contain em dashes."""
    result = await generate_blog(keyword="test keyword")
    
    html = result.html_content
    assert not re.search(r'—|&mdash;|&#8212;', html), "Em dashes found in output"
```

**Action Items:**
- [ ] Create 20+ test cases covering edge cases
- [ ] Run tests against existing showcase blogs
- [ ] Add to CI/CD pipeline
- [ ] Set test coverage target: 95%+

---

## Phase 6: Monitoring & Metrics 📊

### 6.1 Add Quality Metrics Tracking

**File**: `services/blog-writer/pipeline/core/execution_context.py`

```python
class QualityMetrics(BaseModel):
    """Track quality issues detected and fixed."""
    citation_violations_detected: int = 0
    citation_violations_fixed: int = 0
    em_dash_violations_detected: int = 0
    em_dash_violations_fixed: int = 0
    # ... other metrics
```

### 6.2 Add Logging

**File**: `services/blog-writer/pipeline/processors/html_renderer.py`

```python
# Log when cleanup is triggered (should be rare after P0 fixes)
if citation_matches := re.findall(r'\[\d+\]', html):
    logger.warning(
        f"⚠️  Regex cleanup caught {len(citation_matches)} academic citations "
        f"that passed validation. Investigate prompt/schema!"
    )
```

---

## Success Criteria 🎯

### P0 Goals (Must Achieve)
- [ ] **0% academic citations** in generated content (measured over 100 blogs)
- [ ] **0% em dashes** in generated content (measured over 100 blogs)
- [ ] **95%+ test coverage** for validators and quality checks
- [ ] **All showcase blogs pass** validation without regex cleanup

### P1 Goals (Nice to Have)
- [ ] **Zero regex cleanups triggered** (proves P0 layers work)
- [ ] **Quality gate blocks** 100% of violations before HTML render
- [ ] **Prompt-level prevention** reduces violations by 90%+

### Measurement Plan
1. **Baseline**: Run 100 blog generations with current system, count violations
2. **Post-P0**: Run 100 blogs after Phase 1-3, measure reduction
3. **Regression**: Add to nightly test suite, track over time

---

## Implementation Timeline

### Week 1: Prevention (P0)
- **Day 1-2**: Update prompts (Phase 1)
- **Day 3-4**: Add schema validators (Phase 2.1)
- **Day 5**: Add quality checker updates (Phase 2.2)

### Week 2: Validation & Testing (P0)
- **Day 1-2**: Enhance Stage 2b (Phase 3)
- **Day 3-4**: Write unit tests (Phase 5.1-5.2)
- **Day 5**: Run 100-blog validation test

### Week 3: Hardening & Monitoring (P1)
- **Day 1**: Harden regex patterns (Phase 4)
- **Day 2**: Add metrics tracking (Phase 6)
- **Day 3-5**: Final testing and documentation

---

## Risk Assessment & Mitigation

### Risk 1: Schema Validation Breaks Generation
**Impact**: High (blocks all generation if too strict)  
**Mitigation**: 
- Add try-catch in validation
- Log violations but don't block initially (warning mode)
- Gradually enable blocking after testing

### Risk 2: Prompt Changes Degrade Quality
**Impact**: Medium (might affect AEO scores)  
**Mitigation**:
- A/B test new prompts against baseline
- Monitor AEO scores before/after
- Rollback if scores drop >5 points

### Risk 3: Performance Impact
**Impact**: Low (validators add ~10ms per blog)  
**Mitigation**:
- Profile validation code
- Optimize regex patterns
- Cache compiled patterns

---

## Rollout Strategy

### Phase 1: Canary (10% traffic)
- Enable P0 fixes for 10% of blogs
- Monitor for regressions
- Collect metrics on violation rates

### Phase 2: Gradual (50% traffic)
- If canary succeeds, expand to 50%
- Continue monitoring
- Fix any edge cases discovered

### Phase 3: Full (100% traffic)
- Deploy to all blogs
- Enable blocking mode for validators
- Archive old regex-only approach

---

## Alternative Approaches (Rejected)

### Alternative 1: Post-Processing Only (Regex)
**Why Rejected**: Reactive, doesn't fix root cause, brittle

### Alternative 2: Custom Gemini Fine-Tune
**Why Rejected**: Expensive, slow iteration, not guaranteed to work

### Alternative 3: Second-Pass Gemini Call for Cleanup
**Why Rejected**: Doubles cost, adds latency, masks root issue

---

## Conclusion

This plan takes a **defense-in-depth** approach:
1. **Prevent** at source (prompts) - 90% effective
2. **Validate** before render (schema + quality gate) - 9% effective
3. **Cleanup** as last resort (regex) - 1% effective

**Expected Outcome**: 100% elimination of both issues with sustainable, maintainable solution.

**Key Principle**: Fix the root cause (Gemini's output) rather than patching symptoms (HTML cleanup).

