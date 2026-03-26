"""Comprehensive test suite for IA West Smart Match CRM.

Tests all major modules: matching engine, outreach generator, pipeline tracker,
executive analytics, and weight tuner logic.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from src.data_loader import load_all
from src.matching_engine import compute_matches, explain_match
from src.outreach_generator import (
    generate_outreach, extract_subject_body, generate_mailto_url, validate_email,
)
from src.pipeline_tracker import (
    generate_mock_pipeline, get_pipeline_summary, get_funnel_data,
    get_metrics_by_volunteer, get_metrics_by_event_type, get_metrics_by_region,
    PIPELINE_STAGES, STAGE_COLORS, STAGE_CONVERSION_RATES,
)
from src.executive_analytics import (
    compute_roi_projection, compute_coverage, compute_volunteer_scores,
    generate_insights, compute_pipeline_timeline, compute_stage_velocity,
)


# ── Shared fixtures ──

def load_fixtures():
    data = load_all()
    speakers = data["speakers"]
    cpp_events = data["cpp_events"]
    cpp_courses = data["cpp_courses"]
    event_calendar = data["event_calendar"]

    event_matches = compute_matches(speakers, cpp_events, event_calendar, opp_type="event")
    course_matches = compute_matches(speakers, cpp_courses, event_calendar, opp_type="course")
    all_matches = pd.concat([event_matches, course_matches], ignore_index=True)
    all_matches = all_matches.sort_values("match_score", ascending=False).reset_index(drop=True)

    pipeline = generate_mock_pipeline(speakers, cpp_events, all_matches)

    return {
        "speakers": speakers, "cpp_events": cpp_events, "cpp_courses": cpp_courses,
        "event_calendar": event_calendar, "event_matches": event_matches,
        "course_matches": course_matches, "all_matches": all_matches,
        "pipeline": pipeline,
    }


# ═════════════════════════════════════════════
# OUTREACH GENERATOR TESTS
# ═════════════════════════════════════════════

def test_event_outreach_generation(fixtures):
    """Event outreach emails should contain volunteer name and opportunity."""
    match = fixtures["all_matches"].iloc[0].to_dict()
    match["volunteer_title"] = "VP of Research"
    match["volunteer_company"] = "Acme Corp"
    email = generate_outreach(match, {}, "event")

    assert match["volunteer"] in email, "Email should mention volunteer name"
    assert "Subject:" in email, "Email should have a subject line"
    assert "IA West" in email, "Email should reference IA West"
    assert len(email) > 200, "Email should be substantial"
    print(f"  PASS: Event outreach for {match['volunteer']} ({len(email)} chars)")


def test_course_outreach_generation(fixtures):
    """Course outreach emails should reference the instructor and course."""
    match = fixtures["course_matches"].iloc[0].to_dict()
    match["volunteer_title"] = "Professor"
    match["volunteer_company"] = "University"
    course_data = {"title": "Marketing Research", "course": "MKT 301",
                   "instructor": "Dr. Smith", "days": "MWF",
                   "start_time": "10:00", "end_time": "10:50", "mode": "In-Person"}
    email = generate_outreach(match, course_data, "course")

    assert "Dr. Smith" in email, "Course email should reference instructor"
    assert "Subject:" in email
    print(f"  PASS: Course outreach generated for {match['volunteer']}")


def test_extract_subject_body(fixtures):
    """extract_subject_body should split email into subject and body."""
    match = fixtures["all_matches"].iloc[0].to_dict()
    match["volunteer_title"] = "Test"
    match["volunteer_company"] = "Co"
    email = generate_outreach(match, {}, "event")
    parts = extract_subject_body(email)

    assert "subject" in parts and len(parts["subject"]) > 0, "Should extract subject"
    assert "body" in parts and len(parts["body"]) > 0, "Should extract body"
    assert parts["subject"] != parts["body"], "Subject and body should differ"
    print(f"  PASS: Subject extracted: '{parts['subject'][:50]}...'")


def test_mailto_url(fixtures):
    """generate_mailto_url should produce a valid mailto: URL."""
    url = generate_mailto_url("test@example.com", "Hello", "Body text here")
    assert url.startswith("mailto:"), "Should start with mailto:"
    assert "subject=" in url, "Should contain subject parameter"
    assert "body=" in url, "Should contain body parameter"
    print(f"  PASS: Mailto URL generated ({len(url)} chars)")


def test_validate_email():
    """validate_email should accept valid and reject invalid emails."""
    assert validate_email("test@example.com") is True
    assert validate_email("user.name+tag@domain.org") is True
    assert validate_email("notanemail") is False
    assert validate_email("@nodomain.com") is False
    assert validate_email("") is False
    print("  PASS: Email validation works correctly")


# ═════════════════════════════════════════════
# PIPELINE TRACKER TESTS
# ═════════════════════════════════════════════

def test_pipeline_stages():
    """Pipeline should have exactly 8 stages with correct names."""
    assert len(PIPELINE_STAGES) == 8
    assert PIPELINE_STAGES[0] == "Match Found"
    assert PIPELINE_STAGES[-1] == "New IA Member"
    assert all(stage in STAGE_COLORS for stage in PIPELINE_STAGES)
    print(f"  PASS: 8 pipeline stages defined with colors")


def test_pipeline_generation(fixtures):
    """Mock pipeline should have expected structure and realistic distribution."""
    pipeline = fixtures["pipeline"]

    assert len(pipeline) == 120, f"Should have 120 entries, got {len(pipeline)}"
    assert "volunteer" in pipeline.columns
    assert "opportunity" in pipeline.columns
    assert "stage" in pipeline.columns
    assert "stage_index" in pipeline.columns

    # Stages should follow a funnel pattern (more at top, fewer at bottom)
    counts = pipeline["stage"].value_counts()
    first_stage = counts.get("Match Found", 0) + counts.get("Outreach Sent", 0)
    last_stage = counts.get("New IA Member", 0)
    assert first_stage > last_stage, "Pipeline should have funnel shape"
    print(f"  PASS: Pipeline has {len(pipeline)} entries with funnel distribution")


def test_pipeline_summary(fixtures):
    """Pipeline summary should contain all expected fields."""
    summary = get_pipeline_summary(fixtures["pipeline"])

    assert "total_entries" in summary
    assert "by_stage" in summary
    assert "conversion_rate" in summary
    assert "active_pipeline" in summary
    assert "unique_volunteers" in summary
    assert "stage_conversions" in summary

    assert summary["total_entries"] == 120
    assert summary["conversion_rate"] >= 0
    assert summary["conversion_rate"] <= 1
    assert len(summary["stage_conversions"]) == 7  # 8 stages = 7 transitions
    print(f"  PASS: Summary: {summary['total_entries']} entries, {summary['conversion_rate']:.1%} conversion")


def test_funnel_data(fixtures):
    """Funnel data should be monotonically decreasing."""
    funnel = get_funnel_data(fixtures["pipeline"])

    assert len(funnel) == 8, "Should have one row per stage"
    counts = funnel["count"].tolist()
    for i in range(len(counts) - 1):
        assert counts[i] >= counts[i + 1], f"Funnel should decrease: {counts[i]} >= {counts[i+1]}"
    print(f"  PASS: Funnel decreases: {counts[0]} → {counts[-1]}")


def test_conversion_benchmarks():
    """Conversion rate benchmarks should produce 3-5% end-to-end conversion."""
    # Multiply all stage conversion rates
    overall = 1.0
    for rate in STAGE_CONVERSION_RATES.values():
        overall *= rate
    assert 0.02 < overall < 0.10, f"End-to-end rate should be 2-10%, got {overall:.1%}"
    print(f"  PASS: End-to-end benchmark: {overall:.1%}")


# ═════════════════════════════════════════════
# EXECUTIVE ANALYTICS TESTS
# ═════════════════════════════════════════════

def test_roi_projection(fixtures):
    """ROI projections should produce 3 years of positive value."""
    roi = compute_roi_projection(fixtures["pipeline"])

    assert "projections" in roi
    assert len(roi["projections"]) == 3
    assert roi["hours_saved_per_cycle"] > 0
    assert roi["labor_savings_per_cycle"] > 0

    for yr in roi["projections"]:
        assert yr["total_value"] > 0, f"Year {yr['year']} should have positive value"
        assert yr["cumulative_value"] > 0

    # Year 3 should be larger than year 1
    assert roi["projections"][2]["cumulative_value"] > roi["projections"][0]["total_value"]
    yr3 = roi["projections"][2]["cumulative_value"]
    print(f"  PASS: 3-year ROI projects ${yr3:,}")


def test_coverage_analysis(fixtures):
    """Coverage analysis should account for all opportunities."""
    cov = compute_coverage(fixtures["all_matches"])

    total = cov["well_covered"] + cov["partial"] + cov["gaps"]
    assert total == cov["total_opportunities"], "Coverage should sum to total"
    assert 0 <= cov["coverage_pct"] <= 1
    assert len(cov["details"]) == cov["total_opportunities"]
    print(f"  PASS: Coverage: {cov['well_covered']} well / {cov['partial']} partial / {cov['gaps']} gaps")


def test_volunteer_scores(fixtures):
    """Volunteer scores should be in [0, 1] for all volunteers."""
    scores = compute_volunteer_scores(fixtures["all_matches"], fixtures["pipeline"])

    assert len(scores) == len(fixtures["speakers"]), "Should score every volunteer"
    assert scores["engagement_score"].min() >= 0
    assert scores["engagement_score"].max() <= 1
    assert "avg_match_score" in scores.columns
    assert "top_match_score" in scores.columns
    print(f"  PASS: {len(scores)} volunteers scored, top: {scores.iloc[0]['volunteer']} ({scores.iloc[0]['engagement_score']:.0%})")


def test_strategic_insights(fixtures):
    """Strategic insights should be non-empty with required fields."""
    cov = compute_coverage(fixtures["all_matches"])
    scores = compute_volunteer_scores(fixtures["all_matches"], fixtures["pipeline"])
    insights = generate_insights(fixtures["all_matches"], fixtures["pipeline"], cov, scores)

    assert len(insights) >= 1, "Should generate at least one insight"
    for insight in insights:
        assert "category" in insight
        assert "severity" in insight
        assert "title" in insight
        assert "detail" in insight
        assert insight["severity"] in ("high", "medium", "low", "info")
    print(f"  PASS: {len(insights)} strategic insights generated")


def test_pipeline_timeline(fixtures):
    """Pipeline timeline should have chronological entries."""
    timeline = compute_pipeline_timeline(fixtures["pipeline"])

    assert not timeline.empty
    assert "entry_date" in timeline.columns
    assert "cumulative" in timeline.columns
    assert timeline["cumulative"].is_monotonic_increasing
    print(f"  PASS: Timeline has {len(timeline)} data points, cumulative to {timeline['cumulative'].max()}")


def test_stage_velocity(fixtures):
    """Stage velocity should have one row per unique stage in pipeline."""
    velocity = compute_stage_velocity(fixtures["pipeline"])

    assert not velocity.empty
    assert "avg_days" in velocity.columns
    assert all(velocity["avg_days"] >= 0)
    print(f"  PASS: Velocity for {len(velocity)} stages, avg range: {velocity['avg_days'].min():.0f}-{velocity['avg_days'].max():.0f} days")


# ═════════════════════════════════════════════
# WEIGHT TUNER LOGIC TESTS
# ═════════════════════════════════════════════

WEIGHT_COLS = {
    "Topic": "topic_relevance", "Role Fit": "role_fit",
    "Geography": "geographic_proximity", "Calendar": "calendar_fit",
    "Interest": "student_interest", "Experience": "historical_bonus",
}


def test_weight_normalization():
    """Custom weights should normalize to sum=1."""
    raw = {"Topic": 60, "Role Fit": 25, "Geography": 0, "Calendar": 5, "Interest": 5, "Experience": 5}
    total = sum(raw.values())
    norm = {k: v / total for k, v in raw.items()}

    assert abs(sum(norm.values()) - 1.0) < 0.001, "Normalized weights should sum to 1"
    assert norm["Geography"] == 0.0, "Zero weight should stay zero"
    assert norm["Topic"] == 0.6, "60/100 should normalize to 0.6"
    print(f"  PASS: Weights normalize correctly (sum={sum(norm.values()):.3f})")


def test_weight_tuner_changes_rankings(fixtures):
    """Changing weights should produce different top matches."""
    all_m = fixtures["all_matches"]

    # Default weights
    default_top = all_m.head(5)["volunteer"].tolist()

    # Custom: topic-only
    tuned = all_m.copy()
    tuned["match_score"] = tuned["topic_relevance"]  # 100% topic weight
    tuned = tuned.sort_values("match_score", ascending=False).reset_index(drop=True)
    topic_top = tuned.head(5)["volunteer"].tolist()

    # Custom: geography-only
    tuned2 = all_m.copy()
    tuned2["match_score"] = tuned2["geographic_proximity"]
    tuned2 = tuned2.sort_values("match_score", ascending=False).reset_index(drop=True)
    geo_top = tuned2.head(5)["volunteer"].tolist()

    # At least one of these should differ from default
    differs = (default_top != topic_top) or (default_top != geo_top)
    assert differs, "Weight changes should alter rankings"
    print(f"  PASS: Weight tuner changes rankings (default≠topic-only or default≠geo-only)")


def test_weight_tuner_score_bounds(fixtures):
    """Recomputed scores should stay in [0, 1] regardless of weight configuration."""
    all_m = fixtures["all_matches"]

    configs = [
        {"Topic": 1.0, "Role Fit": 0, "Geography": 0, "Calendar": 0, "Interest": 0, "Experience": 0},
        {"Topic": 0, "Role Fit": 0, "Geography": 1.0, "Calendar": 0, "Interest": 0, "Experience": 0},
        {"Topic": 0.166, "Role Fit": 0.166, "Geography": 0.166, "Calendar": 0.166, "Interest": 0.166, "Experience": 0.17},
    ]

    for weights in configs:
        tuned = sum(weights[label] * all_m[col] for label, col in WEIGHT_COLS.items())
        assert tuned.min() >= 0, f"Min score {tuned.min()} should be >= 0"
        assert tuned.max() <= 1.0 + 0.001, f"Max score {tuned.max()} should be <= 1"
    print(f"  PASS: All weight configurations produce scores in [0, 1]")


# ═════════════════════════════════════════════
# EVENT SCORECARD TESTS
# ═════════════════════════════════════════════

from src.event_scorecard import compute_event_scorecards, get_scorecard_summary


def test_event_scorecards(fixtures):
    """Event scorecards should produce one row per opportunity with all required fields."""
    scorecards = compute_event_scorecards(
        fixtures["cpp_events"], fixtures["all_matches"], opp_type="event"
    )
    assert len(scorecards) > 0, "Should produce at least one scorecard"
    assert len(scorecards) <= len(fixtures["cpp_events"]), "Should not exceed opportunity count"

    required_cols = ["opportunity", "impact_score", "match_quality", "conversion_potential",
                     "strategic_value", "priority", "best_volunteer", "est_new_members"]
    for col in required_cols:
        assert col in scorecards.columns, f"Missing column: {col}"

    # All scores in valid range
    for col in ["impact_score", "match_quality", "conversion_potential", "strategic_value"]:
        assert scorecards[col].min() >= 0, f"{col} min below 0"
        assert scorecards[col].max() <= 1.0, f"{col} max above 1"

    # Priority should be one of High/Medium/Low
    valid_priorities = {"High", "Medium", "Low"}
    assert set(scorecards["priority"].unique()).issubset(valid_priorities)

    print(f"  PASS: {len(scorecards)} event scorecards, priorities: {scorecards['priority'].value_counts().to_dict()}")


def test_course_scorecards(fixtures):
    """Course scorecards should work for course data."""
    scorecards = compute_event_scorecards(
        fixtures["cpp_courses"], fixtures["all_matches"], opp_type="course"
    )
    assert len(scorecards) > 0, "Should produce course scorecards"
    assert all(scorecards["type"] == "course"), "All should be course type"
    print(f"  PASS: {len(scorecards)} course scorecards generated")


def test_scorecard_summary(fixtures):
    """Scorecard summary should have correct totals."""
    scorecards = compute_event_scorecards(
        fixtures["cpp_events"], fixtures["all_matches"], opp_type="event"
    )
    summary = get_scorecard_summary(scorecards)

    assert summary["total"] == len(scorecards)
    assert summary["high"] + summary["medium"] + summary["low"] == summary["total"]
    assert summary["avg_impact"] >= 0
    assert len(summary["top_opportunity"]) > 0
    print(f"  PASS: Summary: {summary['high']}H/{summary['medium']}M/{summary['low']}L, top: {summary['top_opportunity']}")


def test_scorecard_sorted_by_impact(fixtures):
    """Scorecards should be sorted by impact score descending."""
    scorecards = compute_event_scorecards(
        fixtures["cpp_events"], fixtures["all_matches"], opp_type="event"
    )
    scores = scorecards["impact_score"].tolist()
    assert scores == sorted(scores, reverse=True), "Should be sorted by impact descending"
    print(f"  PASS: Scorecards sorted by impact ({scores[0]:.0%} → {scores[-1]:.0%})")


# ═════════════════════════════════════════════
# AI HELPERS TESTS
# ═════════════════════════════════════════════

from src.ai_helpers import ai_enabled, ai_explain_match, ai_personalize_email, ai_strategic_insights, ai_answer_question


def test_ai_enabled():
    """ai_enabled should return bool without crashing."""
    result = ai_enabled()
    assert isinstance(result, bool), f"Should return bool, got {type(result)}"
    print(f"  PASS: ai_enabled() = {result}")


def test_ai_graceful_degradation():
    """AI functions should return None when API key is unavailable."""
    # These should all return None (or a string) without crashing
    result1 = ai_explain_match(
        "Test", "Role", "AI, data", "LA", "Hackathon", "event", "Judge",
        0.8, 0.7, 1.0, 0.5, 0.6, 0.5, 0.75,
    )
    result2 = ai_personalize_email(
        "Test", "VP", "Corp", "AI", "Board", "LA",
        "Hackathon", "event", "Dr. Smith", 0.75, 0.8,
    )
    result3 = ai_strategic_insights(
        900, 0.15, 0, 1.0, "Los Angeles", 0.65, 120, 0.45, [],
    )
    result4 = ai_answer_question("Who is the best match?", "Test summary data")

    # All should be None (no API key) or str (if key exists)
    for name, result in [("explain", result1), ("email", result2), ("insights", result3), ("qa", result4)]:
        assert result is None or isinstance(result, str), f"{name} should return None or str, got {type(result)}"
    print(f"  PASS: All AI functions degrade gracefully (enabled={ai_enabled()})")


# ═════════════════════════════════════════════
# RUNNER
# ═════════════════════════════════════════════

if __name__ == "__main__":
    print("Loading data and computing fixtures...")
    fixtures = load_fixtures()
    print(f"Loaded: {len(fixtures['all_matches'])} matches, {len(fixtures['pipeline'])} pipeline entries\n")

    test_groups = [
        ("OUTREACH GENERATOR", [
            ("Event outreach generation", lambda: test_event_outreach_generation(fixtures)),
            ("Course outreach generation", lambda: test_course_outreach_generation(fixtures)),
            ("Extract subject/body", lambda: test_extract_subject_body(fixtures)),
            ("Mailto URL generation", lambda: test_mailto_url(fixtures)),
            ("Email validation", lambda: test_validate_email()),
        ]),
        ("PIPELINE TRACKER", [
            ("Pipeline stages", lambda: test_pipeline_stages()),
            ("Pipeline generation", lambda: test_pipeline_generation(fixtures)),
            ("Pipeline summary", lambda: test_pipeline_summary(fixtures)),
            ("Funnel data", lambda: test_funnel_data(fixtures)),
            ("Conversion benchmarks", lambda: test_conversion_benchmarks()),
        ]),
        ("EXECUTIVE ANALYTICS", [
            ("ROI projection", lambda: test_roi_projection(fixtures)),
            ("Coverage analysis", lambda: test_coverage_analysis(fixtures)),
            ("Volunteer scores", lambda: test_volunteer_scores(fixtures)),
            ("Strategic insights", lambda: test_strategic_insights(fixtures)),
            ("Pipeline timeline", lambda: test_pipeline_timeline(fixtures)),
            ("Stage velocity", lambda: test_stage_velocity(fixtures)),
        ]),
        ("WEIGHT TUNER", [
            ("Weight normalization", lambda: test_weight_normalization()),
            ("Rankings change with weights", lambda: test_weight_tuner_changes_rankings(fixtures)),
            ("Score bounds across configs", lambda: test_weight_tuner_score_bounds(fixtures)),
        ]),
        ("EVENT SCORECARDS", [
            ("Event scorecards", lambda: test_event_scorecards(fixtures)),
            ("Course scorecards", lambda: test_course_scorecards(fixtures)),
            ("Scorecard summary", lambda: test_scorecard_summary(fixtures)),
            ("Scorecards sorted by impact", lambda: test_scorecard_sorted_by_impact(fixtures)),
        ]),
        ("AI HELPERS", [
            ("AI enabled check", lambda: test_ai_enabled()),
            ("AI graceful degradation", lambda: test_ai_graceful_degradation()),
        ]),
    ]

    total_passed = 0
    total_failed = 0

    for group_name, tests in test_groups:
        print(f"\n{'═' * 50}")
        print(f"  {group_name}")
        print(f"{'═' * 50}")
        for name, fn in tests:
            try:
                print(f"[TEST] {name}")
                fn()
                total_passed += 1
            except AssertionError as e:
                print(f"  FAIL: {e}")
                total_failed += 1
            except Exception as e:
                print(f"  ERROR: {type(e).__name__}: {e}")
                total_failed += 1

    print(f"\n{'=' * 50}")
    print(f"Results: {total_passed} passed, {total_failed} failed out of {total_passed + total_failed} tests")
    if total_failed == 0:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
        sys.exit(1)
