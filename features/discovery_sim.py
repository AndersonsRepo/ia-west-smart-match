"""Discovery Simulation — animated scan simulation and pipeline integration."""

import streamlit as st
import time
from datetime import datetime

from src.university_scraper import UNIVERSITY_TEMPLATES


def init_discovery_state():
    """Initialize discovery simulation state."""
    if "discovery_results" not in st.session_state:
        st.session_state.discovery_results = None
    if "discovery_timestamp" not in st.session_state:
        st.session_state.discovery_timestamp = None


def render_discovery_scan_button() -> bool:
    """Render the discovery scan trigger button with live scraping progress.

    Returns True if a scan was just completed, False otherwise.
    """
    init_discovery_state()

    if st.button("🔍 Run Live Discovery Scan", key="discovery_scan_btn"):
        from src.university_scraper import discover_from_templates, _scrape_page

        templates = UNIVERSITY_TEMPLATES
        total_urls = sum(len(t.get_event_urls()) for t in templates)
        progress_bar = st.progress(0)
        status_text = st.empty()
        scanned = 0

        all_results = []
        for tmpl in templates:
            urls = tmpl.get_event_urls()
            for url in urls:
                status_text.text(f"🌐 Scraping {tmpl.short_name}: {url.split('/')[-2] or 'page'}... ({scanned + 1}/{total_urls})")
                page_results = _scrape_page(url, tmpl.selectors or {}, tmpl)
                all_results.extend(page_results)
                scanned += 1
                progress_bar.progress(scanned / total_urls)

        # Store results as list of dicts for the session
        st.session_state.discovery_results = [
            {
                "university": r.university,
                "region": r.region,
                "department": r.department,
                "opportunity_name": r.opportunity_name,
                "opportunity_type": r.opportunity_type,
                "fit_level": r.fit_level,
                "description": r.description,
                "source_url": r.source_url,
                "contact_name": r.contact_name,
                "contact_email": r.contact_email,
                "volunteer_roles": r.volunteer_roles,
                "status": r.status,
            }
            for r in all_results
        ]
        st.session_state.discovery_timestamp = datetime.now().isoformat()
        st.session_state.live_scan_count = len(all_results)

        progress_bar.empty()
        status_text.empty()
        st.toast(f"Live scan complete! Found {len(all_results)} opportunities across {len(templates)} universities.")
        return True

    return False


def render_discovery_add_to_pipeline(discoveries_df):
    """Render 'Add to Pipeline' buttons for high-fit discoveries.

    Parameters
    ----------
    discoveries_df : pd.DataFrame
        DataFrame of discovered opportunities. Must have columns:
        university, opportunity_name, fit_level, region, opportunity_type,
        description.
    """
    high_fit = discoveries_df[discoveries_df["fit_level"] == "High"]

    if high_fit.empty:
        st.info("No high-fit discoveries to add to the pipeline.")
        return

    # Ensure pipeline_data exists in session state
    if "pipeline_data" not in st.session_state:
        st.session_state.pipeline_data = []

    for idx, row in high_fit.iterrows():
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(
                f"**{row['opportunity_name']}** — {row['university']} "
                f"({row['region']})"
            )
            st.caption(row.get("description", ""))
        with col2:
            safe_key = (
                f"{row['university']}_{row['opportunity_name']}"
                .replace(" ", "_")[:60]
            )
            if st.button("➕ Add to Pipeline", key=f"add_pipe_{safe_key}_{idx}"):
                entry = {
                    "id": f"DISC-{len(st.session_state.pipeline_data) + 1:03d}",
                    "volunteer": "Unassigned",
                    "opportunity": row["opportunity_name"],
                    "university": row["university"],
                    "region": row["region"],
                    "opportunity_type": row.get("opportunity_type", "event"),
                    "stage": "Identified",
                    "entry_date": datetime.now().strftime("%Y-%m-%d"),
                    "last_updated": datetime.now().strftime("%Y-%m-%d"),
                    "notes": f"Discovered via scan — {row.get('description', '')}",
                    "source": "discovery_scan",
                }

                # Try importing add_to_pipeline_from_match if available
                try:
                    from features.interactive_pipeline import add_to_pipeline_from_match
                    add_to_pipeline_from_match(entry)
                except (ImportError, ModuleNotFoundError):
                    st.session_state.pipeline_data.append(entry)

                st.toast(
                    f"Added {row['opportunity_name']} to pipeline!"
                )
                st.rerun()
