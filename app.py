"""IA West Smart Match CRM — Streamlit Dashboard."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.data_loader import load_all
from src.matching_engine import compute_matches, get_top_matches, explain_match
from src.outreach_generator import generate_outreach
from src.discovery import run_discovery_simulation, get_discovery_stats, get_expansion_roadmap
from src.pipeline_tracker import (
    generate_mock_pipeline, get_pipeline_summary, get_funnel_data,
    get_metrics_by_speaker, get_metrics_by_event_type, get_metrics_by_region,
    PIPELINE_STAGES, STAGE_COLORS, STAGE_CONVERSION_RATES,
)
from src.university_scraper import UNIVERSITY_TEMPLATES

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
# DATA LOADING (cached)
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
# SIDEBAR
# ─────────────────────────────────────────────
# The sidebar serves as the global navigation panel. It shows the
# project identity, key stats at a glance, and explains the matching
# algorithm — giving judges and viewers instant context.

with st.sidebar:
    st.title("🎯 IA West Smart Match")
    st.caption("AI-Powered Speaker-to-Opportunity CRM")

    st.markdown("---")

    # Quick stats — these 4 numbers tell the story at a glance
    st.markdown("##### 📊 Dataset Overview")
    c1, c2 = st.columns(2)
    c1.metric("Board Members", len(speakers))
    c2.metric("CPP Events", len(cpp_events))
    c1, c2 = st.columns(2)
    c1.metric("Course Sections", len(cpp_courses))
    c2.metric("Regional Events", len(event_calendar))

    st.metric("Total Match Pairs Scored", f"{len(all_matches):,}")

    st.markdown("---")

    # Algorithm explainer — judges will want to know how scoring works
    with st.expander("🧠 How matching works", expanded=False):
        st.markdown("""
        **Composite Score Formula:**
        ```
        SCORE = 0.35 × Topic Relevance
             + 0.25 × Role Fit
             + 0.20 × Geographic Proximity
             + 0.10 × Calendar Fit
             + 0.10 × Experience Bonus
        ```

        | Component | Method |
        |-----------|--------|
        | **Topic** | TF-IDF cosine similarity (bigram) |
        | **Role** | Keyword matching vs role taxonomy |
        | **Geo** | Metro region clustering + adjacency |
        | **Calendar** | IA event schedule overlap |
        | **Experience** | Parsed years + seniority titles |
        """)

    st.markdown("---")
    st.caption("CPP AI Hackathon 2026 · Built with Streamlit + scikit-learn")


# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
# Six tabs, each representing a core CRM capability.
# For the video walkthrough, go left to right — each tab
# builds on the previous one's context.

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "👥 Speakers",
    "🎓 Opportunities",
    "🎯 Smart Matches",
    "✉️ Outreach",
    "📈 Pipeline",
    "🔍 Discovery",
])


# ═══════════════════════════════════════════════
# TAB 1 — SPEAKER PROFILES
# ═══════════════════════════════════════════════
# This tab shows WHO is available. Each board member has
# expertise tags, a company/title, and a metro region.
# The region chart shows geographic distribution across
# IA West's footprint.

with tab1:
    st.header("IA West Board Members")
    st.caption("17 volunteer speakers with expertise tags, roles, and metro regions — the supply side of the matching equation.")

    # Filters row
    col1, col2 = st.columns(2)
    with col1:
        region_filter = st.multiselect(
            "Filter by metro region",
            options=sorted(speakers["metro_region"].unique()),
            key="speaker_region",
        )
    with col2:
        search = st.text_input("Search expertise tags", key="speaker_search",
                               placeholder="e.g. AI, healthcare, focus groups")

    filtered = speakers.copy()
    if region_filter:
        filtered = filtered[filtered["metro_region"].isin(region_filter)]
    if search:
        filtered = filtered[filtered["expertise_tags"].str.contains(search, case=False, na=False)]

    st.caption(f"Showing {len(filtered)} of {len(speakers)} members")

    # Speaker cards — each expander is a mini profile card
    for _, row in filtered.iterrows():
        with st.expander(f"**{row['name']}** — {row['board_role']}", expanded=False):
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown(f"**🏢 Company:** {row['company']}")
                st.markdown(f"**💼 Title:** {row['title']}")
                st.markdown(f"**📍 Region:** {row['metro_region']}")
            with c2:
                st.markdown("**🏷️ Expertise:**")
                tags = row.get("expertise_list", [])
                tag_html = " ".join(
                    [f'<span style="background:#1e3a5f;color:#7ec8e3;padding:3px 10px;border-radius:12px;margin:2px;display:inline-block;font-size:0.85em">{t}</span>' for t in tags]
                )
                st.markdown(tag_html, unsafe_allow_html=True)

                # Top 3 matches for this speaker — shows immediate value
                speaker_matches = all_matches[all_matches["speaker"] == row["name"]].head(3)
                if not speaker_matches.empty:
                    st.markdown("**🎯 Top matches:**")
                    for _, m in speaker_matches.iterrows():
                        score_pct = f"{m['match_score']:.0%}"
                        st.markdown(f"- {m['opportunity']} ({m['opportunity_type']}) — **{score_pct}**")

    # Region distribution — shows the geographic spread
    st.subheader("Geographic distribution")
    region_counts = speakers["metro_region"].value_counts().reset_index()
    region_counts.columns = ["Region", "Count"]
    fig = px.bar(region_counts, x="Region", y="Count", color="Count",
                 color_continuous_scale="Blues", text="Count")
    fig.update_layout(showlegend=False, height=350,
                      margin=dict(l=0, r=0, t=10, b=0),
                      coloraxis_showscale=False)
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════
# TAB 2 — OPPORTUNITIES
# ═══════════════════════════════════════════════
# This tab shows WHERE speakers can contribute. Three sub-tabs:
# CPP Events (hackathons, competitions, symposia),
# CPP Courses (guest lecture slots ranked by fit),
# and the IA Regional Calendar (upcoming events across the West).

with tab2:
    st.header("University Opportunities")
    st.caption("The demand side — events, courses, and regional conferences that need volunteer speakers.")

    opp_sub1, opp_sub2, opp_sub3 = st.tabs(["🎪 CPP Events", "📚 CPP Courses", "🗓️ IA Calendar"])

    with opp_sub1:
        st.subheader("Cal Poly Pomona events & programs")
        st.caption(f"{len(cpp_events)} events across hackathons, competitions, symposia, and workshops.")

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

        # Category breakdown
        cat_counts = cpp_events["category"].value_counts().reset_index()
        cat_counts.columns = ["Category", "Count"]
        fig = px.pie(cat_counts, names="Category", values="Count",
                     title="Events by category", hole=0.45,
                     color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(height=350, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with opp_sub2:
        st.subheader("CPP marketing course sections")
        st.caption("Each course is rated for guest lecture fit based on curriculum alignment.")

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
                "enrollment_cap": st.column_config.NumberColumn("Enrollment Cap"),
                "guest_lecture_fit": st.column_config.TextColumn("Fit Level"),
            },
        )

        # Fit distribution
        fit_counts = cpp_courses["guest_lecture_fit"].value_counts().reset_index()
        fit_counts.columns = ["Fit Level", "Count"]
        fig = px.bar(fit_counts, x="Fit Level", y="Count", color="Fit Level",
                     color_discrete_map={"High": "#28a745", "Medium": "#ffc107", "Low": "#dc3545"},
                     text="Count")
        fig.update_layout(showlegend=False, height=300,
                          margin=dict(l=0, r=0, t=10, b=0))
        fig.update_traces(textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with opp_sub3:
        st.subheader("IA West 2026 regional event calendar")
        st.caption("Upcoming IA events with suggested lecture windows for nearby universities.")

        cal_display = event_calendar.copy()
        cal_display["event_date"] = cal_display["event_date"].dt.strftime("%B %d, %Y")
        st.dataframe(
            cal_display[["event_date", "region", "nearby_universities",
                        "lecture_window", "course_alignment"]],
            use_container_width=True,
            hide_index=True,
        )

        # Timeline visualization
        fig = px.timeline(
            event_calendar.assign(
                end=event_calendar["event_date"] + pd.Timedelta(days=1),
                label=event_calendar["region"],
            ),
            x_start="event_date", x_end="end", y="label",
            color="region",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_layout(showlegend=False, yaxis_title="",
                          height=300, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════
# TAB 3 — SMART MATCHES
# ═══════════════════════════════════════════════
# This is the CORE of the product. The matching engine scores
# every speaker × opportunity pair using a 5-component weighted
# algorithm. This tab shows the ranked results, lets you filter,
# and provides detailed breakdowns with radar charts.

with tab3:
    st.header("Smart Match Recommendations")
    st.caption("Every speaker scored against every opportunity — ranked by composite match score.")

    # Filters row
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

    # Score distribution — shows the bell curve of all match scores
    st.subheader("Score distribution")
    st.caption("How match scores are distributed across all speaker-opportunity pairs.")
    fig = px.histogram(all_matches, x="match_score", nbins=30,
                       color="opportunity_type", barmode="overlay",
                       labels={"match_score": "Match Score", "opportunity_type": "Type"},
                       color_discrete_map={"event": "#007bff", "course": "#28a745"})
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig, use_container_width=True)

    # Top matches table — the ranked leaderboard
    st.subheader(f"Top {len(display_matches)} matches")
    st.dataframe(
        display_matches[["speaker", "speaker_role", "opportunity", "opportunity_type",
                         "topic_relevance", "role_fit", "geographic_proximity",
                         "calendar_fit", "match_score"]],
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
        },
    )

    # Detailed match explanations with radar charts
    st.subheader("Match details & explanations")
    st.caption("Click any match to see why the algorithm recommended it.")
    for idx, row in display_matches.head(10).iterrows():
        score_pct = f"{row['match_score']:.0%}"
        with st.expander(
            f"**{row['speaker']}** → {row['opportunity']} ({score_pct})"
        ):
            c1, c2 = st.columns([3, 2])
            with c1:
                explanation = explain_match(row)
                st.markdown(explanation)
            with c2:
                # Radar chart — visual breakdown of the 5 scoring components
                categories = ["Topic", "Role Fit", "Geography", "Calendar", "Experience"]
                values = [row["topic_relevance"], row["role_fit"],
                          row["geographic_proximity"], row["calendar_fit"],
                          row["historical_bonus"]]

                fig = go.Figure(data=go.Scatterpolar(
                    r=values + [values[0]],
                    theta=categories + [categories[0]],
                    fill="toself",
                    fillcolor="rgba(0,123,255,0.2)",
                    line=dict(color="#007bff", width=2),
                ))
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 1],
                                        gridcolor="rgba(255,255,255,0.1)"),
                        angularaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
                        bgcolor="rgba(0,0,0,0)",
                    ),
                    showlegend=False,
                    height=280,
                    margin=dict(l=50, r=50, t=20, b=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig, use_container_width=True, key=f"radar_{idx}")

    # Heatmap — birds-eye view of speaker × opportunity scores
    st.subheader("Speaker × Opportunity heatmap")
    st.caption("Top 8 opportunities by average score — darker = stronger match.")
    top_opps = all_matches.groupby("opportunity")["match_score"].mean().nlargest(8).index.tolist()
    heatmap_data = all_matches[all_matches["opportunity"].isin(top_opps)]
    pivot = heatmap_data.pivot_table(
        index="speaker", columns="opportunity", values="match_score", aggfunc="first"
    )
    fig = px.imshow(
        pivot, color_continuous_scale="YlGn", aspect="auto",
        labels={"color": "Score"},
    )
    fig.update_layout(height=500, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════
# TAB 4 — OUTREACH
# ═══════════════════════════════════════════════
# Once you've identified the best matches, this tab generates
# personalized outreach emails. Each email is pre-filled with
# the speaker's expertise, the opportunity details, and
# specific reasons why this match makes sense.

with tab4:
    st.header("Outreach Email Generator")
    st.caption("Generate personalized invitation emails for your top matches — ready to send.")

    col1, col2 = st.columns(2)
    with col1:
        selected_speaker = st.selectbox(
            "Select speaker",
            options=["All"] + sorted(speakers["name"].tolist()),
            key="outreach_speaker",
        )
    with col2:
        outreach_type = st.selectbox(
            "Opportunity type",
            options=["event", "course"],
            key="outreach_type",
        )

    outreach_matches = all_matches[all_matches["opportunity_type"] == outreach_type]
    if selected_speaker != "All":
        outreach_matches = outreach_matches[outreach_matches["speaker"] == selected_speaker]
    outreach_matches = outreach_matches.head(5)

    if outreach_matches.empty:
        st.info("No matches found for the selected filters.")
    else:
        for _, match_row in outreach_matches.iterrows():
            speaker_data = speakers[speakers["name"] == match_row["speaker"]].iloc[0]
            enriched = match_row.to_dict()
            enriched["speaker_title"] = speaker_data.get("title", "")
            enriched["speaker_company"] = speaker_data.get("company", "")

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

            with st.expander(
                f"✉️ {match_row['speaker']} → {match_row['opportunity']} ({score_pct})"
            ):
                st.code(email, language=None)
                st.download_button(
                    label="📥 Download draft",
                    data=email,
                    file_name=f"outreach_{match_row['speaker'].replace(' ', '_')}_{match_row['opportunity'][:30].replace(' ', '_')}.txt",
                    mime="text/plain",
                    key=f"dl_{match_row['speaker']}_{match_row['opportunity']}_{outreach_type}",
                )


# ═══════════════════════════════════════════════
# TAB 5 — PIPELINE
# ═══════════════════════════════════════════════
# This tab tracks the engagement funnel — from initial match
# identification all the way to IA membership conversion.
# It shows where speakers are in the pipeline, conversion
# rates at each stage, and comparisons to industry benchmarks.

with tab5:
    st.header("Engagement Pipeline")
    st.caption("Track the journey from opportunity identification to IA membership conversion.")

    pipeline = generate_mock_pipeline(speakers, cpp_events)
    summary = get_pipeline_summary(pipeline)
    funnel = get_funnel_data(pipeline)

    # KPI row — the 4 numbers that matter most
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Entries", summary["total_entries"])
    k2.metric("Active Pipeline", summary["active_pipeline"])
    k3.metric("Conversion Rate", f"{summary['conversion_rate']:.1%}")
    k4.metric("Speakers Engaged", summary["unique_speakers"])

    # Two-column layout: funnel + conversion rates side by side
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Conversion funnel")
        fig = go.Figure(go.Funnel(
            y=funnel["stage"],
            x=funnel["count"],
            textinfo="value+percent initial",
            marker=dict(color=[STAGE_COLORS[s] for s in funnel["stage"]]),
        ))
        fig.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Stage conversion vs benchmark")
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
            height=400, margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Breakdowns by speaker, event type, and region
    pipe_sub1, pipe_sub2, pipe_sub3 = st.tabs([
        "By Speaker", "By Event Type", "By Region"
    ])

    with pipe_sub1:
        speaker_metrics = get_metrics_by_speaker(pipeline)
        if not speaker_metrics.empty:
            st.dataframe(
                speaker_metrics[["speaker", "total_entries", "furthest_stage",
                                 "region", "avg_stage_index"]].rename(columns={
                    "avg_stage_index": "Avg Progress"
                }),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Avg Progress": st.column_config.ProgressColumn(
                        "Avg Progress", min_value=0, max_value=7,
                    ),
                },
            )
            fig = px.bar(speaker_metrics.head(10), x="speaker", y="avg_stage_index",
                         color="furthest_stage", title="Top 10 speakers by pipeline progress",
                         labels={"avg_stage_index": "Avg Stage Progress"})
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True, key="pipe_speaker_chart")

    with pipe_sub2:
        event_metrics = get_metrics_by_event_type(pipeline)
        if not event_metrics.empty:
            st.dataframe(
                event_metrics.rename(columns={"avg_stage_index": "Avg Progress"}),
                use_container_width=True,
                hide_index=True,
            )
            fig = px.bar(event_metrics, x="event_type", y="conversion_rate",
                         color="event_type",
                         title="Conversion rate by event type",
                         labels={"conversion_rate": "Conversion Rate"})
            fig.update_layout(yaxis_tickformat=".0%", showlegend=False,
                              height=350, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True, key="pipe_event_chart")

    with pipe_sub3:
        region_metrics = get_metrics_by_region(pipeline)
        if not region_metrics.empty:
            st.dataframe(
                region_metrics.rename(columns={"avg_stage_index": "Avg Progress"}),
                use_container_width=True,
                hide_index=True,
            )
            fig = px.bar(region_metrics, x="region", y="total_entries",
                         color="conversion_rate",
                         color_continuous_scale="YlGn",
                         title="Pipeline entries by region (colored by conversion rate)")
            fig.update_layout(height=350, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True, key="pipe_region_chart")

    # Stage breakdown bar
    st.subheader("Pipeline by stage")
    stage_df = pd.DataFrame([
        {"Stage": stage, "Count": summary["by_stage"].get(stage, 0)}
        for stage in PIPELINE_STAGES
    ])
    fig = px.bar(stage_df, x="Stage", y="Count", color="Stage",
                 color_discrete_map=STAGE_COLORS, text="Count")
    fig.update_layout(showlegend=False, height=300,
                      margin=dict(l=0, r=0, t=10, b=0))
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

    # Detailed pipeline table
    with st.expander("📋 Full pipeline details"):
        stage_filter = st.multiselect(
            "Filter by stage",
            options=PIPELINE_STAGES,
            default=PIPELINE_STAGES,
            key="pipeline_stage",
        )
        filtered_pipeline = pipeline[pipeline["stage"].isin(stage_filter)]
        st.dataframe(
            filtered_pipeline[["id", "speaker", "opportunity", "stage",
                              "entry_date", "last_updated", "notes"]],
            use_container_width=True,
            hide_index=True,
        )


# ═══════════════════════════════════════════════
# TAB 6 — DISCOVERY
# ═══════════════════════════════════════════════
# This tab shows the opportunity DISCOVERY engine — it
# identifies new volunteer opportunities at universities
# across IA West's regional footprint. Combines real CSV
# data with web scraping templates for scalable expansion.

with tab6:
    st.header("Opportunity Discovery Engine")
    st.caption("Automated discovery of new volunteer opportunities across IA West's university network.")

    disc_sub1, disc_sub2, disc_sub3 = st.tabs([
        "🔎 Discoveries", "🕷️ Scraping Templates", "🗺️ Expansion Roadmap"
    ])

    with disc_sub1:
        discoveries = run_discovery_simulation()
        real_discoveries = discoveries[discoveries["status"] != "Queued"]
        scan_targets = discoveries[discoveries["status"] == "Queued"]
        stats = get_discovery_stats(discoveries)

        # KPI row
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Opportunities Found", stats["total_opportunities"])
        d2.metric("Universities Scanned", stats["universities_scanned"])
        d3.metric("High-Fit Matches", stats["high_fit_count"])
        d4.metric("Scan Targets Queued", stats["scan_targets"])

        # Two-column: by region + by type
        col1, col2 = st.columns(2)
        with col1:
            region_df = pd.DataFrame([
                {"Region": k, "Opportunities": v} for k, v in stats["by_region"].items()
            ])
            if not region_df.empty:
                fig = px.bar(region_df, x="Region", y="Opportunities", color="Region",
                             color_discrete_sequence=px.colors.qualitative.Set2,
                             text="Opportunities")
                fig.update_layout(showlegend=False, height=300,
                                  margin=dict(l=0, r=0, t=10, b=0))
                fig.update_traces(textposition="outside")
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            type_df = pd.DataFrame([
                {"Type": k, "Count": v} for k, v in stats["by_type"].items()
            ])
            if not type_df.empty:
                fig = px.pie(type_df, names="Type", values="Count",
                             hole=0.45,
                             color_discrete_sequence=px.colors.qualitative.Set2)
                fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
                st.plotly_chart(fig, use_container_width=True)

        # Fit level breakdown
        if not real_discoveries.empty and "fit_level" in real_discoveries.columns:
            fit_df = real_discoveries["fit_level"].value_counts().reset_index()
            fit_df.columns = ["Fit Level", "Count"]
            st.subheader("Fit level breakdown")
            c1, c2, c3 = st.columns(3)
            for i, (_, r) in enumerate(fit_df.iterrows()):
                col = [c1, c2, c3][i % 3]
                col.metric(f"{r['Fit Level']} Fit", r["Count"])

        # By university
        if "by_university" in stats and stats["by_university"]:
            st.subheader("By university")
            uni_df = pd.DataFrame([
                {"University": k, "Count": v}
                for k, v in stats["by_university"].items()
            ]).sort_values("Count", ascending=False)
            fig = px.bar(uni_df, x="University", y="Count", color="Count",
                         color_continuous_scale="Blues", text="Count")
            fig.update_layout(showlegend=False, height=350,
                              margin=dict(l=0, r=0, t=10, b=0),
                              coloraxis_showscale=False)
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

        # Results table
        st.subheader("All discovered opportunities")
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
                use_container_width=True,
                hide_index=True,
            )

    with disc_sub2:
        st.subheader("University scraping templates")
        st.caption("Pre-configured web scraping templates for each university — URL patterns and HTML selectors for automated discovery.")

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
            st.subheader("Queued scan targets")
            st.dataframe(
                scan_targets[["university", "region", "opportunity_name",
                              "description", "status"]].rename(columns={
                    "description": "Target URL"
                }),
                use_container_width=True,
                hide_index=True,
            )

    with disc_sub3:
        st.subheader("University expansion roadmap")
        st.caption("Phased rollout plan for expanding IA West's university network.")

        for phase in get_expansion_roadmap():
            priority_color = {"Immediate": "🔴", "High": "🟠", "Medium": "🔵"}.get(
                phase["priority"], "⚪"
            )
            template_status = "✅ Template ready" if phase.get("template_ready") else "⬜ Template needed"
            with st.expander(f"{priority_color} **{phase['phase']}** — {phase['region']}"):
                st.markdown(f"**Universities:** {', '.join(phase['universities'])}")
                st.markdown(f"**Rationale:** {phase['rationale']}")
                st.markdown(f"**Estimated opportunities:** {phase['estimated_opportunities']}")
                st.markdown(f"**Template status:** {template_status}")


# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.caption("---")
st.caption("IA West Smart Match CRM · CPP AI Hackathon 2026 · Streamlit + scikit-learn + TF-IDF")
