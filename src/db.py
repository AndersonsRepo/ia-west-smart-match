"""Supabase data access layer with CSV fallback.

When SUPABASE_URL and SUPABASE_KEY are configured (via st.secrets or env),
all reads/writes go to Supabase. Otherwise, falls back to CSV files +
session state for a fully functional demo mode.
"""

import os
import streamlit as st
import pandas as pd
from datetime import datetime


# ── Mode Detection ────────────────────────────────────────────────────

def is_supabase_mode() -> bool:
    """Check if Supabase credentials are configured."""
    try:
        secrets = st.secrets.get("connections", {}).get("supabase", {})
        url = secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL")
        key = secrets.get("SUPABASE_KEY") or os.environ.get("SUPABASE_KEY")
        return bool(url and key)
    except (FileNotFoundError, AttributeError):
        return False


def _get_client():
    """Return the Supabase client via st.connection (cached by Streamlit)."""
    return st.connection("supabase", type="SupabaseConnection")


# ── Volunteers ────────────────────────────────────────────────────────

def load_volunteers_db() -> pd.DataFrame:
    """Load volunteers from Supabase."""
    conn = _get_client()
    rows = conn.query("*", table="volunteers", ttl="60s").execute()
    df = pd.DataFrame(rows.data)
    if df.empty:
        return df
    # Match CSV loader output format
    df["expertise_list"] = df["expertise_tags"].fillna("").apply(
        lambda x: [t.strip() for t in x.split(",") if t.strip()]
    )
    return df[df.get("is_active", True) != False]


def register_volunteer(data: dict) -> bool:
    """Insert a new volunteer. Returns True on success."""
    if not is_supabase_mode():
        return False
    conn = _get_client()
    conn.table("volunteers").insert(data).execute()
    return True


def update_volunteer(email: str, data: dict) -> bool:
    """Update volunteer by email. Returns True on success."""
    if not is_supabase_mode():
        return False
    conn = _get_client()
    data["updated_at"] = datetime.now().isoformat()
    conn.table("volunteers").update(data).eq("email", email).execute()
    return True


def get_volunteer_by_email(email: str) -> dict | None:
    """Look up a volunteer by email."""
    if not is_supabase_mode():
        return None
    conn = _get_client()
    result = conn.table("volunteers").select("*").eq("email", email).execute()
    if result.data:
        return result.data[0]
    return None


# ── Opportunities ─────────────────────────────────────────────────────

def load_opportunities_db(opp_type: str = "event") -> pd.DataFrame:
    """Load opportunities from Supabase."""
    conn = _get_client()
    rows = conn.query("*", table="opportunities", ttl="60s").execute()
    df = pd.DataFrame(rows.data)
    if df.empty:
        return df
    df = df[df["opp_type"] == opp_type]
    # Match CSV loader format
    if opp_type == "event":
        df["role_list"] = df["volunteer_roles"].fillna("").apply(
            lambda x: [r.strip() for r in x.split(";") if r.strip()]
        )
    return df[df.get("is_active", True) != False]


# ── Match Decisions ───────────────────────────────────────────────────

def get_match_decisions_db() -> dict:
    """Load all match decisions as {volunteer|opportunity: decision}."""
    conn = _get_client()
    rows = conn.table("match_decisions").select("*").execute()
    return {
        f"{r['volunteer_name']}|{r['opportunity_name']}": r["decision"]
        for r in rows.data
    }


def set_match_decision_db(volunteer: str, opportunity: str, decision: str) -> None:
    """Upsert a match decision."""
    conn = _get_client()
    conn.table("match_decisions").upsert({
        "volunteer_name": volunteer,
        "opportunity_name": opportunity,
        "decision": decision,
        "decided_at": datetime.now().isoformat(),
    }, on_conflict="volunteer_name,opportunity_name").execute()


# ── Pipeline Entries ──────────────────────────────────────────────────

def get_pipeline_entries_db() -> list[dict]:
    """Load all pipeline entries as list of dicts."""
    conn = _get_client()
    rows = conn.table("pipeline_entries").select("*").order("last_updated", desc=True).execute()
    # Rename display_id -> id for compatibility with session state format
    entries = []
    for r in rows.data:
        entry = dict(r)
        entry["id"] = entry.pop("display_id", entry.get("id"))
        entries.append(entry)
    return entries


def add_pipeline_entry_db(entry: dict) -> None:
    """Insert a pipeline entry."""
    conn = _get_client()
    db_entry = {
        "display_id": entry["id"],
        "volunteer_name": entry.get("volunteer", ""),
        "opportunity_name": entry.get("opportunity", ""),
        "stage": entry.get("stage", "Match Found"),
        "stage_index": entry.get("stage_index", 0),
        "entry_date": entry.get("entry_date", datetime.now().strftime("%Y-%m-%d")),
        "last_updated": entry.get("last_updated", datetime.now().strftime("%Y-%m-%d")),
        "region": entry.get("region", ""),
        "event_type": entry.get("event_type", ""),
        "match_score": entry.get("match_score"),
        "notes": entry.get("notes", ""),
        "source": entry.get("source", "manual"),
    }
    conn.table("pipeline_entries").insert(db_entry).execute()


def update_pipeline_stage_db(display_id: str, new_stage: str, stage_index: int) -> None:
    """Update a pipeline entry's stage."""
    conn = _get_client()
    conn.table("pipeline_entries").update({
        "stage": new_stage,
        "stage_index": stage_index,
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
    }).eq("display_id", display_id).execute()


def seed_pipeline_db(entries: list[dict]) -> None:
    """Bulk insert pipeline entries (for initial seeding)."""
    conn = _get_client()
    db_entries = []
    for entry in entries:
        db_entries.append({
            "display_id": entry["id"],
            "volunteer_name": entry.get("volunteer", ""),
            "opportunity_name": entry.get("opportunity", ""),
            "stage": entry.get("stage", "Match Found"),
            "stage_index": entry.get("stage_index", 0),
            "entry_date": entry.get("entry_date", datetime.now().strftime("%Y-%m-%d")),
            "last_updated": entry.get("last_updated", datetime.now().strftime("%Y-%m-%d")),
            "region": entry.get("region", ""),
            "event_type": entry.get("event_type", ""),
            "notes": entry.get("notes", ""),
            "source": entry.get("source", "mock"),
        })
    if db_entries:
        conn.table("pipeline_entries").insert(db_entries).execute()


# ── Outreach ──────────────────────────────────────────────────────────

def get_outreach_entries_db() -> dict:
    """Load outreach entries as {volunteer|opportunity: {status, sent_date, notes}}."""
    conn = _get_client()
    rows = conn.table("outreach_entries").select("*").execute()
    return {
        f"{r['volunteer_name']}|{r['opportunity_name']}": {
            "status": r["status"],
            "sent_date": r.get("sent_date"),
            "notes": r.get("notes", ""),
        }
        for r in rows.data
    }


def upsert_outreach_db(volunteer: str, opportunity: str, status: str,
                        sent_date: str | None = None, notes: str = "") -> None:
    """Upsert an outreach entry."""
    conn = _get_client()
    data = {
        "volunteer_name": volunteer,
        "opportunity_name": opportunity,
        "status": status,
        "notes": notes,
    }
    if sent_date:
        data["sent_date"] = sent_date
    conn.table("outreach_entries").upsert(
        data, on_conflict="volunteer_name,opportunity_name"
    ).execute()


# ── Action Log ────────────────────────────────────────────────────────

def log_action_db(action: str, details: str, tab: str = "") -> None:
    """Insert an action log entry."""
    conn = _get_client()
    conn.table("action_log").insert({
        "action": action,
        "details": details,
        "tab": tab,
    }).execute()
