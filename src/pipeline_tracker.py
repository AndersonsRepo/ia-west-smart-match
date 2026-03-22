"""Member journey pipeline tracking: Engagement -> Event -> Membership.

Realistic conversion rates based on industry benchmarks for professional
association volunteer engagement funnels.
"""

import pandas as pd
from datetime import datetime, timedelta
import random

PIPELINE_STAGES = [
    "Identified",       # Opportunity discovered
    "Outreach Sent",    # Email/contact initiated
    "Engaged",          # Responded positively
    "Event Scheduled",  # Committed to an event
    "Event Completed",  # Participated in event
    "Follow-Up",        # Post-event follow-up
    "Membership Lead",  # Expressed interest in IA membership
    "Member",           # Converted to IA member
]

STAGE_COLORS = {
    "Identified": "#6c757d",
    "Outreach Sent": "#17a2b8",
    "Engaged": "#007bff",
    "Event Scheduled": "#ffc107",
    "Event Completed": "#28a745",
    "Follow-Up": "#fd7e14",
    "Membership Lead": "#6610f2",
    "Member": "#e83e8c",
}

# Realistic stage-to-stage conversion rates for VOLUNTEER engagement CRM
# End-to-end target: ~3.7% (120 → 4-5 members), KPI target is 5%
STAGE_CONVERSION_RATES = {
    "Identified → Outreach Sent": 0.90,      # Internal org, nearly all get contacted
    "Outreach Sent → Engaged": 0.55,         # Warm intros from IA board, higher than cold outreach
    "Engaged → Event Scheduled": 0.70,       # Volunteers who respond are usually committed
    "Event Scheduled → Event Completed": 0.85, # Professional volunteers show up
    "Event Completed → Follow-Up": 0.95,     # Automated follow-up
    "Follow-Up → Membership Lead": 0.30,     # Not everyone wants membership
    "Membership Lead → Member": 0.45,        # Warm leads convert well
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
        current_stage = "Identified"
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
        "Identified": f"Identified {opp} as potential match for {volunteer}",
        "Outreach Sent": f"Sent personalized outreach email to {opp} coordinator",
        "Engaged": f"Coordinator responded — interested in having {volunteer} participate",
        "Event Scheduled": f"Confirmed {volunteer} for upcoming {opp} event",
        "Event Completed": f"{volunteer} successfully participated in {opp}",
        "Follow-Up": f"Post-event follow-up sent; {volunteer} interested in continued engagement",
        "Membership Lead": f"Contact from {opp} expressed interest in IA membership",
        "Member": f"New IA member converted from {opp} engagement",
    }
    return notes_map.get(stage, "")


def get_pipeline_summary(pipeline: pd.DataFrame) -> dict:
    """Get pipeline summary statistics."""
    stage_counts = pipeline["stage"].value_counts().to_dict()
    ordered = {stage: stage_counts.get(stage, 0) for stage in PIPELINE_STAGES}

    total = len(pipeline)
    converted = stage_counts.get("Member", 0)
    in_progress = total - stage_counts.get("Identified", 0) - converted

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
        converted = len(group[group["stage"] == "Member"])
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
        converted = len(group[group["stage"] == "Member"])
        metrics.append({
            "region": region,
            "total_entries": len(group),
            "converted": converted,
            "conversion_rate": converted / len(group) if len(group) > 0 else 0,
            "unique_volunteers": group["volunteer"].nunique(),
            "avg_stage_index": group["stage_index"].mean(),
        })
    return pd.DataFrame(metrics).sort_values("total_entries", ascending=False)
