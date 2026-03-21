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

# Realistic stage-to-stage conversion rates (industry benchmarks)
STAGE_CONVERSION_RATES = {
    "Identified → Outreach Sent": 0.85,      # Most identified get outreach
    "Outreach Sent → Engaged": 0.40,         # 40% response rate for warm intros
    "Engaged → Event Scheduled": 0.60,       # Interested contacts schedule well
    "Event Scheduled → Event Completed": 0.80, # Most show up when committed
    "Event Completed → Follow-Up": 0.90,     # Nearly all get follow-ups
    "Follow-Up → Membership Lead": 0.25,     # 25% express membership interest
    "Membership Lead → Member": 0.35,        # 35% of leads convert
}


def generate_mock_pipeline(speakers: pd.DataFrame, opportunities: pd.DataFrame) -> pd.DataFrame:
    """
    Generate realistic mock pipeline data using actual conversion rates.
    Pipeline starts with all speaker-opportunity matches and filters through stages.
    """
    random.seed(7)  # Seed chosen to produce a realistic demo distribution
    records = []
    base_date = datetime(2026, 1, 15)

    speaker_names = speakers["name"].tolist()
    opp_names = (opportunities["event_name"].tolist()
                 if "event_name" in opportunities.columns
                 else opportunities["title"].tolist())

    # Region info for speakers
    speaker_regions = {}
    for _, s in speakers.iterrows():
        speaker_regions[s["name"]] = s.get("metro_region", "")

    # Event types
    opp_categories = {}
    if "category" in opportunities.columns:
        for _, o in opportunities.iterrows():
            opp_categories[o.get("event_name", o.get("title", ""))] = o.get("category", "Event")

    # Start with ~80 identified opportunities, then cascade through stages
    n_identified = 80
    entry_id = 0

    for _ in range(n_identified):
        speaker = random.choice(speaker_names)
        opp = random.choice(opp_names)
        region = speaker_regions.get(speaker, "")
        event_type = opp_categories.get(opp, "Event")
        days_offset = random.randint(0, 60)
        entry_date = base_date + timedelta(days=days_offset)

        # Walk through stages with realistic conversion
        current_stage = "Identified"
        current_date = entry_date

        entry_id += 1
        records.append({
            "id": f"PL-{entry_id:03d}",
            "speaker": speaker,
            "opportunity": opp,
            "stage": current_stage,
            "stage_index": 0,
            "entry_date": entry_date.strftime("%Y-%m-%d"),
            "last_updated": current_date.strftime("%Y-%m-%d"),
            "region": region,
            "event_type": event_type,
            "notes": _generate_note(current_stage, speaker, opp),
        })

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


def _generate_note(stage: str, speaker: str, opp: str) -> str:
    notes_map = {
        "Identified": f"Identified {opp} as potential match for {speaker}",
        "Outreach Sent": f"Sent personalized outreach email to {opp} coordinator",
        "Engaged": f"Coordinator responded — interested in having {speaker} participate",
        "Event Scheduled": f"Confirmed {speaker} for upcoming {opp} event",
        "Event Completed": f"{speaker} successfully participated in {opp}",
        "Follow-Up": f"Post-event follow-up sent; {speaker} interested in continued engagement",
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
        "unique_speakers": pipeline["speaker"].nunique(),
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


def get_metrics_by_speaker(pipeline: pd.DataFrame) -> pd.DataFrame:
    """Per-speaker pipeline metrics."""
    metrics = []
    for speaker, group in pipeline.groupby("speaker"):
        furthest = group["stage_index"].max()
        metrics.append({
            "speaker": speaker,
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
            "unique_speakers": group["speaker"].nunique(),
            "avg_stage_index": group["stage_index"].mean(),
        })
    return pd.DataFrame(metrics).sort_values("total_entries", ascending=False)
