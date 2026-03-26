"""Event Impact Scorecard: per-opportunity scoring for IA chapter leadership.

Generates a structured scorecard for each opportunity showing:
- Volunteer match quality (best/avg scores, number of strong matches)
- Conversion potential (estimated pipeline progression)
- Strategic value (audience reach, role diversity, category value)
- Recommended action priority
"""

import pandas as pd
import numpy as np

# Category-based conversion potential estimates
# Based on challenge doc: hackathons and competitions have highest engagement
CATEGORY_CONVERSION = {
    "AI / Hackathon": 0.85,
    "Hackathon": 0.85,
    "Case competition": 0.80,
    "Research symposium": 0.70,
    "Research showcase": 0.70,
    "Tech symposium / Speakers": 0.65,
    "Entrepreneurship / Pitch": 0.75,
    "Career services": 0.60,
    "Career fairs": 0.60,
}

# Role diversity scoring — more volunteer roles = more engagement angles
ROLE_SCORES = {
    "Judge": 0.9,
    "Mentor": 0.85,
    "Guest speaker": 0.8,
    "Panelist": 0.75,
    "Workshop lead": 0.7,
    "Reviewer": 0.65,
}

# Audience reach multiplier
AUDIENCE_REACH = {
    "all students": 1.0,
    "open": 1.0,
    "students": 0.8,
    "business/tech": 0.7,
    "graduate": 0.6,
    "undergraduate": 0.7,
    "faculty": 0.5,
}


def compute_event_scorecards(
    opportunities: pd.DataFrame,
    all_matches: pd.DataFrame,
    opp_type: str = "event",
) -> pd.DataFrame:
    """Generate impact scorecards for each opportunity.

    Returns a DataFrame with one row per opportunity and columns for
    match quality, conversion potential, strategic value, and overall impact.
    """
    opp_name_col = "event_name" if "event_name" in opportunities.columns else "title"
    results = []

    for _, opp in opportunities.iterrows():
        opp_name = opp[opp_name_col]
        opp_matches = all_matches[all_matches["opportunity"] == opp_name]

        if opp_matches.empty:
            continue

        # ── Match Quality Score (0-1) ──
        best_score = opp_matches["match_score"].max()
        avg_score = opp_matches["match_score"].mean()
        strong_matches = len(opp_matches[opp_matches["match_score"] >= 0.5])
        # Weighted: 40% best, 30% avg, 30% strong count normalized
        match_quality = (
            0.4 * best_score
            + 0.3 * avg_score
            + 0.3 * min(strong_matches / 5, 1.0)
        )

        # ── Conversion Potential (0-1) ──
        category = opp.get("category", "")
        cat_score = CATEGORY_CONVERSION.get(category, 0.5)

        recurrence = str(opp.get("recurrence", "")).lower()
        recurrence_bonus = 0.15 if "annual" in recurrence or "semester" in recurrence else 0
        recurrence_bonus += 0.1 if "annual" in recurrence else 0

        conversion_potential = min(1.0, cat_score + recurrence_bonus)

        # ── Strategic Value (0-1) ──
        # Role diversity
        roles = opp.get("role_list", [])
        if isinstance(roles, str):
            roles = [r.strip() for r in roles.split(";") if r.strip()]
        role_diversity = min(len(roles) / 3, 1.0)  # 3+ roles = full score

        # Audience reach
        audience = str(opp.get("audience", "")).lower()
        audience_score = 0.5
        for key, val in AUDIENCE_REACH.items():
            if key in audience:
                audience_score = max(audience_score, val)

        # Enrollment cap for courses
        if opp_type == "course":
            cap = opp.get("enrollment_cap", 30)
            try:
                cap = int(cap)
            except (ValueError, TypeError):
                cap = 30
            audience_score = min(cap / 45, 1.0)

        strategic_value = 0.4 * role_diversity + 0.3 * audience_score + 0.3 * conversion_potential

        # ── Overall Impact Score ──
        impact_score = (
            0.40 * match_quality
            + 0.30 * conversion_potential
            + 0.30 * strategic_value
        )

        # ── Priority Rating ──
        if impact_score >= 0.70:
            priority = "High"
        elif impact_score >= 0.50:
            priority = "Medium"
        else:
            priority = "Low"

        # ── Estimated conversions ──
        # If we place the best-matched volunteer, what's the expected pipeline outcome?
        est_pipeline_entries = max(1, strong_matches)
        est_engagements = round(est_pipeline_entries * 0.85, 1)  # 85% event completion
        est_leads = round(est_engagements * 0.30, 1)  # 30% become membership leads
        est_members = round(est_leads * 0.45, 1)  # 45% of leads convert

        results.append({
            "opportunity": opp_name,
            "type": opp_type,
            "category": category,
            "match_quality": round(match_quality, 3),
            "best_match_score": round(best_score, 3),
            "avg_match_score": round(avg_score, 3),
            "strong_matches": strong_matches,
            "conversion_potential": round(conversion_potential, 3),
            "strategic_value": round(strategic_value, 3),
            "impact_score": round(impact_score, 3),
            "priority": priority,
            "est_pipeline_entries": est_pipeline_entries,
            "est_engagements": est_engagements,
            "est_membership_leads": est_leads,
            "est_new_members": est_members,
            "roles_available": ", ".join(roles) if isinstance(roles, list) else str(roles),
            "audience": opp.get("audience", ""),
            "recurrence": opp.get("recurrence", ""),
            "best_volunteer": opp_matches.iloc[0]["volunteer"],
        })

    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values("impact_score", ascending=False).reset_index(drop=True)
    return df


def get_scorecard_summary(scorecards: pd.DataFrame) -> dict:
    """Aggregate scorecard statistics for the executive summary."""
    if scorecards.empty:
        return {"total": 0, "high": 0, "medium": 0, "low": 0}

    return {
        "total": len(scorecards),
        "high": len(scorecards[scorecards["priority"] == "High"]),
        "medium": len(scorecards[scorecards["priority"] == "Medium"]),
        "low": len(scorecards[scorecards["priority"] == "Low"]),
        "avg_impact": round(scorecards["impact_score"].mean(), 3),
        "total_est_members": round(scorecards["est_new_members"].sum(), 1),
        "top_opportunity": scorecards.iloc[0]["opportunity"] if len(scorecards) > 0 else "",
        "top_impact": scorecards.iloc[0]["impact_score"] if len(scorecards) > 0 else 0,
    }
