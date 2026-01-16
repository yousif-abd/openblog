# Getting Started with OpenBlog Neo

Complete setup guide to get OpenBlog running with the Legal Content Engine.

---

## Prerequisites

- Python 3.9 or higher
- Git (for version control)
- Windows/Mac/Linux

---

## Step 1: Install Dependencies

```bash
# Navigate to project directory
cd c:\Users\yousi\openblog_scaile\openblog

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browser (needed for Beck-Online automation)
playwright install chromium
```

**Expected output:**
```
Successfully installed google-genai pydantic httpx browser-use playwright langchain-google-genai ...
Chromium 123.0.6312.4 downloaded to ...
```

---

## Step 2: Get Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Get API key" or "Create API key"
3. Copy the API key (starts with `AIza...`)

**Important:** Keep this key secret! Never commit it to git.

---

## Step 3: Create .env File

```bash
# Copy the template
cp .env.template .env

# Or on Windows Command Prompt:
copy .env.template .env
```

Now edit the `.env` file and add your Gemini API key:

**Open `.env` in your text editor** and update:

```bash
# Required: Add your Gemini API key
GEMINI_API_KEY=AIzaSyYOUR_ACTUAL_KEY_HERE

# Optional: Beck-Online credentials (leave empty for now)
BECK_USERNAME=
BECK_PASSWORD=
```

**Save the file.**

---

## Step 4: Verify Installation

Run this quick test to verify everything works:

```bash
python -c "import google.genai as genai; import httpx; import pydantic; print('✓ All dependencies installed correctly!')"
```

**Expected output:**
```
✓ All dependencies installed correctly!
```

---

## Step 5: Test Basic Pipeline (Non-Legal)

Test the basic pipeline without legal features first:

```bash
python run_pipeline.py \
    --url https://example.com \
    --keywords "test topic" \
    --skip-images \
    --output test_results/
```

**What this does:**
- Scrapes context from example.com
- Generates 1 blog article about "test topic"
- Skips image generation (faster)
- Saves results to `test_results/` directory

**Expected output:**
```
============================================================
OpenBlog Neo Pipeline
============================================================
Keywords: 1
Company: https://example.com
Language: en, Market: US
============================================================

[Stage 1] Set Context
  Company: Example Company
  Articles: 1
  Sitemap: 5 pages

[Stages 2-5] Article Processing (parallel)
  Processing article: test topic
    [Stage 2] ✓ Generated: Test Topic Article...
    [Stage 3] ✓ Applied 2 fixes
    [Stage 4] ✓ Verified 3 URLs, replaced 0
    [Stage 5] ✓ Added 1 internal links

============================================================
Pipeline Complete
============================================================
Duration: 15.3s
Articles: 1 successful, 0 failed
============================================================

Output saved to: test_results\pipeline_abc123.json
```

---

## Step 6: Test Legal Pipeline (Mock Data)

Now test the legal content engine with mock data (no Beck-Online credentials needed):

```bash
python run_pipeline.py \
    --url https://www.braun-kollegen.de/ \
    --keywords "Kündigung im Arbeitsrecht" \
    --enable-legal-research \
    --rechtsgebiet Arbeitsrecht \
    --use-mock-legal-data \
    --skip-images \
    --language de \
    --output legal_test_results/
```

**What this does:**
- Enables legal research mode
- Uses mock German court decisions (no credentials needed)
- Generates German legal content
- Runs Stage 2.5 verification

**Expected output:**
```
============================================================
OpenBlog Neo Pipeline
============================================================
Keywords: 1
Company: https://www.braun-kollegen.de/
Language: de, Market: DE
============================================================

[Stage 1] Set Context
  Company: Braun Kollegen
  Articles: 1
  Sitemap: 41 pages
  Conducting legal research: rechtsgebiet=Arbeitsrecht
  Using mock legal data (development mode)
  Legal research complete: 4 court decisions
  Legal Research: Arbeitsrecht (4 court decisions)

[Stages 2-5] Article Processing (parallel)
  Processing article: Kündigung im Arbeitsrecht
    [Stage 2] ✓ Generated: Kündigung im Arbeitsrecht: Was Arbeitnehmer...
    [Stage 2.5] Legal verification...
    [Stage 2.5] ✓ Verified 8 claims (7 supported, 1 unsupported)
    [Stage 3] ✓ Applied 3 fixes
    [Stage 4] ✓ Verified 5 URLs, replaced 0
    [Stage 5] ✓ Added 2 internal links

============================================================
Pipeline Complete
============================================================
Duration: 25.7s
Articles: 1 successful, 0 failed
============================================================
```

**Check the results:**
```bash
# View the generated article
cd legal_test_results
dir /B

# You'll see folders like:
# kundigung-im-arbeitsrecht/

# Inside each folder:
# - article.html (rendered HTML)
# - article.json (full article data)
```

---

## Step 7: Review Generated Legal Article

Open the generated article to verify it has legal citations:

```bash
# Open in browser (Windows)
start legal_test_results\kundigung-im-arbeitsrecht\article.html

# Or view JSON data
type legal_test_results\kundigung-im-arbeitsrecht\article.json
```

**Look for:**
- ✓ German legal citations (e.g., "BAG, Urt. v. 12.05.2024 – 6 AZR 148/22")
- ✓ Statute references (e.g., "§ 623 BGB")
- ✓ Legal disclaimer at the bottom
- ✓ `rechtliche_grundlagen` field populated in JSON

---

## Troubleshooting

### Error: "GEMINI_API_KEY not set"

**Problem:** `.env` file not created or API key not added

**Solution:**
```bash
# 1. Make sure .env exists
ls .env

# 2. Check contents
type .env

# 3. Add your API key
# Edit .env and add: GEMINI_API_KEY=AIzaSy...
```

### Error: "ModuleNotFoundError: No module named 'google.genai'"

**Problem:** Dependencies not installed

**Solution:**
```bash
pip install -r requirements.txt
```

### Error: "Playwright browser not found"

**Problem:** Chromium browser not installed

**Solution:**
```bash
playwright install chromium
```

### Pipeline runs but generates empty content

**Problem:** API key might be invalid or quota exceeded

**Solution:**
1. Verify API key at [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Check API quota/billing
3. Look for error messages in output

### Error: "charmap codec can't encode character"

**Problem:** Windows console encoding issue

**Solution:** Already fixed in test_legal_pipeline.py with UTF-8 encoding

---

## Next Steps

### For Development (Mock Data)

Continue using mock data - no Beck-Online credentials needed:

```bash
python run_pipeline.py \
    --url https://www.braun-kollegen.de/ \
    --keywords "Kündigungsschutzklage" "Außerordentliche Kündigung" \
    --enable-legal-research \
    --rechtsgebiet Arbeitsrecht \
    --use-mock-legal-data \
    --language de \
    --output results/
```

### For Production (Real Beck-Online)

Now that you have Beck-Online credentials, test the full production pipeline:

1. **Verify credentials are in `.env`:**
   ```bash
   # Check your .env file contains:
   GEMINI_API_KEY=AIzaSy...
   BECK_USERNAME=your-actual-username
   BECK_PASSWORD=your-actual-password
   ```

2. **Run production test (with `--no-use-mock-legal-data`):**
   ```bash
   python run_pipeline.py --url https://www.braun-kollegen.de/ --keywords "Kündigung im Arbeitsrecht" --enable-legal-research --rechtsgebiet Arbeitsrecht --no-use-mock-legal-data --language de --skip-images --output beck_prod_test/
   ```

   **What this does:**
   - Connects to **real Beck-Online** using your credentials
   - Searches for actual court decisions on beck-online.beck.de
   - Extracts decisions, Leitsätze, and cited statutes
   - Generates legal article with real citations
   - Runs Stage 2.5 verification with actual legal data

   **Expected output:**
   ```
   ============================================================
   OpenBlog Neo Pipeline
   ============================================================
   Keywords: 1
   Company: https://www.braun-kollegen.de/
   Language: de, Market: DE
   ============================================================

   [Stage 1] Set Context
     Company: Braun Kollegen
     Articles: 1
     Sitemap: 41 pages
     Conducting legal research: rechtsgebiet=Arbeitsrecht
     Using Beck-Online browser agent (production mode)
     Initializing browser agent for Beck-Online research: Arbeitsrecht
     Browser navigating to beck-online.beck.de...
     Authenticating with Beck-Online...
     Searching for: Kündigung im Arbeitsrecht
     Extracted 4 court decisions from Beck-Online
     Legal research complete: 4 court decisions
     Legal Research: Arbeitsrecht (4 court decisions)

   [Stages 2-5] Article Processing (parallel)
     Processing article: Kündigung im Arbeitsrecht
       [Stage 2] ✓ Generated: Kündigung im Arbeitsrecht: Was Arbeitnehmer...
       [Stage 2.5] Legal verification...
       [Stage 2.5] ✓ Verified 10 claims (9 supported, 1 unsupported)
       [Stage 3] ✓ Applied 2 fixes
       [Stage 4] ✓ Verified 6 URLs, replaced 0
       [Stage 5] ✓ Added 3 internal links

   ============================================================
   Pipeline Complete
   ============================================================
   Duration: 45.2s
   Articles: 1 successful, 0 failed
   ============================================================
   ```

3. **Verify Beck-Online integration:**
   ```bash
   # Open generated article
   start beck_prod_test\kundigung-im-arbeitsrecht\article.html

   # Or inspect JSON for Beck-Online URLs
   type beck_prod_test\kundigung-im-arbeitsrecht\article.json | findstr "beck-online"
   ```

   **Look for:**
   - ✓ Court decision URLs: `https://beck-online.beck.de/Dokument?vpath=...`
   - ✓ Real Aktenzeichen (e.g., "BAG, Urt. v. 23.02.2023 – 2 AZR 296/22")
   - ✓ Authentic Leitsätze from actual Beck-Online decisions
   - ✓ Cited statutes match real references (§ 626 BGB, § 1 KSchG, etc.)
   - ✓ Stage 2.5 verification confirms legal claims

4. **Troubleshooting production issues:**

   **Error: "BECK_USERNAME and BECK_PASSWORD must be set"**
   - Solution: Check `.env` file has credentials (no spaces around `=`)

   **Error: "Authentication failed" or browser timeout**
   - Solution: Verify credentials work manually at https://beck-online.beck.de
   - Check for special characters in password that need escaping

   **Fallback to mock data:**
   - If Beck-Online fails, pipeline automatically falls back to mock data
   - Check logs for "Beck-Online research failed: ..." message
   - Verify browser automation works: `playwright install chromium`

   **Slow performance (>60s):**
   - Normal for first run (browser initialization + Beck-Online search)
   - Use `--skip-images` to speed up testing
   - Consider reducing keywords for faster iteration

---

## Testing Different Legal Areas

Test all 5 supported Rechtsgebiete:

```bash
# Arbeitsrecht (Employment Law)
python run_pipeline.py --url https://www.braun-kollegen.de/ \
    --keywords "Kündigung" --enable-legal-research \
    --rechtsgebiet Arbeitsrecht --use-mock-legal-data --language de

# Mietrecht (Rental Law)
python run_pipeline.py --url https://www.braun-kollegen.de/ \
    --keywords "Mieterhöhung" --enable-legal-research \
    --rechtsgebiet Mietrecht --use-mock-legal-data --language de

# Vertragsrecht (Contract Law)
python run_pipeline.py --url https://www.braun-kollegen.de/ \
    --keywords "AGB-Kontrolle" --enable-legal-research \
    --rechtsgebiet Vertragsrecht --use-mock-legal-data --language de

# Familienrecht (Family Law)
python run_pipeline.py --url https://www.braun-kollegen.de/ \
    --keywords "Unterhalt" --enable-legal-research \
    --rechtsgebiet Familienrecht --use-mock-legal-data --language de

# Erbrecht (Inheritance Law)
python run_pipeline.py --url https://www.braun-kollegen.de/ \
    --keywords "Testament" --enable-legal-research \
    --rechtsgebiet Erbrecht --use-mock-legal-data --language de
```

---

## Quick Reference: Command Line Arguments

### Required:
- `--url` - Company website URL
- `--keywords` - Keywords for articles (space-separated)

### Legal Mode:
- `--enable-legal-research` - Enable legal research
- `--rechtsgebiet` - Legal area (Arbeitsrecht, Mietrecht, etc.)
- `--use-mock-legal-data` - Use mock data (default: True)

### Optional:
- `--language` - Target language (default: en)
- `--skip-images` - Skip image generation (faster testing)
- `--output` - Output directory (default: prints to stdout)
- `--export-formats` - Export formats: html, markdown, json, csv, xlsx, pdf

### Examples:

**Basic article:**
```bash
python run_pipeline.py --url https://example.com --keywords "topic"
```

**Legal article (mock):**
```bash
python run_pipeline.py --url https://braun-kollegen.de \
    --keywords "Kündigung" --enable-legal-research \
    --rechtsgebiet Arbeitsrecht --use-mock-legal-data --language de
```

**Legal article (real Beck-Online):**
```bash
python run_pipeline.py --url https://braun-kollegen.de \
    --keywords "Kündigung" --enable-legal-research \
    --rechtsgebiet Arbeitsrecht --language de
```

**Multiple keywords:**
```bash
python run_pipeline.py --url https://braun-kollegen.de \
    --keywords "Kündigung" "Kündigungsschutz" "Abfindung" \
    --enable-legal-research --rechtsgebiet Arbeitsrecht \
    --use-mock-legal-data --language de --output results/
```

---

## File Structure After Running

```
openblog/
├── .env                    # Your credentials (gitignored)
├── .env.template           # Template (committed to git)
├── requirements.txt        # Python dependencies
├── run_pipeline.py         # Main entry point
├── test_legal_pipeline.py  # Test script
├── GETTING_STARTED.md      # This file
└── results/                # Output directory (created on first run)
    └── article-slug/
        ├── article.html    # Rendered HTML
        ├── article.json    # Full article data
        ├── article.md      # Markdown version
        └── article.pdf     # PDF version (if requested)
```

---

## Need Help?

- **Documentation:** See [LEGAL_ENGINE_IMPLEMENTATION.md](LEGAL_ENGINE_IMPLEMENTATION.md)
- **Migration Notes:** See [BECK_MIGRATION.md](BECK_MIGRATION.md)
- **Architecture:** See [CLAUDE_LEGAL.md](CLAUDE_LEGAL.md)
- **Issues:** Report at [GitHub Issues](https://github.com/anthropics/claude-code/issues)

---

## Summary Checklist

### Initial Setup
- [ ] Python 3.9+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Playwright browser installed (`playwright install chromium`)
- [ ] Gemini API key obtained from Google AI Studio
- [ ] `.env` file created with `GEMINI_API_KEY`

### Testing Progression
- [ ] Basic test passed (non-legal pipeline)
- [ ] Legal test passed (mock data pipeline)
- [ ] Reviewed generated legal article (mock)

### Production Ready
- [ ] Beck-Online credentials added to `.env`
- [ ] Production test passed (real Beck-Online)
- [ ] Verified Beck-Online URLs in generated article
- [ ] Confirmed authentic court citations (Aktenzeichen, Leitsätze)

**You're ready to generate legal content with real Beck-Online data!**

Use mock data for development, Beck-Online for production articles.
