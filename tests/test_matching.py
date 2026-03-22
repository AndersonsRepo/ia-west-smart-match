"""Tests for the Smart Match matching engine.

Verifies that the algorithm produces correct, explainable results for
known volunteer-opportunity pairs.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from src.data_loader import load_all
from src.matching_engine import compute_matches, explain_match, get_top_for_volunteer


def setup():
    """Load data and compute all matches."""
    data = load_all()
    event_matches = compute_matches(
        data["speakers"], data["cpp_events"], data["event_calendar"], opp_type="event"
    )
    course_matches = compute_matches(
        data["speakers"], data["cpp_courses"], data["event_calendar"], opp_type="course"
    )
    all_matches = pd.concat([event_matches, course_matches], ignore_index=True)
    all_matches = all_matches.sort_values("match_score", ascending=False).reset_index(drop=True)
    return data, event_matches, course_matches, all_matches


def test_all_speakers_have_matches(data, all_matches):
    """Every volunteer should have at least one match."""
    speaker_names = set(data["speakers"]["name"].tolist())
    matched_volunteers = set(all_matches["volunteer"].unique())
    missing = speaker_names - matched_volunteers
    assert len(missing) == 0, f"Speakers without matches: {missing}"
    print(f"  PASS: All {len(speaker_names)} volunteers have matches")


def test_yufan_lin_ai_hackathon(event_matches):
    """Dr. Yufan Lin (AI, marketing research) should match highest with AI Hackathon events."""
    lin_matches = event_matches[event_matches["volunteer"] == "Dr. Yufan Lin"]
    top_5 = lin_matches.head(5)
    top_opportunities = top_5["opportunity"].tolist()

    # AI Hackathon should be in top 3
    ai_hackathon_match = lin_matches[
        lin_matches["opportunity"].str.contains("AI", case=False)
    ]
    assert not ai_hackathon_match.empty, "Dr. Yufan Lin should match with AI Hackathon events"

    best_ai = ai_hackathon_match.iloc[0]
    assert best_ai["match_score"] >= 0.6, (
        f"AI Hackathon match score for Dr. Lin should be >= 0.6, got {best_ai['match_score']:.3f}"
    )

    # AI Hackathon should be in top 3
    top_3_opps = lin_matches.head(3)["opportunity"].tolist()
    ai_in_top_3 = any("AI" in o for o in top_3_opps)
    assert ai_in_top_3, f"AI Hackathon should be in Lin's top 3, got: {top_3_opps}"

    print(f"  PASS: Dr. Yufan Lin's top AI match: {best_ai['opportunity']} ({best_ai['match_score']:.3f})")


def test_yufan_lin_marketing_courses(course_matches):
    """Dr. Yufan Lin should match well with Marketing Research courses."""
    lin_courses = course_matches[course_matches["volunteer"] == "Dr. Yufan Lin"]
    top_5 = lin_courses.head(5)

    # Marketing Research should appear in top matches
    mktg_research = lin_courses[
        lin_courses["opportunity"].str.contains("Marketing Research|Research", case=False)
    ]
    assert not mktg_research.empty, "Dr. Lin should match with Marketing Research courses"
    assert mktg_research.iloc[0]["match_score"] >= 0.5, (
        f"Marketing Research match should be >= 0.5, got {mktg_research.iloc[0]['match_score']:.3f}"
    )
    print(f"  PASS: Dr. Yufan Lin matches Marketing Research courses (best: {mktg_research.iloc[0]['match_score']:.3f})")


def test_greg_carter_qualitative(event_matches):
    """Greg Carter (40 yrs, focus groups) should match with qualitative-focused events."""
    carter = event_matches[event_matches["volunteer"] == "Greg Carter"]
    assert not carter.empty, "Greg Carter should have event matches"

    # His top matches should include research-oriented events
    top_5 = carter.head(5)
    research_matches = top_5[
        top_5["opportunity"].str.contains("Research|OUR|CARS", case=False)
    ]
    assert not research_matches.empty, (
        f"Carter's top 5 should include research events, got: {top_5['opportunity'].tolist()}"
    )

    # His experience bonus should be high (40 yrs)
    assert carter.iloc[0]["historical_bonus"] >= 0.7, (
        f"Carter's experience bonus should be >= 0.7 (40 yrs), got {carter.iloc[0]['historical_bonus']}"
    )
    print(f"  PASS: Greg Carter matches research events, experience bonus: {carter.iloc[0]['historical_bonus']}")


def test_geographic_la_speakers(event_matches):
    """LA-area volunteers should score higher for CPP (LA) events than remote volunteers."""
    # Compare average geo scores for LA vs non-LA volunteers
    la_regions = ["Los Angeles", "Los Angeles — West", "Los Angeles — North",
                  "Los Angeles — East", "Los Angeles — Long Beach"]

    la_scores = event_matches[event_matches["volunteer_region"].isin(la_regions)]["geographic_proximity"]
    non_la_scores = event_matches[~event_matches["volunteer_region"].isin(la_regions)]["geographic_proximity"]

    assert la_scores.mean() > non_la_scores.mean(), (
        f"LA avg geo ({la_scores.mean():.3f}) should exceed non-LA ({non_la_scores.mean():.3f})"
    )

    # LA volunteers should have geo = 1.0 (same cluster)
    assert (la_scores == 1.0).all(), "All LA volunteers should have geo_proximity = 1.0 for CPP events"

    # Remote speakers should have geo < 1.0
    assert (non_la_scores < 1.0).all(), "Non-LA volunteers should have geo < 1.0"

    print(f"  PASS: LA volunteers geo avg: {la_scores.mean():.3f}, non-LA: {non_la_scores.mean():.3f}")


def test_match_explanations(all_matches):
    """Match explanations should be non-empty and contain key sections."""
    top = all_matches.iloc[0]
    explanation = explain_match(top)

    assert "Why this match?" in explanation
    assert "Topic Relevance" in explanation
    assert "Role Fit" in explanation
    assert "Geographic Proximity" in explanation
    assert "Calendar Fit" in explanation
    assert "Experience Bonus" in explanation
    assert "Score =" in explanation

    # Should mention the volunteer and opportunity by name
    assert top["volunteer"] in explanation
    assert top["opportunity"] in explanation

    print(f"  PASS: Explanation for {top['volunteer']} -> {top['opportunity']} is well-structured")


def test_score_range(all_matches):
    """All scores should be in [0, 1] range."""
    for col in ["match_score", "topic_relevance", "role_fit",
                "geographic_proximity", "calendar_fit", "historical_bonus"]:
        assert all_matches[col].min() >= 0, f"{col} has values below 0"
        assert all_matches[col].max() <= 1.0, f"{col} has values above 1.0"
    print(f"  PASS: All score columns in [0, 1] range")


def test_no_duplicate_matches(all_matches):
    """Each volunteer-opportunity pair should appear at most once per type."""
    dupes = all_matches.duplicated(
        subset=["volunteer", "opportunity", "opportunity_type"], keep=False
    )
    dupe_count = dupes.sum()
    # Courses may have duplicate titles (different sections) so allow those
    event_dupes = all_matches[
        (all_matches["opportunity_type"] == "event") & dupes
    ]
    assert len(event_dupes) == 0, f"Found {len(event_dupes)} duplicate event matches"
    print(f"  PASS: No duplicate event matches")


if __name__ == "__main__":
    print("Loading data and computing matches...")
    data, event_matches, course_matches, all_matches = setup()
    print(f"Computed {len(all_matches)} total matches\n")

    tests = [
        ("All volunteers have matches", lambda: test_all_speakers_have_matches(data, all_matches)),
        ("Dr. Yufan Lin -> AI Hackathon", lambda: test_yufan_lin_ai_hackathon(event_matches)),
        ("Dr. Yufan Lin -> Marketing courses", lambda: test_yufan_lin_marketing_courses(course_matches)),
        ("Greg Carter -> Qualitative events", lambda: test_greg_carter_qualitative(event_matches)),
        ("Geographic: LA > non-LA", lambda: test_geographic_la_speakers(event_matches)),
        ("Match explanations", lambda: test_match_explanations(all_matches)),
        ("Score range [0, 1]", lambda: test_score_range(all_matches)),
        ("No duplicate matches", lambda: test_no_duplicate_matches(all_matches)),
    ]

    passed = 0
    failed = 0
    for name, test_fn in tests:
        try:
            print(f"[TEST] {name}")
            test_fn()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    if failed == 0:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
        sys.exit(1)
