"""
Mock German legal data generator for development and testing.

Generates realistic court decisions for common legal scenarios in various Rechtsgebiete.
Used when beck-online.beck.de credentials are not available or when testing.
"""

from datetime import datetime, timedelta
import random
import sys
from pathlib import Path
from typing import List

# Add stage1 to path for imports
stage1_path = Path(__file__).parent
if str(stage1_path) not in sys.path:
    sys.path.insert(0, str(stage1_path))

from legal_models import CourtDecision, LegalContext


# Mock court decision database by Rechtsgebiet
MOCK_DECISIONS = {
    "Arbeitsrecht": [
        {
            "gericht": "BAG",
            "aktenzeichen": "6 AZR 148/22",
            "datum_offset_days": 180,
            "leitsatz": "Die Kündigung eines Arbeitsverhältnisses bedarf zu ihrer Wirksamkeit der Schriftform (§ 623 BGB). Eine mündliche Kündigung ist unwirksam.",
            "relevante_normen": ["§ 623 BGB"],
            "url": "https://www.beck-online.beck.de/Dokument/mock-bag-6-azr-148-22"
        },
        {
            "gericht": "BAG",
            "aktenzeichen": "2 AZR 235/23",
            "datum_offset_days": 120,
            "leitsatz": "Eine außerordentliche Kündigung nach § 626 BGB setzt einen wichtigen Grund voraus. Die Pflichtverletzung muss so schwerwiegend sein, dass eine Fortsetzung des Arbeitsverhältnisses unzumutbar ist.",
            "relevante_normen": ["§ 626 BGB", "§ 626 Abs. 1 BGB"],
            "url": "https://www.beck-online.beck.de/Dokument/mock-bag-2-azr-235-23"
        },
        {
            "gericht": "BAG",
            "aktenzeichen": "9 AZR 89/23",
            "datum_offset_days": 90,
            "leitsatz": "Der Arbeitnehmer hat bei Beendigung des Arbeitsverhältnisses Anspruch auf ein schriftliches Zeugnis (§ 109 GewO). Das Zeugnis muss klar und verständlich formuliert sein.",
            "relevante_normen": ["§ 109 GewO", "§ 109 Abs. 1 GewO"],
            "url": "https://www.beck-online.beck.de/Dokument/mock-bag-9-azr-89-23"
        },
        {
            "gericht": "BAG",
            "aktenzeichen": "5 AZR 505/22",
            "datum_offset_days": 200,
            "leitsatz": "Die Kündigungsfrist richtet sich nach § 622 BGB. Bei einer Beschäftigungsdauer von mehr als zwei Jahren beträgt die Kündigungsfrist für den Arbeitgeber mindestens einen Monat zum Monatsende.",
            "relevante_normen": ["§ 622 BGB", "§ 622 Abs. 2 BGB"],
            "url": "https://www.beck-online.beck.de/Dokument/mock-bag-5-azr-505-22"
        },
        {
            "gericht": "LAG Berlin-Brandenburg",
            "aktenzeichen": "7 Sa 1456/23",
            "datum_offset_days": 60,
            "leitsatz": "Eine Kündigung ist gemäß § 1 KSchG sozial ungerechtfertigt, wenn sie nicht durch Gründe in der Person oder dem Verhalten des Arbeitnehmers oder durch dringende betriebliche Erfordernisse bedingt ist.",
            "relevante_normen": ["§ 1 KSchG", "§ 1 Abs. 2 KSchG"],
            "url": "https://www.beck-online.beck.de/Dokument/mock-lag-berlin-7-sa-1456-23"
        },
        {
            "gericht": "BAG",
            "aktenzeichen": "10 AZR 678/22",
            "datum_offset_days": 150,
            "leitsatz": "Der gesetzliche Mindesturlaubsanspruch beträgt nach § 3 BUrlG 24 Werktage bei einer Sechs-Tage-Woche. Der Urlaubsanspruch kann nicht durch Vertrag unterschritten werden.",
            "relevante_normen": ["§ 1 BUrlG", "§ 3 BUrlG", "§ 13 BUrlG"],
            "url": "https://www.beck-online.beck.de/Dokument/mock-bag-10-azr-678-22"
        }
    ],
    "Mietrecht": [
        {
            "gericht": "BGH",
            "aktenzeichen": "VIII ZR 118/22",
            "datum_offset_days": 100,
            "leitsatz": "Die Kündigung eines Mietverhältnisses wegen Eigenbedarfs nach § 573 Abs. 2 Nr. 2 BGB setzt ein berechtigtes Interesse des Vermieters voraus. Der Eigenbedarf muss konkret und nachvollziehbar dargelegt werden.",
            "relevante_normen": ["§ 573 BGB", "§ 573 Abs. 2 Nr. 2 BGB"],
            "url": "https://www.beck-online.beck.de/Dokument/mock-bgh-viii-zr-118-22"
        },
        {
            "gericht": "BGH",
            "aktenzeichen": "VIII ZR 247/21",
            "datum_offset_days": 250,
            "leitsatz": "Die Betriebskostenabrechnung muss nach § 556 Abs. 3 BGB spätestens bis zum Ablauf des zwölften Monats nach Ende des Abrechnungszeitraums erteilt werden. Eine verspätete Abrechnung ist unwirksam.",
            "relevante_normen": ["§ 556 BGB", "§ 556 Abs. 3 BGB"],
            "url": "https://www.beck-online.beck.de/Dokument/mock-bgh-viii-zr-247-21"
        },
        {
            "gericht": "LG Berlin",
            "aktenzeichen": "67 S 245/23",
            "datum_offset_days": 45,
            "leitsatz": "Bei erheblichen Mängeln der Mietsache steht dem Mieter nach § 536 BGB ein Minderungsrecht zu. Die Minderung tritt kraft Gesetzes ein, ohne dass es einer Minderungserklärung bedarf.",
            "relevante_normen": ["§ 536 BGB", "§ 536 Abs. 1 BGB"],
            "url": "https://www.beck-online.beck.de/Dokument/mock-lg-berlin-67-s-245-23"
        },
        {
            "gericht": "BGH",
            "aktenzeichen": "VIII ZR 381/22",
            "datum_offset_days": 130,
            "leitsatz": "Eine Mieterhöhung nach § 558 BGB ist nur bis zur ortsüblichen Vergleichsmiete zulässig. Die Zustimmung des Mieters ist erforderlich, wenn die Miete innerhalb der letzten drei Jahre nicht bereits um mehr als 20 % erhöht wurde.",
            "relevante_normen": ["§ 558 BGB", "§ 558 Abs. 1 BGB", "§ 558 Abs. 3 BGB"],
            "url": "https://www.beck-online.beck.de/Dokument/mock-bgh-viii-zr-381-22"
        }
    ],
    "Vertragsrecht": [
        {
            "gericht": "BGH",
            "aktenzeichen": "II ZR 65/22",
            "datum_offset_days": 160,
            "leitsatz": "Ein Vertragsschluss kommt nach §§ 145 ff. BGB durch Angebot und Annahme zustande. Das Angebot muss alle wesentlichen Vertragsbestandteile (essentialia negotii) enthalten.",
            "relevante_normen": ["§ 145 BGB", "§ 147 BGB", "§ 150 BGB"],
            "url": "https://www.beck-online.beck.de/Dokument/mock-bgh-ii-zr-65-22"
        },
        {
            "gericht": "BGH",
            "aktenzeichen": "VII ZR 156/21",
            "datum_offset_days": 290,
            "leitsatz": "Allgemeine Geschäftsbedingungen (AGB) unterliegen der Inhaltskontrolle nach §§ 307 ff. BGB. Überraschende und mehrdeutige Klauseln sind unwirksam.",
            "relevante_normen": ["§ 305 BGB", "§ 307 BGB", "§ 308 BGB", "§ 309 BGB"],
            "url": "https://www.beck-online.beck.de/Dokument/mock-bgh-vii-zr-156-21"
        },
        {
            "gericht": "OLG München",
            "aktenzeichen": "7 U 3456/23",
            "datum_offset_days": 75,
            "leitsatz": "Der Käufer kann bei Mängeln der Kaufsache nach § 437 BGB Nacherfüllung verlangen, vom Vertrag zurücktreten, den Kaufpreis mindern oder Schadensersatz fordern.",
            "relevante_normen": ["§ 433 BGB", "§ 434 BGB", "§ 437 BGB", "§ 439 BGB"],
            "url": "https://www.beck-online.beck.de/Dokument/mock-olg-muenchen-7-u-3456-23"
        }
    ],
    "Familienrecht": [
        {
            "gericht": "BGH",
            "aktenzeichen": "XII ZB 234/22",
            "datum_offset_days": 110,
            "leitsatz": "Bei der Bemessung des Kindesunterhalts ist die Düsseldorfer Tabelle als Orientierungshilfe heranzuziehen. Das unterhaltsrelevante Einkommen ist nach § 1610 BGB zu ermitteln.",
            "relevante_normen": ["§ 1601 BGB", "§ 1610 BGB", "§ 1612 BGB"],
            "url": "https://www.beck-online.beck.de/Dokument/mock-bgh-xii-zb-234-22"
        },
        {
            "gericht": "OLG Frankfurt",
            "aktenzeichen": "4 UF 189/23",
            "datum_offset_days": 50,
            "leitsatz": "Bei der Regelung des Umgangsrechts nach § 1684 BGB ist das Kindeswohl maßgeblich. Das Kind hat ein Recht auf Umgang mit beiden Elternteilen.",
            "relevante_normen": ["§ 1684 BGB", "§ 1684 Abs. 1 BGB"],
            "url": "https://www.beck-online.beck.de/Dokument/mock-olg-frankfurt-4-uf-189-23"
        }
    ],
    "Erbrecht": [
        {
            "gericht": "OLG Köln",
            "aktenzeichen": "2 Wx 456/22",
            "datum_offset_days": 140,
            "leitsatz": "Ein eigenhändiges Testament muss nach § 2247 BGB vollständig handschriftlich verfasst und unterschrieben sein. Maschinengeschriebene Testamente sind formnichtig.",
            "relevante_normen": ["§ 2247 BGB", "§ 2247 Abs. 1 BGB"],
            "url": "https://www.beck-online.beck.de/Dokument/mock-olg-koeln-2-wx-456-22"
        },
        {
            "gericht": "BGH",
            "aktenzeichen": "IV ZR 67/22",
            "datum_offset_days": 210,
            "leitsatz": "Der Pflichtteilsanspruch nach § 2303 BGB beträgt die Hälfte des Wertes des gesetzlichen Erbteils. Der Pflichtteilsberechtigte kann von den Erben Auskunft über den Nachlass verlangen.",
            "relevante_normen": ["§ 2303 BGB", "§ 2303 Abs. 1 BGB", "§ 2314 BGB"],
            "url": "https://www.beck-online.beck.de/Dokument/mock-bgh-iv-zr-67-22"
        }
    ]
}


# German legal disclaimer templates by Rechtsgebiet
DISCLAIMER_TEMPLATES = {
    "Arbeitsrecht": """Rechtlicher Hinweis: Dieser Artikel dient ausschließlich der allgemeinen Information und stellt keine Rechtsberatung dar. Die rechtliche Beurteilung arbeitsrechtlicher Sachverhalte hängt immer von den konkreten Umständen des Einzelfalls ab. Für eine individuelle rechtliche Beratung zu Ihrer arbeitsrechtlichen Situation wenden Sie sich bitte an einen Fachanwalt für Arbeitsrecht.""",

    "Mietrecht": """Rechtlicher Hinweis: Dieser Artikel dient ausschließlich der allgemeinen Information und stellt keine Rechtsberatung dar. Die rechtliche Beurteilung mietrechtlicher Fragen ist stark einzelfallabhängig. Für eine verbindliche rechtliche Einschätzung Ihrer mietrechtlichen Angelegenheit kontaktieren Sie bitte einen Fachanwalt für Miet- und Wohnungseigentumsrecht.""",

    "Vertragsrecht": """Rechtlicher Hinweis: Dieser Artikel dient ausschließlich der allgemeinen Information und stellt keine Rechtsberatung dar. Die vertragsrechtliche Bewertung hängt von den spezifischen Vertragsgestaltungen und Umständen ab. Für eine individuelle rechtliche Prüfung Ihrer Verträge wenden Sie sich bitte an einen Rechtsanwalt.""",

    "Familienrecht": """Rechtlicher Hinweis: Dieser Artikel dient ausschließlich der allgemeinen Information und stellt keine Rechtsberatung dar. Familienrechtliche Angelegenheiten erfordern eine individuelle Beratung unter Berücksichtigung aller persönlichen Umstände. Für eine rechtliche Beratung zu Ihrer familienrechtlichen Situation kontaktieren Sie bitte einen Fachanwalt für Familienrecht.""",

    "Erbrecht": """Rechtlicher Hinweis: Dieser Artikel dient ausschließlich der allgemeinen Information und stellt keine Rechtsberatung dar. Erbrechtliche Gestaltungen müssen immer unter Berücksichtigung der konkreten Vermögens- und Familienverhältnisse erfolgen. Für eine individuelle erbrechtliche Beratung wenden Sie sich bitte an einen Fachanwalt für Erbrecht."""
}


def _calculate_decision_date(offset_days: int) -> str:
    """
    Calculate decision date relative to today.

    Args:
        offset_days: Days in the past from today

    Returns:
        ISO date string (YYYY-MM-DD)
    """
    decision_date = datetime.now() - timedelta(days=offset_days)
    return decision_date.strftime("%Y-%m-%d")


def _select_decisions_for_keywords(
    keywords: List[str],
    rechtsgebiet: str,
    decisions_per_keyword: int = 2
) -> List[CourtDecision]:
    """
    Select relevant mock decisions for keywords.

    Args:
        keywords: List of article keywords
        rechtsgebiet: Legal area
        decisions_per_keyword: How many decisions per keyword

    Returns:
        List of CourtDecision objects
    """
    available_decisions = MOCK_DECISIONS.get(rechtsgebiet, MOCK_DECISIONS.get("Arbeitsrecht", []))

    if not available_decisions:
        available_decisions = MOCK_DECISIONS["Arbeitsrecht"]  # Fallback

    # Select decisions (round-robin to ensure variety)
    selected = []
    num_to_select = min(len(keywords) * decisions_per_keyword, len(available_decisions))

    for i in range(num_to_select):
        decision_template = available_decisions[i % len(available_decisions)]

        selected.append(CourtDecision(
            gericht=decision_template["gericht"],
            aktenzeichen=decision_template["aktenzeichen"],
            datum=_calculate_decision_date(decision_template["datum_offset_days"]),
            leitsatz=decision_template["leitsatz"],
            relevante_normen=decision_template["relevante_normen"],
            url=decision_template["url"],
            rechtsgebiet=rechtsgebiet
        ))

    return selected


async def generate_mock_legal_context(
    keywords: List[str],
    rechtsgebiet: str = "Arbeitsrecht"
) -> LegalContext:
    """
    Generate realistic mock German legal data for development/testing.

    Args:
        keywords: List of keywords for article generation
        rechtsgebiet: German legal area (Arbeitsrecht, Mietrecht, etc.)

    Returns:
        LegalContext with 3-8 mock court decisions

    Example:
        >>> context = await generate_mock_legal_context(
        ...     keywords=["Kündigung", "Kündigungsschutz"],
        ...     rechtsgebiet="Arbeitsrecht"
        ... )
        >>> len(context.court_decisions)
        4
    """
    # Normalize keywords (handle dict format from pipeline)
    normalized_keywords = []
    for kw in keywords:
        if isinstance(kw, dict):
            normalized_keywords.append(kw.get("keyword", ""))
        else:
            normalized_keywords.append(str(kw))

    # Select decisions
    decisions = _select_decisions_for_keywords(
        keywords=normalized_keywords,
        rechtsgebiet=rechtsgebiet,
        decisions_per_keyword=2
    )

    # Get disclaimer
    disclaimer = DISCLAIMER_TEMPLATES.get(
        rechtsgebiet,
        DISCLAIMER_TEMPLATES["Arbeitsrecht"]  # Fallback
    )

    # Build context
    return LegalContext(
        rechtsgebiet=rechtsgebiet,
        court_decisions=decisions,
        statutes=[],  # Phase 2 feature
        disclaimer_template=disclaimer,
        stand_der_rechtsprechung=datetime.now().strftime("%Y-%m-%d"),
        keywords_researched=normalized_keywords
    )


# Utility function for testing
def get_available_rechtsgebiete() -> List[str]:
    """
    Get list of supported legal areas.

    Returns:
        List of Rechtsgebiet names
    """
    return list(MOCK_DECISIONS.keys())
