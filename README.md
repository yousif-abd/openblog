# OpenBlog Neo

AI-powered blog generation pipeline using Gemini with Google Search grounding. Specializes in high-quality content generation with optional German legal research integration.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [CLI Reference](#cli-reference)
- [Legal Content Engine](#legal-content-engine)
- [REST API](#rest-api)
- [Pipeline Architecture](#pipeline-architecture)
- [Output Format](#output-format)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## Features

- **6-Stage Pipeline**: Context → Generation → Legal Verification → Quality → URL Verify → Internal Links
- **Google Search Grounding**: Real-time web research for accurate, cited content
- **Legal Content Engine**: German legal research with Beck-Online integration
- **Smart Keyword Preprocessing**: Converts complex keywords/questions into optimal search terms
- **Legal Claim Verification**: Automatically verifies legal claims against court decisions
- **Parallel Processing**: Generate multiple articles simultaneously
- **Multiple Export Formats**: HTML, Markdown, JSON, CSV, XLSX, PDF
- **Image Generation**: Hero, mid, and bottom images via Google Imagen
- **Voice Matching**: Analyzes existing blog content to match company writing style
- **REST API**: Full async job-based API with FastAPI

## Installation

### 1. Clone and Install Dependencies

```bash
git clone <repository-url>
cd openblog

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
# Required
GEMINI_API_KEY=your-gemini-api-key

# Optional: For German legal content
BECK_USERNAME=your-beck-online-username
BECK_PASSWORD=your-beck-online-password
```

### 3. Install Browser Automation (Legal Engine Only)

If using Beck-Online legal research:

```bash
pip install browser-use playwright
playwright install chromium
```

## Quick Start

### Basic Article Generation

```bash
python run_pipeline.py \
    --url https://www.example.com \
    --keywords "AI in Healthcare" "Machine Learning Basics" \
    --output results/
```

### German Legal Content

```bash
python run_pipeline.py \
    --url https://www.kanzlei.de \
    --keywords "Kündigung im Arbeitsrecht" \
    --language de \
    --enable-legal-research \
    --rechtsgebiet Arbeitsrecht \
    --no-use-mock-legal-data \
    --output results/
```

### All Export Formats

```bash
python run_pipeline.py \
    --url https://www.example.com \
    --keywords "Your Topic" \
    --export-formats html markdown json csv xlsx pdf \
    --output results/
```

## CLI Reference

```
python run_pipeline.py [OPTIONS]

Required (one of):
  --url URL                   Company website URL
  --keywords KEYWORD [...]    Keywords to generate articles for
  --input FILE               JSON file with batch configuration

Output:
  --output, -o DIR           Output directory for generated files
  --export-formats FORMAT    Formats: html, markdown, json, csv, xlsx, pdf
                             (default: html json)

Content Options:
  --language CODE            Content language (default: en)
  --market CODE              Target market (default: US)
  --skip-images              Skip image generation
  --max-parallel N           Max concurrent articles (default: unlimited)

Legal Content Options:
  --enable-legal-research    Enable German legal research
  --rechtsgebiet AREA        Legal area: Arbeitsrecht, Mietrecht, Erbrecht,
                             Familienrecht, Vertragsrecht, Steuerrecht
                             (default: Arbeitsrecht)
  --use-mock-legal-data      Use mock data for testing (default: True)
  --no-use-mock-legal-data   Use real Beck-Online (requires credentials)
```

### Example Commands

**Standard blog generation:**
```bash
python run_pipeline.py \
    --url https://www.techcompany.com \
    --keywords "Cloud Computing Benefits" "DevOps Best Practices" \
    --output results/ \
    --export-formats html json pdf
```

**German legal article with full Beck-Online research:**
```bash
python run_pipeline.py \
    --url https://www.rechtsanwalt.de \
    --keywords "Freibetrag Erbe vs. Schenkung: Wo sind die Unterschiede?" \
    --language de \
    --enable-legal-research \
    --rechtsgebiet Erbrecht \
    --no-use-mock-legal-data \
    --output results/
```

**Testing legal pipeline with mock data:**
```bash
python run_pipeline.py \
    --url https://www.kanzlei.de \
    --keywords "Mietminderung bei Schimmel" \
    --language de \
    --enable-legal-research \
    --rechtsgebiet Mietrecht \
    --use-mock-legal-data \
    --output results/
```

**Batch processing with limited concurrency:**
```bash
python run_pipeline.py \
    --url https://www.company.com \
    --keywords "Topic 1" "Topic 2" "Topic 3" "Topic 4" "Topic 5" \
    --max-parallel 2 \
    --skip-images \
    --output results/
```

**From JSON configuration file:**
```bash
python run_pipeline.py --input batch_config.json --output results/
```

Example `batch_config.json`:
```json
{
  "company_url": "https://www.example.com",
  "keywords": ["Keyword 1", "Keyword 2"],
  "language": "en",
  "market": "US"
}
```

## Legal Content Engine

The Legal Content Engine generates high-quality German legal articles with automatic court decision research and claim verification.

### How It Works

1. **Keyword Preprocessing**: Complex keywords (e.g., "Freibetrag Erbe vs. Schenkung: Wo sind die Unterschiede?") are analyzed by Gemini to extract:
   - Optimal search terms (e.g., "Freibetrag", "Erbschaft", "Schenkung")
   - Correct rechtsgebiet (auto-corrects if provided area is wrong)
   - Relevant statutes (e.g., "§ 16 ErbStG")

2. **Beck-Online Research**: Browser automation logs into Beck-Online and searches for relevant court decisions, extracting:
   - Gericht (court name)
   - Aktenzeichen (case number)
   - Datum (date)
   - Leitsatz (legal principle)
   - Relevante Normen (cited statutes)

3. **Decision-Centric Article Generation (Two-Phase)**:

   **Phase 1 - Structured Outline**: Maps each article section to a specific section type:
   - `decision_anchor`: Content built around a specific court decision (MUST cite the assigned Aktenzeichen)
   - `context`: Statutory references only (§ XYZ BGB), no legal interpretations
   - `practical_advice`: Actionable tips and checklists (no legal claims)

   **Phase 2 - Section Generation**: Each section generated with type-specific prompts ensuring:
   - Every provided court decision is cited in exactly one section
   - No unsupported legal claims in context sections
   - Clear separation between legal facts and practical advice

   Section allocation based on available decisions:
   - 2 decisions → 2 decision_anchor, 2 context, 1 practical
   - 4 decisions → 4 decision_anchor, 1 context, 1 practical
   - 6+ decisions → 5 decision_anchor, 1 context, 1 practical

4. **Fast Verification (Stage 2.5)**: Section-type-aware verification with 0 AI calls:
   - `decision_anchor` sections: Verify cited decision exists (regex match)
   - `context` sections: Check for prohibited patterns (no interpretive claims)
   - `practical_advice` sections: Skip verification (no legal claims expected)

   **Result**: 0 unsupported claims (vs 16+ with legacy approach), 0 AI calls (vs 7+)

5. **Source Validation**: Court decisions are validated to ensure:
   - Non-empty required fields (Gericht, Aktenzeichen, Leitsatz)
   - Valid Beck-Online URLs
   - Real content (not placeholders like "N/A")

### Supported Legal Areas (Rechtsgebiete)

| German | English |
|--------|---------|
| Arbeitsrecht | Employment Law |
| Mietrecht | Tenancy Law |
| Erbrecht | Inheritance Law |
| Familienrecht | Family Law |
| Vertragsrecht | Contract Law |
| Steuerrecht | Tax Law |

### Legal Output Files

Each legal article generates a `legal_sources.md` file:

```markdown
# Legal Sources Log

**Article:** Kündigung im Arbeitsrecht: Ihre Rechte
**Rechtsgebiet:** Arbeitsrecht
**Research Date:** 2026-01-18

## Court Decisions (3)

### 1. BAG - 2 AZR 156/24
- **Date:** 2024-03-15
- **Leitsatz:** Eine Kündigung bedarf der Schriftform...
- **Relevante Normen:** § 623 BGB, § 4 KSchG
- **Source:** [https://beck-online.beck.de/...](...)

## Verification Summary
- **Claims Extracted:** 12
- **Claims Supported:** 10
- **Claims Unsupported:** 2 (removed via regeneration)
- **Verification Status:** issues_found
```

### API Usage Optimization

Beck-Online research is optimized to minimize API costs:

- Vision disabled (~80% reduction in API calls)
- Stable Gemini model (60 RPM vs 10 RPM for experimental)
- Action limiting prevents runaway loops
- Automatic retry with exponential backoff (60s, 120s delays)

Expected: **~10-18 API calls per keyword**

## REST API

### Start the Server

```bash
# Development
uvicorn api:app --reload --port 8000

# Production
uvicorn api:app --host 0.0.0.0 --port 8000
```

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/jobs` | Start async pipeline job |
| `GET` | `/api/v1/jobs` | List all jobs |
| `GET` | `/api/v1/jobs/{job_id}` | Get job status/result |
| `DELETE` | `/api/v1/jobs/{job_id}` | Delete a job |
| `GET` | `/api/v1/jobs/{job_id}/articles` | List articles for job |
| `GET` | `/api/v1/jobs/{job_id}/articles/{keyword}/html` | Get article HTML |
| `POST` | `/api/v1/generate` | Sync generation (max 3 articles) |

### Example: Create a Job

```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["AI in Healthcare"],
    "company_url": "https://example.com",
    "language": "en",
    "export_formats": ["html", "json"]
  }'
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Job created. Processing 1 article(s).",
  "created_at": "2026-01-18T10:30:00Z"
}
```

### Example: Check Job Status

```bash
curl http://localhost:8000/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000
```

## Pipeline Architecture

```
Stage 1: Set Context (runs once per batch)
    ├── Company context extraction (OpenContext)
    ├── Voice analysis (from existing blog posts)
    ├── Sitemap crawling
    └── Legal research (optional, Beck-Online)
         ↓
    ┌────┴────┬─────────┐
    ▼         ▼         ▼
  [Art 1]  [Art 2]  [Art 3]  ← Parallel processing
    │         │         │
    ▼         ▼         ▼
  Stage 2: Blog Generation + Images
    │         │         │
    ▼         ▼         ▼
  Stage 2.5: Legal Verification (if legal mode)
    │         │         │
    ▼         ▼         ▼
  Stage 3: Quality Check
    │         │         │
    ▼         ▼         ▼
  Stage 4: URL Verification
    │         │         │
    ▼         ▼         ▼
  Stage 5: Internal Links
    │         │         │
    ▼         ▼         ▼
  Export: HTML/MD/JSON/CSV/XLSX/PDF
```

### Stage Details

| Stage | Name | AI Calls | Purpose |
|-------|------|----------|---------|
| 1 | Set Context | 0-3 | Company context, voice analysis, sitemap, legal research |
| 2 | Blog Generation | 1-4 (standard) / 7 (legal) | Article content + up to 3 images (Imagen). Legal mode uses decision-centric two-phase generation |
| 2.5 | Legal Verification | 0 (decision-centric) / 1-7 (legacy) | Section-type-aware verification. Decision-centric mode uses regex, no AI calls |
| 3 | Quality Check | 1 | Brand-aligned fixes using voice context |
| 4 | URL Verify | 0-2 | Validate URLs, replace dead links |
| 5 | Internal Links | 1 | Add internal links from sitemap |

## Output Format

### Directory Structure

```
results/
├── 001/                              # First article
│   ├── ai-in-healthcare.html         # Full HTML article
│   ├── ai-in-healthcare.json         # Structured data (40+ fields)
│   ├── ai-in-healthcare.md           # Markdown version
│   ├── ai-in-healthcare.pdf          # PDF export
│   └── legal_sources.md              # Legal research log (if legal mode)
├── 002/                              # Second article
│   └── ...
├── 003/                              # Third article
│   └── ...
└── pipeline_results.json             # Full pipeline summary
```

Folder numbers auto-increment across runs.

### Article Schema (40+ Fields)

| Category | Fields |
|----------|--------|
| Headlines | Headline, Subtitle, Teaser, Meta_Title, Meta_Description |
| Content | Intro, section_01-07_title/content (HTML) |
| SEO | Direct_Answer, Key_Takeaways |
| Q&A | People_Also_Ask (4), FAQs (5-6) |
| Media | hero_image, mid_image, bottom_image (URL, alt, credit) |
| Sources | Verified URLs from Google Search grounding |
| Legal | rechtliche_grundlagen, legal_verification_status, legal_issues |
| Optional | Table_Data, Pros_Cons, CTA, Related_Keywords, Video |

## Project Structure

```
openblog/
├── run_pipeline.py         # Main CLI orchestrator
├── api.py                  # FastAPI REST API
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create this)
│
├── shared/                 # Shared components
│   ├── gemini_client.py    # Unified Gemini client
│   ├── models.py           # ArticleOutput schema
│   ├── html_renderer.py    # HTML rendering
│   ├── article_exporter.py # Multi-format export
│   └── prompt_loader.py    # Prompt file loader
│
├── stage1/                 # Set Context
│   ├── stage_1.py          # Orchestrator
│   ├── opencontext.py      # Company context extraction
│   ├── sitemap_crawler.py  # Sitemap parsing
│   ├── voice_enhancer.py   # Voice analysis
│   ├── legal_researcher.py # Legal research orchestrator
│   ├── browser_agent.py    # Beck-Online automation
│   ├── legal_models.py     # Legal data models + validators
│   └── mock_legal_data.py  # Mock data for testing
│
├── stage2/                 # Blog Generation
│   ├── stage_2.py          # Article generation
│   ├── blog_writer.py      # Content writer
│   └── image_creator.py    # Imagen integration
│
├── stage2_5/               # Legal Verification
│   ├── stage_2_5.py        # Verification orchestrator
│   └── legal_verifier.py   # Claim verification + regeneration
│
├── stage3/                 # Quality Check
│   └── stage_3.py          # Quality fixes
│
├── stage4/                 # URL Verification
│   ├── stage_4.py          # URL verification
│   └── url_verifier.py     # Dead link replacement
│
└── stage5/                 # Internal Links
    └── stage_5.py          # Internal link injection
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `BECK_USERNAME` | For legal | Beck-Online username |
| `BECK_PASSWORD` | For legal | Beck-Online password |

### Gemini API Setup

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create an API key
3. Add to `.env` file

### Beck-Online Setup (Legal Engine)

1. Obtain Beck-Online credentials (institutional access required)
2. Add credentials to `.env` file
3. Install browser automation: `pip install browser-use playwright && playwright install chromium`

## Troubleshooting

### Common Issues

**"GEMINI_API_KEY not set"**
```bash
# Check if .env file exists and contains the key
cat .env | grep GEMINI_API_KEY

# Or set directly
export GEMINI_API_KEY=your-key-here
```

**"browserUse not available"**
```bash
pip install browser-use playwright
playwright install chromium
```

**"Login failed - Abmelden not found"**
- Verify Beck-Online credentials in `.env`
- Check if Beck-Online is accessible (institutional network may be required)
- Try with `--use-mock-legal-data` for testing

**API quota exceeded (429 errors)**
- The pipeline includes automatic retry with exponential backoff
- If persistent, reduce `--max-parallel` to 1
- Wait a few minutes between runs

**Empty or placeholder court decisions**
- Court decisions are now validated before use
- Check logs for "Skipping decision with..." warnings
- Ensure Beck-Online search returns actual results

### Debug Mode

For verbose logging:
```bash
python run_pipeline.py --url ... --keywords ... 2>&1 | tee debug.log
```

### Testing Legal Pipeline

Use mock data to test without Beck-Online:
```bash
python run_pipeline.py \
    --url https://example.de \
    --keywords "Test Keyword" \
    --enable-legal-research \
    --use-mock-legal-data \
    --output test_results/
```

## License

MIT
