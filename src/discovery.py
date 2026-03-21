"""Opportunity discovery — re-exports from university_scraper for backward compat."""

from src.university_scraper import (
    run_full_discovery as run_discovery_simulation,
    get_discovery_stats,
    get_expansion_roadmap,
    discover_from_csv,
    discover_from_templates,
    UNIVERSITY_TEMPLATES,
)

__all__ = [
    "run_discovery_simulation",
    "get_discovery_stats",
    "get_expansion_roadmap",
    "discover_from_csv",
    "discover_from_templates",
    "UNIVERSITY_TEMPLATES",
]
