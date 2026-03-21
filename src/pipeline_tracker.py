"""Member journey pipeline tracking: Engagement -> Event -> Membership."""

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


def generate_mock_pipeline(speakers: pd.DataFrame, opportunities: pd.DataFrame) -> pd.DataFrame:
    """
    Generate realistic mock pipeline data showing the engagement journey.
    Uses actual speaker and opportunity names for realism.
    """
    random.seed(42)
    records = []
    base_date = datetime(2026, 1, 15)

    # Create pipeline entries for a subset of speaker-opportunity combinations
    speaker_names = speakers["name"].tolist()
    opp_names = opportunities["event_name"].tolist() if "event_name" in opportunities.columns else opportunities["title"].tolist()

    # Simulate ~40 pipeline entries with varying stages
    stage_weights = [0.10, 0.15, 0.20, 0.20, 0.15, 0.10, 0.06, 0.04]

    for i in range(40):
        speaker = random.choice(speaker_names)
        opp = random.choice(opp_names)
        stage_idx = random.choices(range(len(PIPELINE_STAGES)), weights=stage_weights, k=1)[0]
        stage = PIPELINE_STAGES[stage_idx]
        days_offset = random.randint(0, 60)
        entry_date = base_date + timedelta(days=days_offset)

        records.append({
            "id": f"PL-{i+1:03d}",
            "speaker": speaker,
            "opportunity": opp,
            "stage": stage,
            "stage_index": stage_idx,
            "entry_date": entry_date.strftime("%Y-%m-%d"),
            "last_updated": (entry_date + timedelta(days=random.randint(0, 14))).strftime("%Y-%m-%d"),
            "notes": _generate_note(stage, speaker, opp),
        })

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
    }


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
