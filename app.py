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
from src.executive_analytics import (
    compute_roi_projection, compute_coverage, compute_volunteer_scores,
    generate_insights, compute_pipeline_timeline, compute_stage_velocity,
)
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
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "👥 Volunteers",
    "🎓 Opportunities",
    "🎯 Smart Matches",
    "✉️ Outreach",
    "📈 Pipeline",
    "🔍 Discovery",
    "📊 Executive",
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
    score_cols = ["topic_relevance", "role_fit", "geographic_proximity",
                  "calendar_fit", "student_interest", "match_score"]
    leaderboard = display_matches[["volunteer", "volunteer_role", "opportunity",
                                    "opportunity_type"] + score_cols].copy()
    for col in score_cols:
        leaderboard[col] = (leaderboard[col] * 100).round(0)
    st.dataframe(
        leaderboard,
        use_container_width=True,
        hide_index=True,
        column_config={
            "match_score": st.column_config.ProgressColumn(
                "Match Score", format="%.0f%%", min_value=0, max_value=100,
            ),
            "topic_relevance": st.column_config.ProgressColumn(
                "Topic", format="%.0f%%", min_value=0, max_value=100,
            ),
            "role_fit": st.column_config.ProgressColumn(
                "Role Fit", format="%.0f%%", min_value=0, max_value=100,
            ),
            "geographic_proximity": st.column_config.ProgressColumn(
                "Geo", format="%.0f%%", min_value=0, max_value=100,
            ),
            "calendar_fit": st.column_config.ProgressColumn(
                "Calendar", format="%.0f%%", min_value=0, max_value=100,
            ),
            "student_interest": st.column_config.ProgressColumn(
                "Interest", format="%.0f%%", min_value=0, max_value=100,
            ),
        },
    )

    # Scoring methodology
    with st.expander("📐 How Smart Match Scores Work", expanded=False):
        st.markdown("""
Each volunteer-opportunity pair is scored across **6 independent components**, then combined into a single composite score:

| Component | Weight | Data Source | Method |
|-----------|--------|-------------|--------|
| **Topic Relevance** | 30% | Volunteer expertise tags vs. opportunity description | TF-IDF cosine similarity with bigrams — measures how well a volunteer's skills match what the opportunity needs |
| **Role Fit** | 25% | Volunteer title/role vs. opportunity role requirements | Keyword taxonomy matching — "Judge", "Mentor", "Speaker" etc. matched against event needs |
| **Geographic Proximity** | 20% | Volunteer metro region vs. opportunity location | Metro region clustering — volunteers near the event score higher (same region = 1.0, adjacent = 0.6) |
| **Calendar Fit** | 10% | IA event calendar vs. opportunity region | Checks if an IA regional event overlaps with the opportunity's area, enabling a combined trip |
| **Student Interest** | 10% | Course enrollment cap / event audience scope | Proxy for demand — high-enrollment courses and open-audience events score higher |
| **Experience Level** | 5% | Volunteer title seniority keywords | Parses titles for seniority indicators (VP, Director, Senior → higher score) |

**Composite formula:** `SCORE = 0.30×Topic + 0.25×Role + 0.20×Geo + 0.10×Calendar + 0.10×Interest + 0.05×Experience`

Scores range from 0% (no match) to 100% (perfect match). A score above **50%** indicates a strong pairing worth pursuing.
""")

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
    st.caption("Top 10 opportunities by average score. Cell values show match percentage.")
    top_opps = all_matches.groupby("opportunity")["match_score"].mean().nlargest(10).index.tolist()
    heatmap_data = all_matches[all_matches["opportunity"].isin(top_opps)]
    pivot = heatmap_data.pivot_table(
        index="volunteer", columns="opportunity", values="match_score", aggfunc="first"
    ).fillna(0)

    # Shorten opportunity names for readability
    short_names = {name: (name[:30] + "…" if len(name) > 30 else name) for name in pivot.columns}
    pivot = pivot.rename(columns=short_names)

    # Annotated heatmap with percentage labels
    text_matrix = (pivot * 100).round(0).astype(int).astype(str) + "%"
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        text=text_matrix.values,
        texttemplate="%{text}",
        textfont=dict(size=11, color="white"),
        colorscale=[
            [0.0, "#0e1117"],
            [0.3, "#1a3a5c"],
            [0.5, "#2563eb"],
            [0.7, "#f59e0b"],
            [0.85, "#ef4444"],
            [1.0, "#ff2d55"],
        ],
        colorbar=dict(
            title="Score",
            tickformat=".0%",
            tickvals=[0, 0.25, 0.5, 0.75, 1.0],
            ticktext=["0%", "25%", "50%", "75%", "100%"],
            len=0.8,
        ),
        hovertemplate="<b>%{y}</b> → %{x}<br>Score: %{z:.0%}<extra></extra>",
        xgap=2,
        ygap=2,
    ))
    fig.update_layout(
        height=max(400, len(pivot) * 35 + 100),
        margin=dict(l=0, r=0, t=10, b=120),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#a0b4c8"),
        xaxis=dict(side="bottom", tickangle=-45),
        yaxis=dict(autorange="reversed"),
    )
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
    # Purpose statement
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0f2027 0%, #1a3a5c 100%);
                border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;
                border: 1px solid rgba(255,255,255,0.08);">
        <h3 style="color: #ffffff; margin: 0 0 0.5rem 0;">📈 Membership Conversion Pipeline</h3>
        <p style="color: #8899aa; margin: 0; font-size: 0.95rem;">
            <strong>Goal:</strong> Turn university engagement opportunities into IA West members.<br>
            Every match starts at <em>Identified</em> and moves through 8 stages toward <em>Member</em>.
            This pipeline tracks where each volunteer-opportunity pair stands and identifies bottlenecks in conversion.
        </p>
    </div>
    """, unsafe_allow_html=True)

    pipeline = get_pipeline_df()
    summary = get_pipeline_summary(pipeline)
    funnel = get_funnel_data(pipeline)
    conversions = summary["stage_conversions"]

    # ── Visual stage flow with counts ──
    stage_icons = {
        "Identified": "🔍", "Outreach Sent": "📤", "Engaged": "💬",
        "Event Scheduled": "📅", "Event Completed": "✅", "Follow-Up": "📞",
        "Membership Lead": "🌟", "Member": "🏆",
    }
    stage_html = ""
    for i, stage in enumerate(PIPELINE_STAGES):
        count = summary["by_stage"].get(stage, 0)
        color = STAGE_COLORS[stage]
        icon = stage_icons.get(stage, "📌")
        arrow = ' <span style="color:#4a5568;font-size:1.2rem;">→</span> ' if i < len(PIPELINE_STAGES) - 1 else ""
        stage_html += (
            f'<span style="display:inline-block;background:{color};color:white;'
            f'padding:6px 12px;border-radius:20px;font-size:0.82rem;margin:3px 2px;'
            f'white-space:nowrap;">{icon} {stage} <strong>({count})</strong></span>{arrow}'
        )
    st.markdown(
        f'<div style="text-align:center;padding:0.5rem 0;line-height:2.5;">{stage_html}</div>',
        unsafe_allow_html=True,
    )

    # ── KPI row ──
    members = summary["by_stage"].get("Member", 0)
    leads = summary["by_stage"].get("Membership Lead", 0)
    active_in_funnel = summary["total_entries"] - summary["by_stage"].get("Identified", 0) - members
    drop_offs = summary["total_entries"] - sum(
        1 for entry in pipeline.to_dict("records") if entry.get("stage_index", 0) >= 1
    )
    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card accent">
            <div class="kpi-value">{summary['total_entries']}</div>
            <div class="kpi-label">Matches Entered</div>
        </div>
        <div class="kpi-card green">
            <div class="kpi-value">{active_in_funnel}</div>
            <div class="kpi-label">In Progress</div>
        </div>
        <div class="kpi-card purple">
            <div class="kpi-value">{leads + members}</div>
            <div class="kpi-label">Leads + Members</div>
        </div>
        <div class="kpi-card orange">
            <div class="kpi-value">{summary['conversion_rate']:.1%}</div>
            <div class="kpi-label">End-to-End Conversion</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Main visuals: Funnel + Bottleneck Analysis ──
    col_funnel, col_bottleneck = st.columns(2)

    with col_funnel:
        st.markdown('<div class="section-header">Conversion Funnel</div>', unsafe_allow_html=True)
        st.caption("How many matches survive each stage.")
        fig = go.Figure(go.Funnel(
            y=funnel["stage"],
            x=funnel["count"],
            textinfo="value+percent initial",
            marker=dict(color=[STAGE_COLORS[s] for s in funnel["stage"]]),
            connector=dict(line=dict(color="rgba(255,255,255,0.1)", width=1)),
        ))
        fig.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font=dict(color="#a0b4c8"))
        st.plotly_chart(fig, use_container_width=True)

    with col_bottleneck:
        st.markdown('<div class="section-header">Where Are We Losing People?</div>', unsafe_allow_html=True)
        st.caption("Stage-to-stage drop-off rates. Red = biggest bottleneck.")

        # Calculate drop-off at each transition
        drop_data = []
        for c in conversions:
            dropped = c["from_count"] - c["to_count"]
            drop_rate = 1 - c["rate"] if c["from_count"] > 0 else 0
            drop_data.append({
                "transition": f"{c['from']} →\n{c['to']}",
                "dropped": dropped,
                "drop_rate": drop_rate,
                "survived": c["to_count"],
                "benchmark_drop": 1 - c["benchmark"],
            })
        drop_df = pd.DataFrame(drop_data)

        # Color bars by severity — worst drop-off is red
        max_drop = drop_df["drop_rate"].max() if not drop_df.empty else 1
        bar_colors = []
        for rate in drop_df["drop_rate"]:
            if rate >= max_drop * 0.8:
                bar_colors.append("#ef4444")  # Red — worst bottleneck
            elif rate >= 0.3:
                bar_colors.append("#f59e0b")  # Amber — concerning
            else:
                bar_colors.append("#22c55e")  # Green — healthy
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=drop_df["transition"],
            y=drop_df["drop_rate"],
            text=drop_df.apply(lambda r: f"{r['drop_rate']:.0%} ({r['dropped']} lost)", axis=1),
            textposition="outside",
            marker_color=bar_colors,
            name="Actual Drop-off",
        ))
        fig.add_trace(go.Scatter(
            x=drop_df["transition"],
            y=drop_df["benchmark_drop"],
            name="Expected Drop-off",
            mode="markers+lines",
            marker=dict(color="#94a3b8", size=7),
            line=dict(dash="dot", color="#94a3b8"),
        ))
        fig.update_layout(
            yaxis_title="Drop-off Rate", yaxis_tickformat=".0%",
            height=420, margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickfont=dict(size=10)),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            font=dict(color="#a0b4c8"),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Breakdowns ──
    st.markdown('<div class="section-header">Pipeline Breakdown</div>', unsafe_allow_html=True)
    pipe_sub1, pipe_sub2, pipe_sub3 = st.tabs(["👤 By Volunteer", "🎯 By Event Type", "📍 By Region"])

    with pipe_sub1:
        volunteer_metrics = get_metrics_by_volunteer(pipeline)
        if not volunteer_metrics.empty:
            # Horizontal bar chart — most engaged volunteers
            vm = volunteer_metrics.head(12)
            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=vm["volunteer"],
                x=vm["avg_stage_index"],
                orientation="h",
                marker_color=[STAGE_COLORS.get(s, "#6c757d") for s in vm["furthest_stage"]],
                text=vm["furthest_stage"],
                textposition="inside",
                hovertemplate="<b>%{y}</b><br>Entries: %{customdata[0]}<br>Furthest: %{text}<extra></extra>",
                customdata=vm[["total_entries"]].values,
            ))
            fig.update_layout(
                height=400, margin=dict(l=0, r=0, t=10, b=0),
                xaxis=dict(title="Avg Pipeline Progress (0-7)", gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(autorange="reversed"),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#a0b4c8"),
            )
            st.plotly_chart(fig, use_container_width=True, key="pipe_volunteer_chart")

    with pipe_sub2:
        event_metrics = get_metrics_by_event_type(pipeline)
        if not event_metrics.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=event_metrics["event_type"],
                y=event_metrics["conversion_rate"],
                text=event_metrics.apply(
                    lambda r: f"{r['conversion_rate']:.0%} ({r['converted']}/{r['total_entries']})", axis=1
                ),
                textposition="outside",
                marker_color="#007bff",
            ))
            fig.update_layout(
                yaxis_title="Conversion Rate", yaxis_tickformat=".0%",
                height=350, margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                font=dict(color="#a0b4c8"),
            )
            st.plotly_chart(fig, use_container_width=True, key="pipe_event_chart")

    with pipe_sub3:
        region_metrics = get_metrics_by_region(pipeline)
        if not region_metrics.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=region_metrics["region"],
                y=region_metrics["total_entries"],
                text=region_metrics.apply(
                    lambda r: f"{r['conversion_rate']:.0%} conv.", axis=1
                ),
                textposition="outside",
                marker_color=region_metrics["conversion_rate"].apply(
                    lambda r: "#ef4444" if r < 0.02 else "#f59e0b" if r < 0.05 else "#22c55e"
                ),
                hovertemplate="<b>%{x}</b><br>Entries: %{y}<br>Converted: %{customdata[0]}<br>Volunteers: %{customdata[1]}<extra></extra>",
                customdata=region_metrics[["converted", "unique_volunteers"]].values,
            ))
            fig.update_layout(
                yaxis_title="Pipeline Entries",
                height=350, margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                font=dict(color="#a0b4c8"),
            )
            st.plotly_chart(fig, use_container_width=True, key="pipe_region_chart")

    # ── Pipeline Manager ──
    st.markdown("---")
    col_add, col_manage = st.columns([1, 2])
    with col_add:
        st.markdown("##### ➕ Add Entry")
        render_add_to_pipeline_form(speakers, cpp_events)
    with col_manage:
        st.markdown("##### ⚙️ Manage Pipeline")
        st.caption("Edit stages, advance or revert entries.")
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


# ═══════════════════════════════════════════════
# TAB 7 — EXECUTIVE ANALYTICS
# ═══════════════════════════════════════════════
with tab7:
    st.markdown('<div class="section-header">📊 Executive Analytics & ROI</div>', unsafe_allow_html=True)
    st.caption("Strategic insights, ROI projections, and coverage analysis for IA West leadership.")

    pipeline = get_pipeline_df()

    # Compute analytics
    roi = compute_roi_projection(pipeline)
    coverage = compute_coverage(all_matches)
    vol_scores = compute_volunteer_scores(all_matches, pipeline)
    insights = generate_insights(all_matches, pipeline, coverage, vol_scores)

    # ── Strategic Insights ──
    st.markdown('<div class="section-header">💡 Strategic Insights</div>', unsafe_allow_html=True)

    severity_styles = {
        "high": ("border-left: 3px solid #dc3545;", "🔴"),
        "medium": ("border-left: 3px solid #ffc107;", "🟡"),
        "low": ("border-left: 3px solid #28a745;", "🟢"),
        "info": ("border-left: 3px solid #007bff;", "🔵"),
    }

    for insight in insights:
        style, icon = severity_styles.get(insight["severity"], ("", "📌"))
        st.markdown(f"""
        <div class="match-card" style="{style}">
            <div class="match-title">{icon} {insight['title']}</div>
            <div class="match-subtitle" style="margin-top:0.4rem">{insight['detail']}</div>
            <div style="margin-top:0.3rem"><span class="tag-pill">{insight['category']}</span></div>
        </div>
        """, unsafe_allow_html=True)

    # ── ROI Projection ──
    exec_sub1, exec_sub2, exec_sub3, exec_sub4 = st.tabs([
        "💰 ROI Projection", "🎯 Coverage Analysis",
        "👤 Volunteer Scores", "📅 Pipeline Trends",
    ])

    with exec_sub1:
        st.markdown('<div class="section-header">💰 3-Year ROI Projection</div>', unsafe_allow_html=True)

        # ROI KPIs
        yr3 = roi["projections"][-1]
        st.markdown(f"""
        <div class="kpi-row">
            <div class="kpi-card accent">
                <div class="kpi-value">{roi['hours_saved_per_cycle']}h</div>
                <div class="kpi-label">Hours Saved / Cycle</div>
            </div>
            <div class="kpi-card green">
                <div class="kpi-value">${roi['labor_savings_per_cycle']:,}</div>
                <div class="kpi-label">Labor Savings / Cycle</div>
            </div>
            <div class="kpi-card orange">
                <div class="kpi-value">{yr3['cumulative_members']}</div>
                <div class="kpi-label">Projected Members (Yr 3)</div>
            </div>
            <div class="kpi-card purple">
                <div class="kpi-value">${yr3['cumulative_value']:,}</div>
                <div class="kpi-label">Cumulative Value (Yr 3)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Stacked bar: revenue breakdown by year
        proj_df = pd.DataFrame(roi["projections"])
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=proj_df["label"], y=proj_df["membership_revenue"],
            name="Membership Revenue", marker_color="#007bff",
        ))
        fig.add_trace(go.Bar(
            x=proj_df["label"], y=proj_df["engagement_value"],
            name="Engagement Value", marker_color="#28a745",
        ))
        fig.add_trace(go.Bar(
            x=proj_df["label"], y=proj_df["labor_savings"],
            name="Labor Savings", marker_color="#ffc107",
        ))
        fig.update_layout(
            barmode="stack", yaxis_title="Value ($)",
            height=380, margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            font=dict(color="#a0b4c8"),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Cumulative value line
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=proj_df["label"], y=proj_df["cumulative_value"],
            mode="lines+markers+text",
            text=[f"${v:,}" for v in proj_df["cumulative_value"]],
            textposition="top center",
            line=dict(color="#7ec8e3", width=3),
            marker=dict(size=10, color="#7ec8e3"),
            fill="tozeroy", fillcolor="rgba(126,200,227,0.1)",
        ))
        fig2.update_layout(
            yaxis_title="Cumulative Value ($)", xaxis_title="",
            height=300, margin=dict(l=0, r=0, t=30, b=0),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            font=dict(color="#a0b4c8"),
        )
        st.plotly_chart(fig2, use_container_width=True)

        # Assumptions
        with st.expander("📐 ROI Model Assumptions"):
            st.markdown(f"""
            | Parameter | Value |
            |-----------|-------|
            | Annual membership dues | ${250} |
            | Event engagement value | ${150}/participation |
            | Manual match+outreach time | {45} min |
            | Smart Match outreach time | {5} min |
            | Coordinator hourly rate | ${35}/hr |
            | Growth rate | 15%/year |
            | Match cycles/year | 2 (spring + fall) |
            """)

    with exec_sub2:
        st.markdown('<div class="section-header">🎯 Opportunity Coverage Analysis</div>', unsafe_allow_html=True)
        st.caption(f"Score threshold: 50%. How well are opportunities covered by volunteer matches?")

        # Coverage KPIs
        st.markdown(f"""
        <div class="kpi-row">
            <div class="kpi-card green">
                <div class="kpi-value">{coverage['well_covered']}</div>
                <div class="kpi-label">Well Covered (3+ matches)</div>
            </div>
            <div class="kpi-card orange">
                <div class="kpi-value">{coverage['partial']}</div>
                <div class="kpi-label">Partial (1-2 matches)</div>
            </div>
            <div class="kpi-card" style="border-left:3px solid #dc3545">
                <div class="kpi-value">{coverage['gaps']}</div>
                <div class="kpi-label">Coverage Gaps</div>
            </div>
            <div class="kpi-card accent">
                <div class="kpi-value">{coverage['coverage_pct']:.0%}</div>
                <div class="kpi-label">Full Coverage Rate</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Coverage breakdown chart
        cov_df = coverage["details"]
        status_colors = {"Well Covered": "#28a745", "Partial": "#ffc107", "Gap": "#dc3545"}
        fig = px.bar(
            cov_df.sort_values("best_score", ascending=True),
            x="best_score", y="opportunity", orientation="h",
            color="coverage_status",
            color_discrete_map=status_colors,
            labels={"best_score": "Best Match Score", "opportunity": ""},
        )
        fig.add_vline(x=0.5, line_dash="dash", line_color="rgba(255,255,255,0.3)")
        fig.update_layout(
            height=max(400, len(cov_df) * 22),
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
            font=dict(color="#a0b4c8"),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Detail table
        with st.expander("📋 Coverage Details"):
            cov_display = cov_df[["opportunity", "best_score", "avg_score", "strong_matches", "coverage_status"]].copy()
            cov_display["best_score"] = (cov_display["best_score"] * 100).round(0)
            cov_display["avg_score"] = (cov_display["avg_score"] * 100).round(0)
            st.dataframe(
                cov_display,
                use_container_width=True, hide_index=True,
                column_config={
                    "best_score": st.column_config.ProgressColumn("Best Score", format="%.0f%%", min_value=0, max_value=100),
                    "avg_score": st.column_config.ProgressColumn("Avg Score", format="%.0f%%", min_value=0, max_value=100),
                },
            )

    with exec_sub3:
        st.markdown('<div class="section-header">👤 Volunteer Engagement Scores</div>', unsafe_allow_html=True)
        st.caption("Composite score: 40% avg match + 30% top match + 15% strong match count + 15% pipeline progress.")

        # Engagement leaderboard
        fig = px.bar(
            vol_scores.head(15),
            x="engagement_score", y="volunteer", orientation="h",
            color="engagement_score",
            color_continuous_scale=["#1a3a5c", "#007bff", "#28a745", "#7ec8e3"],
            text=vol_scores.head(15)["engagement_score"].apply(lambda x: f"{x:.0%}"),
        )
        fig.update_layout(
            height=500, margin=dict(l=0, r=0, t=10, b=0),
            coloraxis_showscale=False,
            yaxis=dict(autorange="reversed"),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Engagement Score"),
            font=dict(color="#a0b4c8"),
        )
        fig.update_traces(textposition="outside", marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

        # Full table
        vol_display = vol_scores[["volunteer", "avg_match_score", "top_match_score",
                                    "strong_matches", "pipeline_entries", "engagement_score"]].copy()
        for c in ["avg_match_score", "top_match_score", "engagement_score"]:
            vol_display[c] = (vol_display[c] * 100).round(0)
        st.dataframe(
            vol_display,
            use_container_width=True, hide_index=True,
            column_config={
                "avg_match_score": st.column_config.ProgressColumn("Avg Match", format="%.0f%%", min_value=0, max_value=100),
                "top_match_score": st.column_config.ProgressColumn("Top Match", format="%.0f%%", min_value=0, max_value=100),
                "engagement_score": st.column_config.ProgressColumn("Engagement", format="%.0f%%", min_value=0, max_value=100),
            },
        )

    with exec_sub4:
        st.markdown('<div class="section-header">📅 Pipeline Trends</div>', unsafe_allow_html=True)

        timeline = compute_pipeline_timeline(pipeline)
        velocity = compute_stage_velocity(pipeline)

        if not timeline.empty:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Cumulative Pipeline Growth**")
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=timeline["entry_date"], y=timeline["cumulative"],
                    mode="lines", fill="tozeroy",
                    line=dict(color="#007bff", width=2),
                    fillcolor="rgba(0,123,255,0.1)",
                ))
                fig.update_layout(
                    height=320, margin=dict(l=0, r=0, t=10, b=0),
                    xaxis_title="", yaxis_title="Entries",
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                    font=dict(color="#a0b4c8"),
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("**Weekly New Entries**")
                weekly = timeline.groupby("week")["new_entries"].sum().reset_index()
                fig = px.bar(weekly, x="week", y="new_entries",
                             labels={"week": "Week #", "new_entries": "New Entries"},
                             color="new_entries",
                             color_continuous_scale=["#1a3a5c", "#007bff", "#7ec8e3"])
                fig.update_layout(
                    height=320, margin=dict(l=0, r=0, t=10, b=0),
                    coloraxis_showscale=False,
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                    font=dict(color="#a0b4c8"),
                )
                st.plotly_chart(fig, use_container_width=True)

        if not velocity.empty:
            st.markdown("**Average Days in Pipeline by Stage**")
            fig = px.bar(velocity, x="stage", y="avg_days",
                         color="avg_days",
                         color_continuous_scale=["#28a745", "#ffc107", "#dc3545"],
                         text=velocity["avg_days"].apply(lambda x: f"{x:.0f}d"),
                         labels={"avg_days": "Avg Days", "stage": ""})
            fig.update_layout(
                height=320, margin=dict(l=0, r=0, t=10, b=0),
                coloraxis_showscale=False,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                font=dict(color="#a0b4c8"),
            )
            fig.update_traces(textposition="outside", marker_line_width=0)
            st.plotly_chart(fig, use_container_width=True)


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
