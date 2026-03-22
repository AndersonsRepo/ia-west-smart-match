"""Match Approval Workflow for Smart Matches (Tab 3).

Provides session-state-backed approval/rejection/shortlisting of
volunteer-opportunity matches, with an action log and decision summary.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from src.db import is_supabase_mode, get_match_decisions_db, set_match_decision_db, log_action_db


# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

DECISION_STYLES = {
    "approved": {
        "bg": "rgba(40,167,69,0.2)",
        "color": "#6dd48f",
        "border": "rgba(40,167,69,0.3)",
        "icon": "✅",
        "label": "Approved",
    },
    "shortlisted": {
        "bg": "rgba(255,193,7,0.2)",
        "color": "#ffe066",
        "border": "rgba(255,193,7,0.3)",
        "icon": "⭐",
        "label": "Shortlisted",
    },
    "rejected": {
        "bg": "rgba(220,53,69,0.2)",
        "color": "#ff8a95",
        "border": "rgba(220,53,69,0.3)",
        "icon": "❌",
        "label": "Rejected",
    },
}


# ─────────────────────────────────────────────
# State Initialization
# ─────────────────────────────────────────────

def init_match_state() -> None:
    """Initialize session state for match decisions and action logging.

    Safe to call multiple times — only sets defaults if keys are missing.
    In Supabase mode, hydrates from the database on first load.
    """
    if "match_decisions" not in st.session_state:
        if is_supabase_mode():
            try:
                st.session_state.match_decisions = get_match_decisions_db()
            except Exception:
                st.session_state.match_decisions = {}
        else:
            st.session_state.match_decisions = {}
    if "action_log" not in st.session_state:
        st.session_state.action_log = []


# ─────────────────────────────────────────────
# Action Logging
# ─────────────────────────────────────────────

def log_action(action: str, details: str, tab: str = "Smart Matches") -> None:
    """Append a timestamped entry to the session action log.

    Args:
        action: Short verb, e.g. "Approved", "Rejected", "Shortlisted".
        details: Human-readable description of what was acted on.
        tab: Which tab the action originated from.
    """
    init_match_state()
    st.session_state.action_log.append({
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "action": action,
        "details": details,
        "tab": tab,
    })
    if is_supabase_mode():
        try:
            log_action_db(action, details, tab)
        except Exception:
            pass


# ─────────────────────────────────────────────
# Decision Badge
# ─────────────────────────────────────────────

def _make_decision_key(volunteer: str, opportunity: str) -> str:
    """Build a canonical key for a volunteer|opportunity pair."""
    return f"{volunteer}|{opportunity}"


def get_decision_badge(volunteer: str, opportunity: str) -> str:
    """Return an HTML badge for the current decision, or empty string.

    Args:
        volunteer: Volunteer name.
        opportunity: Opportunity name.

    Returns:
        HTML string with a styled badge, or "" if undecided.
    """
    init_match_state()
    key = _make_decision_key(volunteer, opportunity)
    decision = st.session_state.match_decisions.get(key)
    if decision is None:
        return ""
    style = DECISION_STYLES[decision]
    return (
        f'<span style="background:{style["bg"]};color:{style["color"]};'
        f'border:1px solid {style["border"]};padding:2px 10px;'
        f'border-radius:12px;font-size:0.82em;margin-left:8px">'
        f'{style["icon"]} {style["label"]}</span>'
    )


# ─────────────────────────────────────────────
# Match Action Buttons
# ─────────────────────────────────────────────

def render_match_actions(volunteer: str, opportunity: str, idx: int) -> None:
    """Render approve / shortlist / reject buttons inside a match expander.

    Args:
        volunteer: Volunteer name.
        opportunity: Opportunity name.
        idx: Unique index for generating non-colliding Streamlit widget keys.
    """
    init_match_state()
    key = _make_decision_key(volunteer, opportunity)
    current = st.session_state.match_decisions.get(key)

    # Show current decision badge if one exists
    if current is not None:
        style = DECISION_STYLES[current]
        st.markdown(
            f'<div style="margin-bottom:0.6rem">'
            f'<span style="color:#8899aa;font-size:0.85em">Current status:</span> '
            f'{get_decision_badge(volunteer, opportunity)}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Action buttons in 3 columns
    col_approve, col_shortlist, col_reject = st.columns(3)

    with col_approve:
        if st.button(
            "✅ Approve",
            key=f"approve_{idx}",
            type="primary" if current != "approved" else "secondary",
            use_container_width=True,
        ):
            st.session_state.match_decisions[key] = "approved"
            if is_supabase_mode():
                try:
                    set_match_decision_db(volunteer, opportunity, "approved")
                except Exception:
                    pass
            log_action("Approved", f"{volunteer} → {opportunity}")
            st.toast(f"Approved: {volunteer} → {opportunity}", icon="✅")
            st.rerun()

    with col_shortlist:
        if st.button(
            "⭐ Shortlist",
            key=f"shortlist_{idx}",
            type="primary" if current != "shortlisted" else "secondary",
            use_container_width=True,
        ):
            st.session_state.match_decisions[key] = "shortlisted"
            if is_supabase_mode():
                try:
                    set_match_decision_db(volunteer, opportunity, "shortlisted")
                except Exception:
                    pass
            log_action("Shortlisted", f"{volunteer} → {opportunity}")
            st.toast(f"Shortlisted: {volunteer} → {opportunity}", icon="⭐")
            st.rerun()

    with col_reject:
        if st.button(
            "❌ Reject",
            key=f"reject_{idx}",
            type="primary" if current != "rejected" else "secondary",
            use_container_width=True,
        ):
            st.session_state.match_decisions[key] = "rejected"
            if is_supabase_mode():
                try:
                    set_match_decision_db(volunteer, opportunity, "rejected")
                except Exception:
                    pass
            log_action("Rejected", f"{volunteer} → {opportunity}")
            st.toast(f"Rejected: {volunteer} → {opportunity}", icon="❌")
            st.rerun()


# ─────────────────────────────────────────────
# Decision Summary
# ─────────────────────────────────────────────

def render_decision_summary(all_matches: pd.DataFrame) -> None:
    """Render a summary section of all match decisions made so far.

    Only renders if at least one decision has been made. Shows KPI cards
    with counts and a filterable table of decided matches.

    Args:
        all_matches: The full matches DataFrame (needs 'volunteer' and
                     'opportunity' columns to cross-reference decisions).
    """
    init_match_state()
    decisions = st.session_state.match_decisions

    if not decisions:
        return

    # Count by status
    approved = sum(1 for v in decisions.values() if v == "approved")
    shortlisted = sum(1 for v in decisions.values() if v == "shortlisted")
    rejected = sum(1 for v in decisions.values() if v == "rejected")
    total_matches = len(all_matches)
    decided = approved + shortlisted + rejected
    undecided = total_matches - decided

    # Section header
    st.markdown(
        '<div class="section-header">📋 Decision Summary</div>',
        unsafe_allow_html=True,
    )

    # KPI row
    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card green">
            <div class="kpi-value">{approved}</div>
            <div class="kpi-label">Approved</div>
        </div>
        <div class="kpi-card orange">
            <div class="kpi-value">{shortlisted}</div>
            <div class="kpi-label">Shortlisted</div>
        </div>
        <div class="kpi-card" style="border-left:3px solid #dc3545">
            <div class="kpi-value">{rejected}</div>
            <div class="kpi-label">Rejected</div>
        </div>
        <div class="kpi-card accent">
            <div class="kpi-value">{undecided:,}</div>
            <div class="kpi-label">Undecided</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Build a table of decided matches
    rows = []
    for pair_key, status in decisions.items():
        parts = pair_key.split("|", 1)
        if len(parts) != 2:
            continue
        volunteer_name, opportunity = parts
        style = DECISION_STYLES[status]
        rows.append({
            "Volunteer": volunteer_name,
            "Opportunity": opportunity,
            "Status": style["label"],
        })

    if not rows:
        return

    decided_df = pd.DataFrame(rows)

    # Status filter
    status_filter = st.multiselect(
        "Filter by decision",
        options=["Approved", "Shortlisted", "Rejected"],
        default=["Approved", "Shortlisted", "Rejected"],
        key="decision_summary_filter",
    )

    if status_filter:
        decided_df = decided_df[decided_df["Status"].isin(status_filter)]

    st.dataframe(
        decided_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Volunteer": st.column_config.TextColumn("Volunteer", width="medium"),
            "Opportunity": st.column_config.TextColumn("Opportunity", width="large"),
            "Status": st.column_config.TextColumn("Status", width="small"),
        },
    )
