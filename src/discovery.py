"""Automated opportunity discovery simulator.

In production, this would use web scraping and search APIs to find
new university programs, events, and courses. For the MVP, we simulate
discovery with realistic mock data showing how the system would expand
to new universities.
"""

import pandas as pd
from datetime import datetime, timedelta
import random

# Simulated discovery results for demo purposes
DISCOVERY_UNIVERSITIES = [
    {
        "university": "UCLA Anderson School of Management",
        "region": "Los Angeles",
        "department": "Marketing",
        "programs_found": [
            {"name": "Marketing Analytics Capstone", "type": "Course", "fit": "High",
             "description": "Students work on real marketing analytics projects with industry partners"},
            {"name": "UCLA Startup Fair", "type": "Entrepreneurship Event", "fit": "Medium",
             "description": "Annual showcase of student startups, needs industry judges and mentors"},
            {"name": "Digital Marketing Speaker Series", "type": "Speaker Series", "fit": "High",
             "description": "Weekly industry speakers on digital marketing trends"},
        ],
    },
    {
        "university": "USC Marshall School of Business",
        "region": "Los Angeles",
        "department": "Marketing",
        "programs_found": [
            {"name": "MKT 525 — Market Research Methods", "type": "Graduate Course", "fit": "High",
             "description": "MBA elective on quantitative and qualitative research methods"},
            {"name": "Trojan Entrepreneurs Network", "type": "Entrepreneurship", "fit": "Medium",
             "description": "Pitch competitions and mentoring for student entrepreneurs"},
        ],
    },
    {
        "university": "San Diego State University",
        "region": "San Diego",
        "department": "Marketing",
        "programs_found": [
            {"name": "SDSU Research Symposium", "type": "Research Event", "fit": "High",
             "description": "Annual undergraduate research presentations"},
            {"name": "MKT 370 — Marketing Research", "type": "Undergraduate Course", "fit": "High",
             "description": "Core marketing research course with guest lecture slots"},
            {"name": "Lavin Center Pitch Competition", "type": "Entrepreneurship", "fit": "Medium",
             "description": "Student entrepreneurship competition needing industry judges"},
        ],
    },
    {
        "university": "UC Berkeley Haas School of Business",
        "region": "San Francisco",
        "department": "Marketing",
        "programs_found": [
            {"name": "Berkeley Haas Innovation Lab", "type": "Innovation Hub", "fit": "High",
             "description": "Student innovation projects with industry mentorship"},
            {"name": "UGBA 106 — Marketing", "type": "Undergraduate Course", "fit": "Medium",
             "description": "Introductory marketing course, large enrollment"},
        ],
    },
    {
        "university": "University of Washington Foster School",
        "region": "Seattle",
        "department": "Marketing & International Business",
        "programs_found": [
            {"name": "Foster Case Competition", "type": "Case Competition", "fit": "High",
             "description": "Annual case competition with industry sponsorship opportunities"},
            {"name": "MKTG 450 — Consumer Behavior Research", "type": "Course", "fit": "High",
             "description": "Advanced consumer research methods with practitioner panels"},
            {"name": "HuskyHacks", "type": "Hackathon", "fit": "Medium",
             "description": "Annual student hackathon with industry judges and mentors"},
        ],
    },
    {
        "university": "Portland State University",
        "region": "Portland",
        "department": "Marketing & Business",
        "programs_found": [
            {"name": "PSU Innovation Challenge", "type": "Innovation Event", "fit": "Medium",
             "description": "Cross-disciplinary innovation competition"},
            {"name": "MKTG 464 — Marketing Research", "type": "Course", "fit": "High",
             "description": "Marketing research methods with industry project option"},
        ],
    },
]


def run_discovery_simulation() -> pd.DataFrame:
    """
    Simulate an automated discovery scan across universities.
    Returns a DataFrame of discovered opportunities.
    """
    results = []
    scan_date = datetime.now()

    for uni in DISCOVERY_UNIVERSITIES:
        for prog in uni["programs_found"]:
            results.append({
                "university": uni["university"],
                "region": uni["region"],
                "department": uni["department"],
                "opportunity_name": prog["name"],
                "opportunity_type": prog["type"],
                "fit_level": prog["fit"],
                "description": prog["description"],
                "discovered_date": scan_date.strftime("%Y-%m-%d"),
                "status": "New",
                "source": "Web Discovery (Simulated)",
            })

    return pd.DataFrame(results)


def get_discovery_stats(discoveries: pd.DataFrame) -> dict:
    """Get summary statistics from a discovery scan."""
    return {
        "total_opportunities": len(discoveries),
        "universities_scanned": discoveries["university"].nunique(),
        "high_fit_count": len(discoveries[discoveries["fit_level"] == "High"]),
        "by_type": discoveries["opportunity_type"].value_counts().to_dict(),
        "by_region": discoveries["region"].value_counts().to_dict(),
    }


def get_expansion_roadmap() -> list:
    """Return a prioritized expansion roadmap for new universities."""
    return [
        {
            "phase": "Phase 1 — Q2 2026",
            "universities": ["UCLA", "USC", "SDSU"],
            "region": "Southern California",
            "rationale": "Highest board member density; same-day travel; existing IA event schedule overlap",
            "estimated_opportunities": 8,
            "priority": "Immediate",
        },
        {
            "phase": "Phase 2 — Q3 2026",
            "universities": ["UC Berkeley Haas", "USF", "SFSU", "Santa Clara"],
            "region": "San Francisco Bay Area",
            "rationale": "Active metro director (Liz O'Hara); IA event in July; strong tech/analytics programs",
            "estimated_opportunities": 10,
            "priority": "High",
        },
        {
            "phase": "Phase 3 — Q3-Q4 2026",
            "universities": ["UW Foster", "Seattle U"],
            "region": "Pacific Northwest (Seattle)",
            "rationale": "Dedicated metro director (Greg Carter); two IA events scheduled; strong business programs",
            "estimated_opportunities": 6,
            "priority": "High",
        },
        {
            "phase": "Phase 4 — Q4 2026",
            "universities": ["Portland State", "U of Oregon"],
            "region": "Pacific Northwest (Portland)",
            "rationale": "Metro director (Katie Nelson); IA event in April; growing market research programs",
            "estimated_opportunities": 5,
            "priority": "Medium",
        },
        {
            "phase": "Phase 5 — 2027",
            "universities": ["CSULB", "Chapman", "UCI", "CSUF", "CLU", "CSUCI"],
            "region": "Orange County / Ventura",
            "rationale": "IA events in Oct and Sep; large student populations; adjacent to LA board members",
            "estimated_opportunities": 12,
            "priority": "Medium",
        },
    ]
