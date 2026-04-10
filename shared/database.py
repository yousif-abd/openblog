"""
OpenBlog Neo - SQLite Database Layer

Persistent storage for Beck-Online resources, webinar extracts, and content plan entries.
All modules share this single database file.

Usage:
    from shared.database import OpenBlogDB
    db = OpenBlogDB()
    db.store_beck_resources("Kündigungsschutz", resources)
    enrichment = db.get_enrichment_for_keyword("Kündigungsschutz")
"""

import json
import logging
import os
import re
import sqlite3
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default DB path (relative to project root)
_PROJECT_ROOT = Path(__file__).parent.parent
_DEFAULT_DB_PATH = os.getenv("OPENBLOG_DB_PATH", str(_PROJECT_ROOT / "data" / "openblog.db"))

_SCHEMA_VERSION = 1


def _normalize_keyword(keyword: str) -> str:
    """Normalize keyword for consistent matching (lowercase, strip, NFC unicode)."""
    text = unicodedata.normalize("NFC", keyword.strip().lower())
    return text


class OpenBlogDB:
    """Thread-safe SQLite database for OpenBlog persistent storage."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or _DEFAULT_DB_PATH
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get a new connection (SQLite connections are not thread-safe)."""
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self):
        """Create tables if they don't exist."""
        conn = self._get_conn()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS beck_resources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    keyword_normalized TEXT NOT NULL,
                    rechtsgebiet TEXT NOT NULL DEFAULT '',
                    gericht TEXT DEFAULT '',
                    aktenzeichen TEXT DEFAULT '',
                    datum TEXT DEFAULT '',
                    leitsatz TEXT DEFAULT '',
                    relevante_normen TEXT DEFAULT '[]',
                    url TEXT DEFAULT '',
                    volltext_auszug TEXT DEFAULT '',
                    orientierungssatz TEXT DEFAULT '',
                    kommentar_titel TEXT DEFAULT '',
                    kommentar_auszug TEXT DEFAULT '',
                    relevance_score REAL DEFAULT 0.0,
                    extracted_at TEXT NOT NULL,
                    UNIQUE(keyword_normalized, aktenzeichen)
                );

                CREATE INDEX IF NOT EXISTS idx_beck_keyword
                    ON beck_resources(keyword_normalized);
                CREATE INDEX IF NOT EXISTS idx_beck_rechtsgebiet
                    ON beck_resources(rechtsgebiet);

                CREATE TABLE IF NOT EXISTS webinars (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    drive_file_id TEXT UNIQUE NOT NULL,
                    filename TEXT NOT NULL,
                    title TEXT DEFAULT '',
                    duration_seconds INTEGER DEFAULT 0,
                    transcript TEXT DEFAULT '',
                    summary TEXT DEFAULT '',
                    key_points TEXT DEFAULT '[]',
                    legal_references TEXT DEFAULT '[]',
                    topics TEXT DEFAULT '[]',
                    speaker_names TEXT DEFAULT '[]',
                    rechtsgebiet TEXT DEFAULT '',
                    processed_at TEXT NOT NULL,
                    newsletter_month TEXT DEFAULT ''
                );

                CREATE INDEX IF NOT EXISTS idx_webinar_month
                    ON webinars(newsletter_month);
                CREATE INDEX IF NOT EXISTS idx_webinar_rechtsgebiet
                    ON webinars(rechtsgebiet);

                CREATE TABLE IF NOT EXISTS content_plan (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    keyword TEXT DEFAULT '',
                    keyword_normalized TEXT DEFAULT '',
                    rechtsgebiet TEXT DEFAULT '',
                    target_date TEXT DEFAULT '',
                    priority TEXT DEFAULT '',
                    author TEXT DEFAULT '',
                    word_count INTEGER DEFAULT 2000,
                    notes TEXT DEFAULT '',
                    instructions TEXT DEFAULT '',
                    status TEXT DEFAULT 'planned',
                    imported_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_plan_keyword
                    ON content_plan(keyword_normalized);
                CREATE INDEX IF NOT EXISTS idx_plan_status
                    ON content_plan(status);

                CREATE TABLE IF NOT EXISTS webinar_keyword_links (
                    webinar_id INTEGER REFERENCES webinars(id) ON DELETE CASCADE,
                    keyword_normalized TEXT NOT NULL,
                    relevance_score REAL DEFAULT 0.0,
                    PRIMARY KEY (webinar_id, keyword_normalized)
                );

                CREATE INDEX IF NOT EXISTS idx_wkl_keyword
                    ON webinar_keyword_links(keyword_normalized);

                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER NOT NULL
                );
            """)

            # Set schema version if not set
            row = conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
            if not row:
                conn.execute("INSERT INTO schema_version (version) VALUES (?)", (_SCHEMA_VERSION,))

            conn.commit()
            logger.debug(f"Database initialized: {self.db_path}")
        finally:
            conn.close()

    # =========================================================================
    # Beck Resources
    # =========================================================================

    def store_beck_resources(self, keyword: str, resources: List[Dict[str, Any]]) -> int:
        """
        Store Beck-Online resources linked to a keyword.

        Args:
            keyword: Article keyword/title
            resources: List of CourtDecision-like dicts

        Returns:
            Number of resources stored (new or updated)
        """
        conn = self._get_conn()
        stored = 0
        kw_norm = _normalize_keyword(keyword)
        now = datetime.now(timezone.utc).isoformat()

        try:
            for res in resources:
                normen = res.get("relevante_normen", [])
                if isinstance(normen, list):
                    normen = json.dumps(normen, ensure_ascii=False)

                conn.execute("""
                    INSERT INTO beck_resources (
                        keyword, keyword_normalized, rechtsgebiet,
                        gericht, aktenzeichen, datum, leitsatz,
                        relevante_normen, url, volltext_auszug,
                        orientierungssatz, kommentar_titel, kommentar_auszug,
                        relevance_score, extracted_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(keyword_normalized, aktenzeichen) DO UPDATE SET
                        leitsatz = excluded.leitsatz,
                        volltext_auszug = excluded.volltext_auszug,
                        orientierungssatz = excluded.orientierungssatz,
                        kommentar_titel = excluded.kommentar_titel,
                        kommentar_auszug = excluded.kommentar_auszug,
                        relevance_score = excluded.relevance_score,
                        extracted_at = excluded.extracted_at
                """, (
                    keyword, kw_norm, res.get("rechtsgebiet", ""),
                    res.get("gericht", ""), res.get("aktenzeichen", ""),
                    res.get("datum", ""), res.get("leitsatz", ""),
                    normen, res.get("url", ""),
                    res.get("volltext_auszug", ""),
                    res.get("orientierungssatz", ""),
                    res.get("kommentar_titel", ""),
                    res.get("kommentar_auszug", ""),
                    res.get("relevance_score", 0.0), now,
                ))
                stored += 1

            conn.commit()
            logger.info(f"Stored {stored} Beck resources for keyword: {keyword}")
        finally:
            conn.close()

        return stored

    def get_beck_resources(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Get Beck resources for a keyword (exact match on normalized keyword).

        Returns list of CourtDecision-compatible dicts.
        """
        conn = self._get_conn()
        kw_norm = _normalize_keyword(keyword)

        try:
            rows = conn.execute(
                "SELECT * FROM beck_resources WHERE keyword_normalized = ? ORDER BY relevance_score DESC",
                (kw_norm,)
            ).fetchall()
            return [self._row_to_court_decision(row) for row in rows]
        finally:
            conn.close()

    def get_beck_resources_by_rechtsgebiet(self, rechtsgebiet: str) -> List[Dict[str, Any]]:
        """Get all Beck resources for a legal area."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM beck_resources WHERE rechtsgebiet = ? ORDER BY relevance_score DESC",
                (rechtsgebiet,)
            ).fetchall()
            return [self._row_to_court_decision(row) for row in rows]
        finally:
            conn.close()

    def _get_beck_resources_fuzzy(self, keyword: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Find Beck resources by topic word overlap with stored keywords.

        Uses two strategies:
        1. Multi-word phrase matching: if a 2+ word phrase from the article keyword
           appears in a Beck keyword, it's a strong topical match (score boosted to 5+)
        2. Single-word overlap: counts individual significant words that appear in
           the Beck keyword + leitsatz

        Returns resources with a `_fuzzy_overlap` field indicating match quality.
        """
        # Extract significant words (4+ chars, skip common words)
        skip_words = {"und", "oder", "die", "der", "das", "den", "dem", "des",
                      "ein", "eine", "für", "mit", "von", "bei", "nach", "über",
                      "wie", "was", "sich", "ihre", "sein", "sind", "haben",
                      "werden", "nicht", "auch", "noch", "alle", "kann", "muss",
                      "checkliste", "richtig", "aufsetzen", "tipps", "ratgeber"}
        words = [
            w.lower() for w in re.split(r'[\s:,;!?\-—–]+', keyword)
            if len(w) >= 4 and w.lower() not in skip_words
        ]
        if not words:
            return []

        # Build multi-word phrases from consecutive significant words in keyword
        # e.g. "Berliner Testament" from "Testamentsgestaltung: Ehegattentestament und Berliner Testament"
        keyword_lower = keyword.lower()
        phrases = []
        for i in range(len(words) - 1):
            # Check if these words appear consecutively in the original keyword
            phrase = words[i] + " " + words[i + 1]
            if phrase in keyword_lower or (words[i] + " " + words[i + 1]) in keyword_lower:
                phrases.append(phrase)

        conn = self._get_conn()
        try:
            all_rows = conn.execute(
                "SELECT * FROM beck_resources ORDER BY relevance_score DESC"
            ).fetchall()

            scored = []
            for row in all_rows:
                d = dict(row)
                kw_stored = (d.get("keyword_normalized", "") or "").lower()
                leitsatz = (d.get("leitsatz", "") or "").lower()
                combined_text = kw_stored + " " + leitsatz

                # Strategy 1: phrase match (strong signal — boost to 5+)
                phrase_match = False
                for phrase in phrases:
                    if phrase in kw_stored:
                        phrase_match = True
                        break

                # Strategy 2: word overlap
                overlap = sum(1 for w in words if w in combined_text)

                if phrase_match:
                    # Phrase match = strong topical relevance, boost score
                    score = max(overlap, 5)
                elif overlap >= 2:
                    score = overlap
                else:
                    continue

                scored.append((score, row))

            scored.sort(key=lambda x: x[0], reverse=True)
            results = []
            for overlap_count, row in scored[:max_results]:
                res = self._row_to_court_decision(row)
                res["_fuzzy_overlap"] = overlap_count
                results.append(res)
            return results
        finally:
            conn.close()

    def _row_to_court_decision(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a beck_resources row to a CourtDecision-compatible dict."""
        d = dict(row)
        # Parse JSON fields
        normen = d.get("relevante_normen", "[]")
        if isinstance(normen, str):
            try:
                d["relevante_normen"] = json.loads(normen)
            except json.JSONDecodeError:
                d["relevante_normen"] = []
        # Remove internal fields
        d.pop("id", None)
        d.pop("keyword_normalized", None)
        d.pop("extracted_at", None)
        return d

    # =========================================================================
    # Webinars
    # =========================================================================

    def store_webinar(self, webinar: Dict[str, Any]) -> int:
        """
        Store a processed webinar.

        Args:
            webinar: Dict with drive_file_id, filename, title, transcript, summary,
                     key_points, legal_references, topics, speaker_names, etc.

        Returns:
            Webinar ID
        """
        conn = self._get_conn()
        now = datetime.now(timezone.utc).isoformat()

        # Determine newsletter month from processed date
        month = webinar.get("newsletter_month", "")
        if not month:
            month = now[:7]  # YYYY-MM

        try:
            cursor = conn.execute("""
                INSERT INTO webinars (
                    drive_file_id, filename, title, duration_seconds,
                    transcript, summary, key_points, legal_references,
                    topics, speaker_names, rechtsgebiet, processed_at,
                    newsletter_month
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(drive_file_id) DO UPDATE SET
                    title = excluded.title,
                    transcript = excluded.transcript,
                    summary = excluded.summary,
                    key_points = excluded.key_points,
                    legal_references = excluded.legal_references,
                    topics = excluded.topics,
                    speaker_names = excluded.speaker_names,
                    rechtsgebiet = excluded.rechtsgebiet,
                    processed_at = excluded.processed_at
            """, (
                webinar["drive_file_id"], webinar["filename"],
                webinar.get("title", ""), webinar.get("duration_seconds", 0),
                webinar.get("transcript", ""), webinar.get("summary", ""),
                json.dumps(webinar.get("key_points", []), ensure_ascii=False),
                json.dumps(webinar.get("legal_references", []), ensure_ascii=False),
                json.dumps(webinar.get("topics", []), ensure_ascii=False),
                json.dumps(webinar.get("speaker_names", []), ensure_ascii=False),
                webinar.get("rechtsgebiet", ""), now, month,
            ))
            conn.commit()
            webinar_id = cursor.lastrowid
            logger.info(f"Stored webinar: {webinar.get('title', webinar['filename'])} (id={webinar_id})")
            return webinar_id
        finally:
            conn.close()

    def is_webinar_processed(self, drive_file_id: str) -> bool:
        """Check if a webinar has already been processed."""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT 1 FROM webinars WHERE drive_file_id = ?", (drive_file_id,)
            ).fetchone()
            return row is not None
        finally:
            conn.close()

    def get_webinars_for_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Get webinars linked to a keyword via webinar_keyword_links.

        Falls back to topic-based matching if no exact keyword link exists:
        extracts significant words from the article keyword and matches
        against webinar topics and linked keywords.

        Returns list of webinar dicts with summary, key_points, legal_references.
        """
        conn = self._get_conn()
        kw_norm = _normalize_keyword(keyword)

        try:
            # Strategy 1: exact keyword link
            rows = conn.execute("""
                SELECT w.* FROM webinars w
                JOIN webinar_keyword_links wkl ON w.id = wkl.webinar_id
                WHERE wkl.keyword_normalized = ?
                ORDER BY wkl.relevance_score DESC
            """, (kw_norm,)).fetchall()

            if rows:
                return [self._row_to_webinar(row) for row in rows]

            # Strategy 2: match by webinar title using phrase + distinctive word matching
            # This avoids cross-contamination from generic topic words like "Testament"
            skip = {"und", "oder", "die", "der", "das", "den", "für", "mit",
                    "von", "wie", "was", "sich", "richtig", "aufsetzen", "tipps",
                    "checkliste", "ratgeber", "muss", "drinstehen"}
            kw_words = [
                w.lower() for w in re.split(r'[\s:,;!?\-—–]+', keyword)
                if len(w) >= 4 and w.lower() not in skip
            ]
            if not kw_words:
                return []

            # Build multi-word phrases from consecutive significant words
            keyword_lower = keyword.lower()
            phrases = []
            for i in range(len(kw_words) - 1):
                phrase = kw_words[i] + " " + kw_words[i + 1]
                if phrase in keyword_lower:
                    phrases.append(phrase)

            # Distinctive words: long words (≥8 chars) are topic-specific
            distinctive_words = {w for w in kw_words if len(w) >= 8}

            all_webinars = conn.execute("SELECT * FROM webinars").fetchall()
            matched = []
            seen_ids = set()
            for w_row in all_webinars:
                w = dict(w_row)
                w_id = w["id"]
                if w_id in seen_ids:
                    continue

                w_title_lower = (w.get("title") or "").lower()
                score = 0

                # Phrase match against title (strong signal — score 3)
                for phrase in phrases:
                    if phrase in w_title_lower:
                        score += 3
                        break

                # Distinctive word match against title (score 2 per match)
                for dw in distinctive_words:
                    if dw in w_title_lower:
                        score += 2

                if score >= 2:
                    matched.append((score, w_row))
                    seen_ids.add(w_id)

            if matched:
                matched.sort(key=lambda x: x[0], reverse=True)
                logger.info(f"Found {len(matched)} webinars via title matching for '{keyword[:50]}'")
                return [self._row_to_webinar(row) for _, row in matched]

            return []
        finally:
            conn.close()

    def get_webinars_by_topic(self, topic: str) -> List[Dict[str, Any]]:
        """Get webinars whose topics JSON array contains the given topic (case-insensitive)."""
        conn = self._get_conn()
        try:
            # SQLite LIKE for JSON array search
            rows = conn.execute(
                "SELECT * FROM webinars WHERE LOWER(topics) LIKE ? ORDER BY processed_at DESC",
                (f'%{topic.lower()}%',)
            ).fetchall()
            return [self._row_to_webinar(row) for row in rows]
        finally:
            conn.close()

    def get_webinars_for_newsletter(self, month: str) -> List[Dict[str, Any]]:
        """
        Get webinars for a specific newsletter month.

        Args:
            month: Format "YYYY-MM" (e.g., "2026-03")
        """
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM webinars WHERE newsletter_month = ? ORDER BY processed_at ASC",
                (month,)
            ).fetchall()
            return [self._row_to_webinar(row) for row in rows]
        finally:
            conn.close()

    def get_all_webinars(self) -> List[Dict[str, Any]]:
        """Get all processed webinars."""
        conn = self._get_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM webinars ORDER BY processed_at DESC"
            ).fetchall()
            return [self._row_to_webinar(row) for row in rows]
        finally:
            conn.close()

    def _row_to_webinar(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a webinars row to a dict with parsed JSON fields."""
        d = dict(row)
        for field in ("key_points", "legal_references", "topics", "speaker_names"):
            val = d.get(field, "[]")
            if isinstance(val, str):
                try:
                    d[field] = json.loads(val)
                except json.JSONDecodeError:
                    d[field] = []
        return d

    # =========================================================================
    # Webinar-Keyword Links
    # =========================================================================

    def link_webinar_to_keyword(self, webinar_id: int, keyword: str, relevance_score: float = 1.0):
        """Link a webinar to a keyword for pipeline enrichment."""
        conn = self._get_conn()
        kw_norm = _normalize_keyword(keyword)
        try:
            conn.execute("""
                INSERT INTO webinar_keyword_links (webinar_id, keyword_normalized, relevance_score)
                VALUES (?, ?, ?)
                ON CONFLICT(webinar_id, keyword_normalized) DO UPDATE SET
                    relevance_score = excluded.relevance_score
            """, (webinar_id, kw_norm, relevance_score))
            conn.commit()
        finally:
            conn.close()

    def auto_link_webinars_to_keywords(self):
        """
        Auto-link webinars to content plan keywords based on topic overlap.

        Matches webinar topics against content plan keywords (normalized).
        """
        conn = self._get_conn()
        try:
            webinars = conn.execute("SELECT id, topics, rechtsgebiet FROM webinars").fetchall()
            plan_entries = conn.execute(
                "SELECT keyword_normalized, rechtsgebiet FROM content_plan WHERE keyword_normalized != ''"
            ).fetchall()

            linked = 0
            for webinar in webinars:
                topics = json.loads(webinar["topics"]) if webinar["topics"] else []
                topics_lower = [t.lower() for t in topics]
                w_rechtsgebiet = (webinar["rechtsgebiet"] or "").lower()

                for entry in plan_entries:
                    kw_norm = entry["keyword_normalized"]
                    e_rechtsgebiet = (entry["rechtsgebiet"] or "").lower()

                    # Match if any topic contains the keyword or vice versa
                    score = 0.0
                    for topic in topics_lower:
                        if kw_norm in topic or topic in kw_norm:
                            score = max(score, 0.8)
                        # Boost if same rechtsgebiet
                        if w_rechtsgebiet and e_rechtsgebiet and w_rechtsgebiet == e_rechtsgebiet:
                            score = min(score + 0.2, 1.0)

                    if score > 0:
                        conn.execute("""
                            INSERT INTO webinar_keyword_links (webinar_id, keyword_normalized, relevance_score)
                            VALUES (?, ?, ?)
                            ON CONFLICT(webinar_id, keyword_normalized) DO UPDATE SET
                                relevance_score = MAX(excluded.relevance_score, webinar_keyword_links.relevance_score)
                        """, (webinar["id"], kw_norm, score))
                        linked += 1

            conn.commit()
            logger.info(f"Auto-linked {linked} webinar-keyword pairs")
            return linked
        finally:
            conn.close()

    # =========================================================================
    # Content Plan
    # =========================================================================

    def import_content_plan(self, entries: List[Dict[str, Any]]) -> int:
        """
        Import content plan entries. Updates existing entries with same keyword.

        Args:
            entries: List of dicts with title, keyword, rechtsgebiet, etc.

        Returns:
            Number of entries imported
        """
        conn = self._get_conn()
        now = datetime.now(timezone.utc).isoformat()
        imported = 0

        try:
            for entry in entries:
                keyword = entry.get("keyword", "") or entry.get("title", "")
                kw_norm = _normalize_keyword(keyword) if keyword else ""

                conn.execute("""
                    INSERT INTO content_plan (
                        title, keyword, keyword_normalized, rechtsgebiet,
                        target_date, priority, author, word_count,
                        notes, instructions, status, imported_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.get("title", ""), keyword, kw_norm,
                    entry.get("rechtsgebiet", ""),
                    entry.get("target_date", ""),
                    entry.get("priority", ""),
                    entry.get("author", ""),
                    entry.get("word_count", 2000),
                    entry.get("notes", ""),
                    entry.get("instructions", ""),
                    entry.get("status", "planned"), now,
                ))
                imported += 1

            conn.commit()
            logger.info(f"Imported {imported} content plan entries")
        finally:
            conn.close()

        return imported

    def get_content_plan(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get content plan entries, optionally filtered by status."""
        conn = self._get_conn()
        try:
            if status:
                rows = conn.execute(
                    "SELECT * FROM content_plan WHERE status = ? ORDER BY target_date ASC, priority ASC",
                    (status,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM content_plan ORDER BY target_date ASC, priority ASC"
                ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_plan_entry(self, keyword: str) -> Optional[Dict[str, Any]]:
        """Get a single content plan entry by keyword."""
        conn = self._get_conn()
        kw_norm = _normalize_keyword(keyword)
        try:
            row = conn.execute(
                "SELECT * FROM content_plan WHERE keyword_normalized = ? LIMIT 1",
                (kw_norm,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def update_plan_status(self, keyword: str, status: str):
        """Update status of a content plan entry."""
        conn = self._get_conn()
        kw_norm = _normalize_keyword(keyword)
        try:
            conn.execute(
                "UPDATE content_plan SET status = ? WHERE keyword_normalized = ?",
                (status, kw_norm)
            )
            conn.commit()
        finally:
            conn.close()

    def update_plan_instructions(self, keyword: str, instructions: str):
        """Update instructions for a content plan entry."""
        conn = self._get_conn()
        kw_norm = _normalize_keyword(keyword)
        try:
            conn.execute(
                "UPDATE content_plan SET instructions = ? WHERE keyword_normalized = ?",
                (instructions, kw_norm)
            )
            conn.commit()
        finally:
            conn.close()

    # =========================================================================
    # Enrichment (used by pipeline)
    # =========================================================================

    def get_enrichment_for_keyword(self, keyword: str, rechtsgebiet: str = "") -> Dict[str, Any]:
        """
        Get all stored enrichment data for a keyword.

        Falls back to rechtsgebiet-based Beck lookup when exact keyword match
        returns no results, ensuring legal articles always have court decisions.

        Returns:
            {
                "beck_resources": List[dict],  # CourtDecision-compatible
                "webinar_content": List[dict],  # Webinar summaries + key points + transcript segments
            }
        """
        beck = self.get_beck_resources(keyword)

        # Fallback 1: try fuzzy keyword match (more targeted than rechtsgebiet)
        if not beck:
            beck = self._get_beck_resources_fuzzy(keyword)
            if beck:
                logger.info(
                    f"Found {len(beck)} Beck resources via fuzzy keyword match "
                    f"(overlaps: {[r.get('_fuzzy_overlap', '?') for r in beck]})"
                )

        # Fallback 2: search by rechtsgebiet (broader, cap at 5 most relevant)
        # Mark these as rechtsgebiet-only matches so the pipeline can decide
        if not beck and rechtsgebiet:
            beck = self.get_beck_resources_by_rechtsgebiet(rechtsgebiet)[:5]
            if beck:
                for r in beck:
                    r["_match_type"] = "rechtsgebiet_only"
                logger.info(
                    f"No Beck resources for exact keyword, "
                    f"using {len(beck)} from rechtsgebiet '{rechtsgebiet}' "
                    f"(rechtsgebiet-only match — may not be topically relevant)"
                )

        webinars = self.get_webinars_for_keyword(keyword)

        # For webinars, return content relevant for article generation
        # INCLUDING relevant transcript segments with actual quotes and examples
        webinar_content = []
        for w in webinars:
            transcript = w.get("transcript", "")
            topics = w.get("topics", [])
            key_points = w.get("key_points", [])

            # Extract relevant transcript segments for this keyword
            segments = _extract_transcript_segments(
                transcript=transcript,
                keyword=keyword,
                topics=topics,
                max_segments=4,
                max_total_chars=5000,
            )

            webinar_content.append({
                "title": w.get("title", ""),
                "summary": w.get("summary", ""),
                "key_points": key_points,
                "legal_references": w.get("legal_references", []),
                "topics": topics,
                "rechtsgebiet": w.get("rechtsgebiet", ""),
                "transcript_segments": segments,
            })

        return {
            "beck_resources": beck,
            "webinar_content": webinar_content,
        }


def _extract_transcript_segments(
    transcript: str,
    keyword: str,
    topics: List[str],
    max_segments: int = 6,
    max_total_chars: int = 8000,
) -> List[str]:
    """
    Extract the most relevant transcript passages for a given keyword.

    Splits transcript at speaker turns, scores each segment by keyword/topic
    relevance, and returns the top segments as actual quotable text.

    Args:
        transcript: Full webinar transcript text
        keyword: The article keyword to match against
        topics: Webinar topics list for broader matching
        max_segments: Maximum number of segments to return
        max_total_chars: Maximum total characters across all segments

    Returns:
        List of transcript passage strings, ordered by relevance
    """
    if not transcript or len(transcript) < 100:
        return []

    # Split at speaker turns (e.g. "Sprecher 1:", "Moderatorin:")
    raw_segments = re.split(r'(?=(?:Sprecher \d+|Moderator(?:in)?):)', transcript)

    # Further split very long segments (~2000 char chunks at sentence boundaries)
    chunks: List[str] = []
    for seg in raw_segments:
        seg = seg.strip()
        if not seg:
            continue
        if len(seg) <= 2500:
            chunks.append(seg)
        else:
            # Split at sentence boundaries within the segment
            sentences = re.split(r'(?<=[.!?])\s+', seg)
            current_chunk = ""
            for sent in sentences:
                if len(current_chunk) + len(sent) > 2000 and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sent
                else:
                    current_chunk = current_chunk + " " + sent if current_chunk else sent
            if current_chunk.strip():
                chunks.append(current_chunk.strip())

    if not chunks:
        return []

    # Build search terms from keyword and topics
    # e.g. "Testamente unter Ehegatten richtig gemacht: Typische Irrtümer" →
    #       ["testamente", "ehegatten", "irrtümer", "testament", "ehegatte"]
    search_terms = set()
    for word in re.split(r'[\s:,;!?\-—–]+', keyword.lower()):
        if len(word) >= 4:  # skip short words like "und", "die", "das"
            search_terms.add(word)
            # Add stem-like variants (remove common German suffixes)
            for suffix in ("en", "er", "es", "em", "ung", "keit", "heit", "isch", "liche"):
                if word.endswith(suffix) and len(word) - len(suffix) >= 3:
                    search_terms.add(word[:-len(suffix)])
    for topic in topics:
        for word in topic.lower().split():
            if len(word) >= 4:
                search_terms.add(word)

    # Score each chunk by how many search terms appear
    scored: List[tuple] = []
    for chunk in chunks:
        chunk_lower = chunk.lower()
        score = 0
        for term in search_terms:
            count = chunk_lower.count(term)
            if count > 0:
                score += count
        # Bonus for chunks with concrete examples (numbers, §, case references)
        if re.search(r'§\s*\d+', chunk):
            score += 2
        if re.search(r'\d+\.?\d*\s*(?:Euro|EUR|Prozent|%)', chunk):
            score += 2
        if any(w in chunk_lower for w in ("beispiel", "fall", "mandant", "praxis", "erfahrung")):
            score += 3
        # Skip very short or moderator-only chunks
        if len(chunk) < 80 or score == 0:
            continue
        scored.append((score, chunk))

    # Sort by score descending, take top N
    scored.sort(key=lambda x: x[0], reverse=True)

    result: List[str] = []
    total_chars = 0
    for _score, chunk in scored[:max_segments * 2]:  # overfetch then trim by char limit
        if len(result) >= max_segments:
            break
        if total_chars + len(chunk) > max_total_chars:
            continue
        result.append(chunk)
        total_chars += len(chunk)

    logger.info(f"Extracted {len(result)} transcript segments ({total_chars} chars) for '{keyword[:50]}'")
    return result
