"""
HTML Renderer - Premium article viewer for ArticleOutput.

Renders article dict to semantic HTML5 page with:
- Premium typography (Inter + Playfair Display via Google Fonts)
- Schema.org JSON-LD structured data (Article, FAQPage, BreadcrumbList)
- Responsive design with mobile breakpoints
- Accordion FAQ/PAA sections (pure CSS)
- TLDR summary box
- Reading time estimate
- Lazy-loaded images with captions
"""

import json
import logging
import re
from html import escape, unescape
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class HTMLRenderer:
    """Premium HTML renderer with structured data and modern design."""

    @staticmethod
    def render(
        article: Dict[str, Any],
        company_name: str = "",
        company_url: str = "",
        author_name: str = "",
        language: str = "en",
    ) -> str:
        """
        Render article to production HTML.

        Args:
            article: ArticleOutput dict
            company_name: Company name for meta
            company_url: Company URL for links
            author_name: Author name (defaults to company_name)
            language: Language code for HTML lang attribute (default: "en")

        Returns:
            Complete HTML document string
        """
        # Extract fields
        headline = HTMLRenderer._strip_html(article.get("Headline", "Untitled"))
        teaser = HTMLRenderer._strip_html(article.get("Teaser", ""))
        intro = article.get("Intro", "")
        meta_title = HTMLRenderer._strip_html(article.get("Meta_Title", headline))
        meta_desc = HTMLRenderer._strip_html(article.get("Meta_Description", teaser))
        direct_answer = article.get("Direct_Answer", "")
        sources = article.get("Sources", "")
        tldr = article.get("TLDR", "")
        slug = article.get("slug", "")

        # Author
        author = author_name or company_name or "Author"

        # Images
        hero_image = article.get("image_01_url", "")
        default_alt = f"Image for {headline}"
        if len(default_alt) > 125:
            default_alt = default_alt[:122] + "..."
        hero_alt = article.get("image_01_alt_text") or default_alt
        hero_credit = article.get("image_01_credit", "")
        mid_image = article.get("image_02_url", "")
        mid_alt = article.get("image_02_alt_text", "")
        mid_credit = article.get("image_02_credit", "")
        bottom_image = article.get("image_03_url", "")
        bottom_alt = article.get("image_03_alt_text", "")
        bottom_credit = article.get("image_03_credit", "")

        # Reading time
        reading_time = article.get("reading_time_min")
        if not reading_time:
            word_count = len(HTMLRenderer._strip_html(intro).split())
            for i in range(1, 10):
                content = article.get(f"section_{i:02d}_content", "")
                if content:
                    word_count += len(HTMLRenderer._strip_html(content).split())
            reading_time = max(1, round(word_count / 220))

        # Date (timezone-aware)
        now = datetime.now(timezone.utc)
        pub_date = now.strftime("%Y-%m-%d")
        display_date = now.strftime("%d. %B %Y") if language == "de" else now.strftime("%b %d, %Y")

        # German month names
        if language == "de":
            de_months = {
                "January": "Januar", "February": "Februar", "March": "März",
                "April": "April", "May": "Mai", "June": "Juni",
                "July": "Juli", "August": "August", "September": "September",
                "October": "Oktober", "November": "November", "December": "Dezember"
            }
            for en, de in de_months.items():
                display_date = display_date.replace(en, de)

        # Render components
        sections_html = HTMLRenderer._render_sections(
            article, mid_image, mid_alt, mid_credit,
            bottom_image, bottom_alt, bottom_credit
        )
        intro_html = HTMLRenderer._render_intro(intro)
        direct_html = HTMLRenderer._render_direct_answer(direct_answer, language)
        tldr_html = HTMLRenderer._render_tldr_compact(article, language)
        toc_html = HTMLRenderer._render_toc(article, language)
        takeaways_html = HTMLRenderer._render_takeaways(article, language)
        faq_html = HTMLRenderer._render_faq(article, language)
        paa_html = HTMLRenderer._render_paa(article, language)
        sources_html = HTMLRenderer._render_sources(sources, language)
        tables_html = HTMLRenderer._render_tables(article.get("tables", []))
        disclaimer_html = HTMLRenderer._render_disclaimer(article, language)
        next_steps_html = HTMLRenderer._render_next_steps(article, company_name, company_url, language)
        schema_html = HTMLRenderer._render_schema(
            article, headline, meta_desc, author, company_name,
            company_url, hero_image, pub_date, slug, language
        )

        # Reading time label
        rt_label = f"{reading_time} Min. Lesezeit" if language == "de" else f"{reading_time} min read"

        # CSS
        css = HTMLRenderer._get_css()

        # Build HTML
        html = f"""<!DOCTYPE html>
<html lang="{escape(language)}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(meta_title)}</title>
    <meta name="description" content="{escape(meta_desc)}">
    <meta name="author" content="{escape(author)}">
    <meta name="robots" content="index, follow">
    {f'<link rel="canonical" href="{escape(company_url)}/magazine/{escape(slug)}">' if slug and company_url else ''}

    <!-- Open Graph -->
    <meta property="og:title" content="{escape(meta_title)}">
    <meta property="og:description" content="{escape(meta_desc)}">
    <meta property="og:type" content="article">
    <meta property="og:locale" content="{escape(language + '_' + language.upper())}">
    <meta property="article:published_time" content="{pub_date}">
    <meta property="article:author" content="{escape(author)}">
    {f'<meta property="og:image" content="{escape(hero_image)}">' if hero_image else ''}

    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{escape(meta_title)}">
    <meta name="twitter:description" content="{escape(meta_desc)}">
    {f'<meta name="twitter:image" content="{escape(hero_image)}">' if hero_image else ''}

    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;500;600;700&family=Source+Serif+4:wght@600;700;800&display=swap" rel="stylesheet">

    {schema_html}

    <style>
{css}
    </style>
</head>
<body>
    <!-- Reading progress bar -->
    <div class="progress-bar" aria-hidden="true"></div>

    <header class="article-header">
        <div class="container">
            <div class="header-meta">
                <span class="author-name">{escape(author)}</span>
                <span class="meta-dot">&middot;</span>
                <time datetime="{pub_date}">{display_date}</time>
                <span class="meta-dot">&middot;</span>
                <span class="reading-time">&#128214; {rt_label}</span>
            </div>
            <h1>{escape(headline)}</h1>
            {f'<p class="teaser">{escape(teaser)}</p>' if teaser else ''}
        </div>
    </header>

    <main class="container">
        {HTMLRenderer._render_hero_image(hero_image, hero_alt, hero_credit)}

        {direct_html}
        {tldr_html}
        {intro_html}
        {toc_html}

        <article>
            {sections_html}
        </article>

        {tables_html}
        {takeaways_html}
        {disclaimer_html}
        {paa_html}
        {faq_html}
        {next_steps_html}
        {sources_html}
    </main>

    <script>
    // Reading progress bar
    window.addEventListener('scroll', function() {{
        var h = document.documentElement;
        var pct = (h.scrollTop / (h.scrollHeight - h.clientHeight)) * 100;
        document.querySelector('.progress-bar').style.width = pct + '%';
    }});
    </script>
</body>
</html>"""

        return html

    @staticmethod
    def _get_css() -> str:
        """Return premium CSS stylesheet."""
        return """
        :root {
            --font-body: 'Source Sans 3', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            --font-heading: 'Source Serif 4', Georgia, 'Times New Roman', serif;
            --primary: #1e3a8a; /* Deep elegant blue */
            --primary-light: #eff6ff;
            --primary-dark: #172554;
            --accent: #f59e0b;
            --text: #1e293b;
            --text-secondary: #475569;
            --text-light: #94a3b8;
            --bg: #ffffff;
            --bg-warm: #fdfaf6; /* Warmer background like Peec */
            --bg-card: #f8fafc;
            --bg-highlight: #f0fdf4;
            --border: #e2e8f0;
            --border-light: #f1f5f9;
            --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
            --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05);
            --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.04);
            --radius: 12px;
            --radius-sm: 8px;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        html { scroll-behavior: smooth; }

        body {
            font-family: var(--font-body);
            font-size: 18px;
            line-height: 1.75;
            color: var(--text);
            background: var(--bg);
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        /* --- Reading Progress Bar --- */
        .progress-bar {
            position: fixed;
            top: 0;
            left: 0;
            width: 0%;
            height: 3px;
            background: linear-gradient(90deg, var(--primary), var(--accent));
            z-index: 9999;
            transition: width 0.1s ease-out;
        }

        /* --- Container --- */
        .container {
            max-width: 780px;
            margin: 0 auto;
            padding: 0 24px;
        }

        /* --- Header --- */
        .article-header {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
            color: #fff;
            padding: 60px 0 50px;
            margin-bottom: 40px;
        }
        .article-header .container {
            position: relative;
        }
        .article-header::after {
            content: '';
            display: block;
            width: 60px;
            height: 4px;
            background: linear-gradient(90deg, var(--primary), var(--accent));
            border-radius: 2px;
            margin-top: 24px;
        }
        .header-meta {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.85rem;
            color: #94a3b8;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .meta-dot { color: #475569; }
        .author-name { font-weight: 600; color: #cbd5e1; }
        .reading-time { color: #94a3b8; }
        h1 {
            font-family: var(--font-heading);
            font-size: clamp(2rem, 4vw, 2.75rem);
            font-weight: 800;
            line-height: 1.15;
            letter-spacing: -0.02em;
            color: #fff;
        }
        .teaser {
            font-size: 1.15rem;
            color: #cbd5e1;
            margin-top: 16px;
            line-height: 1.6;
            max-width: 640px;
        }

        /* --- Hero Image --- */
        .hero-figure {
            margin: -20px 0 40px;
            border-radius: var(--radius);
            overflow: hidden;
            box-shadow: var(--shadow-lg);
        }
        .hero-figure img {
            width: 100%;
            height: auto;
            display: block;
            aspect-ratio: 16 / 9;
            object-fit: cover;
        }
        .image-credit {
            font-size: 0.78rem;
            color: var(--text-light);
            padding: 8px 16px;
            background: var(--bg-card);
            text-align: right;
        }

        /* --- Direct Answer --- */
        .direct-answer {
            margin: 0 0 32px;
            padding: 24px 28px;
            background: var(--bg-highlight);
            border-left: 4px solid var(--primary);
            border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
            font-size: 1.05rem;
            line-height: 1.7;
            color: var(--text);
        }
        .direct-answer .da-label {
            display: block;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--primary);
            margin-bottom: 8px;
        }

        /* --- Das Thema kurz und kompakt --- */
        .tldr {
            margin: 48px 0;
            padding: 32px;
            background: linear-gradient(135deg, #fffbeb, #fef3c7);
            border: 1px solid #fde68a;
            border-radius: var(--radius);
            box-shadow: var(--shadow-sm);
        }
        .tldr .tldr-label {
            font-family: var(--font-heading);
            font-size: 1.35rem;
            font-weight: 700;
            color: #92400e;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .tldr p {
            color: #78350f;
            font-size: 1rem;
            line-height: 1.65;
        }
        .tldr-bullets {
            list-style: none;
            margin: 0;
            padding: 0;
        }
        .tldr-bullets li {
            position: relative;
            padding-left: 28px;
            margin: 14px 0;
            color: #78350f;
            font-size: 1.05rem;
            line-height: 1.6;
            font-weight: 500;
        }
        .tldr-bullets li::before {
            content: "→";
            position: absolute;
            left: 0;
            top: 0;
            color: #d97706;
            font-weight: 700;
            font-size: 1.2rem;
        }

        /* --- Section Numbers --- */
        .section-num {
            display: inline-block;
            font-family: var(--font-body);
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-light);
            margin-right: 10px;
            opacity: 0.5;
            vertical-align: baseline;
        }

        /* --- Section Type Labels --- */
        .section-type-label {
            display: inline-block;
            font-family: var(--font-body);
            font-size: 0.65rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            padding: 3px 10px;
            border-radius: 99px;
            margin-bottom: 6px;
        }
        .label-recht {
            background: #dbeafe;
            color: #1e40af;
        }
        .label-gesetz {
            background: #e0e7ff;
            color: #3730a3;
        }
        .label-praxis {
            background: #dcfce7;
            color: #166534;
        }

        /* --- Legal Disclaimer --- */
        .legal-disclaimer {
            margin: 48px 0;
            padding: 24px 28px;
            background: #f8fafc;
            border: 1px solid #cbd5e1;
            border-left: 4px solid #64748b;
            border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
        }
        .disclaimer-label {
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #475569;
            margin-bottom: 8px;
        }
        .legal-disclaimer p {
            font-size: 0.88rem;
            color: #64748b;
            line-height: 1.6;
        }

        /* --- Next Steps / CTA --- */
        .next-steps {
            margin: 48px 0;
            padding: 32px;
            background: linear-gradient(135deg, #eff6ff, #dbeafe);
            border: 1px solid #bfdbfe;
            border-radius: var(--radius);
            text-align: center;
        }
        .next-steps h2 {
            font-family: var(--font-heading);
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 12px;
        }
        .next-steps p {
            color: var(--text-secondary);
            font-size: 1rem;
            margin-bottom: 20px;
        }
        .next-steps-cta {
            display: inline-block;
            padding: 12px 28px;
            background: var(--primary);
            color: #fff;
            font-weight: 600;
            font-size: 0.95rem;
            text-decoration: none;
            border-radius: var(--radius-sm);
            transition: background 0.2s, transform 0.2s;
        }
        .next-steps-cta:hover {
            background: var(--primary-dark);
            transform: translateY(-1px);
        }

        /* --- Intro --- */
        .intro {
            font-size: 1.05rem;
            margin-bottom: 36px;
            padding: 24px 28px;
            background: var(--bg-warm);
            border-radius: var(--radius);
            color: var(--text);
            line-height: 1.75;
        }
        .intro p { margin-bottom: 12px; }
        .intro p:last-child { margin-bottom: 0; }

        /* --- TOC --- */
        .toc {
            margin: 0 0 48px;
            padding: 28px 32px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
        }
        .toc h2 {
            font-family: var(--font-body);
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--text-secondary);
            margin-bottom: 16px;
        }
        .toc ol {
            list-style: none;
            counter-reset: toc-counter;
        }
        .toc li {
            counter-increment: toc-counter;
            margin: 0;
        }
        .toc a {
            display: flex;
            align-items: baseline;
            gap: 12px;
            padding: 10px 0;
            color: var(--text);
            text-decoration: none;
            font-size: 0.95rem;
            font-weight: 500;
            border-bottom: 1px solid var(--border-light);
            transition: color 0.2s, padding-left 0.2s;
        }
        .toc li:last-child a { border-bottom: none; }
        .toc a::before {
            content: counter(toc-counter, decimal-leading-zero);
            font-size: 0.78rem;
            font-weight: 600;
            color: var(--primary);
            min-width: 22px;
        }
        .toc a:hover {
            color: var(--primary);
            padding-left: 4px;
        }

        /* --- Article Body --- */
        article { margin: 0 0 48px; }
        article h2 {
            font-family: var(--font-heading);
            font-size: 1.65rem;
            font-weight: 700;
            line-height: 1.25;
            margin: 56px 0 20px;
            padding: 8px 0 14px;
            color: var(--text);
            letter-spacing: -0.01em;
            border-bottom: 2px solid var(--primary-light);
            position: relative;
        }

        article h2::after {
            content: '';
            position: absolute;
            bottom: -2px;
            left: 0;
            width: 48px;
            height: 2px;
            background: var(--primary);
        }

        article h2:first-child {
            margin-top: 0;
        }

        article h3 {
            font-family: var(--font-heading);
            font-size: 1.2rem;
            font-weight: 600;
            margin: 36px 0 14px;
            padding-left: 14px;
            color: var(--text);
            border-left: 3px solid var(--primary);
        }
        article p {
            margin: 16px 0;
            color: var(--text);
        }
        article ul, article ol {
            margin: 16px 0 16px 28px;
        }
        article li {
            margin: 8px 0;
            padding-left: 4px;
        }
        article li::marker { color: var(--primary); }
        article a {
            color: var(--primary);
            text-decoration: underline;
            text-decoration-color: var(--primary-light);
            text-underline-offset: 3px;
            transition: text-decoration-color 0.2s;
        }
        article a:hover {
            text-decoration-color: var(--primary);
        }
        article strong { font-weight: 600; color: #0f172a; }
        article blockquote {
            margin: 32px 0;
            padding: 28px 32px;
            border: none;
            background: var(--bg-warm);
            border-left: 4px solid var(--accent);
            border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
            font-family: var(--font-heading);
            font-weight: 600;
            font-size: 1.15rem;
            color: var(--text);
            line-height: 1.6;
            position: relative;
        }
        article blockquote::before {
            content: "“";
            position: absolute;
            top: 5px;
            left: -20px;
            font-size: 4rem;
            color: var(--accent);
            opacity: 0.3;
            line-height: 1;
        }

        /* --- Inline Images --- */
        .inline-figure {
            margin: 40px 0;
            border-radius: var(--radius);
            overflow: hidden;
            box-shadow: var(--shadow-md);
        }
        .inline-figure img {
            width: 100%;
            height: auto;
            display: block;
        }

        /* --- Key Takeaways --- */
        .takeaways {
            margin: 48px 0;
            padding: 32px;
            background: linear-gradient(135deg, #f0fdf4, #ecfdf5);
            border: 1px solid #bbf7d0;
            border-radius: var(--radius);
        }
        .takeaways h2 {
            font-family: var(--font-body);
            font-size: 0.85rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #166534;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .takeaways ul { list-style: none; }
        .takeaways li {
            margin: 14px 0;
            padding-left: 28px;
            position: relative;
            color: #14532d;
            line-height: 1.6;
        }
        .takeaways li::before {
            content: "\\2713";
            position: absolute;
            left: 0;
            color: #16a34a;
            font-weight: 700;
            font-size: 1.1em;
        }

        /* --- FAQ / PAA Accordion --- */
        .faq, .paa { margin: 48px 0; }
        .faq > h2, .paa > h2 {
            font-family: var(--font-heading);
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 20px;
            color: var(--text);
        }
        .accordion-item {
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            margin-bottom: 10px;
            overflow: hidden;
            transition: box-shadow 0.2s;
        }
        .accordion-item:hover { box-shadow: var(--shadow-sm); }
        .accordion-item summary {
            padding: 18px 24px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            list-style: none;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: var(--text);
            background: var(--bg);
            transition: background 0.2s;
        }
        .accordion-item summary:hover { background: var(--bg-card); }
        .accordion-item summary::-webkit-details-marker { display: none; }
        .accordion-item summary::after {
            content: "+";
            font-size: 1.3rem;
            font-weight: 400;
            color: var(--text-light);
            transition: transform 0.2s;
        }
        .accordion-item[open] summary::after {
            content: "\\2212";
        }
        .accordion-item[open] summary {
            border-bottom: 1px solid var(--border-light);
            background: var(--bg-card);
        }
        .accordion-answer {
            padding: 18px 24px;
            color: var(--text-secondary);
            line-height: 1.7;
            font-size: 0.95rem;
        }

        /* --- Sources --- */
        .sources {
            margin: 48px 0;
            padding: 28px 32px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius);
        }
        .sources h2 {
            font-family: var(--font-body);
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--text-secondary);
            margin-bottom: 16px;
        }
        .sources ol { margin: 0 0 0 20px; }
        .sources li {
            margin: 8px 0;
            font-size: 0.88rem;
            color: var(--text-secondary);
            line-height: 1.5;
        }
        .sources a {
            color: var(--primary);
            text-decoration: none;
            word-break: break-word;
        }
        .sources a:hover { text-decoration: underline; }

        /* --- Comparison Tables --- */
        .comparison-table {
            margin: 40px 0;
            overflow-x: auto;
            border-radius: var(--radius);
            box-shadow: var(--shadow-md);
        }
        .comparison-table h3 {
            font-size: 1.1rem;
            font-weight: 600;
            padding: 16px 20px;
            background: var(--bg-card);
            border-bottom: 1px solid var(--border);
            margin: 0;
        }
        .comparison-table table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.92rem;
        }
        .comparison-table th {
            padding: 14px 18px;
            text-align: left;
            background: #f1f5f9;
            font-weight: 600;
            color: var(--text);
            border-bottom: 2px solid var(--border);
        }
        .comparison-table td {
            padding: 12px 18px;
            text-align: left;
            border-bottom: 1px solid var(--border-light);
            color: var(--text-secondary);
        }
        .comparison-table tr:nth-child(even) td { background: #fafbfc; }
        .comparison-table tr:hover td { background: var(--bg-highlight); }

        /* --- Responsive --- */
        @media (max-width: 768px) {
            body { font-size: 16px; }
            .container { padding: 0 16px; }
            .article-header { padding: 40px 0 32px; }
            h1 { font-size: 1.75rem; }
            article h2 { font-size: 1.4rem; margin-top: 40px; }
            .toc, .takeaways, .sources { padding: 20px 24px; }
            .accordion-item summary { padding: 14px 18px; }
            .accordion-answer { padding: 14px 18px; }
        }

        @media (max-width: 480px) {
            .article-header { padding: 28px 0 24px; }
            h1 { font-size: 1.5rem; }
            .teaser { font-size: 1rem; }
            .header-meta { font-size: 0.78rem; }
            .direct-answer, .tldr, .intro { padding: 18px 20px; }
        }

        /* Print styles */
        @media print {
            .progress-bar { display: none; }
            .article-header { background: #fff; color: #000; padding: 20px 0; }
            .article-header h1 { color: #000; }
            .teaser, .header-meta, .author-name { color: #333; }
            .accordion-item { break-inside: avoid; }
            .accordion-item[open] .accordion-answer { display: block; }
        }
"""

    @staticmethod
    def _sanitize_html(html: str) -> str:
        """Sanitize HTML content by removing dangerous elements."""
        if not html:
            return ""
        sanitized = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.IGNORECASE | re.DOTALL)
        sanitized = re.sub(r'<style[^>]*>.*?</style>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        sanitized = re.sub(r'<iframe[^>]*>.*?</iframe>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        sanitized = re.sub(r'<iframe[^>]*/>', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'<object[^>]*>.*?</object>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        sanitized = re.sub(r'<embed[^>]*/?>', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'<form[^>]*>.*?</form>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        sanitized = re.sub(r'\s*on\w+\s*=["\'][^"\']*["\']', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'\s*on\w+\s*=\S+', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'href\s*=\s*["\']javascript:[^"\']*["\']', 'href="#"', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'src\s*=\s*["\']javascript:[^"\']*["\']', 'src=""', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'href\s*=\s*["\']data:[^"\']*["\']', 'href="#"', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'src\s*=\s*["\']data:(?!image/)[^"\']*["\']', 'src=""', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'<base[^>]*/?>', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'<meta[^>]*http-equiv\s*=\s*["\']refresh["\'][^>]*/?>',
                           '', sanitized, flags=re.IGNORECASE)
        return sanitized

    @staticmethod
    def _render_hero_image(image: str, alt: str, credit: str) -> str:
        """Render hero image with figure/figcaption."""
        if not image:
            return ""
        credit_html = f'<figcaption class="image-credit">{escape(credit)}</figcaption>' if credit else ""
        return f"""<figure class="hero-figure">
            <img src="{escape(image)}" alt="{escape(alt)}">
            {credit_html}
        </figure>"""

    @staticmethod
    def _render_inline_image(image: str, alt: str, credit: str, lazy: bool = True) -> str:
        """Render inline image with figure/figcaption."""
        if not image:
            return ""
        loading = ' loading="lazy"' if lazy else ''
        credit_html = f'<figcaption class="image-credit">{escape(credit)}</figcaption>' if credit else ""
        return f"""<figure class="inline-figure">
            <img src="{escape(image)}" alt="{escape(alt)}"{loading}>
            {credit_html}
        </figure>"""

    @staticmethod
    def _render_direct_answer(answer: str, language: str = "en") -> str:
        """Render direct answer box."""
        if not answer:
            return ""
        label = "Kurze Antwort" if language == "de" else "Quick Answer"
        return f"""<div class="direct-answer">
            <span class="da-label">{label}</span>
            {escape(answer)}
        </div>"""

    @staticmethod
    def _render_tldr_compact(article: Dict[str, Any], language: str = "en") -> str:
        """Render 'Das Thema kurz und kompakt' box with ONLY short key takeaways."""
        bullets = []
        for i in range(1, 4):
            t = article.get(f"key_takeaway_{i:02d}", "")
            if t:
                bullets.append(escape(t))
        if not bullets:
            return ""
        label = "Das Thema kurz und kompakt" if language == "de" else "Key Points at a Glance"
        items_html = ''.join(f'<li>{b}</li>' for b in bullets)
        return f"""<div class="tldr">
            <div class="tldr-label">&#9889; {label}</div>
            <ul class="tldr-bullets">{items_html}</ul>
        </div>"""
        if not bullets:
            return ""
        label = "Das Thema kurz und kompakt" if language == "de" else "Key Points at a Glance"
        items_html = ''.join(f'<li>{b}</li>' for b in bullets)
        return f"""<div class="tldr">
            <div class="tldr-label">&#9889; {label}</div>
            <ul class="tldr-bullets">{items_html}</ul>
        </div>"""

    @staticmethod
    def _render_disclaimer(article: Dict[str, Any], language: str = "en") -> str:
        """Render legal disclaimer as styled callout."""
        disclaimer = article.get("legal_disclaimer", "")
        if not disclaimer:
            return ""
        label = "Rechtlicher Hinweis" if language == "de" else "Legal Notice"
        return f"""<aside class="legal-disclaimer">
            <div class="disclaimer-label">&#9878; {label}</div>
            <p>{escape(disclaimer)}</p>
        </aside>"""

    @staticmethod
    def _render_next_steps(
        article: Dict[str, Any],
        company_name: str = "",
        company_url: str = "",
        language: str = "en"
    ) -> str:
        """Render 'Wie geht es weiter?' closing section."""
        # Use CTA text if available, else generate a default
        cta = article.get("cta_text", "")
        if not cta and not company_name:
            return ""
        label = "Wie geht es weiter?" if language == "de" else "What's Next?"
        if cta:
            body = escape(cta)
        elif language == "de":
            body = (f"Haben Sie weitere Fragen zu diesem Thema? "
                    f"Die Experten von {escape(company_name)} beraten Sie gerne persönlich.")
        else:
            body = (f"Have more questions? "
                    f"The experts at {escape(company_name)} are happy to help.")
        link_html = ""
        if company_url:
            link_label = "Kontakt aufnehmen" if language == "de" else "Get in Touch"
            base = escape(company_url.rstrip("/"))
            link_html = f'<a href="{base}/kontakt" class="next-steps-cta">{link_label} &rarr;</a>'
        return f"""<section class="next-steps">
            <h2>{label}</h2>
            <p>{body}</p>
            {link_html}
        </section>"""

    @staticmethod
    def _render_intro(intro: str) -> str:
        """Render intro section with sanitized HTML (preserves <p>, <a>, <strong> etc)."""
        if not intro:
            return ""
        sanitized = HTMLRenderer._sanitize_html(intro)
        # If the intro doesn't already have <p> tags, wrap it
        if '<p>' not in sanitized.lower():
            sanitized = f'<p>{sanitized}</p>'
        return f'<div class="intro">{sanitized}</div>'

    @staticmethod
    def _render_sections(
        article: Dict[str, Any],
        mid_image: str, mid_alt: str, mid_credit: str,
        bottom_image: str, bottom_alt: str, bottom_credit: str
    ) -> str:
        """Render article sections with inline images."""
        parts = []
        section_count = 0

        for i in range(1, 10):
            title = article.get(f"section_{i:02d}_title", "")
            content = article.get(f"section_{i:02d}_content", "")

            if not title and not content:
                continue

            section_count += 1
            anchor = f"section-{i}"
            # Section type label (from decision-centric metadata)
            section_types = article.get("section_types_metadata") or {}
            type_label = ""
            section_key = f"section_{i:02d}"
            stype = section_types.get(section_key, "")
            if stype == "decision_anchor":
                type_label = '<span class="section-type-label label-recht">Rechtsprechung</span>'
            elif stype == "context":
                type_label = '<span class="section-type-label label-gesetz">Gesetz</span>'
            elif stype == "practical_advice":
                type_label = '<span class="section-type-label label-praxis">Praxistipp</span>'
            if title:
                clean_title = HTMLRenderer._strip_html(title)
                number_prefix = f'<span class="section-num">{section_count:02d}</span>'
                parts.append(f'{type_label}<h2 id="{anchor}">{number_prefix}{escape(clean_title)}</h2>')

            if content and content.strip():
                parts.append(HTMLRenderer._sanitize_html(content))

            # Mid-article image after section 3
            if i == 3 and mid_image:
                parts.append(HTMLRenderer._render_inline_image(mid_image, mid_alt, mid_credit))

        # Bottom image after last section
        if bottom_image:
            parts.append(HTMLRenderer._render_inline_image(bottom_image, bottom_alt, bottom_credit))

        return '\n'.join(parts)

    @staticmethod
    def _render_toc(article: Dict[str, Any], language: str = "en") -> str:
        """Render table of contents as numbered list."""
        items = []
        for i in range(1, 10):
            title = article.get(f"section_{i:02d}_title", "")
            if title:
                anchor = f"section-{i}"
                clean_title = HTMLRenderer._strip_html(title)
                items.append(f'<li><a href="#{anchor}">{escape(clean_title)}</a></li>')

        if not items:
            return ""

        label = "Inhaltsverzeichnis" if language == "de" else "Table of Contents"
        return f"""<nav class="toc">
            <h2>{label}</h2>
            <ol>
                {''.join(items)}
            </ol>
        </nav>"""

    @staticmethod
    def _render_takeaways(article: Dict[str, Any], language: str = "en") -> str:
        """Render key takeaways."""
        items = []
        for i in range(1, 4):
            takeaway = article.get(f"key_takeaway_{i:02d}", "")
            if takeaway:
                items.append(f"<li>{escape(takeaway)}</li>")

        if not items:
            return ""

        label = "Das Wichtigste auf einen Blick" if language == "de" else "Key Takeaways"
        return f"""<section class="takeaways">
            <h2>&#9989; {label}</h2>
            <ul>{''.join(items)}</ul>
        </section>"""

    @staticmethod
    def _render_faq(article: Dict[str, Any], language: str = "en") -> str:
        """Render FAQ section as accordion."""
        items = []
        for i in range(1, 7):
            q = article.get(f"faq_{i:02d}_question", "")
            a = article.get(f"faq_{i:02d}_answer", "")
            if q and a:
                items.append(f"""<details class="accordion-item">
                    <summary>{escape(q)}</summary>
                    <div class="accordion-answer">{a}</div>
                </details>""")

        if not items:
            return ""

        label = "Häufig gestellte Fragen" if language == "de" else "Frequently Asked Questions"
        return f"""<section class="faq">
            <h2>{label}</h2>
            {''.join(items)}
        </section>"""

    @staticmethod
    def _render_paa(article: Dict[str, Any], language: str = "en") -> str:
        """Render People Also Ask section as accordion."""
        items = []
        for i in range(1, 5):
            q = article.get(f"paa_{i:02d}_question", "")
            a = article.get(f"paa_{i:02d}_answer", "")
            if q and a:
                items.append(f"""<details class="accordion-item">
                    <summary>{escape(q)}</summary>
                    <div class="accordion-answer">{a}</div>
                </details>""")

        if not items:
            return ""

        label = "Nutzer fragen auch" if language == "de" else "People Also Ask"
        return f"""<section class="paa">
            <h2>{label}</h2>
            {''.join(items)}
        </section>"""

    @staticmethod
    def _render_sources(sources, language: str = "en") -> str:
        """Render sources section. Handles list of {title, url} or string."""
        if not sources:
            return ""

        label = "Quellen" if language == "de" else "Sources"

        # New format: list of Source objects or dicts
        if isinstance(sources, list):
            items = []
            for s in sources:
                if hasattr(s, 'title'):
                    items.append(
                        f'<li><a href="{escape(s.url)}" target="_blank" rel="noopener noreferrer">'
                        f'{escape(s.title)}</a></li>'
                    )
                elif isinstance(s, dict):
                    url = s.get("url") or ""
                    title = s.get("title") or ""
                    if url:
                        items.append(
                            f'<li><a href="{escape(url)}" target="_blank" rel="noopener noreferrer">'
                            f'{escape(title)}</a></li>'
                        )
            if not items:
                return ""
            return f"""<section class="sources">
                <h2>{label}</h2>
                <ol>{''.join(items)}</ol>
            </section>"""

        # Legacy string format
        if not str(sources).strip():
            return ""

        if '<ol>' in sources or '<li>' in sources:
            sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sources, flags=re.IGNORECASE | re.DOTALL)
            sanitized = re.sub(r'<style[^>]*>.*?</style>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
            sanitized = re.sub(r'\s*on\w+\s*=["\'][^"\']*["\']', '', sanitized, flags=re.IGNORECASE)
            sanitized = re.sub(r'\s*on\w+\s*=\S+', '', sanitized, flags=re.IGNORECASE)
            return f"""<section class="sources">
                <h2>{label}</h2>
                {sanitized}
            </section>"""

        lines = str(sources).strip().split('\n')
        items = []
        for line in lines:
            line = line.strip()
            if line:
                items.append(f"<li>{escape(line)}</li>")

        if not items:
            return ""

        return f"""<section class="sources">
            <h2>{label}</h2>
            <ol>{''.join(items)}</ol>
        </section>"""

    @staticmethod
    def _render_tables(tables) -> str:
        """Render comparison tables."""
        if not tables:
            return ""

        parts = []
        for table in tables:
            if hasattr(table, 'title'):
                title = table.title
                headers = table.headers
                rows = table.rows
            else:
                title = table.get('title', '')
                headers = table.get('headers', [])
                rows = table.get('rows', [])

            if not headers or not rows:
                continue

            header_html = ''.join(f'<th>{escape(h)}</th>' for h in headers)
            rows_html = ''
            for row in rows:
                cells = ''.join(f'<td>{escape(str(c))}</td>' for c in row)
                rows_html += f'<tr>{cells}</tr>'

            parts.append(f"""<div class="comparison-table">
                <h3>{escape(title)}</h3>
                <table>
                    <thead><tr>{header_html}</tr></thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>""")

        return '\n'.join(parts)

    @staticmethod
    def _render_schema(
        article: Dict[str, Any],
        headline: str, description: str, author: str,
        company_name: str, company_url: str,
        image: str, pub_date: str, slug: str,
        language: str = "en"
    ) -> str:
        """Render Schema.org JSON-LD structured data."""
        schemas = []

        # 1. Article schema
        article_schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": headline,
            "description": description,
            "author": {
                "@type": "Organization",
                "name": author,
            },
            "publisher": {
                "@type": "Organization",
                "name": company_name or author,
            },
            "datePublished": pub_date,
            "dateModified": pub_date,
            "inLanguage": language,
        }
        if image:
            article_schema["image"] = image
        if company_url and slug:
            article_schema["mainEntityOfPage"] = f"{company_url}/magazine/{slug}"
        if company_url:
            article_schema["publisher"]["url"] = company_url
        schemas.append(article_schema)

        # 2. FAQPage schema
        faq_items = []
        for i in range(1, 7):
            q = article.get(f"faq_{i:02d}_question", "")
            a = article.get(f"faq_{i:02d}_answer", "")
            if q and a:
                faq_items.append({
                    "@type": "Question",
                    "name": q,
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": a,
                    }
                })
        # Also include PAA questions
        for i in range(1, 5):
            q = article.get(f"paa_{i:02d}_question", "")
            a = article.get(f"paa_{i:02d}_answer", "")
            if q and a:
                faq_items.append({
                    "@type": "Question",
                    "name": q,
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": a,
                    }
                })

        if faq_items:
            schemas.append({
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": faq_items,
            })

        # 3. BreadcrumbList schema
        breadcrumb = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "Home" if language != "de" else "Startseite",
                    "item": company_url or "/",
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": "Magazine" if language != "de" else "Magazin",
                    "item": f"{company_url}/magazine/" if company_url else "/magazine/",
                },
                {
                    "@type": "ListItem",
                    "position": 3,
                    "name": headline[:60],
                },
            ]
        }
        schemas.append(breadcrumb)

        # Render all schemas
        parts = []
        for schema in schemas:
            json_str = json.dumps(schema, ensure_ascii=False, indent=2)
            parts.append(f'<script type="application/ld+json">\n{json_str}\n</script>')

        return '\n    '.join(parts)

    @staticmethod
    def _strip_html(text: str) -> str:
        """Strip HTML tags and decode entities."""
        if not text:
            return ""
        clean = re.sub(r'<[^>]+>', '', str(text))
        return unescape(clean).strip()
