"""Volunteer Self-Service Portal — register, update profile, view matches."""

import streamlit as st
import pandas as pd
from src.db import is_supabase_mode, register_volunteer, update_volunteer, get_volunteer_by_email
from src.matching_engine import compute_matches, get_top_matches

st.set_page_config(
    page_title="Volunteer Portal — IA West",
    page_icon="🙋",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
.block-container { padding-top: 1rem; }
.hero-banner {
    background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    border-radius: 16px;
    padding: 2.5rem 2rem;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(255,255,255,0.08);
}
.hero-banner h1 { color: #ffffff; font-size: 2rem; margin-bottom: 0.3rem; }
.hero-banner p { color: #8899aa; font-size: 1.1rem; }
.portal-card {
    background: rgba(26,31,46,0.7);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
    <h1>🙋 Volunteer Portal</h1>
    <p>Register as a volunteer, update your profile, and view your top matches.</p>
</div>
""", unsafe_allow_html=True)

REGIONS = [
    "Los Angeles — East",
    "Los Angeles — West",
    "Los Angeles — Long Beach",
    "Orange County",
    "Inland Empire",
    "San Diego",
    "San Francisco",
    "Ventura / Thousand Oaks",
    "Other",
]

ENGAGEMENT_TYPES = [
    "Judge", "Mentor", "Guest Speaker", "Workshop Facilitator",
    "Panel Moderator", "Career Advisor", "Hackathon Coach",
]

if not is_supabase_mode():
    st.warning(
        "**Demo Mode** — Volunteer self-service requires a Supabase connection. "
        "The form below is for demonstration purposes only.",
        icon="📁",
    )

# ── Tabs ──────────────────────────────────────────────────────────────
tab_register, tab_update, tab_matches = st.tabs([
    "📝 Register", "✏️ Update Profile", "🎯 My Matches"
])

# ── Register Tab ──────────────────────────────────────────────────────
with tab_register:
    st.markdown('<div class="portal-card">', unsafe_allow_html=True)
    st.subheader("Join as a Volunteer")
    st.caption("Fill in your details to be matched with university engagement opportunities.")

    with st.form("volunteer_register", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name *", placeholder="Jane Doe")
            email = st.text_input("Email *", placeholder="jane@company.com")
            company = st.text_input("Company", placeholder="Acme Corp")
            title = st.text_input("Title / Role", placeholder="VP of Research")
        with col2:
            region = st.selectbox("Metro Region *", options=REGIONS)
            board_role = st.text_input("Board Role (if any)", placeholder="e.g. Treasurer")
            linkedin = st.text_input("LinkedIn URL", placeholder="https://linkedin.com/in/...")
            engagements = st.multiselect(
                "Preferred Engagement Types",
                options=ENGAGEMENT_TYPES,
                default=["Guest Speaker"],
            )

        expertise = st.text_area(
            "Expertise Tags (comma-separated) *",
            placeholder="AI, market research, data analytics, mentorship",
        )
        bio = st.text_area(
            "Short Bio",
            placeholder="Tell us about your background and what motivates you to volunteer...",
            max_chars=500,
        )

        submitted = st.form_submit_button("Register", type="primary", use_container_width=True)

    if submitted:
        if not name or not email or not expertise:
            st.error("Please fill in all required fields (Name, Email, Expertise).")
        elif is_supabase_mode():
            existing = get_volunteer_by_email(email)
            if existing:
                st.warning(f"A volunteer with email **{email}** already exists. Use the Update tab instead.")
            else:
                data = {
                    "name": name,
                    "email": email,
                    "company": company,
                    "title": title,
                    "metro_region": region,
                    "board_role": board_role,
                    "linkedin_url": linkedin,
                    "expertise_tags": expertise,
                    "bio": bio,
                    "source": "self_registered",
                }
                try:
                    register_volunteer(data)
                    st.success(f"Welcome aboard, **{name}**! You're now registered as a volunteer.", icon="🎉")
                    st.balloons()
                except Exception as e:
                    st.error(f"Registration failed: {e}")
        else:
            st.info("In demo mode, registration is simulated. Connect Supabase to persist data.")
            st.success(f"Welcome aboard, **{name}**! (Demo — not persisted)", icon="🎉")

    st.markdown('</div>', unsafe_allow_html=True)

# ── Update Profile Tab ────────────────────────────────────────────────
with tab_update:
    st.markdown('<div class="portal-card">', unsafe_allow_html=True)
    st.subheader("Update Your Profile")

    lookup_email = st.text_input("Enter your registered email", placeholder="jane@company.com", key="lookup_email")

    if lookup_email and is_supabase_mode():
        profile = get_volunteer_by_email(lookup_email)
        if profile:
            st.success(f"Found profile for **{profile['name']}**")

            with st.form("volunteer_update"):
                col1, col2 = st.columns(2)
                with col1:
                    u_company = st.text_input("Company", value=profile.get("company", ""))
                    u_title = st.text_input("Title", value=profile.get("title", ""))
                    u_region = st.selectbox(
                        "Metro Region",
                        options=REGIONS,
                        index=REGIONS.index(profile.get("metro_region", REGIONS[0]))
                        if profile.get("metro_region") in REGIONS else 0,
                    )
                with col2:
                    u_board_role = st.text_input("Board Role", value=profile.get("board_role", ""))
                    u_linkedin = st.text_input("LinkedIn URL", value=profile.get("linkedin_url", ""))

                u_expertise = st.text_area("Expertise Tags", value=profile.get("expertise_tags", ""))
                u_bio = st.text_area("Bio", value=profile.get("bio", ""), max_chars=500)

                update_submitted = st.form_submit_button("Save Changes", type="primary", use_container_width=True)

            if update_submitted:
                try:
                    update_volunteer(lookup_email, {
                        "company": u_company,
                        "title": u_title,
                        "metro_region": u_region,
                        "board_role": u_board_role,
                        "linkedin_url": u_linkedin,
                        "expertise_tags": u_expertise,
                        "bio": u_bio,
                    })
                    st.success("Profile updated!", icon="✅")
                except Exception as e:
                    st.error(f"Update failed: {e}")
        else:
            st.warning("No profile found with that email. Please register first.")
    elif lookup_email and not is_supabase_mode():
        st.info("Profile lookup requires a Supabase connection. Currently in demo mode.")

    st.markdown('</div>', unsafe_allow_html=True)

# ── My Matches Tab ────────────────────────────────────────────────────
with tab_matches:
    st.markdown('<div class="portal-card">', unsafe_allow_html=True)
    st.subheader("Your Top Matches")
    st.caption("See which university opportunities best match your expertise.")

    match_email = st.text_input("Enter your email to view matches", placeholder="jane@company.com", key="match_email")

    if match_email:
        profile = None
        volunteer_name = None

        if is_supabase_mode():
            profile = get_volunteer_by_email(match_email)
            if profile:
                volunteer_name = profile["name"]

        if not volunteer_name:
            # Fallback: try matching by email in CSV data
            try:
                from src.data_loader import load_all
                data = load_all()
                speakers = data["speakers"]
                # In demo mode, just let user pick from known volunteers
                if not is_supabase_mode():
                    st.info("In demo mode, select a volunteer name to preview matches:")
                    volunteer_name = st.selectbox(
                        "Select volunteer",
                        options=speakers["name"].tolist(),
                        key="demo_volunteer_select",
                    )
            except Exception:
                pass

        if volunteer_name:
            try:
                from src.data_loader import load_all
                data = load_all()
                speakers = data["speakers"]
                cpp_events = data["cpp_events"]
                event_calendar = data["event_calendar"]

                all_matches = compute_matches(speakers, cpp_events, event_calendar)
                vol_matches = all_matches[all_matches["volunteer"] == volunteer_name].head(5)

                if vol_matches.empty:
                    st.info(f"No matches found for {volunteer_name}.")
                else:
                    st.markdown(f"**Top 5 matches for {volunteer_name}:**")
                    for _, row in vol_matches.iterrows():
                        score = row.get("composite_score", 0)
                        opp = row.get("opportunity", row.get("event_name", ""))
                        with st.expander(f"🎯 {opp} — Score: {score:.1%}"):
                            cols = st.columns(6)
                            components = [
                                ("Topic", "topic_score"),
                                ("Role Fit", "role_score"),
                                ("Geo", "geo_score"),
                                ("Calendar", "calendar_score"),
                                ("Interest", "student_interest"),
                                ("Experience", "experience_score"),
                            ]
                            for col, (label, key) in zip(cols, components):
                                val = row.get(key, 0)
                                col.metric(label, f"{val:.0%}" if val else "N/A")
                            explanation = explain_match(row)
                            st.markdown(explanation)
            except Exception as e:
                st.error(f"Error computing matches: {e}")
        elif match_email and is_supabase_mode():
            st.warning("No profile found with that email. Please register first.")

    st.markdown('</div>', unsafe_allow_html=True)
