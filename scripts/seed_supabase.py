"""Seed Supabase tables from CSV files.

Usage:
    python scripts/seed_supabase.py

Requires SUPABASE_URL and SUPABASE_KEY environment variables.
"""

import os
import sys
import pandas as pd
from pathlib import Path
from supabase import create_client

DATA_DIR = Path(__file__).parent.parent / "data"

def get_client():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        print("Error: Set SUPABASE_URL and SUPABASE_KEY environment variables.")
        sys.exit(1)
    return create_client(url, key)


def seed_volunteers(client):
    """Seed volunteers from speaker_profiles.csv."""
    df = pd.read_csv(DATA_DIR / "speaker_profiles.csv")
    df.columns = [c.strip() for c in df.columns]

    rows = []
    for _, row in df.iterrows():
        rows.append({
            "name": row.get("Name", ""),
            "board_role": row.get("Board Role", ""),
            "metro_region": row.get("Metro Region", ""),
            "company": row.get("Company", ""),
            "title": row.get("Title", ""),
            "expertise_tags": row.get("Expertise Tags", ""),
            "source": "csv_import",
        })

    if rows:
        client.table("volunteers").upsert(rows, on_conflict="name").execute()
        print(f"  Seeded {len(rows)} volunteers")


def seed_events(client):
    """Seed events from cpp_events.csv."""
    df = pd.read_csv(DATA_DIR / "cpp_events.csv")
    df.columns = [c.strip() for c in df.columns]

    rows = []
    for _, row in df.iterrows():
        name = row.get("Event / Program", "")
        desc = " ".join(str(row.get(c, "")) for c in df.columns if pd.notna(row.get(c)))
        rows.append({
            "name": name,
            "opp_type": "event",
            "category": str(row.get("Category", "")),
            "host": str(row.get("Host / Unit", "")),
            "recurrence": str(row.get("Recurrence (typical)", "")),
            "volunteer_roles": str(row.get("Volunteer Roles (fit)", "")),
            "audience": str(row.get("Primary Audience", "")),
            "url": str(row.get("Public URL", "")),
            "contact_name": str(row.get("Point(s) of Contact (published)", "")),
            "contact_email": str(row.get("Contact Email / Phone (published)", "")),
            "description_blob": desc,
        })

    if rows:
        client.table("opportunities").upsert(rows, on_conflict="name,opp_type").execute()
        print(f"  Seeded {len(rows)} events")


def seed_courses(client):
    """Seed courses from cpp_courses.csv."""
    df = pd.read_csv(DATA_DIR / "cpp_courses.csv")
    df.columns = [c.strip() for c in df.columns]

    rows = []
    for _, row in df.iterrows():
        title = str(row.get("Title", ""))
        rows.append({
            "name": title,
            "opp_type": "course",
            "instructor": str(row.get("Instructor", "")),
            "course_code": str(row.get("Course", "")),
            "section": str(row.get("Section", "")),
            "days": str(row.get("Days", "")),
            "start_time": str(row.get("Start Time", "")),
            "end_time": str(row.get("End Time", "")),
            "enrollment_cap": int(row["Enrl Cap"]) if pd.notna(row.get("Enrl Cap")) else None,
            "mode": str(row.get("Mode", "")),
            "guest_lecture_fit": str(row.get("Guest Lecture Fit", "Low")),
            "description_blob": f"{title} {row.get('Course', '')} {row.get('Guest Lecture Fit', '')}",
        })

    if rows:
        client.table("opportunities").upsert(rows, on_conflict="name,opp_type").execute()
        print(f"  Seeded {len(rows)} courses")


def seed_calendar(client):
    """Seed event calendar from event_calendar.csv."""
    df = pd.read_csv(DATA_DIR / "event_calendar.csv")
    df.columns = [c.strip() for c in df.columns]

    rows = []
    for _, row in df.iterrows():
        date_str = str(row.get("IA Event Date", ""))
        rows.append({
            "event_date": date_str,
            "region": str(row.get("Region", "")),
            "nearby_universities": str(row.get("Nearby Universities", "")),
            "lecture_window": str(row.get("Suggested Lecture Window", "")),
            "course_alignment": str(row.get("Course Alignment", "")),
        })

    if rows:
        client.table("event_calendar").insert(rows).execute()
        print(f"  Seeded {len(rows)} calendar entries")


if __name__ == "__main__":
    print("Seeding Supabase from CSV files...")
    client = get_client()

    seed_volunteers(client)
    seed_events(client)
    seed_courses(client)
    seed_calendar(client)

    print("Done!")
