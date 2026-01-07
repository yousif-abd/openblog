# OpenBlog Neo

AI-powered blog generation pipeline using Gemini 3 Flash Preview with Google Search grounding.

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

## Stages

| Stage | Name | AI Calls | Purpose |
|-------|------|----------|---------|
| 1 | Set Context | 0-2 | Company context + voice enhancement + sitemap (runs once per batch) |
| 2 | Blog Gen + Images | 1-4 | Generate article with Gemini + 3 images with Imagen |
| 3 | Quality Check | 1 | Surgical find/replace fixes (uses structured schema) |
| 4 | URL Verify | 0-2 | Validate/replace dead URLs (uses structured schema) |
| 5 | Internal Links | 1 | Embed internal links from sitemap (uses structured schema) |
| Export | - | 0 | HTML, Markdown, JSON, CSV, XLSX, PDF |

## Data Flow

- **Stage1Output**: Shared context for all articles (company, authors, visual_identity, sitemap)
- **ArticleOutput**: Created in Stage 2, mutated through Stages 3-5 (40+ fields)
- **Export**: Renders to HTML via HTMLRenderer, exports via ArticleExporter

## Project Structure

```
openblog-neo/
├── shared/                 # Shared components
│   ├── gemini_client.py    # Unified Gemini client (URL Context + Google Search + JSON schema)
│   ├── models.py           # ArticleOutput schema (40+ fields)
│   ├── field_utils.py      # DRY field derivation from ArticleOutput
│   ├── html_renderer.py    # Render article to HTML
│   ├── article_exporter.py # Export to multiple formats
│   ├── prompt_loader.py    # Load prompts from text files
│   └── constants.py        # GEMINI_MODEL, MAX_SITEMAP_URLS
├── stage1/                 # Set Context (company, authors, sitemap)
├── stage2/                 # Blog Gen + Images
├── stage3/                 # Quality Check
├── stage4/                 # URL Verify
├── stage5/                 # Internal Links
├── run_pipeline.py         # Main orchestrator
└── requirements.txt
```

## Key Design Decisions

1. **Shared GeminiClient**: All stages use `shared.gemini_client.GeminiClient` for consistency
2. **JSON Schema Output**: Stages 3-5 use `generate_with_schema()` for structured responses
3. **Micro-API Pattern**: Each stage is JSON in → JSON out, can run standalone or be orchestrated
4. **Parallel Processing**: Stage 1 runs once, Stages 2-5 run per article in parallel
5. **Mutation Pattern**: ArticleOutput is created in Stage 2 and mutated in subsequent stages
6. **DRY Fields**: `shared/field_utils.py` derives field lists from ArticleOutput model

## Environment Variables

```
GEMINI_API_KEY=your-gemini-api-key
```

## Usage

```bash
# Run full pipeline with exports
python run_pipeline.py --url https://example.com --keywords "keyword 1" "keyword 2" \
    --output results/ --export-formats html markdown json

# All export formats
python run_pipeline.py --url https://example.com --keywords "topic" \
    --output results/ --export-formats html markdown json csv xlsx pdf

# Skip images, limit parallelism
python run_pipeline.py --url https://example.com --keywords "topic" \
    --output results/ --skip-images --max-parallel 2

# Run individual stage
python stage1/stage_1.py --url https://example.com --keywords "keyword 1"
```

## Dependencies

- `google-genai>=1.0` - Gemini API client
- `pydantic>=2.0` - Data validation
- `httpx>=0.25` - Async HTTP client
- `python-dotenv>=1.0` - Environment variables
- `defusedxml>=0.7` - Secure XML parsing
- `markdownify>=0.11` - HTML to Markdown conversion
- `openpyxl>=3.1` - Excel export
