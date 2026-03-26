"""AI-enhanced features powered by Claude API.

All functions gracefully degrade: if the API key is missing or the call fails,
they return None so callers fall back to deterministic logic.
"""

import streamlit as st

_client = None

def _get_client():
    """Lazy-init Anthropic client from Streamlit secrets."""
    global _client
    if _client is not None:
        return _client
    try:
        import anthropic
        key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if not key:
            return None
        _client = anthropic.Anthropic(api_key=key)
        return _client
    except Exception:
        return None


def ai_enabled() -> bool:
    """Check if AI features are available (API key configured)."""
    return _get_client() is not None


@st.cache_data(ttl=3600, show_spinner=False)
def ai_explain_match(
    volunteer_name: str, volunteer_role: str, volunteer_expertise: str, volunteer_region: str,
    opportunity: str, opp_type: str, opp_roles: str,
    topic: float, role_fit: float, geo: float, calendar: float, interest: float, experience: float,
    composite: float,
) -> str | None:
    """Generate an AI-powered match explanation."""
    client = _get_client()
    if not client:
        return None
    try:
        prompt = f"""You are an analyst for the Insights Association West Chapter, explaining why a volunteer is a good match for a university engagement opportunity.

Volunteer: {volunteer_name}
Role: {volunteer_role}
Expertise: {volunteer_expertise}
Region: {volunteer_region}

Opportunity: {opportunity} ({opp_type})
Roles needed: {opp_roles}

Match scores (0-1 scale):
- Topic Relevance: {topic:.2f} (TF-IDF cosine similarity)
- Role Fit: {role_fit:.2f} (keyword taxonomy match)
- Geographic Proximity: {geo:.2f} (1.0=same region, 0.5=adjacent, 0.2=remote)
- Calendar Fit: {calendar:.2f} (IA event overlap)
- Student Interest: {interest:.2f} (enrollment/audience signal)
- Experience: {experience:.2f} (seniority heuristic)
- COMPOSITE: {composite:.2f}

Write a concise 3-4 sentence explanation of why this is a {_score_label(composite)} match. Reference specific expertise areas and how they connect to the opportunity. Be specific, not generic. Do not mention the numerical scores."""
        
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def ai_personalize_email(
    volunteer_name: str, volunteer_title: str, volunteer_company: str,
    volunteer_expertise: str, volunteer_role: str, volunteer_region: str,
    opportunity: str, opp_type: str, contact_name: str,
    match_score: float, topic_score: float,
) -> str | None:
    """Generate a personalized outreach email using AI."""
    client = _get_client()
    if not client:
        return None
    try:
        prompt = f"""Write a professional outreach email from the Insights Association West Chapter to connect a volunteer with a university engagement opportunity.

Volunteer: {volunteer_name}, {volunteer_title} at {volunteer_company}
IA West Role: {volunteer_role}
Expertise: {volunteer_expertise}
Region: {volunteer_region}

Opportunity: {opportunity} ({'University Event' if opp_type == 'event' else 'Course Guest Lecture'})
Contact: {contact_name or 'Program Coordinator'}
Match Strength: {_score_label(match_score)} ({match_score:.0%})

Write a concise, professional email with:
- Subject line (start with "Subject: ")
- Warm but professional tone
- Specific connection between the volunteer's expertise and the opportunity
- Clear call to action
- Sign off as "IA West Smart Match Team"

Keep it under 200 words. Do not use markdown formatting."""
        
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text
    except Exception:
        return None


@st.cache_data(ttl=1800, show_spinner=False)
def ai_strategic_insights(
    total_matches: int, high_quality_pct: float,
    coverage_gaps: int, coverage_pct: float,
    top_region: str, top_region_avg: float,
    pipeline_count: int, engaged_rate: float,
    underutilized_names: list[str],
) -> str | None:
    """Generate AI-powered strategic insights from match and pipeline data."""
    client = _get_client()
    if not client:
        return None
    try:
        prompt = f"""You are a strategic advisor for the Insights Association West Chapter analyzing their volunteer-to-university matching CRM data.

Data snapshot:
- Total match pairs: {total_matches}
- High-quality matches (>60%): {high_quality_pct:.0%}
- Coverage gaps (opportunities with no strong volunteer): {coverage_gaps}
- Overall coverage: {coverage_pct:.0%}
- Strongest region: {top_region} (avg {top_region_avg:.0%})
- Pipeline entries: {pipeline_count}
- Engagement rate (past "Engaged" stage): {engaged_rate:.0%}
- High-scoring volunteers not in pipeline: {', '.join(underutilized_names[:5]) if underutilized_names else 'None'}

Generate 3 specific, actionable strategic recommendations. Each should be 1-2 sentences. Focus on what IA West leadership should do next to maximize membership growth through university engagement. Be concrete — reference the data points above."""
        
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text
    except Exception:
        return None


@st.cache_data(ttl=600, show_spinner=False)
def ai_answer_question(question: str, data_summary: str) -> str | None:
    """Answer a natural language question about the match data."""
    client = _get_client()
    if not client:
        return None
    try:
        prompt = f"""You are an AI assistant for the IA West Smart Match CRM — a system that matches Insights Association West board member volunteers to Cal Poly Pomona university engagement opportunities (events, courses, guest lectures).

Here is the current data summary:
{data_summary}

Answer the following question concisely (2-4 sentences). If the data doesn't contain enough info to answer, say so. Reference specific volunteers, opportunities, or numbers when possible.

Question: {question}"""
        
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=250,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text
    except Exception as e:
        return f"AI query failed: {str(e)}"


def _score_label(score: float) -> str:
    if score >= 0.7:
        return "strong"
    elif score >= 0.5:
        return "good"
    elif score >= 0.3:
        return "moderate"
    return "potential"
