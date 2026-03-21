"""Core matching algorithm: speaker-to-opportunity scoring.

Uses TF-IDF cosine similarity for topic relevance, role-keyword mapping for
role fit, geographic clustering for proximity, and IA event calendar overlap
for schedule scoring.  Every match includes a human-readable explanation.
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------------------------------------------------------------------
# Geographic proximity model
# ---------------------------------------------------------------------------
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
    ("LA", "SD"), ("SD", "LA"),
}

# Friendly names for explanations
CLUSTER_LABELS = {
    "LA": "Greater Los Angeles",
    "LA_ADJ": "Ventura / LA Adjacent",
    "SD": "San Diego",
    "SF": "San Francisco Bay Area",
    "SEA": "Seattle",
    "POR": "Portland",
}


def _geo_score(speaker_region: str, opp_region: str) -> float:
    """Geographic proximity score."""
    s_cluster = REGION_CLUSTERS.get(speaker_region, speaker_region)
    o_cluster = REGION_CLUSTERS.get(opp_region, "LA")  # CPP default
    if s_cluster == o_cluster:
        return 1.0
    if (s_cluster, o_cluster) in ADJACENT_CLUSTERS:
        return 0.5
    return 0.2


# ---------------------------------------------------------------------------
# Role-fit model
# ---------------------------------------------------------------------------
ROLE_KEYWORD_MAP = {
    "judge": ["analytics", "research", "ai", "innovation", "marketing science",
              "econometrics", "data", "quantitative"],
    "mentor": ["mentorship", "client development", "experience", "operations",
               "yrs experience", "strategic"],
    "guest speaker": ["research", "marketing", "ai", "analytics", "strategy",
                      "innovation", "qualitative", "quantitative", "brand",
                      "econometrics", "generative ai", "focus groups"],
    "workshop lead": ["methodology", "research design", "analytics", "ai tools",
                      "generative ai", "digital transformation"],
    "panelist": ["industry", "strategy", "client", "experience", "brand",
                 "storytelling", "diversity"],
    "reviewer": ["research", "analytics", "methodology", "econometrics",
                 "marketing science"],
    "workshop speaker": ["innovation", "strategy", "startup", "entrepreneurship",
                         "digital transformation"],
}


def _role_fit_score(speaker_tags: str, event_roles: str) -> float:
    """Role-fit score based on keyword overlap between expertise and needed roles."""
    tags_lower = speaker_tags.lower()
    roles_lower = event_roles.lower()

    matched_roles = 0
    total_roles = 0
    for role, keywords in ROLE_KEYWORD_MAP.items():
        if role in roles_lower:
            total_roles += 1
            for kw in keywords:
                if kw in tags_lower:
                    matched_roles += 1
                    break

    if total_roles == 0:
        return 0.3
    return max(0.3, min(1.0, matched_roles / total_roles))


def _role_fit_details(speaker_tags: str, event_roles: str) -> list[str]:
    """Return which roles matched for explanation purposes."""
    tags_lower = speaker_tags.lower()
    roles_lower = event_roles.lower()
    matched = []
    for role, keywords in ROLE_KEYWORD_MAP.items():
        if role in roles_lower:
            for kw in keywords:
                if kw in tags_lower:
                    matched.append((role, kw))
                    break
    return matched


# ---------------------------------------------------------------------------
# Calendar / schedule overlap
# ---------------------------------------------------------------------------
def _calendar_fit_score(speaker_region: str, event_calendar: pd.DataFrame,
                        opp_region: str = None) -> float:
    """
    Check if there is an IA regional event that aligns both the speaker's
    location and the opportunity's location in the same time window.
    """
    if event_calendar is None or event_calendar.empty:
        return 0.5

    s_cluster = REGION_CLUSTERS.get(speaker_region, speaker_region)
    o_cluster = REGION_CLUSTERS.get(opp_region, "LA") if opp_region else "LA"

    best = 0.3
    for _, row in event_calendar.iterrows():
        e_cluster = REGION_CLUSTERS.get(row.get("region", ""), "")
        # Best: IA event in the same region as both speaker AND opportunity
        if s_cluster == e_cluster and o_cluster == e_cluster:
            return 1.0
        # Good: IA event in speaker's region (they'll already be travelling)
        if s_cluster == e_cluster:
            best = max(best, 0.85)
        # Okay: adjacent
        if (s_cluster, e_cluster) in ADJACENT_CLUSTERS:
            best = max(best, 0.6)
    return best


# ---------------------------------------------------------------------------
# Experience bonus (heuristic from expertise tags)
# ---------------------------------------------------------------------------
def _experience_bonus(expertise_tags: str) -> float:
    """Parse years-of-experience mentions for a seniority bonus."""
    import re
    text = expertise_tags.lower()
    m = re.search(r'(\d+)\+?\s*yr', text)
    if m:
        yrs = int(m.group(1))
        if yrs >= 30:
            return 0.9
        if yrs >= 15:
            return 0.7
        if yrs >= 5:
            return 0.5
    # Founder / CEO / SVP etc. imply seniority
    for marker in ["founder", "ceo", "svp", "vp", "director", "leader"]:
        if marker in text:
            return 0.6
    return 0.4


# ---------------------------------------------------------------------------
# Main matching engine
# ---------------------------------------------------------------------------
def compute_matches(
    speakers: pd.DataFrame,
    opportunities: pd.DataFrame,
    event_calendar: pd.DataFrame = None,
    opp_type: str = "event",
) -> pd.DataFrame:
    """
    Compute match scores between all speakers and all opportunities.

    MATCH_SCORE = 0.35 * topic_relevance   (TF-IDF cosine similarity)
               + 0.25 * role_fit           (keyword matching)
               + 0.20 * geographic_proximity
               + 0.10 * calendar_fit       (IA event overlap)
               + 0.10 * historical_bonus   (experience heuristic)
    """
    # Build enriched text for better TF-IDF matching
    speaker_texts = []
    for _, s in speakers.iterrows():
        # Repeat expertise tags to boost signal; include role and company context
        tags = s.get("expertise_tags", "")
        role = s.get("board_role", "")
        title = s.get("title", "")
        text = f"{tags} {tags} {role} {title}"
        speaker_texts.append(text)

    opp_texts = []
    for _, o in opportunities.iterrows():
        blob = o.get("description_blob", "")
        # Enrich course descriptions with the fit level
        if opp_type == "course":
            fit = o.get("guest_lecture_fit", "")
            blob = f"{blob} {fit} marketing research guest lecture industry"
        opp_texts.append(blob)

    all_texts = speaker_texts + opp_texts
    vectorizer = TfidfVectorizer(
        stop_words="english",
        max_features=800,
        ngram_range=(1, 2),        # bigrams capture "generative ai", "focus groups"
        sublinear_tf=True,          # dampen high-frequency terms
    )
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    speaker_vectors = tfidf_matrix[:len(speaker_texts)]
    opp_vectors = tfidf_matrix[len(speaker_texts):]

    sim_matrix = cosine_similarity(speaker_vectors, opp_vectors)

    # Normalise cosine similarities to [0, 1] range within this batch
    sim_min = sim_matrix.min()
    sim_max = sim_matrix.max()
    if sim_max > sim_min:
        sim_norm = (sim_matrix - sim_min) / (sim_max - sim_min)
    else:
        sim_norm = sim_matrix

    results = []
    opp_name_col = "event_name" if "event_name" in opportunities.columns else "title"
    opp_roles_col = "volunteer_roles" if "volunteer_roles" in opportunities.columns else "guest_lecture_fit"

    for i, (_, speaker) in enumerate(speakers.iterrows()):
        for j, (_, opp) in enumerate(opportunities.iterrows()):
            topic_score = float(sim_norm[i, j])
            raw_cosine = float(sim_matrix[i, j])

            role_score = _role_fit_score(
                speaker.get("expertise_tags", ""),
                opp.get(opp_roles_col, ""),
            )

            opp_region = opp.get("region", "Los Angeles — East")
            geo_score = _geo_score(speaker.get("metro_region", ""), opp_region)

            cal_score = _calendar_fit_score(
                speaker.get("metro_region", ""),
                event_calendar,
                opp_region,
            )

            historical = _experience_bonus(speaker.get("expertise_tags", ""))

            composite = (
                0.35 * topic_score
                + 0.25 * role_score
                + 0.20 * geo_score
                + 0.10 * cal_score
                + 0.10 * historical
            )

            results.append({
                "speaker": speaker["name"],
                "speaker_role": speaker.get("board_role", ""),
                "speaker_expertise": speaker.get("expertise_tags", ""),
                "speaker_region": speaker.get("metro_region", ""),
                "opportunity": opp[opp_name_col],
                "opportunity_type": opp_type,
                "opp_roles": opp.get(opp_roles_col, ""),
                "opp_region": opp_region,
                "topic_relevance": round(topic_score, 3),
                "raw_cosine": round(raw_cosine, 4),
                "role_fit": round(role_score, 3),
                "geographic_proximity": round(geo_score, 3),
                "calendar_fit": round(cal_score, 3),
                "historical_bonus": round(historical, 3),
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
    """Generate a rich, human-readable explanation for a match."""
    parts = []

    # Header
    parts.append(f"### Why this match?")
    parts.append(f"**{row['speaker']}** ({row['speaker_role']}) matched to "
                 f"**{row['opportunity']}** with a composite score of "
                 f"**{row['match_score']:.1%}**.\n")

    # --- Topic relevance ---
    topic_pct = row['topic_relevance']
    parts.append(f"**Topic Relevance** ({topic_pct:.0%}) — "
                 f"{'Strong' if topic_pct > 0.6 else 'Moderate' if topic_pct > 0.3 else 'Low'} "
                 f"overlap between expertise tags and opportunity description.")
    # Show which tags likely drove the match
    speaker_tags = [t.strip() for t in str(row.get('speaker_expertise', '')).split(',') if t.strip()]
    opp_text = str(row.get('opportunity', '')).lower() + " " + str(row.get('opp_roles', '')).lower()
    overlapping = [t for t in speaker_tags if any(w in opp_text for w in t.lower().split())]
    if overlapping:
        parts.append(f"  - Key matching tags: *{', '.join(overlapping[:4])}*")

    # --- Role fit ---
    role_pct = row['role_fit']
    role_details = _role_fit_details(
        str(row.get('speaker_expertise', '')),
        str(row.get('opp_roles', ''))
    )
    parts.append(f"\n**Role Fit** ({role_pct:.0%}) — "
                 f"{'Strong' if role_pct > 0.6 else 'Moderate' if role_pct > 0.3 else 'Baseline'} "
                 f"alignment with needed volunteer roles.")
    if role_details:
        for role_name, matched_kw in role_details[:3]:
            parts.append(f"  - Can serve as **{role_name}** (matched on *{matched_kw}*)")

    # --- Geographic proximity ---
    geo_pct = row['geographic_proximity']
    s_region = row.get('speaker_region', '')
    o_region = row.get('opp_region', 'Cal Poly Pomona area')
    if geo_pct >= 1.0:
        geo_note = f"Same metro region ({s_region})"
    elif geo_pct >= 0.5:
        geo_note = f"Adjacent region ({s_region} near {o_region})"
    else:
        geo_note = f"Remote ({s_region}); virtual participation recommended"
    parts.append(f"\n**Geographic Proximity** ({geo_pct:.0%}) — {geo_note}")

    # --- Calendar fit ---
    cal_pct = row['calendar_fit']
    if cal_pct >= 0.85:
        cal_note = "IA regional event in speaker's area creates a natural travel window"
    elif cal_pct >= 0.6:
        cal_note = "IA event in an adjacent region; could combine trips"
    else:
        cal_note = "No IA event nearby; dedicated trip needed"
    parts.append(f"\n**Calendar Fit** ({cal_pct:.0%}) — {cal_note}")

    # --- Historical / experience ---
    hist_pct = row['historical_bonus']
    if hist_pct >= 0.7:
        hist_note = "Senior professional with extensive industry experience"
    elif hist_pct >= 0.5:
        hist_note = "Established professional with solid experience base"
    else:
        hist_note = "Standard experience level"
    parts.append(f"\n**Experience Bonus** ({hist_pct:.0%}) — {hist_note}")

    # --- Score formula ---
    parts.append(f"\n---\n*Score = 0.35({topic_pct:.2f}) + 0.25({role_pct:.2f}) "
                 f"+ 0.20({geo_pct:.2f}) + 0.10({cal_pct:.2f}) + 0.10({hist_pct:.2f}) "
                 f"= **{row['match_score']:.3f}***")

    return "\n".join(parts)
