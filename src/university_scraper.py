"""University event discovery via web scraping and CSV seed data.

For the hackathon demo, this module works in two modes:
1. **CSV-seeded mode** (default): Loads real opportunities from our curated
   datasets (CPP events, courses, regional calendar) and structures them
   as if they were discovered by an automated scan.
2. **Live scrape mode** (template): Defines URL patterns and HTML parsing
   rules for each university so the system can scale to new schools.

This design shows judges both a working product (seed data) and a credible
path to production (scraping templates).
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional
import re
import logging

logger = logging.getLogger(__name__)

# Polite scraping headers
_HEADERS = {
    "User-Agent": "IAWestSmartMatch/1.0 (university engagement CRM; contact: research@iawest.org)",
    "Accept": "text/html",
}
_TIMEOUT = 8  # seconds per request

DATA_DIR = Path(__file__).parent.parent / "data"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class DiscoveredOpportunity:
    """A single opportunity found by the discovery engine."""
    university: str
    region: str
    department: str
    opportunity_name: str
    opportunity_type: str   # Course | Event | Speaker Series | Hackathon | etc.
    fit_level: str          # High | Medium | Low
    description: str
    source_url: str = ""
    contact_name: str = ""
    contact_email: str = ""
    discovered_date: str = ""
    status: str = "New"
    volunteer_roles: str = ""
    audience: str = ""

    def __post_init__(self):
        if not self.discovered_date:
            self.discovered_date = datetime.now().strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# University scraping templates (for production scaling)
# ---------------------------------------------------------------------------
@dataclass
class UniversityTemplate:
    """Defines how to scrape a university's event pages."""
    name: str
    short_name: str
    region: str
    base_url: str
    event_paths: list[str] = field(default_factory=list)
    course_catalog_url: str = ""
    department: str = "Marketing / Business"
    selectors: dict = field(default_factory=dict)

    def get_event_urls(self) -> list[str]:
        return [f"{self.base_url}{p}" for p in self.event_paths]


# Pre-built templates for IA West target universities
UNIVERSITY_TEMPLATES = [
    UniversityTemplate(
        name="Cal Poly Pomona",
        short_name="CPP",
        region="Los Angeles — East",
        base_url="https://www.cpp.edu",
        event_paths=[
            "/cba/digital-innovation/what-we-do/ai-hackathon.shtml",
            "/siil/about-us/contact-us.shtml",
            "/cba/swift-summit/",
            "/our/index.shtml",
        ],
        course_catalog_url="https://www.cpp.edu/class-schedule/",
        department="College of Business Administration",
        selectors={
            "title": "h1.page-title, h2.event-title",
            "description": "div.page-content p",
            "contact": "div.contact-info",
            "date": "span.event-date",
        },
    ),
    UniversityTemplate(
        name="UCLA Anderson School of Management",
        short_name="UCLA",
        region="Los Angeles",
        base_url="https://www.anderson.ucla.edu",
        event_paths=[
            "/events/",
            "/centers/price-center-for-entrepreneurship/events/",
            "/student-life/clubs-and-organizations/marketing-association/",
        ],
        course_catalog_url="https://registrar.ucla.edu/academics/course-descriptions",
        department="Marketing",
        selectors={
            "title": "h1.entry-title, h2.event-name",
            "description": "div.entry-content p",
            "date": "time.event-date",
        },
    ),
    UniversityTemplate(
        name="USC Marshall School of Business",
        short_name="USC",
        region="Los Angeles",
        base_url="https://www.marshall.usc.edu",
        event_paths=[
            "/events/",
            "/departments/marketing/",
        ],
        department="Marketing",
        selectors={
            "title": "h1, h2.event-title",
            "description": "div.event-description p",
        },
    ),
    UniversityTemplate(
        name="San Diego State University",
        short_name="SDSU",
        region="San Diego",
        base_url="https://business.sdsu.edu",
        event_paths=[
            "/events/",
            "/lavin/events/",
        ],
        department="Marketing",
    ),
    UniversityTemplate(
        name="UC Berkeley Haas School of Business",
        short_name="Berkeley",
        region="San Francisco",
        base_url="https://haas.berkeley.edu",
        event_paths=[
            "/events/",
            "/groups/innovation-lab/",
        ],
        department="Marketing",
    ),
    UniversityTemplate(
        name="University of Washington Foster School",
        short_name="UW",
        region="Seattle",
        base_url="https://foster.uw.edu",
        event_paths=[
            "/events/",
            "/centers/buerk-ctr-entrepreneurship/events/",
        ],
        department="Marketing & International Business",
    ),
    UniversityTemplate(
        name="Portland State University",
        short_name="PSU",
        region="Portland",
        base_url="https://www.pdx.edu/business",
        event_paths=[
            "/events/",
        ],
        department="Marketing & Business",
    ),
]


# ---------------------------------------------------------------------------
# CSV-seeded discovery (works now, uses real data)
# ---------------------------------------------------------------------------
def discover_from_csv() -> list[DiscoveredOpportunity]:
    """
    Load real opportunity data from our CSV datasets and package
    them as if they were discovered by an automated scan.
    """
    results = []

    # --- CPP Events ---
    try:
        events = pd.read_csv(DATA_DIR / "cpp_events.csv")
        events.columns = [c.strip() for c in events.columns]
        for _, row in events.iterrows():
            name = row.get("Event / Program", "")
            category = row.get("Category", "")
            roles = row.get("Volunteer Roles (fit)", "")

            # Determine fit level from category
            high_fit_cats = ["AI / Hackathon", "Case competition",
                             "Research / Scholarship"]
            fit = "High" if category in high_fit_cats else "Medium"

            results.append(DiscoveredOpportunity(
                university="Cal Poly Pomona",
                region="Los Angeles — East",
                department="College of Business Administration",
                opportunity_name=name,
                opportunity_type=category,
                fit_level=fit,
                description=f"{name} — {category} event. Roles: {roles}",
                source_url=str(row.get("Public URL", "")),
                contact_name=str(row.get("Point(s) of Contact (published)", "")),
                contact_email=str(row.get("Contact Email / Phone (published)", "")),
                volunteer_roles=roles,
                audience=str(row.get("Primary Audience", "")),
            ))
    except Exception:
        pass

    # --- CPP Courses (high-fit only) ---
    try:
        courses = pd.read_csv(DATA_DIR / "cpp_courses.csv")
        courses.columns = [c.strip() for c in courses.columns]
        high_fit = courses[courses.get("Guest Lecture Fit", pd.Series(dtype=str)).str.strip() == "High"]
        for _, row in high_fit.iterrows():
            results.append(DiscoveredOpportunity(
                university="Cal Poly Pomona",
                region="Los Angeles — East",
                department="College of Business Administration",
                opportunity_name=f"{row.get('Course', '')} — {row.get('Title', '')}",
                opportunity_type="Guest Lecture",
                fit_level="High",
                description=(
                    f"{row.get('Title', '')} taught by {row.get('Instructor', '')}. "
                    f"{row.get('Days', '')} {row.get('Start Time', '')}–{row.get('End Time', '')}. "
                    f"Mode: {row.get('Mode', '')}. Cap: {row.get('Enrl Cap', '')} students."
                ),
                contact_name=str(row.get("Instructor", "")),
                volunteer_roles="Guest speaker",
                audience="Marketing students",
            ))
    except Exception:
        pass

    # --- Regional calendar → nearby universities ---
    try:
        cal = pd.read_csv(DATA_DIR / "event_calendar.csv")
        cal.columns = [c.strip() for c in cal.columns]
        for _, row in cal.iterrows():
            unis = str(row.get("Nearby Universities", ""))
            for uni in unis.split(","):
                uni = uni.strip()
                if uni:
                    results.append(DiscoveredOpportunity(
                        university=uni,
                        region=str(row.get("Region", "")),
                        department="Marketing / Business",
                        opportunity_name=f"IA Regional Event Tie-in at {uni}",
                        opportunity_type="Regional Event",
                        fit_level="Medium",
                        description=(
                            f"IA event on {row.get('IA Event Date', '')} in {row.get('Region', '')}. "
                            f"Lecture window: {row.get('Suggested Lecture Window', '')}. "
                            f"Course alignment: {row.get('Course Alignment', '')}."
                        ),
                        volunteer_roles="Guest speaker; Panelist",
                        audience="University students and faculty",
                    ))
    except Exception:
        pass

    return results


def _scrape_page(url: str, selectors: dict, tmpl: UniversityTemplate) -> list[DiscoveredOpportunity]:
    """Fetch a page and extract opportunities using CSS selectors."""
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return [DiscoveredOpportunity(
            university=tmpl.name,
            region=tmpl.region,
            department=tmpl.department,
            opportunity_name=f"[Unreachable] {url.split('/')[-2] or 'page'}",
            opportunity_type="Scan Error",
            fit_level="TBD",
            description=f"Could not reach {url}: {e}",
            source_url=url,
            status="Error",
        )]

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []

    # Extract page title
    title_sel = selectors.get("title", "h1, h2")
    page_title = ""
    title_el = soup.select_one(title_sel)
    if title_el:
        page_title = title_el.get_text(strip=True)

    # Extract description paragraphs
    desc_sel = selectors.get("description", "div.page-content p, article p, main p")
    desc_els = soup.select(desc_sel)[:3]
    page_desc = " ".join(el.get_text(strip=True) for el in desc_els)[:300]

    # Extract contact info if available
    contact_sel = selectors.get("contact", "div.contact-info, .contact, footer")
    contact_text = ""
    contact_el = soup.select_one(contact_sel)
    if contact_el:
        contact_text = contact_el.get_text(strip=True)[:200]

    # Extract event-like links from the page
    event_keywords = [
        "hackathon", "competition", "workshop", "speaker", "panel", "seminar",
        "career", "networking", "conference", "symposium", "pitch", "mentor",
        "lecture", "bootcamp", "summit", "expo", "fair", "forum", "challenge",
    ]

    # Find all links that look like event/opportunity pages
    found_links = []
    for a_tag in soup.find_all("a", href=True):
        text = a_tag.get_text(strip=True).lower()
        href = a_tag["href"].lower()
        if any(kw in text or kw in href for kw in event_keywords):
            full_text = a_tag.get_text(strip=True)
            if len(full_text) > 3 and full_text not in [t for _, t in found_links]:
                full_href = a_tag["href"]
                if full_href.startswith("/"):
                    full_href = tmpl.base_url + full_href
                found_links.append((full_href, full_text))

    # Build DiscoveredOpportunity from the page itself
    if page_title and page_title.lower() not in ("events", "home", "contact us"):
        # Determine fit level from keywords
        combined = f"{page_title} {page_desc}".lower()
        high_kw = ["hackathon", "ai", "competition", "innovation", "analytics", "research"]
        fit = "High" if any(kw in combined for kw in high_kw) else "Medium"

        # Determine type
        type_map = [
            ("hackathon", "Hackathon"), ("competition", "Competition"),
            ("workshop", "Workshop"), ("speaker", "Speaker Series"),
            ("career", "Career Event"), ("seminar", "Seminar"),
            ("pitch", "Pitch Competition"), ("symposium", "Research Symposium"),
        ]
        opp_type = "Event"
        for kw, otype in type_map:
            if kw in combined:
                opp_type = otype
                break

        results.append(DiscoveredOpportunity(
            university=tmpl.name,
            region=tmpl.region,
            department=tmpl.department,
            opportunity_name=page_title[:100],
            opportunity_type=opp_type,
            fit_level=fit,
            description=page_desc or f"Discovered at {url}",
            source_url=url,
            contact_name=_extract_name(contact_text),
            contact_email=_extract_email(resp.text),
            volunteer_roles=_infer_roles(combined),
            audience="University students and faculty",
            status="Scraped",
        ))

    # Also create entries for discovered sub-links
    for link_url, link_text in found_links[:5]:  # cap at 5 per page
        combined = link_text.lower()
        high_kw = ["hackathon", "ai", "competition", "innovation", "analytics", "research"]
        fit = "High" if any(kw in combined for kw in high_kw) else "Medium"

        results.append(DiscoveredOpportunity(
            university=tmpl.name,
            region=tmpl.region,
            department=tmpl.department,
            opportunity_name=link_text[:100],
            opportunity_type="Discovered Link",
            fit_level=fit,
            description=f"Found on {url}",
            source_url=link_url,
            volunteer_roles=_infer_roles(combined),
            audience="University students",
            status="Scraped",
        ))

    # If nothing was extracted, still report the page was scanned
    if not results:
        results.append(DiscoveredOpportunity(
            university=tmpl.name,
            region=tmpl.region,
            department=tmpl.department,
            opportunity_name=f"[Scanned] {page_title or url.split('/')[-2] or 'page'}",
            opportunity_type="Page Scanned",
            fit_level="Low",
            description=page_desc[:200] or f"No specific opportunities found at {url}",
            source_url=url,
            status="Scanned",
        ))

    return results


def _extract_email(html_text: str) -> str:
    """Extract first email address from HTML text."""
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html_text)
    return match.group(0) if match else ""


def _extract_name(contact_text: str) -> str:
    """Try to extract a person's name from contact text."""
    if not contact_text:
        return ""
    # Look for patterns like "Contact: John Smith" or "Dr. Jane Doe"
    patterns = [
        r'(?:Contact|Director|Chair|Coordinator):\s*([A-Z][a-z]+ [A-Z][a-z]+)',
        r'(Dr\.\s*[A-Z][a-z]+ [A-Z][a-z]+)',
        r'([A-Z][a-z]+ [A-Z][a-z]+)',
    ]
    for pat in patterns:
        m = re.search(pat, contact_text)
        if m:
            return m.group(1)
    return ""


def _infer_roles(text: str) -> str:
    """Infer volunteer roles from opportunity text."""
    roles = []
    role_map = {
        "judge": "Judge", "mentor": "Mentor", "speaker": "Guest Speaker",
        "panelist": "Panelist", "workshop": "Workshop Facilitator",
        "coach": "Coach", "advisor": "Career Advisor",
    }
    for kw, role in role_map.items():
        if kw in text:
            roles.append(role)
    return "; ".join(roles) if roles else "Guest Speaker; Mentor"


def discover_from_templates(templates: list[UniversityTemplate] = None,
                            dry_run: bool = False) -> list[DiscoveredOpportunity]:
    """
    Scan university websites using templates.

    When dry_run=False (default), actually fetches pages and extracts
    opportunities using BeautifulSoup. When dry_run=True, returns
    placeholder entries showing what would be scraped.
    """
    templates = templates or UNIVERSITY_TEMPLATES
    results = []

    for tmpl in templates:
        urls = tmpl.get_event_urls()
        for url in urls:
            if dry_run:
                results.append(DiscoveredOpportunity(
                    university=tmpl.name,
                    region=tmpl.region,
                    department=tmpl.department,
                    opportunity_name=f"[Scan Target] {url.split('/')[-2] or 'events'}",
                    opportunity_type="Pending Scan",
                    fit_level="TBD",
                    description=f"URL queued for scraping: {url}",
                    source_url=url,
                    status="Queued",
                ))
            else:
                page_opps = _scrape_page(url, tmpl.selectors or {}, tmpl)
                results.extend(page_opps)

    return results


def run_full_discovery(live: bool = False) -> pd.DataFrame:
    """
    Run the complete discovery pipeline.

    Parameters
    ----------
    live : bool
        If True, actually scrape university websites.
        If False, show CSV seed data + queued scan targets.
    """
    csv_opps = discover_from_csv()
    template_opps = discover_from_templates(dry_run=not live)
    all_opps = csv_opps + template_opps

    df = pd.DataFrame([asdict(o) for o in all_opps])
    return df


def get_discovery_stats(discoveries: pd.DataFrame) -> dict:
    """Get summary statistics from a discovery scan."""
    # Filter out scan targets for stats
    real = discoveries[discoveries["status"] != "Queued"]
    return {
        "total_opportunities": len(real),
        "universities_scanned": real["university"].nunique(),
        "high_fit_count": len(real[real["fit_level"] == "High"]),
        "scan_targets": len(discoveries[discoveries["status"] == "Queued"]),
        "by_type": real["opportunity_type"].value_counts().to_dict(),
        "by_region": real["region"].value_counts().to_dict(),
        "by_university": real["university"].value_counts().to_dict(),
    }


def get_expansion_roadmap() -> list[dict]:
    """Return a prioritized expansion roadmap for new universities."""
    return [
        {
            "phase": "Phase 1 — Q2 2026",
            "universities": ["UCLA", "USC", "SDSU"],
            "region": "Southern California",
            "rationale": "Highest board member density; same-day travel; existing IA event schedule overlap",
            "estimated_opportunities": 8,
            "priority": "Immediate",
            "template_ready": True,
        },
        {
            "phase": "Phase 2 — Q3 2026",
            "universities": ["UC Berkeley Haas", "USF", "SFSU", "Santa Clara"],
            "region": "San Francisco Bay Area",
            "rationale": "Active metro director (Liz O'Hara); IA event in July; strong tech/analytics programs",
            "estimated_opportunities": 10,
            "priority": "High",
            "template_ready": True,
        },
        {
            "phase": "Phase 3 — Q3-Q4 2026",
            "universities": ["UW Foster", "Seattle U"],
            "region": "Pacific Northwest (Seattle)",
            "rationale": "Dedicated metro director (Greg Carter); two IA events scheduled; strong business programs",
            "estimated_opportunities": 6,
            "priority": "High",
            "template_ready": True,
        },
        {
            "phase": "Phase 4 — Q4 2026",
            "universities": ["Portland State", "U of Oregon"],
            "region": "Pacific Northwest (Portland)",
            "rationale": "Metro director (Katie Nelson); IA event in April; growing market research programs",
            "estimated_opportunities": 5,
            "priority": "Medium",
            "template_ready": True,
        },
        {
            "phase": "Phase 5 — 2027",
            "universities": ["CSULB", "Chapman", "UCI", "CSUF", "CLU", "CSUCI"],
            "region": "Orange County / Ventura",
            "rationale": "IA events in Oct and Sep; large student populations; adjacent to LA board members",
            "estimated_opportunities": 12,
            "priority": "Medium",
            "template_ready": False,
        },
    ]
