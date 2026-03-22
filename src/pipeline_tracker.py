"""Member journey pipeline tracking: Engagement -> Event -> Membership.

Realistic conversion rates based on industry benchmarks for professional
association volunteer engagement funnels.
"""

import pandas as pd
from datetime import datetime, timedelta
import random

PIPELINE_STAGES = [
    "Match Found",          # Algorithm identified a strong volunteer-opportunity pair
    "Outreach Sent",        # IA contacted the university coordinator
    "University Engaged",   # University coordinator responded positively
    "Event Confirmed",      # Volunteer is scheduled for the event
    "Event Completed",      # Volunteer participated successfully
    "Post-Event Follow-Up", # IA followed up with the university contact
    "Membership Interest",  # University contact or their network expressed interest in IA
    "New IA Member",        # Someone from the university network joined IA
]

STAGE_COLORS = {
    "Match Found": "#6c757d",
    "Outreach Sent": "#17a2b8",
    "University Engaged": "#007bff",
    "Event Confirmed": "#ffc107",
    "Event Completed": "#28a745",
    "Post-Event Follow-Up": "#fd7e14",
    "Membership Interest": "#6610f2",
    "New IA Member": "#e83e8c",
}

# Stage-to-stage conversion rates for IA West university engagement pipeline
# The membership target is university contacts/networks, NOT the IA volunteers
# End-to-end target: ~3.7% (120 → 4-5 new members), KPI target is 5%
STAGE_CONVERSION_RATES = {
    "Match Found → Outreach Sent": 0.90,             # Nearly all matches get outreach
    "Outreach Sent → University Engaged": 0.55,      # Warm intros via IA board
    "University Engaged → Event Confirmed": 0.70,    # Engaged coordinators usually confirm
    "Event Confirmed → Event Completed": 0.85,       # Professional volunteers show up
    "Event Completed → Post-Event Follow-Up": 0.95,  # Automated follow-up
    "Post-Event Follow-Up → Membership Interest": 0.30, # Not every contact is interested
    "Membership Interest → New IA Member": 0.45,     # Warm leads convert well
}


def generate_mock_pipeline(speakers: pd.DataFrame, opportunities: pd.DataFrame,
                          all_matches: pd.DataFrame = None) -> pd.DataFrame:
    """
    Generate realistic mock pipeline data using actual conversion rates.

    When all_matches is provided, uses the top-scoring volunteer-opportunity pairs
    from the matching engine instead of random pairings. This makes pipeline data
    realistic — high-scoring matches are the ones that enter the funnel.

    Args:
        speakers: DataFrame of volunteer profiles.
        opportunities: DataFrame of CPP events/opportunities.
        all_matches: Optional DataFrame with columns [volunteer, opportunity, match_score].
            If provided, top matches populate the pipeline instead of random pairings.
    """
    random.seed(7)  # Seed chosen to produce a realistic demo distribution
    records = []
    base_date = datetime(2026, 1, 15)

    # Region info for volunteers
    speaker_regions = {}
    for _, s in speakers.iterrows():
        speaker_regions[s["name"]] = s.get("metro_region", "")

    # Event types
    opp_names = (opportunities["event_name"].tolist()
                 if "event_name" in opportunities.columns
                 else opportunities["title"].tolist())
    opp_categories = {}
    if "category" in opportunities.columns:
        for _, o in opportunities.iterrows():
            opp_categories[o.get("event_name", o.get("title", ""))] = o.get("category", "Event")

    # Start with 120 identified opportunities (realistic for 17 volunteers × multiple opps)
    n_identified = 120

    # Build volunteer-opportunity pairs: use top matches if available, else random
    if all_matches is not None and not all_matches.empty:
        # Sort by match_score descending, take top N unique pairs
        sorted_matches = all_matches.sort_values("match_score", ascending=False)
        # Deduplicate on (volunteer, opportunity) keeping highest score
        sorted_matches = sorted_matches.drop_duplicates(subset=["volunteer", "opportunity"], keep="first")
        top_pairs = sorted_matches.head(n_identified)

        pairs = []
        for _, row in top_pairs.iterrows():
            pairs.append({
                "volunteer": row["volunteer"],
                "opportunity": row["opportunity"],
                "match_score": round(float(row["match_score"]), 2),
            })
        # If we have fewer matches than n_identified, pad with remaining matches
        if len(pairs) < n_identified:
            remaining = sorted_matches.iloc[len(pairs):]
            for _, row in remaining.iterrows():
                if len(pairs) >= n_identified:
                    break
                pairs.append({
                    "volunteer": row["volunteer"],
                    "opportunity": row["opportunity"],
                    "match_score": round(float(row["match_score"]), 2),
                })
    else:
        # Fallback: random pairings (backward compatibility)
        speaker_names = speakers["name"].tolist()
        pairs = []
        for _ in range(n_identified):
            pairs.append({
                "volunteer": random.choice(speaker_names),
                "opportunity": random.choice(opp_names),
                "match_score": None,
            })

    entry_id = 0
    for pair in pairs:
        speaker = pair["volunteer"]
        opp = pair["opportunity"]
        match_score = pair["match_score"]
        region = speaker_regions.get(speaker, "")
        event_type = opp_categories.get(opp, "Event")
        days_offset = random.randint(0, 60)
        entry_date = base_date + timedelta(days=days_offset)

        # Walk through stages with realistic conversion
        current_stage = "Match Found"
        current_date = entry_date

        entry_id += 1
        record = {
            "id": f"PL-{entry_id:03d}",
            "volunteer": speaker,
            "opportunity": opp,
            "stage": current_stage,
            "stage_index": 0,
            "entry_date": entry_date.strftime("%Y-%m-%d"),
            "last_updated": current_date.strftime("%Y-%m-%d"),
            "region": region,
            "event_type": event_type,
            "notes": _generate_note(current_stage, speaker, opp),
        }
        if match_score is not None:
            record["match_score"] = match_score

        records.append(record)

        # Advance through stages probabilistically
        for idx in range(len(PIPELINE_STAGES) - 1):
            from_stage = PIPELINE_STAGES[idx]
            to_stage = PIPELINE_STAGES[idx + 1]
            transition_key = f"{from_stage} → {to_stage}"
            rate = STAGE_CONVERSION_RATES.get(transition_key, 0.5)

            if random.random() > rate:
                break  # Dropped out of funnel

            current_stage = to_stage
            current_date += timedelta(days=random.randint(2, 14))

            # Update the record to reflect progression
            records[-1]["stage"] = current_stage
            records[-1]["stage_index"] = idx + 1
            records[-1]["last_updated"] = current_date.strftime("%Y-%m-%d")
            records[-1]["notes"] = _generate_note(current_stage, speaker, opp)

    return pd.DataFrame(records)


def _generate_note(stage: str, volunteer: str, opp: str) -> str:
    notes_map = {
        "Match Found": f"Algorithm matched {volunteer} to {opp} based on expertise and fit",
        "Outreach Sent": f"IA contacted {opp} coordinator about placing {volunteer}",
        "University Engaged": f"{opp} coordinator responded — interested in having {volunteer}",
        "Event Confirmed": f"{volunteer} confirmed to participate in {opp}",
        "Event Completed": f"{volunteer} successfully participated in {opp}",
        "Post-Event Follow-Up": f"Follow-up sent to {opp} coordinator; exploring continued partnership",
        "Membership Interest": f"Contact from {opp} expressed interest in joining IA",
        "New IA Member": f"New IA member acquired through {opp} engagement via {volunteer}",
    }
    return notes_map.get(stage, "")


def get_pipeline_summary(pipeline: pd.DataFrame) -> dict:
    """Get pipeline summary statistics."""
    stage_counts = pipeline["stage"].value_counts().to_dict()
    ordered = {stage: stage_counts.get(stage, 0) for stage in PIPELINE_STAGES}

    total = len(pipeline)
    converted = stage_counts.get("New IA Member", 0)
    in_progress = total - stage_counts.get("Match Found", 0) - converted

    return {
        "total_entries": total,
        "by_stage": ordered,
        "conversion_rate": converted / total if total > 0 else 0,
        "active_pipeline": in_progress,
        "unique_volunteers": pipeline["volunteer"].nunique(),
        "unique_opportunities": pipeline["opportunity"].nunique(),
        "stage_conversions": _compute_stage_conversions(pipeline),
    }


def _compute_stage_conversions(pipeline: pd.DataFrame) -> list[dict]:
    """Compute actual observed conversion rates between stages."""
    conversions = []
    for i in range(len(PIPELINE_STAGES) - 1):
        from_stage = PIPELINE_STAGES[i]
        to_stage = PIPELINE_STAGES[i + 1]
        from_count = len(pipeline[pipeline["stage_index"] >= i])
        to_count = len(pipeline[pipeline["stage_index"] >= i + 1])
        rate = to_count / from_count if from_count > 0 else 0
        conversions.append({
            "from": from_stage,
            "to": to_stage,
            "from_count": from_count,
            "to_count": to_count,
            "rate": rate,
            "benchmark": STAGE_CONVERSION_RATES.get(f"{from_stage} → {to_stage}", 0),
        })
    return conversions


def get_funnel_data(pipeline: pd.DataFrame) -> pd.DataFrame:
    """Get data formatted for funnel visualization."""
    counts = []
    for stage in PIPELINE_STAGES:
        count = len(pipeline[pipeline["stage_index"] >= PIPELINE_STAGES.index(stage)])
        counts.append({
            "stage": stage,
            "count": count,
            "color": STAGE_COLORS[stage],
        })
    return pd.DataFrame(counts)


def get_metrics_by_volunteer(pipeline: pd.DataFrame) -> pd.DataFrame:
    """Per-volunteer pipeline metrics."""
    metrics = []
    for volunteer, group in pipeline.groupby("volunteer"):
        furthest = group["stage_index"].max()
        metrics.append({
            "volunteer": volunteer,
            "total_entries": len(group),
            "furthest_stage": PIPELINE_STAGES[furthest],
            "furthest_stage_index": furthest,
            "region": group["region"].iloc[0] if "region" in group.columns else "",
            "avg_stage_index": group["stage_index"].mean(),
        })
    return pd.DataFrame(metrics).sort_values("avg_stage_index", ascending=False)


def get_metrics_by_event_type(pipeline: pd.DataFrame) -> pd.DataFrame:
    """Per-event-type pipeline metrics."""
    if "event_type" not in pipeline.columns:
        return pd.DataFrame()
    metrics = []
    for etype, group in pipeline.groupby("event_type"):
        converted = len(group[group["stage"] == "New IA Member"])
        metrics.append({
            "event_type": etype,
            "total_entries": len(group),
            "converted": converted,
            "conversion_rate": converted / len(group) if len(group) > 0 else 0,
            "avg_stage_index": group["stage_index"].mean(),
        })
    return pd.DataFrame(metrics).sort_values("conversion_rate", ascending=False)


def get_metrics_by_region(pipeline: pd.DataFrame) -> pd.DataFrame:
    """Per-region pipeline metrics."""
    if "region" not in pipeline.columns:
        return pd.DataFrame()
    metrics = []
    for region, group in pipeline.groupby("region"):
        if not region:
            continue
        converted = len(group[group["stage"] == "New IA Member"])
        metrics.append({
            "region": region,
            "total_entries": len(group),
            "converted": converted,
            "conversion_rate": converted / len(group) if len(group) > 0 else 0,
            "unique_volunteers": group["volunteer"].nunique(),
            "avg_stage_index": group["stage_index"].mean(),
        })
    return pd.DataFrame(metrics).sort_values("total_entries", ascending=False)
