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

# --- Page Config ---
st.set_page_config(
    page_title="IA West Smart Match CRM",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Load Data ---
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

# --- Sidebar ---
st.sidebar.image("https://img.icons8.com/fluency/96/handshake.png", width=64)
st.sidebar.title("IA West Smart Match")
st.sidebar.markdown("**AI-Powered Volunteer-to-Opportunity Matching**")
st.sidebar.markdown("---")
st.sidebar.markdown(f"**{len(speakers)}** Board Members")
st.sidebar.markdown(f"**{len(cpp_events)}** CPP Events/Programs")
st.sidebar.markdown(f"**{len(cpp_courses)}** Course Sections")
st.sidebar.markdown(f"**{len(event_calendar)}** Regional Events")
st.sidebar.markdown(f"**{len(all_matches)}** Total Match Pairs Scored")

# Algorithm info
with st.sidebar.expander("Matching Algorithm"):
    st.markdown("""
    **Composite Score Formula:**
    ```
    SCORE = 0.35 * Topic Relevance
          + 0.25 * Role Fit
          + 0.20 * Geographic Proximity
          + 0.10 * Calendar Fit
          + 0.10 * Experience Bonus
    ```

    - **Topic**: TF-IDF cosine similarity (bigram, sublinear TF)
    - **Role**: Keyword matching against volunteer role taxonomy
    - **Geo**: Metro region clustering with adjacency model
    - **Calendar**: IA event schedule overlap scoring
    - **Experience**: Parsed from expertise tags (years, titles)
    """)

# --- Tabs ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Speaker Profiles",
    "Opportunities",
    "Smart Matches",
    "Outreach",
    "Pipeline",
    "Discovery",
])

# ============================================================
# TAB 1: Speaker Profiles
# ============================================================
with tab1:
    st.header("IA West Board Members")
    st.markdown("Speaker profiles with expertise tags, metro regions, and roles.")

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        region_filter = st.multiselect(
            "Filter by Metro Region",
            options=sorted(speakers["metro_region"].unique()),
            key="speaker_region",
        )
    with col2:
        search = st.text_input("Search expertise tags", key="speaker_search")

    filtered = speakers.copy()
    if region_filter:
        filtered = filtered[filtered["metro_region"].isin(region_filter)]
    if search:
        filtered = filtered[filtered["expertise_tags"].str.contains(search, case=False, na=False)]

    # Display cards
    for _, row in filtered.iterrows():
        with st.expander(f"**{row['name']}** — {row['board_role']}", expanded=False):
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown(f"**Company:** {row['company']}")
                st.markdown(f"**Title:** {row['title']}")
                st.markdown(f"**Region:** {row['metro_region']}")
            with c2:
                st.markdown("**Expertise:**")
                tags = row.get("expertise_list", [])
                tag_html = " ".join(
                    [f'<span style="background:#e3f2fd;padding:2px 8px;border-radius:12px;margin:2px;display:inline-block;font-size:0.85em">{t}</span>' for t in tags]
                )
                st.markdown(tag_html, unsafe_allow_html=True)

                # Top matches for this speaker
                speaker_matches = all_matches[all_matches["speaker"] == row["name"]].head(3)
                if not speaker_matches.empty:
                    st.markdown("**Top Matches:**")
                    for _, m in speaker_matches.iterrows():
                        st.markdown(f"- {m['opportunity']} ({m['opportunity_type']}) — **{m['match_score']:.0%}**")

    # Region distribution chart
    st.subheader("Board Member Distribution by Region")
    region_counts = speakers["metro_region"].value_counts().reset_index()
    region_counts.columns = ["Region", "Count"]
    fig = px.bar(region_counts, x="Region", y="Count", color="Count",
                 color_continuous_scale="Blues", title="Board Members per Metro Region")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# TAB 2: Opportunities
# ============================================================
with tab2:
    st.header("University Opportunities")

    opp_subtab1, opp_subtab2, opp_subtab3 = st.tabs(["CPP Events", "CPP Courses", "IA Event Calendar"])

    with opp_subtab1:
        st.subheader("Cal Poly Pomona Events & Programs")
        for _, row in cpp_events.iterrows():
            with st.expander(f"**{row['event_name']}** — {row['category']}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Host:** {row['host']}")
                    st.markdown(f"**Recurrence:** {row['recurrence']}")
                    st.markdown(f"**Audience:** {row['audience']}")
                with c2:
                    st.markdown(f"**Volunteer Roles:** {row['volunteer_roles']}")
                    st.markdown(f"**Contact:** {row['contact_name']}")
                    st.markdown(f"**Email:** {row['contact_email']}")
                    if pd.notna(row.get("url")):
                        st.markdown(f"[Event Page]({row['url']})")

        # Category breakdown
        cat_counts = cpp_events["category"].value_counts().reset_index()
        cat_counts.columns = ["Category", "Count"]
        fig = px.pie(cat_counts, names="Category", values="Count",
                     title="Events by Category", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

    with opp_subtab2:
        st.subheader("CPP Marketing Course Sections")

        fit_filter = st.multiselect(
            "Filter by Guest Lecture Fit",
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
        )

        # Fit distribution
        fit_counts = cpp_courses["guest_lecture_fit"].value_counts().reset_index()
        fit_counts.columns = ["Fit Level", "Count"]
        fig = px.bar(fit_counts, x="Fit Level", y="Count", color="Fit Level",
                     color_discrete_map={"High": "#28a745", "Medium": "#ffc107", "Low": "#dc3545"},
                     title="Course Sections by Guest Lecture Fit")
        st.plotly_chart(fig, use_container_width=True)

    with opp_subtab3:
        st.subheader("IA West 2026 Regional Event Calendar")

        cal_display = event_calendar.copy()
        cal_display["event_date"] = cal_display["event_date"].dt.strftime("%B %d, %Y")
        st.dataframe(
            cal_display[["event_date", "region", "nearby_universities",
                        "lecture_window", "course_alignment"]],
            use_container_width=True,
            hide_index=True,
        )

        # Timeline
        fig = px.timeline(
            event_calendar.assign(
                end=event_calendar["event_date"] + pd.Timedelta(days=1),
                label=event_calendar["region"],
            ),
            x_start="event_date", x_end="end", y="label",
            title="2026 IA West Event Timeline",
            color="region",
        )
        fig.update_layout(showlegend=False, yaxis_title="Region")
        st.plotly_chart(fig, use_container_width=True)


# ============================================================
# TAB 3: Smart Matches
# ============================================================
with tab3:
    st.header("Smart Match Recommendations")
    st.markdown("""
    Matches are scored using a weighted composite algorithm:
    `SCORE = 0.35 x Topic Relevance + 0.25 x Role Fit + 0.20 x Geographic Proximity + 0.10 x Calendar Fit + 0.10 x Experience Bonus`
    """)

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        match_type = st.selectbox("Opportunity Type", ["All", "event", "course"])
    with col2:
        min_score = st.slider("Minimum Match Score", 0.0, 1.0, 0.3, 0.05)
    with col3:
        top_n = st.number_input("Show Top N", min_value=5, max_value=100, value=20)

    display_matches = all_matches.copy()
    if match_type != "All":
        display_matches = display_matches[display_matches["opportunity_type"] == match_type]
    display_matches = display_matches[display_matches["match_score"] >= min_score].head(top_n)

    # Score distribution
    fig = px.histogram(all_matches, x="match_score", nbins=30,
                       color="opportunity_type", barmode="overlay",
                       title="Match Score Distribution",
                       labels={"match_score": "Match Score", "opportunity_type": "Type"})
    st.plotly_chart(fig, use_container_width=True)

    # Top matches table
    st.subheader(f"Top {len(display_matches)} Matches")
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
        },
    )

    # Detailed match cards with explanations
    st.subheader("Match Details & Explanations")
    for idx, row in display_matches.head(10).iterrows():
        with st.expander(
            f"**{row['speaker']}** -> {row['opportunity']} ({row['match_score']:.0%})"
        ):
            explanation = explain_match(row)
            st.markdown(explanation)

            # Score breakdown radar
            categories = ["Topic\nRelevance", "Role\nFit", "Geographic\nProximity",
                          "Calendar\nFit", "Experience\nBonus"]
            values = [row["topic_relevance"], row["role_fit"],
                      row["geographic_proximity"], row["calendar_fit"],
                      row["historical_bonus"]]

            fig = go.Figure(data=go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill="toself",
                fillcolor="rgba(0,123,255,0.15)",
                line=dict(color="#007bff"),
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                showlegend=False,
                height=300,
                margin=dict(l=60, r=60, t=30, b=30),
            )
            st.plotly_chart(fig, use_container_width=True)

    # Heatmap: speakers vs top opportunities
    st.subheader("Speaker-Opportunity Match Heatmap")
    top_opps = all_matches.groupby("opportunity")["match_score"].mean().nlargest(8).index.tolist()
    heatmap_data = all_matches[all_matches["opportunity"].isin(top_opps)]
    pivot = heatmap_data.pivot_table(
        index="speaker", columns="opportunity", values="match_score", aggfunc="first"
    )
    fig = px.imshow(
        pivot, color_continuous_scale="YlGn", aspect="auto",
        title="Match Score Heatmap (Top 8 Opportunities)",
        labels={"color": "Score"},
    )
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# TAB 4: Outreach
# ============================================================
with tab4:
    st.header("Outreach Email Generator")
    st.markdown("Generate personalized outreach emails for top matches.")

    col1, col2 = st.columns(2)
    with col1:
        selected_speaker = st.selectbox(
            "Select Speaker",
            options=["All"] + sorted(speakers["name"].tolist()),
            key="outreach_speaker",
        )
    with col2:
        outreach_type = st.selectbox(
            "Opportunity Type",
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
            # Enrich match data with speaker details
            speaker_data = speakers[speakers["name"] == match_row["speaker"]].iloc[0]
            enriched = match_row.to_dict()
            enriched["speaker_title"] = speaker_data.get("title", "")
            enriched["speaker_company"] = speaker_data.get("company", "")

            # Get opportunity data for template
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

            with st.expander(
                f"Email: {match_row['speaker']} -> {match_row['opportunity']} ({match_row['match_score']:.0%})"
            ):
                st.code(email, language=None)
                st.download_button(
                    label="Download Email Draft",
                    data=email,
                    file_name=f"outreach_{match_row['speaker'].replace(' ', '_')}_{match_row['opportunity'][:30].replace(' ', '_')}.txt",
                    mime="text/plain",
                    key=f"dl_{match_row['speaker']}_{match_row['opportunity']}_{outreach_type}",
                )


# ============================================================
# TAB 5: Pipeline
# ============================================================
with tab5:
    st.header("Engagement Pipeline")
    st.markdown("Track the journey from opportunity identification to IA membership conversion.")

    pipeline = generate_mock_pipeline(speakers, cpp_events)
    summary = get_pipeline_summary(pipeline)
    funnel = get_funnel_data(pipeline)

    # KPI row
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Pipeline Entries", summary["total_entries"])
    k2.metric("Active Pipeline", summary["active_pipeline"])
    k3.metric("Conversion Rate", f"{summary['conversion_rate']:.1%}")
    k4.metric("Unique Speakers Engaged", summary["unique_speakers"])

    # Funnel chart
    st.subheader("Conversion Funnel")
    fig = go.Figure(go.Funnel(
        y=funnel["stage"],
        x=funnel["count"],
        textinfo="value+percent initial",
        marker=dict(color=[STAGE_COLORS[s] for s in funnel["stage"]]),
    ))
    fig.update_layout(height=400, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, use_container_width=True)

    # Stage-to-stage conversion rates
    st.subheader("Stage-to-Stage Conversion Rates")
    conversions = summary["stage_conversions"]
    conv_df = pd.DataFrame(conversions)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[f"{c['from']} -> {c['to']}" for c in conversions],
        y=[c['rate'] for c in conversions],
        name="Observed",
        marker_color="#007bff",
    ))
    fig.add_trace(go.Scatter(
        x=[f"{c['from']} -> {c['to']}" for c in conversions],
        y=[c['benchmark'] for c in conversions],
        name="Benchmark",
        mode="markers+lines",
        marker=dict(color="#dc3545", size=10),
        line=dict(dash="dash"),
    ))
    fig.update_layout(
        yaxis_title="Conversion Rate",
        yaxis_tickformat=".0%",
        height=350,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Sub-tabs for per-speaker, per-event-type, per-region
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
            )
            fig = px.bar(speaker_metrics.head(10), x="speaker", y="avg_stage_index",
                         color="furthest_stage", title="Top 10 Speakers by Pipeline Progress",
                         labels={"avg_stage_index": "Avg Stage Progress"})
            st.plotly_chart(fig, use_container_width=True)

    with pipe_sub2:
        event_metrics = get_metrics_by_event_type(pipeline)
        if not event_metrics.empty:
            st.dataframe(
                event_metrics.rename(columns={
                    "avg_stage_index": "Avg Progress"
                }),
                use_container_width=True,
                hide_index=True,
            )
            fig = px.bar(event_metrics, x="event_type", y="conversion_rate",
                         color="event_type",
                         title="Conversion Rate by Event Type",
                         labels={"conversion_rate": "Conversion Rate"})
            fig.update_layout(yaxis_tickformat=".0%", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with pipe_sub3:
        region_metrics = get_metrics_by_region(pipeline)
        if not region_metrics.empty:
            st.dataframe(
                region_metrics.rename(columns={
                    "avg_stage_index": "Avg Progress"
                }),
                use_container_width=True,
                hide_index=True,
            )
            fig = px.bar(region_metrics, x="region", y="total_entries",
                         color="conversion_rate",
                         color_continuous_scale="YlGn",
                         title="Pipeline Entries by Region (colored by conversion rate)")
            st.plotly_chart(fig, use_container_width=True)

    # Stage breakdown
    st.subheader("Pipeline by Stage")
    stage_df = pd.DataFrame([
        {"Stage": stage, "Count": summary["by_stage"].get(stage, 0)}
        for stage in PIPELINE_STAGES
    ])
    fig = px.bar(stage_df, x="Stage", y="Count", color="Stage",
                 color_discrete_map=STAGE_COLORS,
                 title="Pipeline Entries by Stage")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # Detailed pipeline table
    st.subheader("Pipeline Details")
    stage_filter = st.multiselect(
        "Filter by Stage",
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


# ============================================================
# TAB 6: Discovery
# ============================================================
with tab6:
    st.header("Opportunity Discovery Engine")
    st.markdown("""
    Automated discovery engine that identifies new volunteer opportunities
    at universities across IA West's regional footprint. Uses real CSV data
    from CPP events, courses, and IA regional calendar.
    """)

    disc_sub1, disc_sub2, disc_sub3 = st.tabs([
        "Discovered Opportunities", "Scraping Templates", "Expansion Roadmap"
    ])

    with disc_sub1:
        discoveries = run_discovery_simulation()
        # Split real vs scan targets
        real_discoveries = discoveries[discoveries["status"] != "Queued"]
        scan_targets = discoveries[discoveries["status"] == "Queued"]
        stats = get_discovery_stats(discoveries)

        # KPI row
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Opportunities Found", stats["total_opportunities"])
        d2.metric("Universities Scanned", stats["universities_scanned"])
        d3.metric("High-Fit Matches", stats["high_fit_count"])
        d4.metric("Scan Targets Queued", stats["scan_targets"])

        # Results by region
        st.subheader("Discoveries by Region")
        region_df = pd.DataFrame([
            {"Region": k, "Opportunities": v} for k, v in stats["by_region"].items()
        ])
        if not region_df.empty:
            fig = px.bar(region_df, x="Region", y="Opportunities", color="Region",
                         title="Discovered Opportunities by Region")
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        # Results by type
        col1, col2 = st.columns(2)
        with col1:
            type_df = pd.DataFrame([
                {"Type": k, "Count": v} for k, v in stats["by_type"].items()
            ])
            if not type_df.empty:
                fig = px.pie(type_df, names="Type", values="Count",
                             title="By Opportunity Type", hole=0.4)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            if not real_discoveries.empty and "fit_level" in real_discoveries.columns:
                fit_df = real_discoveries["fit_level"].value_counts().reset_index()
                fit_df.columns = ["Fit Level", "Count"]
                fig = px.pie(fit_df, names="Fit Level", values="Count",
                             title="By Fit Level", hole=0.4,
                             color_discrete_map={"High": "#28a745", "Medium": "#ffc107", "Low": "#dc3545"})
                st.plotly_chart(fig, use_container_width=True)

        # By university
        st.subheader("Opportunities by University")
        if "by_university" in stats and stats["by_university"]:
            uni_df = pd.DataFrame([
                {"University": k, "Count": v}
                for k, v in stats["by_university"].items()
            ]).sort_values("Count", ascending=False)
            fig = px.bar(uni_df, x="University", y="Count", color="Count",
                         color_continuous_scale="Blues",
                         title="Opportunities Found per University")
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        # Detailed results
        st.subheader("All Discovered Opportunities")
        uni_filter = st.multiselect(
            "Filter by University",
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
        st.subheader("University Scraping Templates")
        st.markdown("""
        Each university has a configured scraping template with URL patterns
        and HTML selectors. In production, these templates enable automated
        discovery of new events and courses at scale.
        """)

        for tmpl in UNIVERSITY_TEMPLATES:
            with st.expander(f"**{tmpl.name}** ({tmpl.region})"):
                st.markdown(f"**Base URL:** `{tmpl.base_url}`")
                st.markdown(f"**Department:** {tmpl.department}")
                st.markdown("**Event Pages to Scan:**")
                for url in tmpl.get_event_urls():
                    st.markdown(f"- `{url}`")
                if tmpl.course_catalog_url:
                    st.markdown(f"**Course Catalog:** `{tmpl.course_catalog_url}`")
                if tmpl.selectors:
                    st.markdown("**HTML Selectors:**")
                    for key, sel in tmpl.selectors.items():
                        st.markdown(f"- `{key}`: `{sel}`")

        # Show scan targets
        if not scan_targets.empty:
            st.subheader("Queued Scan Targets")
            st.dataframe(
                scan_targets[["university", "region", "opportunity_name",
                              "description", "status"]].rename(columns={
                    "description": "Target URL"
                }),
                use_container_width=True,
                hide_index=True,
            )

    with disc_sub3:
        st.subheader("University Expansion Roadmap")
        roadmap = get_expansion_roadmap()
        for phase in roadmap:
            priority_color = {"Immediate": "red", "High": "orange", "Medium": "blue"}.get(
                phase["priority"], "gray"
            )
            template_status = "Template Ready" if phase.get("template_ready") else "Template Needed"
            with st.expander(f"**{phase['phase']}** — {phase['region']} (Priority: {phase['priority']})"):
                st.markdown(f"**Universities:** {', '.join(phase['universities'])}")
                st.markdown(f"**Rationale:** {phase['rationale']}")
                st.markdown(f"**Estimated Opportunities:** {phase['estimated_opportunities']}")
                st.markdown(f"**Scraping Template:** {template_status}")


# --- Footer ---
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#888;font-size:0.85em'>"
    "IA West Smart Match CRM | CPP AI Hackathon 2026 | "
    "Built with Streamlit + scikit-learn + TF-IDF Cosine Similarity"
    "</div>",
    unsafe_allow_html=True,
)
