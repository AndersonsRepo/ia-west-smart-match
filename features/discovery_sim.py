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
    """Render the discovery scan trigger button with animated progress.

    Returns True if a scan was just completed, False otherwise.
    """
    init_discovery_state()

    if st.button("🔍 Run Discovery Scan", key="discovery_scan_btn"):
        templates = UNIVERSITY_TEMPLATES
        total = len(templates)
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, tmpl in enumerate(templates, start=1):
            status_text.text(f"Scanning {tmpl.name}... ({i}/{total})")
            progress_bar.progress(i / total)
            time.sleep(0.4)

        # Build results from templates
        results = []
        for tmpl in templates:
            results.append({
                "university": tmpl.name,
                "region": tmpl.region,
                "department": tmpl.department,
                "base_url": tmpl.base_url,
                "event_urls": tmpl.get_event_urls(),
                "course_catalog_url": tmpl.course_catalog_url or "",
                "selectors": tmpl.selectors or {},
                "scan_status": "Complete",
            })

        st.session_state.discovery_results = results
        st.session_state.discovery_timestamp = datetime.now().isoformat()

        progress_bar.empty()
        status_text.empty()
        st.toast("Discovery scan complete!")
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
