"""Outreach Tracking — status tracking, contact resolution, and response monitoring."""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime, timedelta
import random

from src.db import is_supabase_mode, get_outreach_entries_db, upsert_outreach_db
from src.outreach_generator import (
    generate_outreach, extract_subject_body, generate_mailto_url, validate_email,
)


def init_outreach_state():
    """Initialize outreach tracking in session state."""
    if "outreach_status" not in st.session_state:
        if is_supabase_mode():
            try:
                st.session_state.outreach_status = get_outreach_entries_db()
            except Exception:
                st.session_state.outreach_status = {}
        else:
            st.session_state.outreach_status = {}
    if "action_log" not in st.session_state:
        st.session_state.action_log = []


def _outreach_key(volunteer: str, opportunity: str) -> str:
    return f"{volunteer}|{opportunity}"


def _status_badge_html(status: str) -> str:
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
            "responded_date": None,
            "notes": "",
            "contact_email": "",
            "contact_name": "",
        }
        if is_supabase_mode():
            try:
                upsert_outreach_db(volunteer, opportunity, "draft")
            except Exception:
                pass


# ── Contact Info Display ─────────────────────────────────────────────

def render_contact_info(contact_name: str, contact_email: str, opp_name: str):
    """Display contact information with status indicator and mailto link."""
    has_email = bool(contact_email and contact_email not in ("See page", "", "N/A"))
    is_valid = validate_email(contact_email) if has_email else False

    if is_valid:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin:0.5rem 0">'
            f'<span style="color:#6dd48f;font-size:1.1em">✅</span>'
            f'<span style="color:#c8d6e5"><strong>{contact_name}</strong></span>'
            f'<a href="mailto:{contact_email}" style="color:#7ec8e3">{contact_email}</a>'
            f'</div>',
            unsafe_allow_html=True,
        )
    elif has_email:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin:0.5rem 0">'
            f'<span style="color:#ffe066;font-size:1.1em">⚠️</span>'
            f'<span style="color:#c8d6e5"><strong>{contact_name}</strong></span>'
            f'<span style="color:#8899aa">{contact_email}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;margin:0.5rem 0">'
            f'<span style="color:#ff8a95;font-size:1.1em">❌</span>'
            f'<span style="color:#c8d6e5"><strong>{contact_name or "Unknown Contact"}</strong></span>'
            f'<span style="color:#8899aa">No email found</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


# ── One-Click Send Actions ───────────────────────────────────────────

def render_send_actions(volunteer: str, opportunity: str, outreach_type: str,
                        email_text: str, contact_email: str, contact_name: str):
    """Render send email button (mailto:), copy to clipboard, and download."""
    safe_key = f"{volunteer}_{opportunity}_{outreach_type}".replace(" ", "_")[:80]
    parsed = extract_subject_body(email_text)

    has_valid_email = validate_email(contact_email) if contact_email else False

    col_send, col_copy, col_dl = st.columns(3)

    with col_send:
        if has_valid_email:
            mailto_url = generate_mailto_url(contact_email, parsed["subject"], parsed["body"])
            st.markdown(
                f'<a href="{mailto_url}" target="_blank" style="'
                f'display:inline-block;background:linear-gradient(135deg,#007bff,#0056b3);'
                f'color:white;padding:8px 20px;border-radius:8px;text-decoration:none;'
                f'font-weight:600;font-size:0.85rem;text-align:center;width:100%">'
                f'📧 Send Email</a>',
                unsafe_allow_html=True,
            )
        else:
            st.button("📧 Send Email", disabled=True, key=f"send_disabled_{safe_key}",
                       help="No valid contact email found")

    with col_copy:
        # JS-based copy to clipboard
        clean_text = email_text.replace("**", "").replace("*", "").replace("`", "\\`").replace("\n", "\\n")
        copy_js = f"""
        <button onclick="navigator.clipboard.writeText(`{clean_text}`).then(() => {{
            this.innerText = '✅ Copied!';
            setTimeout(() => this.innerText = '📋 Copy Email', 2000);
        }})" style="
            background: linear-gradient(135deg, #2c5364, #203a43);
            color: white; padding: 8px 20px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);
            cursor: pointer; font-weight: 600; font-size: 0.85rem; width: 100%;
        ">📋 Copy Email</button>
        """
        components.html(copy_js, height=42)

    with col_dl:
        st.download_button(
            label="📥 Download",
            data=email_text,
            file_name=f"outreach_{volunteer.replace(' ', '_')}_{opportunity[:30].replace(' ', '_')}.txt",
            mime="text/plain",
            key=f"dl_{safe_key}",
            use_container_width=True,
        )


def render_outreach_actions(volunteer: str, opportunity: str, outreach_type: str):
    """Render outreach status controls: status badge, transition buttons, notes."""
    init_outreach_state()
    key = _outreach_key(volunteer, opportunity)

    if key not in st.session_state.outreach_status:
        st.session_state.outreach_status[key] = {
            "status": "draft", "sent_date": None, "responded_date": None,
            "notes": "", "contact_email": "", "contact_name": "",
        }

    entry = st.session_state.outreach_status[key]
    status = entry["status"]

    st.markdown(_status_badge_html(status), unsafe_allow_html=True)

    safe_key = f"{volunteer}_{opportunity}_{outreach_type}".replace(" ", "_")[:80]

    col1, col2 = st.columns(2)
    with col1:
        if status == "draft":
            if st.button("📤 Mark as Sent", key=f"sent_{safe_key}"):
                entry["status"] = "sent"
                entry["sent_date"] = datetime.now().isoformat()
                st.session_state.action_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "action": "outreach_sent",
                    "details": f"Sent: {volunteer} → {opportunity}",
                    "volunteer": volunteer, "opportunity": opportunity,
                    "type": outreach_type,
                })
                if is_supabase_mode():
                    try:
                        upsert_outreach_db(volunteer, opportunity, "sent", entry["sent_date"])
                    except Exception:
                        pass
                st.toast(f"Marked outreach to {volunteer} as sent!")
                st.rerun()

    with col2:
        if status == "sent":
            if st.button("✅ Mark Response Received", key=f"resp_{safe_key}"):
                entry["status"] = "responded"
                entry["responded_date"] = datetime.now().isoformat()
                st.session_state.action_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "action": "outreach_responded",
                    "details": f"Response: {volunteer} → {opportunity}",
                    "volunteer": volunteer, "opportunity": opportunity,
                    "type": outreach_type,
                })
                if is_supabase_mode():
                    try:
                        upsert_outreach_db(volunteer, opportunity, "responded")
                    except Exception:
                        pass
                st.toast(f"Response received from {volunteer}!")
                st.rerun()

    if entry.get("sent_date"):
        sent_dt = datetime.fromisoformat(entry["sent_date"])
        days_ago = (datetime.now() - sent_dt).days
        st.caption(f"Sent on {sent_dt.strftime('%b %d, %Y at %I:%M %p')} ({days_ago}d ago)")

    notes_val = st.text_input(
        "Follow-up notes", value=entry.get("notes", ""),
        key=f"notes_{safe_key}", placeholder="Add follow-up notes...",
    )
    if notes_val != entry.get("notes", ""):
        entry["notes"] = notes_val


# ── Manual Add Form ──────────────────────────────────────────────────

def render_manual_outreach_form(speakers_df, events_df):
    """Render a form to manually add an outreach entry."""
    with st.expander("➕ Add Custom Outreach", expanded=False):
        with st.form("manual_outreach_form"):
            st.markdown("**Add an outreach entry for any volunteer-opportunity pair.**")

            form_col1, form_col2 = st.columns(2)
            with form_col1:
                volunteer = st.selectbox(
                    "Volunteer", options=sorted(speakers_df["name"].tolist()),
                    key="manual_outreach_vol",
                )
                opportunity = st.text_input("Opportunity Name", key="manual_outreach_opp",
                                            placeholder="e.g. Marketing Research Symposium")
                opp_type = st.selectbox("Type", ["event", "course"], key="manual_outreach_type")

            with form_col2:
                contact_name = st.text_input("Contact Name", key="manual_outreach_contact",
                                             placeholder="e.g. Dr. Sarah Johnson")
                contact_email = st.text_input("Contact Email", key="manual_outreach_email",
                                              placeholder="e.g. sjohnson@cpp.edu")
                notes = st.text_area("Notes", key="manual_outreach_notes",
                                     placeholder="Any context for this outreach...", height=80)

            submitted = st.form_submit_button("Add Outreach Entry", use_container_width=True)

            if submitted:
                if not volunteer or not opportunity:
                    st.error("Volunteer and Opportunity are required.")
                elif contact_email and not validate_email(contact_email):
                    st.error("Please enter a valid email address.")
                else:
                    key = _outreach_key(volunteer, opportunity)
                    st.session_state.outreach_status[key] = {
                        "status": "draft",
                        "sent_date": None,
                        "responded_date": None,
                        "notes": notes,
                        "contact_email": contact_email,
                        "contact_name": contact_name,
                    }
                    st.session_state.action_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "action": "outreach_manual_add",
                        "details": f"Added: {volunteer} → {opportunity}",
                        "volunteer": volunteer,
                        "opportunity": opportunity,
                    })
                    if is_supabase_mode():
                        try:
                            upsert_outreach_db(volunteer, opportunity, "draft", notes=notes)
                        except Exception:
                            pass
                    st.success(f"Added outreach entry: {volunteer} → {opportunity}")
                    st.rerun()


# ── Response Monitor ─────────────────────────────────────────────────

def render_response_monitor():
    """Render response monitoring section with pending outreach and simulation."""
    init_outreach_state()
    entries = st.session_state.outreach_status

    sent_entries = {k: v for k, v in entries.items() if v["status"] == "sent"}

    with st.expander(f"📬 Response Monitor ({len(sent_entries)} pending)", expanded=False):
        if not sent_entries:
            st.info("No outreach emails currently pending response. Mark emails as 'Sent' to track them here.")
            return

        st.markdown("**Pending Responses**")
        st.caption("Outreach emails awaiting replies, sorted by days waiting.")

        # Build pending table
        pending_data = []
        for key, entry in sent_entries.items():
            parts = key.split("|", 1)
            volunteer = parts[0] if len(parts) > 0 else ""
            opportunity = parts[1] if len(parts) > 1 else ""
            sent_date = entry.get("sent_date")
            if sent_date:
                try:
                    days = (datetime.now() - datetime.fromisoformat(sent_date)).days
                except (ValueError, TypeError):
                    days = 0
            else:
                days = 0

            urgency = "🔴" if days > 7 else "🟡" if days > 3 else "🟢"
            pending_data.append({
                "": urgency,
                "Volunteer": volunteer,
                "Opportunity": opportunity,
                "Days Waiting": days,
                "Notes": entry.get("notes", ""),
            })

        pending_df = pd.DataFrame(pending_data).sort_values("Days Waiting", ascending=False)
        st.dataframe(pending_df, use_container_width=True, hide_index=True)

        # Simulation button for demo
        st.markdown("---")
        sim_col1, sim_col2 = st.columns([2, 1])
        with sim_col1:
            st.markdown(
                '<span style="color:#8899aa;font-size:0.85em">'
                '💡 <em>In production, this connects to Gmail/Outlook APIs for automated response detection.</em></span>',
                unsafe_allow_html=True,
            )
        with sim_col2:
            if st.button("🎲 Simulate Response", key="sim_response",
                          help="Demo: simulate a response for testing"):
                if sent_entries:
                    # Pick a random sent entry
                    sim_key = random.choice(list(sent_entries.keys()))
                    entries[sim_key]["status"] = "responded"
                    entries[sim_key]["responded_date"] = datetime.now().isoformat()
                    parts = sim_key.split("|", 1)
                    st.session_state.action_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "action": "outreach_responded",
                        "details": f"Response: {parts[0]} → {parts[1]}",
                        "volunteer": parts[0],
                        "opportunity": parts[1] if len(parts) > 1 else "",
                    })
                    if is_supabase_mode():
                        try:
                            upsert_outreach_db(parts[0], parts[1] if len(parts) > 1 else "", "responded")
                        except Exception:
                            pass
                    st.balloons()
                    st.toast(f"Response received from {parts[0]}!")
                    st.rerun()


# ── Dashboard KPIs ───────────────────────────────────────────────────

def render_outreach_dashboard():
    """Render KPI cards and mini funnel summarizing outreach status."""
    init_outreach_state()
    entries = st.session_state.outreach_status

    if not entries:
        return

    total = len(entries)
    draft_count = sum(1 for e in entries.values() if e["status"] == "draft")
    sent_count = sum(1 for e in entries.values() if e["status"] in ("sent", "responded"))
    responded_count = sum(1 for e in entries.values() if e["status"] == "responded")
    response_rate = f"{responded_count / sent_count:.0%}" if sent_count > 0 else "N/A"

    # Count pending > 3 days
    pending_overdue = 0
    for e in entries.values():
        if e["status"] == "sent" and e.get("sent_date"):
            try:
                days = (datetime.now() - datetime.fromisoformat(e["sent_date"])).days
                if days > 3:
                    pending_overdue += 1
            except (ValueError, TypeError):
                pass

    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card accent">
            <div class="kpi-value">{total}</div>
            <div class="kpi-label">Total Tracked</div>
        </div>
        <div class="kpi-card" style="border-left: 3px solid #ffe066;">
            <div class="kpi-value">{draft_count}</div>
            <div class="kpi-label">Drafts</div>
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
        <div class="kpi-card" style="border-left: 3px solid #dc3545;">
            <div class="kpi-value">{pending_overdue}</div>
            <div class="kpi-label">Overdue (3d+)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Mini funnel visualization
    import plotly.graph_objects as go
    fig = go.Figure(go.Funnel(
        y=["Drafts", "Sent", "Responded"],
        x=[draft_count, sent_count - (sent_count - responded_count if responded_count < sent_count else 0), responded_count],
        textinfo="value+percent initial",
        marker=dict(color=["#ffc107", "#007bff", "#28a745"]),
        connector=dict(line=dict(color="rgba(255,255,255,0.1)", width=1)),
    ))
    fig.update_layout(
        title_text="Outreach Funnel", title_font_size=16, title_x=0.5,
        height=250, margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#a0b4c8"),
    )
    st.plotly_chart(fig, use_container_width=True, key="outreach_funnel")
