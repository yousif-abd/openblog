# OpenBlog Neo

AI-powered blog generation pipeline using Gemini 3 Flash Preview with Google Search grounding.

## Features

- **5-Stage Pipeline**: Context → Generation → Quality → URL Verify → Internal Links
- **Legal Content Engine**: Automated German legal research with Beck-Online integration
- **Legal Verification (Stage 2.5)**: Automatic claim verification against court decisions
- **Google Search Grounding**: Real-time web research for accurate, sourced content
- **Parallel Processing**: Generate multiple articles simultaneously
- **Multiple Export Formats**: HTML, Markdown, JSON, CSV, XLSX, PDF
- **Image Generation**: Optional hero, mid, and bottom images via Google Imagen
- **Voice Enhancement**: Analyzes existing blog content to match company writing style

## Architecture

```
Stage 1 (once per batch)
     ↓
┌────┴────┬─────────┐
▼         ▼         ▼
[Art 1]  [Art 2]  [Art 3]  ← parallel processing
  │         │         │
  ▼         ▼         ▼
Stage 2   Stage 2   Stage 2   ← Blog Gen + Images
  │         │         │
  ▼         ▼         ▼
Stage 2.5 Stage 2.5 Stage 2.5 ← Legal Verification (optional)
  │         │         │
  ▼         ▼         ▼
Stage 3   Stage 3   Stage 3   ← Quality Check
  │         │         │
  ▼         ▼         ▼
Stage 4   Stage 4   Stage 4   ← URL Verify
  │         │         │
  ▼         ▼         ▼
Stage 5   Stage 5   Stage 5   ← Internal Links
  │         │         │
  ▼         ▼         ▼
Export    Export    Export    ← HTML/MD/JSON/CSV/XLSX/PDF
```

## Pipeline Stages

| Stage | Name | AI Calls | Purpose |
|-------|------|----------|---------|
| 1 | Set Context | 0-2 | Company context + voice enhancement + sitemap + legal research (runs once per batch) |
| 2 | Blog Gen + Images | 1-4 | Generate article with Gemini + 3 images with Imagen |
| 2.5 | Legal Verification | 1 | Verify legal claims against court decisions (optional, legal mode only) |
| 3 | Quality Check | 1 | Surgical find/replace fixes (uses structured schema) |
| 4 | URL Verify | 0-2 | Validate/replace dead URLs (uses structured schema) |
| 5 | Internal Links | 1 | Embed internal links from sitemap (uses structured schema) |

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export GEMINI_API_KEY=your-gemini-api-key
```

Or create a `.env` file:
```
GEMINI_API_KEY=your-gemini-api-key

# Optional: For German legal content generation
BECK_USERNAME=your-beck-username
BECK_PASSWORD=your-beck-password
```

### 3. Run the Pipeline (CLI)

```bash
# Basic usage
python run_pipeline.py --url https://example.com --keywords "keyword 1" "keyword 2" --output results/

# With all export formats
python run_pipeline.py --url https://example.com --keywords "topic" \
    --output results/ --export-formats html markdown json csv xlsx pdf

# Skip images, limit parallelism
python run_pipeline.py --url https://example.com --keywords "topic" \
    --output results/ --skip-images --max-parallel 2

# German legal content with Beck-Online research
python run_pipeline.py \
    --url https://www.lawfirm.de/ \
    --keywords "Kündigung im Arbeitsrecht" \
    --language de \
    --enable-legal-research \
    --rechtsgebiet Arbeitsrecht \
    --output results/
```

## Full Execution Example

### Running the Pipeline

```bash
# Generate 3 articles with all export formats
python run_pipeline.py \
    --url https://www.example.com \
    --keywords "AI in Healthcare" "Machine Learning Basics" "Data Science Trends" \
    --output results/ \
    --export-formats html markdown json pdf

# German legal content with Beck-Online research
python run_pipeline.py \
    --url https://www.kanzlei.de/ \
    --keywords "Kündigung im Arbeitsrecht" "Abfindung berechnen" \
    --language de \
    --enable-legal-research \
    --rechtsgebiet Arbeitsrecht \
    --output results/ \
    --export-formats html json pdf
```

### Output Structure

All results are stored in a single `results/` folder with numbered subfolders:

```
results/
├── 001/                              # First article
│   ├── ai-in-healthcare-2026.html    # Full HTML article
│   ├── ai-in-healthcare-2026.json    # Structured article data
│   ├── ai-in-healthcare-2026.md      # Markdown version
│   ├── ai-in-healthcare-2026.pdf     # PDF export
│   └── legal_sources.md              # Legal research log (if legal mode)
├── 002/                              # Second article
│   ├── machine-learning-basics.html
│   ├── machine-learning-basics.json
│   └── ...
├── 003/                              # Third article
│   └── ...
└── pipeline_results.json             # Full pipeline summary
```

**Folder numbering auto-increments** - if you already have `001`, `002`, `003`, the next run creates `004`, `005`, etc.

### Accessing Results

**1. View the HTML article:**
Open `results/001/article-headline.html` in any browser.

**2. Access structured data:**
The JSON file contains all 40+ article fields:
```bash
# View article headline and sections
cat results/001/article-headline.json | jq '.Headline, .section_01_title'
```

**3. Check legal sources (legal mode only):**
```bash
cat results/001/legal_sources.md
```

Example `legal_sources.md`:
```markdown
# Legal Sources Log

**Article:** Kündigung im Arbeitsrecht: Ihre Rechte und Pflichten
**Rechtsgebiet:** Arbeitsrecht
**Research Date:** 2026-01-17

## Court Decisions (5)

### 1. BAG - 6 AZR 123/23
- **Date:** 2024-03-15
- **Source:** [https://beck-online.beck.de/...](https://beck-online.beck.de/...)

### 2. LAG Berlin-Brandenburg - 15 Sa 1234/23
- **Date:** 2024-02-20
- **Source:** [https://beck-online.beck.de/...](https://beck-online.beck.de/...)

## Verification Summary
- **Claims Extracted:** 12
- **Claims Supported:** 10
- **Claims Unsupported:** 2
- **Verification Status:** issues_found

## Keywords Researched
Kündigung im Arbeitsrecht, Abfindung berechnen
```

**4. Review pipeline summary:**
```bash
cat results/pipeline_results.json | jq '.articles_successful, .duration_seconds'
```

The `pipeline_results.json` contains:
- Job ID and timestamps
- Company context extracted
- Per-article results with stage reports
- Export file paths
- Beck-Online data used (if legal mode)

### 4. Run the API Server

```bash
# Start the FastAPI server
uvicorn api:app --reload --port 8000

# Or run directly
python api.py
```

**API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## REST API

The API provides async job-based processing for blog generation.

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/health` | Health check (alias) |
| `POST` | `/api/v1/jobs` | Start a new pipeline job (async) |
| `GET` | `/api/v1/jobs` | List all jobs |
| `GET` | `/api/v1/jobs/{job_id}` | Get job status and result |
| `DELETE` | `/api/v1/jobs/{job_id}` | Delete a job |
| `GET` | `/api/v1/jobs/{job_id}/articles` | List articles for a job |
| `GET` | `/api/v1/jobs/{job_id}/articles/{keyword}/html` | Get article HTML |
| `POST` | `/api/v1/generate` | Generate articles (sync, max 3) |

### Example: Create a Job

```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["AI in healthcare", "Machine learning basics"],
    "company_url": "https://example.com",
    "language": "en",
    "market": "US",
    "skip_images": false,
    "export_formats": ["html", "json"]
  }'
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Job created. Processing 2 article(s).",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Example: Check Job Status

```bash
curl http://localhost:8000/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000
```

## Command Line Options

```
--url                      Company website URL (required)
--keywords                 List of keywords to generate articles for (required)
--output                   Output directory for generated files
--export-formats           Formats to export (html, markdown, json, csv, xlsx, pdf)
--skip-images              Skip image generation
--max-parallel             Maximum parallel article processing (default: 3)
--language                 Content language (default: en)
--market                   Target market (default: US)
--word-count               Target word count per article (default: 2000)

# Legal Content Options
--enable-legal-research    Enable German legal research (requires Beck-Online credentials)
--rechtsgebiet             Legal area (Arbeitsrecht, Mietrecht, Familienrecht, etc.)
--use-mock-legal-data      Use mock data instead of Beck-Online (for testing)
```

## Legal Content Engine

OpenBlog Neo includes a specialized **Legal Content Engine** for generating high-quality German legal articles with automatic claim verification.

### Features

- **Beck-Online Integration**: Automated browser-based research on beck-online.beck.de
- **Court Decision Extraction**: Automatically extracts relevant court decisions (Gericht, Aktenzeichen, Datum, Leitsatz, Normen)
- **Legal Verification (Stage 2.5)**: Verifies every legal claim against extracted court decisions
- **API Quota Optimization**: Optimized to minimize Gemini API usage (80% reduction)
- **Automatic Retry Logic**: Exponential backoff on quota errors
- **German Legal Disclaimers**: Automatic generation of rechtsgebiet-specific disclaimers

### Setup

1. **Install browser-use dependencies**:
```bash
pip install browser-use playwright
playwright install chromium
```

2. **Set Beck-Online credentials** in `.env`:
```bash
BECK_USERNAME=your-username
BECK_PASSWORD=your-password
GEMINI_API_KEY=your-api-key
```

3. **Run with legal research enabled**:
```bash
python run_pipeline.py \
    --url https://www.lawfirm.de/ \
    --keywords "Kündigung im Arbeitsrecht" "Mietminderung" \
    --language de \
    --enable-legal-research \
    --rechtsgebiet Arbeitsrecht \
    --output results/
```

### Supported Rechtsgebiete

- Arbeitsrecht (Employment Law)
- Mietrecht (Tenancy Law)
- Familienrecht (Family Law)
- Vertragsrecht (Contract Law)
- Erbrecht (Inheritance Law)

### Legal Verification System

Every article generated in legal mode goes through **Stage 2.5: Legal Verification**:

1. **Extract Claims**: Identifies all legal claims in the article
2. **Verify Against Court Decisions**: Checks each claim against Beck-Online court decisions
3. **Flag Unsupported Claims**: Marks claims without legal backing for review
4. **Report Status**: Provides detailed verification report in pipeline output

Example verification output:
```json
{
  "stage2_5": {
    "claims_extracted": 10,
    "claims_supported": 8,
    "claims_unsupported": 2,
    "verification_status": "issues_found",
    "ai_calls": 1
  }
}
```

### API Quota Optimization

Beck-Online scraping is optimized to minimize Gemini API usage:

- **Vision Disabled**: Reduces API calls by ~80%
- **Stable Model**: Uses `gemini-2.0-flash` (60 RPM vs 10 RPM for experimental)
- **Action Limiting**: Prevents runaway browser loops
- **Automatic Retry**: Exponential backoff on quota errors (60s, 120s delays)

Expected API usage: **~10-18 calls per keyword** (well under 60 RPM limit)

### Mock Data Mode

For testing without Beck-Online access:
```bash
python run_pipeline.py \
    --url https://www.lawfirm.de/ \
    --keywords "Kündigung" \
    --enable-legal-research \
    --rechtsgebiet Arbeitsrecht \
    --use-mock-legal-data
```

### Documentation

For detailed implementation documentation, see [LEGAL_ENGINE_IMPLEMENTATION.md](LEGAL_ENGINE_IMPLEMENTATION.md)

## Project Structure

```
openblog-neo/
├── shared/                 # Shared components
│   ├── gemini_client.py    # Unified Gemini client
│   ├── models.py           # ArticleOutput schema (40+ fields)
│   ├── html_renderer.py    # Render article to HTML
│   ├── article_exporter.py # Export to multiple formats
│   ├── field_utils.py      # DRY field derivation
│   └── constants.py        # Model configuration
├── stage1/                 # Set Context
│   ├── stage_1.py          # Company context + sitemap
│   ├── browser_agent.py    # Beck-Online browser automation
│   ├── legal_researcher.py # Legal research orchestrator
│   ├── legal_models.py     # Legal data models
│   └── mock_legal_data.py  # Mock data for testing
├── stage2/                 # Blog Gen + Images
│   └── prompts/            # Legal-specific prompts
├── stage2_5/               # Legal Verification
│   └── stage_2_5.py        # Claim verification
├── stage3/                 # Quality Check
├── stage4/                 # URL Verify
├── stage5/                 # Internal Links
├── run_pipeline.py         # Main orchestrator
├── api.py                  # FastAPI REST API
└── requirements.txt
```

## Output Schema

Each article includes 40+ fields:

- **Headlines**: Headline, Subtitle, Teaser, Meta Title, Meta Description
- **Content**: Intro, 4-9 sections with HTML content
- **SEO**: Direct Answer (featured snippets), Key Takeaways
- **Q&A**: 4 People Also Ask, 5-6 FAQs
- **Media**: 3 image slots with URLs, alt text, credits
- **Sources**: Verified URLs from Google Search grounding
- **Optional**: Tables, Pros/Cons, CTA, Related Keywords, Video embed

## License

MIT
