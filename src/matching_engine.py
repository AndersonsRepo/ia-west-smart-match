"""Core matching algorithm: speaker-to-opportunity scoring."""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Metro region proximity map (same = 1.0, adjacent = 0.5, far = 0.2)
REGION_CLUSTERS = {
    "Los Angeles": "LA",
    "Los Angeles — West": "LA",
    "Los Angeles — North": "LA",
    "Los Angeles — East": "LA",
    "Los Angeles — Long Beach": "LA",
    "Orange County / Long Beach": "LA",
    "Ventura / Thousand Oaks": "LA_ADJ",
    "San Diego": "SD",
    "San Francisco": "SF",
    "Seattle": "SEA",
    "Portland": "POR",
}

ADJACENT_CLUSTERS = {
    ("LA", "LA_ADJ"), ("LA_ADJ", "LA"),
    ("SF", "POR"), ("POR", "SF"),
    ("SEA", "POR"), ("POR", "SEA"),
}


def _geo_score(speaker_region: str, opp_region: str) -> float:
    """Geographic proximity score."""
    s_cluster = REGION_CLUSTERS.get(speaker_region, speaker_region)
    # CPP events are all in LA area
    o_cluster = REGION_CLUSTERS.get(opp_region, "LA")

    if s_cluster == o_cluster:
        return 1.0
    if (s_cluster, o_cluster) in ADJACENT_CLUSTERS:
        return 0.5
    return 0.2


def _role_fit_score(speaker_tags: str, event_roles: str) -> float:
    """Binary role fit: does the speaker's expertise align with needed roles?"""
    tags_lower = speaker_tags.lower()
    roles_lower = event_roles.lower()

    role_keyword_map = {
        "judge": ["analytics", "research", "ai", "innovation", "marketing science"],
        "mentor": ["mentorship", "client development", "experience", "operations"],
        "guest speaker": ["research", "marketing", "ai", "analytics", "strategy",
                         "innovation", "qualitative", "quantitative"],
        "workshop lead": ["methodology", "research design", "analytics", "ai tools"],
        "panelist": ["industry", "strategy", "client", "experience"],
        "reviewer": ["research", "analytics", "methodology"],
    }

    score = 0.0
    matches = 0
    for role, keywords in role_keyword_map.items():
        if role in roles_lower:
            for kw in keywords:
                if kw in tags_lower:
                    matches += 1
                    break
            score += 1

    if score == 0:
        return 0.3  # Base score for any volunteer
    return min(1.0, matches / max(score, 1))


def _calendar_fit_score(speaker_region: str, event_calendar: pd.DataFrame) -> float:
    """Check if there's an IA event in the speaker's region (upcoming window)."""
    if event_calendar is None or event_calendar.empty:
        return 0.5  # Default

    s_cluster = REGION_CLUSTERS.get(speaker_region, speaker_region)

    for _, row in event_calendar.iterrows():
        e_cluster = REGION_CLUSTERS.get(row.get("region", ""), "")
        if s_cluster == e_cluster:
            return 1.0
        if (s_cluster, e_cluster) in ADJACENT_CLUSTERS:
            return 0.7
    return 0.3


def compute_matches(
    speakers: pd.DataFrame,
    opportunities: pd.DataFrame,
    event_calendar: pd.DataFrame = None,
    opp_type: str = "event",
) -> pd.DataFrame:
    """
    Compute match scores between all speakers and all opportunities.

    MATCH_SCORE = 0.30 * topic_relevance
               + 0.25 * role_fit
               + 0.20 * geographic_proximity
               + 0.15 * calendar_fit
               + 0.10 * historical_bonus
    """
    # Build TF-IDF vectors
    speaker_texts = speakers["expertise_tags"].fillna("").tolist()
    opp_texts = opportunities["description_blob"].fillna("").tolist()

    all_texts = speaker_texts + opp_texts
    vectorizer = TfidfVectorizer(stop_words="english", max_features=500)
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    speaker_vectors = tfidf_matrix[: len(speaker_texts)]
    opp_vectors = tfidf_matrix[len(speaker_texts) :]

    # Cosine similarity matrix: speakers x opportunities
    sim_matrix = cosine_similarity(speaker_vectors, opp_vectors)

    results = []
    opp_name_col = "event_name" if "event_name" in opportunities.columns else "title"
    opp_roles_col = "volunteer_roles" if "volunteer_roles" in opportunities.columns else "guest_lecture_fit"

    for i, speaker in speakers.iterrows():
        for j, opp in opportunities.iterrows():
            topic_score = float(sim_matrix[i, j])

            role_score = _role_fit_score(
                speaker.get("expertise_tags", ""),
                opp.get(opp_roles_col, ""),
            )

            opp_region = opp.get("region", "Los Angeles — East")  # CPP default
            geo_score = _geo_score(speaker.get("metro_region", ""), opp_region)

            cal_score = _calendar_fit_score(
                speaker.get("metro_region", ""), event_calendar
            )

            historical = 0.5  # Placeholder

            composite = (
                0.30 * topic_score
                + 0.25 * role_score
                + 0.20 * geo_score
                + 0.15 * cal_score
                + 0.10 * historical
            )

            results.append({
                "speaker": speaker["name"],
                "speaker_role": speaker.get("board_role", ""),
                "speaker_expertise": speaker.get("expertise_tags", ""),
                "speaker_region": speaker.get("metro_region", ""),
                "opportunity": opp[opp_name_col],
                "opportunity_type": opp_type,
                "topic_relevance": round(topic_score, 3),
                "role_fit": round(role_score, 3),
                "geographic_proximity": round(geo_score, 3),
                "calendar_fit": round(cal_score, 3),
                "historical_bonus": historical,
                "match_score": round(composite, 3),
            })

    df = pd.DataFrame(results)
    df = df.sort_values("match_score", ascending=False).reset_index(drop=True)
    return df


def get_top_matches(matches: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Return the top N matches overall."""
    return matches.head(n)


def get_top_for_speaker(matches: pd.DataFrame, speaker_name: str, n: int = 5) -> pd.DataFrame:
    """Return top N matches for a specific speaker."""
    return matches[matches["speaker"] == speaker_name].head(n)


def get_top_for_opportunity(matches: pd.DataFrame, opp_name: str, n: int = 5) -> pd.DataFrame:
    """Return top N speakers for a specific opportunity."""
    return matches[matches["opportunity"] == opp_name].head(n)


def explain_match(row: pd.Series) -> str:
    """Generate a human-readable explanation for a match."""
    parts = []
    parts.append(f"**{row['speaker']}** ({row['speaker_role']}) matched to **{row['opportunity']}**")
    parts.append(f"with a composite score of **{row['match_score']:.1%}**.")
    parts.append("")
    parts.append("Score breakdown:")
    parts.append(f"- Topic Relevance (30%): {row['topic_relevance']:.1%} — expertise overlap with opportunity description")
    parts.append(f"- Role Fit (25%): {row['role_fit']:.1%} — alignment between skills and needed volunteer roles")
    parts.append(f"- Geographic Proximity (20%): {row['geographic_proximity']:.1%} — metro region distance")
    parts.append(f"- Calendar Fit (15%): {row['calendar_fit']:.1%} — IA event schedule alignment in their region")
    parts.append(f"- Historical Bonus (10%): {row['historical_bonus']:.1%} — engagement history (default for MVP)")
    return "\n".join(parts)
