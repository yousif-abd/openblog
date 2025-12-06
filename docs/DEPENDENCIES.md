# Blog Writer Service

AI-powered blog generation with 12-stage pipeline.

## Dependencies

This service uses:
- **[OpenFigma](https://github.com/federicodeponte/openfigma)** - Graphics generation library
- **Google GenAI SDK** - Direct Gemini API integration
- **Playwright** - HTML to PNG conversion

## Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

## Graphics

Graphics are generated using the OpenFigma library, imported as a dependency.
See OpenFigma repo for graphics documentation and customization.

