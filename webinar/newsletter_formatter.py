"""
Newsletter Formatter

Formats webinar summaries for monthly newsletter output.
Produces both HTML snippets and plain text.
"""

import logging
from typing import Dict, List, Optional

from shared.database import OpenBlogDB

logger = logging.getLogger(__name__)


class NewsletterFormatter:
    """Format webinar data for newsletter inclusion."""

    def __init__(self, db: Optional[OpenBlogDB] = None):
        self.db = db or OpenBlogDB()

    def format_monthly(self, month: str) -> Dict:
        """
        Generate newsletter content for a specific month.

        Args:
            month: Format "YYYY-MM" (e.g., "2026-03")

        Returns:
            Dict with month, webinars list, html_snippet, plain_text
        """
        webinars = self.db.get_webinars_for_newsletter(month)

        if not webinars:
            return {
                "month": month,
                "webinars": [],
                "html_snippet": "",
                "plain_text": f"Keine Webinare im {month}.",
            }

        formatted_webinars = []
        for w in webinars:
            duration_min = (w.get("duration_seconds", 0) or 0) // 60
            formatted_webinars.append({
                "title": w.get("title", w.get("filename", "")),
                "summary": w.get("summary", ""),
                "key_points": w.get("key_points", []),
                "duration": f"{duration_min} Min." if duration_min else "",
                "rechtsgebiet": w.get("rechtsgebiet", ""),
                "speaker_names": w.get("speaker_names", []),
                "practical_tips": w.get("practical_tips", []) if "practical_tips" in w else [],
            })

        html = self._render_html(month, formatted_webinars)
        text = self._render_text(month, formatted_webinars)

        return {
            "month": month,
            "webinars": formatted_webinars,
            "html_snippet": html,
            "plain_text": text,
        }

    def _render_html(self, month: str, webinars: List[Dict]) -> str:
        """Render newsletter HTML snippet."""
        parts = [
            f'<div class="newsletter-webinars">',
            f'<h2>Webinar-Zusammenfassungen {month}</h2>',
        ]

        for w in webinars:
            parts.append('<div class="webinar-summary" style="margin-bottom: 24px;">')
            parts.append(f'<h3>{_escape(w["title"])}</h3>')

            if w.get("duration") or w.get("rechtsgebiet"):
                meta_parts = []
                if w.get("rechtsgebiet"):
                    meta_parts.append(w["rechtsgebiet"])
                if w.get("duration"):
                    meta_parts.append(w["duration"])
                if w.get("speaker_names"):
                    meta_parts.append(", ".join(w["speaker_names"]))
                parts.append(f'<p style="color: #666; font-size: 14px;">{" | ".join(meta_parts)}</p>')

            if w.get("summary"):
                parts.append(f'<p>{_escape(w["summary"])}</p>')

            if w.get("key_points"):
                parts.append("<h4>Wichtigste Erkenntnisse:</h4>")
                parts.append("<ul>")
                for kp in w["key_points"][:5]:  # Limit to 5 for newsletter
                    parts.append(f"<li>{_escape(kp)}</li>")
                parts.append("</ul>")

            if w.get("practical_tips"):
                parts.append("<h4>Praxistipps:</h4>")
                parts.append("<ul>")
                for tip in w["practical_tips"][:3]:
                    parts.append(f"<li>{_escape(tip)}</li>")
                parts.append("</ul>")

            parts.append("</div>")

        parts.append("</div>")
        return "\n".join(parts)

    def _render_text(self, month: str, webinars: List[Dict]) -> str:
        """Render newsletter plain text."""
        lines = [
            f"Webinar-Zusammenfassungen {month}",
            "=" * 40,
            "",
        ]

        for w in webinars:
            lines.append(f"## {w['title']}")

            meta_parts = []
            if w.get("rechtsgebiet"):
                meta_parts.append(w["rechtsgebiet"])
            if w.get("duration"):
                meta_parts.append(w["duration"])
            if meta_parts:
                lines.append(f"   {' | '.join(meta_parts)}")

            lines.append("")

            if w.get("summary"):
                lines.append(w["summary"])
                lines.append("")

            if w.get("key_points"):
                lines.append("Wichtigste Erkenntnisse:")
                for kp in w["key_points"][:5]:
                    lines.append(f"  - {kp}")
                lines.append("")

            if w.get("practical_tips"):
                lines.append("Praxistipps:")
                for tip in w["practical_tips"][:3]:
                    lines.append(f"  - {tip}")
                lines.append("")

            lines.append("-" * 40)
            lines.append("")

        return "\n".join(lines)


def _escape(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
