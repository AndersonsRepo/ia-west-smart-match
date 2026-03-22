"""Executive analytics: ROI projections, coverage analysis, and strategic insights.

Synthesizes data from matching engine + pipeline into actionable executive metrics.
No LLM calls — all insights are deterministic from the data.
"""

import pandas as pd
import numpy as np
from src.pipeline_tracker import PIPELINE_STAGES, STAGE_CONVERSION_RATES


# ---------------------------------------------------------------------------
# ROI Model
# ---------------------------------------------------------------------------
# IA West membership dues and engagement value benchmarks
MEMBERSHIP_ANNUAL_DUES = 250  # Estimated annual dues per member
EVENT_ENGAGEMENT_VALUE = 150  # Value of a single event participation (brand, networking)
OUTREACH_COST_MANUAL = 45     # Minutes per manual match + outreach
OUTREACH_COST_SMART = 5       # Minutes per Smart Match outreach
HOURLY_RATE_COORDINATOR = 35  # Estimated coordinator hourly rate


def compute_roi_projection(pipeline: pd.DataFrame, n_years: int = 3) -> dict:
    """Project ROI from Smart Match over N years.

    Returns yearly projections of membership revenue, time savings, and
    total value generated.
    """
    total_entries = len(pipeline)
    members = len(pipeline[pipeline["stage"] == "Member"])
    conversion_rate = members / total_entries if total_entries > 0 else 0.037

    # Time savings per match cycle
    matches_per_cycle = total_entries
    manual_hours = (matches_per_cycle * OUTREACH_COST_MANUAL) / 60
    smart_hours = (matches_per_cycle * OUTREACH_COST_SMART) / 60
    hours_saved = manual_hours - smart_hours
    labor_savings = hours_saved * HOURLY_RATE_COORDINATOR

    projections = []
    cumulative_members = members
    cumulative_revenue = 0

    for year in range(1, n_years + 1):
        # Each year: run ~2 full match cycles (spring + fall semesters)
        cycles = 2
        new_entries = int(matches_per_cycle * cycles * (1 + 0.15 * (year - 1)))  # 15% growth
        new_members = int(new_entries * conversion_rate)
        cumulative_members += new_members

        membership_revenue = cumulative_members * MEMBERSHIP_ANNUAL_DUES
        engagement_value = new_entries * EVENT_ENGAGEMENT_VALUE * 0.3  # 30% participate in events
        annual_labor_savings = labor_savings * cycles * (1 + 0.15 * (year - 1))

        total_value = membership_revenue + engagement_value + annual_labor_savings
        cumulative_revenue += total_value

        projections.append({
            "year": year,
            "label": f"Year {year}",
            "new_entries": new_entries,
            "new_members": new_members,
            "cumulative_members": cumulative_members,
            "membership_revenue": round(membership_revenue),
            "engagement_value": round(engagement_value),
            "labor_savings": round(annual_labor_savings),
            "total_value": round(total_value),
            "cumulative_value": round(cumulative_revenue),
        })

    return {
        "current_conversion_rate": conversion_rate,
        "hours_saved_per_cycle": round(hours_saved, 1),
        "labor_savings_per_cycle": round(labor_savings),
        "projections": projections,
    }


# ---------------------------------------------------------------------------
# Coverage Analysis
# ---------------------------------------------------------------------------
def compute_coverage(all_matches: pd.DataFrame, threshold: float = 0.5) -> dict:
    """Analyze which opportunities have strong volunteer coverage and which are gaps."""
    above = all_matches[all_matches["match_score"] >= threshold]

    opp_coverage = all_matches.groupby("opportunity").agg(
        best_score=("match_score", "max"),
        avg_score=("match_score", "mean"),
        strong_matches=("match_score", lambda x: (x >= threshold).sum()),
        total_matches=("match_score", "count"),
    ).reset_index()

    opp_coverage["coverage_status"] = opp_coverage["strong_matches"].apply(
        lambda x: "Well Covered" if x >= 3 else "Partial" if x >= 1 else "Gap"
    )

    well_covered = len(opp_coverage[opp_coverage["coverage_status"] == "Well Covered"])
    partial = len(opp_coverage[opp_coverage["coverage_status"] == "Partial"])
    gaps = len(opp_coverage[opp_coverage["coverage_status"] == "Gap"])

    return {
        "total_opportunities": len(opp_coverage),
        "well_covered": well_covered,
        "partial": partial,
        "gaps": gaps,
        "coverage_pct": well_covered / len(opp_coverage) if len(opp_coverage) > 0 else 0,
        "details": opp_coverage.sort_values("best_score", ascending=False),
    }


# ---------------------------------------------------------------------------
# Volunteer Engagement Scores
# ---------------------------------------------------------------------------
def compute_volunteer_scores(all_matches: pd.DataFrame, pipeline: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-volunteer engagement score combining match quality + pipeline progress."""
    match_agg = all_matches.groupby("volunteer").agg(
        avg_match_score=("match_score", "mean"),
        top_match_score=("match_score", "max"),
        strong_matches=("match_score", lambda x: (x >= 0.5).sum()),
    ).reset_index()

    if not pipeline.empty and "volunteer" in pipeline.columns:
        pipe_agg = pipeline.groupby("volunteer").agg(
            pipeline_entries=("stage", "count"),
            furthest_stage=("stage_index", "max"),
        ).reset_index()
        merged = match_agg.merge(pipe_agg, on="volunteer", how="left")
    else:
        merged = match_agg
        merged["pipeline_entries"] = 0
        merged["furthest_stage"] = 0

    merged = merged.fillna(0)

    # Engagement score: weighted combination
    merged["engagement_score"] = (
        0.40 * merged["avg_match_score"]
        + 0.30 * (merged["top_match_score"])
        + 0.15 * (merged["strong_matches"] / max(merged["strong_matches"].max(), 1))
        + 0.15 * (merged["furthest_stage"] / max(len(PIPELINE_STAGES) - 1, 1))
    )
    merged["engagement_score"] = merged["engagement_score"].clip(0, 1).round(3)

    return merged.sort_values("engagement_score", ascending=False)


# ---------------------------------------------------------------------------
# Strategic Insights (deterministic, rule-based)
# ---------------------------------------------------------------------------
def generate_insights(
    all_matches: pd.DataFrame,
    pipeline: pd.DataFrame,
    coverage: dict,
    volunteer_scores: pd.DataFrame,
) -> list[dict]:
    """Generate actionable strategic insights from the data."""
    insights = []

    # 1. Coverage gaps
    if coverage["gaps"] > 0:
        gap_opps = coverage["details"][coverage["details"]["coverage_status"] == "Gap"]
        gap_names = gap_opps["opportunity"].head(3).tolist()
        insights.append({
            "category": "Coverage Gap",
            "icon": "warning",
            "severity": "high",
            "title": f"{coverage['gaps']} opportunities lack strong volunteer matches",
            "detail": f"These opportunities have no volunteer scoring above 50%: "
                       f"{', '.join(gap_names)}. Consider recruiting new volunteers with "
                       f"expertise in these areas or adjusting event descriptions.",
        })

    # 2. Top volunteers underutilized
    top_vols = volunteer_scores.head(5)
    underused = top_vols[top_vols["pipeline_entries"] == 0]
    if not underused.empty:
        names = underused["volunteer"].tolist()
        insights.append({
            "category": "Underutilized Talent",
            "icon": "star",
            "severity": "medium",
            "title": f"{len(names)} high-scoring volunteers not yet in pipeline",
            "detail": f"These volunteers have strong match scores but haven't entered "
                       f"the engagement pipeline: {', '.join(names)}. Prioritize outreach "
                       f"to maximize their impact.",
        })

    # 3. Geographic concentration
    if "volunteer_region" in all_matches.columns:
        region_counts = all_matches.groupby("volunteer_region")["match_score"].agg(["mean", "count"])
        top_region = region_counts["mean"].idxmax()
        insights.append({
            "category": "Geographic Strategy",
            "icon": "globe",
            "severity": "info",
            "title": f"{top_region} volunteers have the highest average match scores",
            "detail": f"Volunteers from {top_region} average "
                       f"{region_counts.loc[top_region, 'mean']:.0%} match scores. "
                       f"Focus event scheduling around IA events in this region to "
                       f"maximize in-person engagement.",
        })

    # 4. Pipeline health
    if not pipeline.empty:
        engaged_rate = len(pipeline[pipeline["stage_index"] >= 2]) / len(pipeline)
        if engaged_rate < 0.3:
            insights.append({
                "category": "Pipeline Health",
                "icon": "activity",
                "severity": "high",
                "title": "Low engagement rate in pipeline",
                "detail": f"Only {engaged_rate:.0%} of pipeline entries have progressed "
                           f"past the Engaged stage. Review outreach messaging and follow-up "
                           f"cadence to improve conversion.",
            })
        else:
            insights.append({
                "category": "Pipeline Health",
                "icon": "check_circle",
                "severity": "low",
                "title": f"Healthy pipeline: {engaged_rate:.0%} engagement rate",
                "detail": "Pipeline conversion rates are tracking at or above benchmarks. "
                           "Maintain current outreach strategy and follow-up cadence.",
            })

    # 5. Matching algorithm quality
    high_quality = len(all_matches[all_matches["match_score"] >= 0.6]) / len(all_matches)
    insights.append({
        "category": "Algorithm Quality",
        "icon": "cpu",
        "severity": "info",
        "title": f"{high_quality:.0%} of matches score 60%+ (strong alignment)",
        "detail": f"The matching algorithm produces {len(all_matches[all_matches['match_score'] >= 0.6])} "
                   f"high-quality matches out of {len(all_matches)} total pairs. "
                   f"This indicates good data quality and algorithm calibration.",
    })

    return insights


# ---------------------------------------------------------------------------
# Time-series pipeline metrics
# ---------------------------------------------------------------------------
def compute_pipeline_timeline(pipeline: pd.DataFrame) -> pd.DataFrame:
    """Compute cumulative pipeline entries over time for trend visualization."""
    if pipeline.empty or "entry_date" not in pipeline.columns:
        return pd.DataFrame()

    pipeline = pipeline.copy()
    pipeline["entry_date"] = pd.to_datetime(pipeline["entry_date"])

    daily = pipeline.groupby("entry_date").size().reset_index(name="new_entries")
    daily = daily.sort_values("entry_date")
    daily["cumulative"] = daily["new_entries"].cumsum()
    daily["week"] = daily["entry_date"].dt.isocalendar().week.astype(int)

    return daily


def compute_stage_velocity(pipeline: pd.DataFrame) -> pd.DataFrame:
    """Average days between stages (estimated from entry_date and last_updated)."""
    if pipeline.empty:
        return pd.DataFrame()

    pipeline = pipeline.copy()
    pipeline["entry_date"] = pd.to_datetime(pipeline["entry_date"])
    pipeline["last_updated"] = pd.to_datetime(pipeline["last_updated"])
    pipeline["days_in_pipeline"] = (pipeline["last_updated"] - pipeline["entry_date"]).dt.days

    velocity = pipeline.groupby("stage").agg(
        avg_days=("days_in_pipeline", "mean"),
        count=("stage", "count"),
    ).reset_index()

    # Reorder by stage index
    stage_order = {s: i for i, s in enumerate(PIPELINE_STAGES)}
    velocity["stage_idx"] = velocity["stage"].map(stage_order)
    velocity = velocity.sort_values("stage_idx").drop(columns="stage_idx")

    return velocity
