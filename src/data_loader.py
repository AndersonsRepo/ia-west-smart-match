"""Load and normalize all CSV data sources."""

import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def load_speakers() -> pd.DataFrame:
    """Load speaker profiles with normalized columns."""
    df = pd.read_csv(DATA_DIR / "speaker_profiles.csv")
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={
        "Name": "name",
        "Board Role": "board_role",
        "Metro Region": "metro_region",
        "Company": "company",
        "Title": "title",
        "Expertise Tags": "expertise_tags",
    })
    df["expertise_tags"] = df["expertise_tags"].fillna("")
    df["expertise_list"] = df["expertise_tags"].apply(
        lambda x: [t.strip() for t in x.split(",") if t.strip()]
    )
    return df


def load_cpp_events() -> pd.DataFrame:
    """Load CPP events/contacts with normalized columns."""
    df = pd.read_csv(DATA_DIR / "cpp_events.csv")
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={
        "Event / Program": "event_name",
        "Category": "category",
        "Recurrence (typical)": "recurrence",
        "Host / Unit": "host",
        "Volunteer Roles (fit)": "volunteer_roles",
        "Primary Audience": "audience",
        "Public URL": "url",
        "Point(s) of Contact (published)": "contact_name",
        "Contact Email / Phone (published)": "contact_email",
    })
    df["volunteer_roles"] = df["volunteer_roles"].fillna("")
    df["role_list"] = df["volunteer_roles"].apply(
        lambda x: [r.strip() for r in x.split(";") if r.strip()]
    )
    # Build a text blob for matching
    df["description_blob"] = (
        df["event_name"].fillna("") + " " +
        df["category"].fillna("") + " " +
        df["volunteer_roles"].fillna("") + " " +
        df["audience"].fillna("") + " " +
        df["host"].fillna("")
    )
    return df


def load_event_calendar() -> pd.DataFrame:
    """Load IA West event calendar."""
    df = pd.read_csv(DATA_DIR / "event_calendar.csv")
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={
        "IA Event Date": "event_date",
        "Region": "region",
        "Nearby Universities": "nearby_universities",
        "Suggested Lecture Window": "lecture_window",
        "Course Alignment": "course_alignment",
    })
    df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce")
    return df


def load_cpp_courses() -> pd.DataFrame:
    """Load CPP course schedule."""
    df = pd.read_csv(DATA_DIR / "cpp_courses.csv")
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={
        "Instructor": "instructor",
        "Course": "course",
        "Section": "section",
        "Title": "title",
        "Days": "days",
        "Start Time": "start_time",
        "End Time": "end_time",
        "Enrl Cap": "enrollment_cap",
        "Mode": "mode",
        "Guest Lecture Fit": "guest_lecture_fit",
    })
    df["guest_lecture_fit"] = df["guest_lecture_fit"].fillna("Low")
    # Build description for matching
    df["description_blob"] = (
        df["title"].fillna("") + " " +
        df["course"].fillna("") + " " +
        df["guest_lecture_fit"].fillna("")
    )
    return df


def load_all():
    """Load all datasets and return as dict."""
    return {
        "speakers": load_speakers(),
        "cpp_events": load_cpp_events(),
        "event_calendar": load_event_calendar(),
        "cpp_courses": load_cpp_courses(),
    }
