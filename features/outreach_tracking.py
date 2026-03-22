"""Outreach Tracking — status tracking for volunteer outreach campaigns."""

import streamlit as st
from datetime import datetime


def init_outreach_state():
    """Initialize outreach tracking in session state.

    Keys: "volunteer|opportunity" -> {"status": "draft"/"sent"/"responded",
    "sent_date": None, "notes": ""}
    """
    if "outreach_status" not in st.session_state:
        st.session_state.outreach_status = {}
    if "action_log" not in st.session_state:
        st.session_state.action_log = []


def _outreach_key(volunteer: str, opportunity: str) -> str:
    return f"{volunteer}|{opportunity}"


def _status_badge_html(status: str) -> str:
    """Return colored HTML badge for the given status."""
    colors = {
        "draft": ("rgba(255,193,7,0.2)", "#ffe066", "rgba(255,193,7,0.3)"),
        "sent": ("rgba(0,123,255,0.2)", "#7ec8e3", "rgba(0,123,255,0.3)"),
        "responded": ("rgba(40,167,69,0.2)", "#6dd48f", "rgba(40,167,69,0.3)"),
    }
    bg, fg, border = colors.get(status, colors["draft"])
    label = status.capitalize()
    return (
        f'<span style="background:{bg};color:{fg};border:1px solid {border};'
        f'padding:2px 10px;border-radius:12px;font-size:0.82em">{label}</span>'
    )


def auto_create_draft(volunteer: str, opportunity: str):
    """Create a draft outreach entry when a match is approved."""
    init_outreach_state()
    key = _outreach_key(volunteer, opportunity)
    if key not in st.session_state.outreach_status:
        st.session_state.outreach_status[key] = {
            "status": "draft",
            "sent_date": None,
            "notes": "",
        }


def render_outreach_actions(volunteer: str, opportunity: str, outreach_type: str):
    """Render outreach status controls inside an expander.

    Displays a status badge, transition buttons, and a notes field.
    Uses volunteer+opportunity+outreach_type to build unique widget keys.
    """
    init_outreach_state()
    key = _outreach_key(volunteer, opportunity)

    # Ensure entry exists
    if key not in st.session_state.outreach_status:
        st.session_state.outreach_status[key] = {
            "status": "draft",
            "sent_date": None,
            "notes": "",
        }

    entry = st.session_state.outreach_status[key]
    status = entry["status"]

    # Status badge
    st.markdown(_status_badge_html(status), unsafe_allow_html=True)

    # Build a safe suffix for widget keys
    safe_key = f"{volunteer}_{opportunity}_{outreach_type}".replace(" ", "_")[:80]

    # Transition buttons
    col1, col2 = st.columns(2)
    with col1:
        if status == "draft":
            if st.button("📤 Mark as Sent", key=f"sent_{safe_key}"):
                entry["status"] = "sent"
                entry["sent_date"] = datetime.now().isoformat()
                st.session_state.action_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "action": "outreach_sent",
                    "volunteer": volunteer,
                    "opportunity": opportunity,
                    "type": outreach_type,
                })
                st.toast(f"Marked outreach to {volunteer} as sent!")
                st.rerun()

    with col2:
        if status == "sent":
            if st.button("✅ Mark Response Received", key=f"resp_{safe_key}"):
                entry["status"] = "responded"
                st.session_state.action_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "action": "outreach_responded",
                    "volunteer": volunteer,
                    "opportunity": opportunity,
                    "type": outreach_type,
                })
                st.toast(f"Response received from {volunteer}!")
                st.rerun()

    # Sent date display
    if entry["sent_date"]:
        sent_dt = datetime.fromisoformat(entry["sent_date"])
        st.caption(f"Sent on {sent_dt.strftime('%b %d, %Y at %I:%M %p')}")

    # Notes field
    notes_val = st.text_input(
        "Follow-up notes",
        value=entry["notes"],
        key=f"notes_{safe_key}",
        placeholder="Add follow-up notes...",
    )
    if notes_val != entry["notes"]:
        entry["notes"] = notes_val


def render_outreach_dashboard():
    """Render KPI cards summarizing outreach status at the top of Tab 4.

    Only renders if there are tracked outreach entries.
    """
    init_outreach_state()
    entries = st.session_state.outreach_status

    if not entries:
        return

    total = len(entries)
    sent_count = sum(1 for e in entries.values() if e["status"] in ("sent", "responded"))
    responded_count = sum(1 for e in entries.values() if e["status"] == "responded")
    response_rate = f"{responded_count / sent_count:.0%}" if sent_count > 0 else "N/A"

    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card accent">
            <div class="kpi-value">{total}</div>
            <div class="kpi-label">Total Tracked</div>
        </div>
        <div class="kpi-card green">
            <div class="kpi-value">{sent_count}</div>
            <div class="kpi-label">Sent</div>
        </div>
        <div class="kpi-card orange">
            <div class="kpi-value">{responded_count}</div>
            <div class="kpi-label">Responses</div>
        </div>
        <div class="kpi-card purple">
            <div class="kpi-value">{response_rate}</div>
            <div class="kpi-label">Response Rate</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
