"""IA West Smart Match CRM — Streamlit Dashboard."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.data_loader import load_all
from src.db import is_supabase_mode
from src.matching_engine import compute_matches, get_top_matches, explain_match
from src.outreach_generator import generate_outreach
from src.discovery import run_discovery_simulation, get_discovery_stats, get_expansion_roadmap
from src.pipeline_tracker import (
    generate_mock_pipeline, get_pipeline_summary, get_funnel_data,
    get_metrics_by_volunteer, get_metrics_by_event_type, get_metrics_by_region,
    PIPELINE_STAGES, STAGE_COLORS, STAGE_CONVERSION_RATES,
)
from src.university_scraper import UNIVERSITY_TEMPLATES
from features.match_approval import (
    init_match_state, log_action, get_decision_badge,
    render_match_actions, render_decision_summary,
)
from features.interactive_pipeline import (
    init_pipeline_state, get_pipeline_df,
    render_add_to_pipeline_form, render_pipeline_controls,
    add_to_pipeline_from_match,
)
from features.outreach_tracking import (
    init_outreach_state, render_outreach_actions,
    render_outreach_dashboard, auto_create_draft,
)
from features.discovery_sim import (
    init_discovery_state, render_discovery_scan_button,
    render_discovery_add_to_pipeline,
)

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="IA West Smart Match",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS — Premium visual styling
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Global ── */
.block-container { padding-top: 1rem; }

/* ── Hero banner ── */
.hero-banner {
    background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    border-radius: 16px;
    padding: 2.5rem 2rem;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(255,255,255,0.08);
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(0,123,255,0.15) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-banner h1 {
    font-size: 2.4rem;
    font-weight: 700;
    margin: 0 0 0.3rem 0;
    background: linear-gradient(90deg, #ffffff 0%, #7ec8e3 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero-banner p {
    color: #a0b4c8;
    font-size: 1.05rem;
    margin: 0;
}

/* ── KPI Cards ── */
.kpi-row {
    display: flex;
    gap: 1rem;
    margin: 1.5rem 0;
    flex-wrap: wrap;
}
.kpi-card {
    flex: 1;
    min-width: 160px;
    background: linear-gradient(145deg, #1a1f2e 0%, #141924 100%);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    text-align: center;
}
.kpi-card .kpi-value {
    font-size: 2rem;
    font-weight: 700;
    color: #7ec8e3;
    line-height: 1.2;
}
.kpi-card .kpi-label {
    font-size: 0.8rem;
    color: #8899aa;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.3rem;
}
.kpi-card.accent { border-left: 3px solid #007bff; }
.kpi-card.green { border-left: 3px solid #28a745; }
.kpi-card.orange { border-left: 3px solid #ffc107; }
.kpi-card.purple { border-left: 3px solid #9b59b6; }

/* ── Section headers ── */
.section-header {
    font-size: 1.3rem;
    font-weight: 600;
    color: #e8eef3;
    padding-bottom: 0.5rem;
    margin-top: 1.5rem;
    border-bottom: 2px solid rgba(0,123,255,0.3);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* ── Match cards ── */
.match-card {
    background: linear-gradient(145deg, #1a1f2e 0%, #161b27 100%);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.8rem;
    transition: border-color 0.2s;
}
.match-card:hover { border-color: rgba(0,123,255,0.4); }
.match-card .match-title {
    font-size: 1rem;
    font-weight: 600;
    color: #e8eef3;
}
.match-card .match-subtitle {
    font-size: 0.85rem;
    color: #8899aa;
}

/* ── Score bar ── */
.score-bar-container {
    background: rgba(255,255,255,0.05);
    border-radius: 8px;
    height: 8px;
    width: 100%;
    margin-top: 0.4rem;
}
.score-bar {
    height: 8px;
    border-radius: 8px;
    background: linear-gradient(90deg, #007bff 0%, #28a745 100%);
}

/* ── Expertise tags ── */
.tag-pill {
    background: rgba(0,123,255,0.15);
    color: #7ec8e3;
    padding: 4px 12px;
    border-radius: 20px;
    margin: 3px;
    display: inline-block;
    font-size: 0.82em;
    border: 1px solid rgba(0,123,255,0.2);
}

/* ── Fit badges ── */
.fit-high { background: rgba(40,167,69,0.2); color: #6dd48f; border: 1px solid rgba(40,167,69,0.3); padding: 2px 10px; border-radius: 12px; font-size: 0.82em; }
.fit-medium { background: rgba(255,193,7,0.2); color: #ffe066; border: 1px solid rgba(255,193,7,0.3); padding: 2px 10px; border-radius: 12px; font-size: 0.82em; }
.fit-low { background: rgba(220,53,69,0.2); color: #ff8a95; border: 1px solid rgba(220,53,69,0.3); padding: 2px 10px; border-radius: 12px; font-size: 0.82em; }

/* ── Email preview ── */
.email-preview {
    background: #1a1f2e;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 1.5rem;
    font-family: 'Georgia', serif;
    font-size: 0.9rem;
    line-height: 1.6;
    color: #c8d6e5;
    white-space: pre-wrap;
}

/* ── Phase cards (roadmap) ── */
.phase-card {
    background: linear-gradient(145deg, #1a1f2e 0%, #161b27 100%);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.8rem;
}
.phase-card.priority-immediate { border-left: 3px solid #dc3545; }
.phase-card.priority-high { border-left: 3px solid #ffc107; }
.phase-card.priority-medium { border-left: 3px solid #007bff; }

/* ── Plotly chart backgrounds ── */
.stPlotlyChart { border-radius: 12px; overflow: hidden; }

/* ── Sidebar polish ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0e1117 0%, #141924 100%);
}
[data-testid="stSidebar"] .block-container { padding-top: 1rem; }

/* ── Tabs styling ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 0.5rem 1rem;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    return load_all()

@st.cache_data
def compute_all_matches(speakers, cpp_events, cpp_courses, event_calendar):
    event_matches = compute_matches(speakers, cpp_events, event_calendar, opp_type="event")
    course_matches = compute_matches(speakers, cpp_courses, event_calendar, opp_type="course")
    all_matches = pd.concat([event_matches, course_matches], ignore_index=True)
    all_matches = all_matches.sort_values("match_score", ascending=False).reset_index(drop=True)
    return event_matches, course_matches, all_matches

data = load_data()
speakers = data["speakers"]
cpp_events = data["cpp_events"]
event_calendar = data["event_calendar"]
cpp_courses = data["cpp_courses"]

event_matches, course_matches, all_matches = compute_all_matches(
    speakers, cpp_events, cpp_courses, event_calendar
)

# ─────────────────────────────────────────────
# SESSION STATE INITIALIZATION
# ─────────────────────────────────────────────
init_match_state()
init_pipeline_state(speakers, cpp_events, all_matches)
init_outreach_state()
init_discovery_state()


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎯 Smart Match")
    st.caption("AI-Powered Volunteer CRM")
    st.markdown("---")

    st.markdown("##### How Matching Works")
    st.markdown("""
    ```
    SCORE = 0.30 × Topic
         + 0.25 × Role Fit
         + 0.20 × Geography
         + 0.10 × Calendar
         + 0.10 × Student Interest
         + 0.05 × Experience
    ```
    """)

    st.markdown("---")

    st.markdown("##### Algorithm Details")
    st.markdown("""
    | Component | Method |
    |-----------|--------|
    | **Topic** | TF-IDF cosine similarity |
    | **Role** | Keyword taxonomy match |
    | **Geo** | Metro region clustering |
    | **Calendar** | IA event overlap |
    | **Interest** | Enrollment + audience signals |
    | **Experience** | Seniority parsing |
    """)

    st.markdown("---")
    st.caption("CPP AI Hackathon 2026")
    st.caption("IA West · Community Growth & Membership")

    # Data mode indicator
    if is_supabase_mode():
        st.success("🔗 Connected to Supabase", icon="🔗")
    else:
        st.info("📁 Demo Mode (CSV)", icon="📁")

    # Activity feed
    if st.session_state.action_log:
        st.markdown("---")
        st.markdown("##### 📋 Recent Activity")
        action_icons = {
            "Approved": "✅", "Rejected": "❌", "Shortlisted": "⭐",
            "pipeline_add": "➕", "pipeline_advance": "⏩",
            "pipeline_revert": "⏪", "pipeline_add_from_match": "🎯",
            "pipeline_stage_edit": "✏️",
            "outreach_sent": "📤", "outreach_responded": "📬",
        }
        for entry in reversed(st.session_state.action_log[-5:]):
            icon = action_icons.get(entry["action"], "📌")
            details = entry.get("details", entry.get("volunteer", ""))
            ts = entry["timestamp"].split("T")[-1][:8] if "T" in entry["timestamp"] else entry["timestamp"][-8:]
            st.caption(f"{icon} {details} · {ts}")


# ─────────────────────────────────────────────
# HERO BANNER
# ─────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
    <h1>🎯 IA West Smart Match</h1>
    <p>AI-powered CRM that matches IA West board member volunteers to university engagement opportunities using a 6-component scoring algorithm, then tracks the membership conversion pipeline.</p>
</div>
""", unsafe_allow_html=True)

# KPI Cards
avg_score = all_matches["match_score"].mean()
top_match_pct = f"{all_matches['match_score'].max():.0%}"
st.markdown(f"""
<div class="kpi-row">
    <div class="kpi-card accent">
        <div class="kpi-value">{len(speakers)}</div>
        <div class="kpi-label">Board Members</div>
    </div>
    <div class="kpi-card green">
        <div class="kpi-value">{len(cpp_events) + len(cpp_courses)}</div>
        <div class="kpi-label">Opportunities</div>
    </div>
    <div class="kpi-card orange">
        <div class="kpi-value">{len(all_matches):,}</div>
        <div class="kpi-label">Match Pairs Scored</div>
    </div>
    <div class="kpi-card purple">
        <div class="kpi-value">{top_match_pct}</div>
        <div class="kpi-label">Best Match Score</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "👥 Volunteers",
    "🎓 Opportunities",
    "🎯 Smart Matches",
    "✉️ Outreach",
    "📈 Pipeline",
    "🔍 Discovery",
])


# ═══════════════════════════════════════════════
# TAB 1 — VOLUNTEER PROFILES
# ═══════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">👥 IA West Board Members</div>', unsafe_allow_html=True)
    st.caption("The supply side — 17 board member volunteers with expertise, roles, and metro regions.")

    col1, col2 = st.columns(2)
    with col1:
        region_filter = st.multiselect(
            "Filter by metro region",
            options=sorted(speakers["metro_region"].unique()),
            key="volunteer_region_filter",
        )
    with col2:
        search = st.text_input("Search expertise", key="volunteer_search",
                               placeholder="e.g. AI, healthcare, focus groups")

    filtered = speakers.copy()
    if region_filter:
        filtered = filtered[filtered["metro_region"].isin(region_filter)]
    if search:
        filtered = filtered[filtered["expertise_tags"].str.contains(search, case=False, na=False)]

    st.caption(f"Showing {len(filtered)} of {len(speakers)} members")

    # Volunteer profile cards
    for _, row in filtered.iterrows():
        tags = row.get("expertise_list", [])
        tag_html = "".join([f'<span class="tag-pill">{t}</span>' for t in tags])

        volunteer_matches = all_matches[all_matches["volunteer"] == row["name"]].head(3)
        matches_html = ""
        if not volunteer_matches.empty:
            for _, m in volunteer_matches.iterrows():
                pct = int(m["match_score"] * 100)
                matches_html += f"""
                <div style="margin:4px 0;display:flex;justify-content:space-between;align-items:center">
                    <span style="color:#c8d6e5;font-size:0.85em">{m['opportunity']}</span>
                    <span style="color:#7ec8e3;font-weight:600;font-size:0.85em">{pct}%</span>
                </div>
                <div class="score-bar-container"><div class="score-bar" style="width:{pct}%"></div></div>
                """

        with st.expander(f"**{row['name']}** — {row['board_role']}", expanded=False):
            c1, c2 = st.columns([2, 3])
            with c1:
                st.markdown(f"""
                **🏢** {row['company']}
                **💼** {row['title']}
                **📍** {row['metro_region']}
                """)
            with c2:
                st.markdown(tag_html, unsafe_allow_html=True)
                if matches_html:
                    st.markdown("**Top matches:**")
                    st.markdown(matches_html, unsafe_allow_html=True)

    # Region chart
    st.markdown('<div class="section-header">📍 Geographic Distribution</div>', unsafe_allow_html=True)
    region_counts = speakers["metro_region"].value_counts().reset_index()
    region_counts.columns = ["Region", "Count"]
    fig = px.bar(region_counts, x="Region", y="Count", color="Count",
                 color_continuous_scale=["#1a3a5c", "#007bff", "#7ec8e3"], text="Count")
    fig.update_layout(showlegend=False, height=320,
                      margin=dict(l=0, r=0, t=10, b=0),
                      coloraxis_showscale=False,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                      yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
    fig.update_traces(textposition="outside", marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════
# TAB 2 — OPPORTUNITIES
# ═══════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">🎓 University Opportunities</div>', unsafe_allow_html=True)
    st.caption("The demand side — events, courses, and regional conferences seeking board member volunteers.")

    opp_sub1, opp_sub2, opp_sub3 = st.tabs(["🎪 CPP Events", "📚 CPP Courses", "🗓️ IA Calendar"])

    with opp_sub1:
        st.markdown(f'<div class="section-header">🎪 Cal Poly Pomona Events ({len(cpp_events)})</div>', unsafe_allow_html=True)

        for _, row in cpp_events.iterrows():
            with st.expander(f"**{row['event_name']}** — {row['category']}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Host:** {row['host']}")
                    st.markdown(f"**Recurrence:** {row['recurrence']}")
                    st.markdown(f"**Audience:** {row['audience']}")
                with c2:
                    st.markdown(f"**Volunteer roles:** {row['volunteer_roles']}")
                    st.markdown(f"**Contact:** {row['contact_name']}")
                    st.markdown(f"**Email:** {row['contact_email']}")
                    if pd.notna(row.get("url")):
                        st.markdown(f"[🔗 Event page]({row['url']})")

        cat_counts = cpp_events["category"].value_counts().reset_index()
        cat_counts.columns = ["Category", "Count"]
        fig = px.pie(cat_counts, names="Category", values="Count",
                     hole=0.5, color_discrete_sequence=["#007bff", "#28a745", "#ffc107", "#9b59b6", "#e74c3c"])
        fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0),
                          paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    with opp_sub2:
        st.markdown('<div class="section-header">📚 CPP Course Sections</div>', unsafe_allow_html=True)
        st.caption("Each course rated for guest lecture fit based on curriculum alignment.")

        fit_filter = st.multiselect(
            "Filter by guest lecture fit",
            options=["High", "Medium", "Low"],
            default=["High", "Medium"],
            key="course_fit",
        )

        filtered_courses = cpp_courses[cpp_courses["guest_lecture_fit"].isin(fit_filter)]
        st.dataframe(
            filtered_courses[["instructor", "course", "title", "days", "start_time",
                             "end_time", "enrollment_cap", "mode", "guest_lecture_fit"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "enrollment_cap": st.column_config.NumberColumn("Cap"),
                "guest_lecture_fit": st.column_config.TextColumn("Fit"),
            },
        )

        # Fit distribution
        fit_counts = cpp_courses["guest_lecture_fit"].value_counts().reset_index()
        fit_counts.columns = ["Fit Level", "Count"]
        fig = px.bar(fit_counts, x="Fit Level", y="Count", color="Fit Level",
                     color_discrete_map={"High": "#28a745", "Medium": "#ffc107", "Low": "#dc3545"},
                     text="Count")
        fig.update_layout(showlegend=False, height=280,
                          margin=dict(l=0, r=0, t=10, b=0),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                          yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

    with opp_sub3:
        st.markdown('<div class="section-header">🗓️ IA West 2026 Regional Calendar</div>', unsafe_allow_html=True)

        cal_display = event_calendar.copy()
        cal_display["event_date"] = cal_display["event_date"].dt.strftime("%B %d, %Y")
        st.dataframe(
            cal_display[["event_date", "region", "nearby_universities",
                        "lecture_window", "course_alignment"]],
            use_container_width=True,
            hide_index=True,
        )

        fig = px.timeline(
            event_calendar.assign(
                end=event_calendar["event_date"] + pd.Timedelta(days=1),
                label=event_calendar["region"],
            ),
            x_start="event_date", x_end="end", y="label",
            color="region",
            color_discrete_sequence=["#007bff", "#28a745", "#ffc107", "#9b59b6", "#e74c3c", "#1abc9c"],
        )
        fig.update_layout(showlegend=False, yaxis_title="",
                          height=280, margin=dict(l=0, r=0, t=10, b=0),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════
# TAB 3 — SMART MATCHES
# ═══════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">🎯 Smart Match Recommendations</div>', unsafe_allow_html=True)
    st.caption("Every volunteer scored against every opportunity using a 5-component weighted algorithm.")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        match_type = st.selectbox("Opportunity type", ["All", "event", "course"])
    with col2:
        min_score = st.slider("Minimum score", 0.0, 1.0, 0.3, 0.05)
    with col3:
        top_n = st.number_input("Show top N", min_value=5, max_value=100, value=20)

    display_matches = all_matches.copy()
    if match_type != "All":
        display_matches = display_matches[display_matches["opportunity_type"] == match_type]
    display_matches = display_matches[display_matches["match_score"] >= min_score].head(top_n)

    # Score distribution
    st.markdown('<div class="section-header">📊 Score Distribution</div>', unsafe_allow_html=True)
    fig = px.histogram(all_matches, x="match_score", nbins=30,
                       color="opportunity_type", barmode="overlay",
                       labels={"match_score": "Match Score", "opportunity_type": "Type"},
                       color_discrete_map={"event": "#007bff", "course": "#28a745"})
    fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                      yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
    st.plotly_chart(fig, use_container_width=True)

    # Ranked leaderboard
    st.markdown(f'<div class="section-header">🏆 Top {len(display_matches)} Matches</div>', unsafe_allow_html=True)
    st.dataframe(
        display_matches[["volunteer", "volunteer_role", "opportunity", "opportunity_type",
                         "topic_relevance", "role_fit", "geographic_proximity",
                         "calendar_fit", "student_interest", "match_score"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "match_score": st.column_config.ProgressColumn(
                "Match Score", format="%.0f%%", min_value=0, max_value=1,
            ),
            "topic_relevance": st.column_config.ProgressColumn(
                "Topic", format="%.0f%%", min_value=0, max_value=1,
            ),
            "role_fit": st.column_config.ProgressColumn(
                "Role Fit", format="%.0f%%", min_value=0, max_value=1,
            ),
            "geographic_proximity": st.column_config.ProgressColumn(
                "Geo", format="%.0f%%", min_value=0, max_value=1,
            ),
            "calendar_fit": st.column_config.ProgressColumn(
                "Calendar", format="%.0f%%", min_value=0, max_value=1,
            ),
            "student_interest": st.column_config.ProgressColumn(
                "Interest", format="%.0f%%", min_value=0, max_value=1,
            ),
        },
    )

    # Match detail cards with radar charts
    st.markdown('<div class="section-header">🔍 Match Explanations</div>', unsafe_allow_html=True)
    st.caption("Click any match to see why the algorithm recommended it.")
    for idx, row in display_matches.head(10).iterrows():
        score_pct = f"{row['match_score']:.0%}"
        with st.expander(f"**{row['volunteer']}** → {row['opportunity']} — **{score_pct}**"):
            c1, c2 = st.columns([3, 2])
            with c1:
                explanation = explain_match(row)
                st.markdown(explanation)
            with c2:
                categories = ["Topic", "Role Fit", "Geography", "Calendar", "Interest", "Experience"]
                values = [row["topic_relevance"], row["role_fit"],
                          row["geographic_proximity"], row["calendar_fit"],
                          row["student_interest"], row["historical_bonus"]]

                fig = go.Figure(data=go.Scatterpolar(
                    r=values + [values[0]],
                    theta=categories + [categories[0]],
                    fill="toself",
                    fillcolor="rgba(0,123,255,0.15)",
                    line=dict(color="#7ec8e3", width=2),
                    marker=dict(size=6, color="#7ec8e3"),
                ))
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 1],
                                        gridcolor="rgba(255,255,255,0.08)",
                                        linecolor="rgba(255,255,255,0.08)"),
                        angularaxis=dict(gridcolor="rgba(255,255,255,0.08)",
                                          linecolor="rgba(255,255,255,0.08)"),
                        bgcolor="rgba(0,0,0,0)",
                    ),
                    showlegend=False,
                    height=260,
                    margin=dict(l=40, r=40, t=20, b=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#a0b4c8"),
                )
                st.plotly_chart(fig, use_container_width=True, key=f"radar_{idx}")

            # Match approval buttons
            render_match_actions(row["volunteer"], row["opportunity"], idx)

    # Heatmap
    st.markdown('<div class="section-header">🗺️ Volunteer × Opportunity Heatmap</div>', unsafe_allow_html=True)
    st.caption("Top 8 opportunities by average score.")
    top_opps = all_matches.groupby("opportunity")["match_score"].mean().nlargest(8).index.tolist()
    heatmap_data = all_matches[all_matches["opportunity"].isin(top_opps)]
    pivot = heatmap_data.pivot_table(
        index="volunteer", columns="opportunity", values="match_score", aggfunc="first"
    )
    fig = px.imshow(
        pivot, color_continuous_scale=["#0e1117", "#1a3a5c", "#28a745", "#7ec8e3"], aspect="auto",
        labels={"color": "Score"},
    )
    fig.update_layout(height=450, margin=dict(l=0, r=0, t=10, b=0),
                      paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(color="#a0b4c8"))
    st.plotly_chart(fig, use_container_width=True)

    # Decision summary
    render_decision_summary(all_matches)


# ═══════════════════════════════════════════════
# TAB 4 — OUTREACH
# ═══════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">✉️ Outreach Email Generator</div>', unsafe_allow_html=True)
    st.caption("Generate personalized invitation emails — ready to send.")

    # Outreach dashboard KPIs
    render_outreach_dashboard()

    col1, col2 = st.columns(2)
    with col1:
        selected_volunteer = st.selectbox(
            "Select volunteer",
            options=["All"] + sorted(speakers["name"].tolist()),
            key="outreach_volunteer",
        )
    with col2:
        outreach_type = st.selectbox(
            "Opportunity type",
            options=["event", "course"],
            key="outreach_type",
        )

    outreach_matches = all_matches[all_matches["opportunity_type"] == outreach_type]
    if selected_volunteer != "All":
        outreach_matches = outreach_matches[outreach_matches["volunteer"] == selected_volunteer]
    outreach_matches = outreach_matches.head(5)

    if outreach_matches.empty:
        st.info("No matches found for the selected filters.")
    else:
        for _, match_row in outreach_matches.iterrows():
            volunteer_data = speakers[speakers["name"] == match_row["volunteer"]].iloc[0]
            enriched = match_row.to_dict()
            enriched["volunteer_title"] = volunteer_data.get("title", "")
            enriched["volunteer_company"] = volunteer_data.get("company", "")

            opp_data = {}
            if outreach_type == "event":
                opp_rows = cpp_events[cpp_events["event_name"] == match_row["opportunity"]]
                if not opp_rows.empty:
                    opp_data = opp_rows.iloc[0].to_dict()
            else:
                opp_rows = cpp_courses[cpp_courses["title"] == match_row["opportunity"]]
                if not opp_rows.empty:
                    opp_data = opp_rows.iloc[0].to_dict()

            email = generate_outreach(enriched, opp_data, outreach_type)
            score_pct = f"{match_row['match_score']:.0%}"

            with st.expander(f"✉️ **{match_row['volunteer']}** → {match_row['opportunity']} ({score_pct})"):
                st.markdown(f'<div class="email-preview">{email}</div>', unsafe_allow_html=True)
                st.download_button(
                    label="📥 Download draft",
                    data=email,
                    file_name=f"outreach_{match_row['volunteer'].replace(' ', '_')}_{match_row['opportunity'][:30].replace(' ', '_')}.txt",
                    mime="text/plain",
                    key=f"dl_{match_row['volunteer']}_{match_row['opportunity']}_{outreach_type}",
                )
                st.markdown("---")
                render_outreach_actions(match_row['volunteer'], match_row['opportunity'], outreach_type)


# ═══════════════════════════════════════════════
# TAB 5 — PIPELINE
# ═══════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-header">📈 Engagement Pipeline</div>', unsafe_allow_html=True)
    st.caption("Track the journey from opportunity identification to IA membership conversion.")

    # Add to pipeline form
    with st.expander("➕ Add new pipeline entry", expanded=False):
        render_add_to_pipeline_form(speakers, cpp_events)

    pipeline = get_pipeline_df()
    summary = get_pipeline_summary(pipeline)
    funnel = get_funnel_data(pipeline)

    # KPI row
    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card accent">
            <div class="kpi-value">{summary['total_entries']}</div>
            <div class="kpi-label">Total Entries</div>
        </div>
        <div class="kpi-card green">
            <div class="kpi-value">{summary['active_pipeline']}</div>
            <div class="kpi-label">Active Pipeline</div>
        </div>
        <div class="kpi-card orange">
            <div class="kpi-value">{summary['conversion_rate']:.1%}</div>
            <div class="kpi-label">Conversion Rate</div>
        </div>
        <div class="kpi-card purple">
            <div class="kpi-value">{summary["unique_volunteers"]}</div>
            <div class="kpi-label">Volunteers Engaged</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Funnel + Conversion side by side
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-header">Conversion Funnel</div>', unsafe_allow_html=True)
        fig = go.Figure(go.Funnel(
            y=funnel["stage"],
            x=funnel["count"],
            textinfo="value+percent initial",
            marker=dict(color=[STAGE_COLORS[s] for s in funnel["stage"]]),
        ))
        fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font=dict(color="#a0b4c8"))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Actual vs Benchmark</div>', unsafe_allow_html=True)
        conversions = summary["stage_conversions"]
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[f"{c['from']} →\n{c['to']}" for c in conversions],
            y=[c['rate'] for c in conversions],
            name="Actual",
            marker_color="#007bff",
        ))
        fig.add_trace(go.Scatter(
            x=[f"{c['from']} →\n{c['to']}" for c in conversions],
            y=[c['benchmark'] for c in conversions],
            name="Benchmark",
            mode="markers+lines",
            marker=dict(color="#ff6b6b", size=8),
            line=dict(dash="dash", color="#ff6b6b"),
        ))
        fig.update_layout(
            yaxis_title="Rate", yaxis_tickformat=".0%",
            height=380, margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            font=dict(color="#a0b4c8"),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Sub-breakdowns
    pipe_sub1, pipe_sub2, pipe_sub3 = st.tabs(["By Volunteer", "By Event Type", "By Region"])

    with pipe_sub1:
        volunteer_metrics = get_metrics_by_volunteer(pipeline)
        if not volunteer_metrics.empty:
            st.dataframe(
                volunteer_metrics[["volunteer", "total_entries", "furthest_stage",
                                 "region", "avg_stage_index"]].rename(columns={
                    "avg_stage_index": "Avg Progress"
                }),
                use_container_width=True, hide_index=True,
                column_config={
                    "Avg Progress": st.column_config.ProgressColumn("Progress", min_value=0, max_value=7),
                },
            )
            fig = px.bar(volunteer_metrics.head(10), x="volunteer", y="avg_stage_index",
                         color="furthest_stage",
                         labels={"avg_stage_index": "Avg Progress"})
            fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font=dict(color="#a0b4c8"))
            st.plotly_chart(fig, use_container_width=True, key="pipe_volunteer_chart")

    with pipe_sub2:
        event_metrics = get_metrics_by_event_type(pipeline)
        if not event_metrics.empty:
            st.dataframe(
                event_metrics.rename(columns={"avg_stage_index": "Avg Progress"}),
                use_container_width=True, hide_index=True,
            )
            fig = px.bar(event_metrics, x="event_type", y="conversion_rate",
                         color="event_type",
                         labels={"conversion_rate": "Conversion Rate"})
            fig.update_layout(yaxis_tickformat=".0%", showlegend=False,
                              height=320, margin=dict(l=0, r=0, t=10, b=0),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font=dict(color="#a0b4c8"))
            st.plotly_chart(fig, use_container_width=True, key="pipe_event_chart")

    with pipe_sub3:
        region_metrics = get_metrics_by_region(pipeline)
        if not region_metrics.empty:
            st.dataframe(
                region_metrics.rename(columns={"avg_stage_index": "Avg Progress"}),
                use_container_width=True, hide_index=True,
            )
            fig = px.bar(region_metrics, x="region", y="total_entries",
                         color="conversion_rate",
                         color_continuous_scale=["#1a3a5c", "#28a745", "#7ec8e3"])
            fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font=dict(color="#a0b4c8"))
            st.plotly_chart(fig, use_container_width=True, key="pipe_region_chart")

    # Stage breakdown
    st.markdown('<div class="section-header">Pipeline by Stage</div>', unsafe_allow_html=True)
    stage_df = pd.DataFrame([
        {"Stage": stage, "Count": summary["by_stage"].get(stage, 0)}
        for stage in PIPELINE_STAGES
    ])
    fig = px.bar(stage_df, x="Stage", y="Count", color="Stage",
                 color_discrete_map=STAGE_COLORS, text="Count")
    fig.update_layout(showlegend=False, height=280,
                      margin=dict(l=0, r=0, t=10, b=0),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color="#a0b4c8"))
    fig.update_traces(textposition="outside", marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 Pipeline manager — edit stages, advance, or revert entries"):
        render_pipeline_controls(pipeline)


# ═══════════════════════════════════════════════
# TAB 6 — DISCOVERY
# ═══════════════════════════════════════════════
with tab6:
    st.markdown('<div class="section-header">🔍 Opportunity Discovery Engine</div>', unsafe_allow_html=True)
    st.caption("Automated discovery across IA West's university network.")

    disc_sub1, disc_sub2, disc_sub3 = st.tabs(["🔎 Discoveries", "🕷️ Scraping Templates", "🗺️ Expansion Roadmap"])

    with disc_sub1:
        # Discovery scan button with progress animation
        scan_completed = render_discovery_scan_button()

        discoveries = run_discovery_simulation()
        real_discoveries = discoveries[discoveries["status"] != "Queued"]
        scan_targets = discoveries[discoveries["status"] == "Queued"]
        stats = get_discovery_stats(discoveries)

        if st.session_state.discovery_timestamp:
            from datetime import datetime
            ts = datetime.fromisoformat(st.session_state.discovery_timestamp)
            st.caption(f"Last scan: {ts.strftime('%b %d, %Y at %I:%M %p')}")

        # KPI row
        st.markdown(f"""
        <div class="kpi-row">
            <div class="kpi-card accent">
                <div class="kpi-value">{stats['total_opportunities']}</div>
                <div class="kpi-label">Opportunities Found</div>
            </div>
            <div class="kpi-card green">
                <div class="kpi-value">{stats['universities_scanned']}</div>
                <div class="kpi-label">Universities Scanned</div>
            </div>
            <div class="kpi-card orange">
                <div class="kpi-value">{stats['high_fit_count']}</div>
                <div class="kpi-label">High-Fit Matches</div>
            </div>
            <div class="kpi-card purple">
                <div class="kpi-value">{stats['scan_targets']}</div>
                <div class="kpi-label">Scan Targets Queued</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Region + Type side by side
        col1, col2 = st.columns(2)
        with col1:
            region_df = pd.DataFrame([
                {"Region": k, "Opportunities": v} for k, v in stats["by_region"].items()
            ])
            if not region_df.empty:
                fig = px.bar(region_df, x="Region", y="Opportunities", color="Region",
                             color_discrete_sequence=["#007bff", "#28a745", "#ffc107", "#9b59b6", "#e74c3c"],
                             text="Opportunities")
                fig.update_layout(showlegend=False, height=280,
                                  margin=dict(l=0, r=0, t=10, b=0),
                                  paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                  font=dict(color="#a0b4c8"))
                fig.update_traces(textposition="outside", marker_line_width=0)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            type_df = pd.DataFrame([
                {"Type": k, "Count": v} for k, v in stats["by_type"].items()
            ])
            if not type_df.empty:
                fig = px.pie(type_df, names="Type", values="Count",
                             hole=0.5,
                             color_discrete_sequence=["#007bff", "#28a745", "#ffc107", "#9b59b6"])
                fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0),
                                  paper_bgcolor="rgba(0,0,0,0)",
                                  font=dict(color="#a0b4c8"))
                st.plotly_chart(fig, use_container_width=True)

        # By university
        if "by_university" in stats and stats["by_university"]:
            st.markdown('<div class="section-header">🏛️ By University</div>', unsafe_allow_html=True)
            uni_df = pd.DataFrame([
                {"University": k, "Count": v}
                for k, v in stats["by_university"].items()
            ]).sort_values("Count", ascending=False)
            fig = px.bar(uni_df, x="University", y="Count", color="Count",
                         color_continuous_scale=["#1a3a5c", "#007bff", "#7ec8e3"], text="Count")
            fig.update_layout(showlegend=False, height=320,
                              margin=dict(l=0, r=0, t=10, b=0),
                              coloraxis_showscale=False,
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font=dict(color="#a0b4c8"))
            fig.update_traces(textposition="outside", marker_line_width=0)
            st.plotly_chart(fig, use_container_width=True)

        # Results table
        st.markdown('<div class="section-header">📋 All Discoveries</div>', unsafe_allow_html=True)
        uni_filter = st.multiselect(
            "Filter by university",
            options=sorted(real_discoveries["university"].unique()) if not real_discoveries.empty else [],
            key="disc_uni",
        )
        display_disc = real_discoveries if not uni_filter else real_discoveries[real_discoveries["university"].isin(uni_filter)]
        if not display_disc.empty:
            st.dataframe(
                display_disc[["university", "region", "opportunity_name", "opportunity_type",
                              "fit_level", "description", "status"]],
                use_container_width=True, hide_index=True,
            )

            # Add high-fit discoveries to pipeline
            st.markdown('<div class="section-header">🎯 Add High-Fit Discoveries to Pipeline</div>', unsafe_allow_html=True)
            render_discovery_add_to_pipeline(display_disc)

    with disc_sub2:
        st.markdown('<div class="section-header">🕷️ University Scraping Templates</div>', unsafe_allow_html=True)
        st.caption("Pre-configured URL patterns and HTML selectors for automated discovery at scale.")

        for tmpl in UNIVERSITY_TEMPLATES:
            with st.expander(f"**{tmpl.name}** — {tmpl.region}"):
                st.markdown(f"**🌐 Base URL:** `{tmpl.base_url}`")
                st.markdown(f"**🏛️ Department:** {tmpl.department}")
                st.markdown("**📄 Event pages:**")
                for url in tmpl.get_event_urls():
                    st.markdown(f"- `{url}`")
                if tmpl.course_catalog_url:
                    st.markdown(f"**📚 Course catalog:** `{tmpl.course_catalog_url}`")
                if tmpl.selectors:
                    st.markdown("**🔧 HTML selectors:**")
                    for key, sel in tmpl.selectors.items():
                        st.markdown(f"- `{key}`: `{sel}`")

        if not scan_targets.empty:
            st.markdown('<div class="section-header">Queued Scan Targets</div>', unsafe_allow_html=True)
            st.dataframe(
                scan_targets[["university", "region", "opportunity_name",
                              "description", "status"]].rename(columns={"description": "Target URL"}),
                use_container_width=True, hide_index=True,
            )

    with disc_sub3:
        st.markdown('<div class="section-header">🗺️ University Expansion Roadmap</div>', unsafe_allow_html=True)
        st.caption("Phased rollout plan for expanding IA West's university network.")

        for phase in get_expansion_roadmap():
            priority_class = {"Immediate": "priority-immediate", "High": "priority-high", "Medium": "priority-medium"}.get(phase["priority"], "")
            priority_icon = {"Immediate": "🔴", "High": "🟠", "Medium": "🔵"}.get(phase["priority"], "⚪")
            template_status = "✅ Template ready" if phase.get("template_ready") else "⬜ Template needed"

            st.markdown(f"""
            <div class="phase-card {priority_class}">
                <div style="font-weight:600;font-size:1.05rem;color:#e8eef3">{priority_icon} {phase['phase']} — {phase['region']}</div>
                <div style="color:#8899aa;font-size:0.9rem;margin-top:0.5rem">
                    <strong>Universities:</strong> {', '.join(phase['universities'])}<br>
                    <strong>Rationale:</strong> {phase['rationale']}<br>
                    <strong>Est. opportunities:</strong> {phase['estimated_opportunities']}<br>
                    <strong>Template:</strong> {template_status}
                </div>
            </div>
            """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;padding:1rem 0">
    <span style="color:#4a5568;font-size:0.85em">
        IA West Smart Match CRM · CPP AI Hackathon 2026 · 
        Community Growth & Membership · Built with Streamlit + scikit-learn + TF-IDF
    </span>
</div>
""", unsafe_allow_html=True)
