"""Interactive pipeline management for Tab 5.

Provides session-state-backed pipeline data with add, advance, and revert
capabilities — all driven through Streamlit widgets.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from src.pipeline_tracker import generate_mock_pipeline, PIPELINE_STAGES
from src.db import is_supabase_mode, get_pipeline_entries_db, add_pipeline_entry_db, update_pipeline_stage_db, seed_pipeline_db, log_action_db


# ── Helpers ──────────────────────────────────────────────────────────


def _log_action(action: str, details: str) -> None:
    """Append an entry to the session-state action log."""
    if "action_log" not in st.session_state:
        st.session_state.action_log = []
    st.session_state.action_log.append(
        {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "details": details,
        }
    )


def _next_pipeline_id(records: list[dict]) -> str:
    """Generate the next PL-### id."""
    max_id = 0
    for r in records:
        try:
            num = int(str(r.get("id", "PL-000")).split("-")[1])
            if num > max_id:
                max_id = num
        except (IndexError, ValueError):
            pass
    return f"PL-{max_id + 1:03d}"


# ── Public API ───────────────────────────────────────────────────────


def init_pipeline_state(
    speakers: pd.DataFrame, cpp_events: pd.DataFrame,
    all_matches: pd.DataFrame = None,
) -> None:
    """Initialise ``st.session_state.pipeline_data`` with mock data.

    Only runs once per session — subsequent calls are no-ops so the user's
    edits are preserved across reruns. In Supabase mode, loads from DB.
    """
    if "pipeline_data" not in st.session_state:
        if is_supabase_mode():
            try:
                entries = get_pipeline_entries_db()
                if entries:
                    st.session_state.pipeline_data = entries
                else:
                    # First run — seed Supabase with mock data
                    mock = generate_mock_pipeline(
                        speakers, cpp_events, all_matches=all_matches
                    ).to_dict("records")
                    st.session_state.pipeline_data = mock
                    try:
                        seed_pipeline_db(mock)
                    except Exception:
                        pass
            except Exception:
                st.session_state.pipeline_data = generate_mock_pipeline(
                    speakers, cpp_events, all_matches=all_matches
                ).to_dict("records")
        else:
            st.session_state.pipeline_data = generate_mock_pipeline(
                speakers, cpp_events, all_matches=all_matches
            ).to_dict("records")


def get_pipeline_df() -> pd.DataFrame:
    """Return the current pipeline as a DataFrame."""
    return pd.DataFrame(st.session_state.pipeline_data)


def render_add_to_pipeline_form(
    speakers: pd.DataFrame, cpp_events: pd.DataFrame
) -> None:
    """Render a form that lets the user add a new pipeline entry."""
    with st.form("add_pipeline_entry", clear_on_submit=True):
        st.subheader("Add Pipeline Entry")

        col1, col2 = st.columns(2)
        with col1:
            speaker = st.selectbox(
                "Volunteer",
                options=speakers["name"].tolist(),
                key="pipe_form_speaker",
            )
        with col2:
            opportunity = st.selectbox(
                "Opportunity",
                options=cpp_events["event_name"].tolist(),
                key="pipe_form_opportunity",
            )

        col3, col4 = st.columns(2)
        with col3:
            stage = st.selectbox(
                "Starting Stage",
                options=PIPELINE_STAGES,
                index=0,  # default "Identified"
                key="pipe_form_stage",
            )
        with col4:
            notes = st.text_input("Notes", key="pipe_form_notes")

        submitted = st.form_submit_button("Add to Pipeline", type="primary")

    if submitted:
        records: list[dict] = st.session_state.pipeline_data
        new_entry = {
            "id": _next_pipeline_id(records),
            "volunteer": speaker,
            "opportunity": opportunity,
            "stage": stage,
            "stage_index": PIPELINE_STAGES.index(stage),
            "entry_date": datetime.now().strftime("%Y-%m-%d"),
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "region": "",
            "event_type": "",
            "notes": notes or f"Manually added — {speaker} × {opportunity}",
        }
        records.append(new_entry)
        st.session_state.pipeline_data = records
        _log_action(
            "pipeline_add",
            f"Added {new_entry['id']}: {speaker} → {opportunity} at {stage}",
        )
        if is_supabase_mode():
            try:
                add_pipeline_entry_db(new_entry)
            except Exception:
                pass
        st.toast(f"Added {new_entry['id']} to pipeline", icon="✅")


def render_pipeline_controls(pipeline_df: pd.DataFrame) -> None:
    """Render an interactive, editable pipeline table.

    Uses ``st.data_editor`` with a ``SelectboxColumn`` for the stage field
    so users can change stages inline.  Advance / Revert buttons are shown
    below for batch-style operations.
    """
    if pipeline_df.empty:
        st.info("Pipeline is empty — add an entry above.")
        return

    st.subheader("Pipeline Manager")

    # ── Inline data editor ───────────────────────────────────────────
    display_cols = ["id", "volunteer", "opportunity", "stage", "notes", "last_updated"]
    available_cols = [c for c in display_cols if c in pipeline_df.columns]
    edit_df = pipeline_df[available_cols].copy()

    edited = st.data_editor(
        edit_df,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key="pipeline_editor",
        column_config={
            "id": st.column_config.TextColumn("ID", disabled=True, width="small"),
            "volunteer": st.column_config.TextColumn("Volunteer", disabled=True),
            "opportunity": st.column_config.TextColumn("Opportunity", disabled=True),
            "stage": st.column_config.SelectboxColumn(
                "Stage",
                options=PIPELINE_STAGES,
                required=True,
                width="medium",
            ),
            "notes": st.column_config.TextColumn("Notes"),
            "last_updated": st.column_config.TextColumn(
                "Last Updated", disabled=True, width="small"
            ),
        },
    )

    # Detect stage changes made via data_editor
    _sync_editor_changes(pipeline_df, edited)

    # ── Advance / Revert buttons ─────────────────────────────────────
    st.markdown("---")
    st.caption("Bulk stage operations")

    col_sel, col_adv, col_rev = st.columns([3, 1, 1])
    with col_sel:
        entry_options = [
            f"{r['id']} — {r['volunteer']} → {r['opportunity']}"
            for r in st.session_state.pipeline_data
        ]
        selected_label = st.selectbox(
            "Select entry",
            options=entry_options,
            key="pipe_bulk_select",
        )

    if selected_label:
        selected_id = selected_label.split(" — ")[0]
        idx = _find_record_index(selected_id)

        if idx is not None:
            record = st.session_state.pipeline_data[idx]
            current_stage_idx = PIPELINE_STAGES.index(record["stage"])

            with col_adv:
                can_advance = current_stage_idx < len(PIPELINE_STAGES) - 1
                if st.button(
                    "⏩ Advance",
                    disabled=not can_advance,
                    key="pipe_advance",
                    use_container_width=True,
                ):
                    new_stage = PIPELINE_STAGES[current_stage_idx + 1]
                    _update_stage(idx, new_stage)
                    _log_action(
                        "pipeline_advance",
                        f"{record['id']}: {record['stage']} → {new_stage}",
                    )
                    st.toast(
                        f"Advanced {record['id']} to {new_stage}", icon="⏩"
                    )
                    st.rerun()

            with col_rev:
                can_revert = current_stage_idx > 0
                if st.button(
                    "⏪ Revert",
                    disabled=not can_revert,
                    key="pipe_revert",
                    use_container_width=True,
                ):
                    new_stage = PIPELINE_STAGES[current_stage_idx - 1]
                    _update_stage(idx, new_stage)
                    _log_action(
                        "pipeline_revert",
                        f"{record['id']}: {record['stage']} → {new_stage}",
                    )
                    st.toast(
                        f"Reverted {record['id']} to {new_stage}", icon="⏪"
                    )
                    st.rerun()


def add_to_pipeline_from_match(speaker: str, opportunity: str) -> bool:
    """Programmatically add an entry at the *Identified* stage.

    Returns ``True`` on success, ``False`` if a duplicate already exists.
    """
    if "pipeline_data" not in st.session_state:
        st.session_state.pipeline_data = []

    records: list[dict] = st.session_state.pipeline_data

    # Duplicate check
    for r in records:
        if r["volunteer"] == speaker and r["opportunity"] == opportunity:
            return False

    new_entry = {
        "id": _next_pipeline_id(records),
        "volunteer": speaker,
        "opportunity": opportunity,
        "stage": "Identified",
        "stage_index": 0,
        "entry_date": datetime.now().strftime("%Y-%m-%d"),
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "region": "",
        "event_type": "",
        "notes": f"Added from match — {speaker} × {opportunity}",
    }
    records.append(new_entry)
    st.session_state.pipeline_data = records
    _log_action(
        "pipeline_add_from_match",
        f"Added {new_entry['id']}: {speaker} → {opportunity}",
    )
    if is_supabase_mode():
        try:
            add_pipeline_entry_db(new_entry)
        except Exception:
            pass
    return True


# ── Internal helpers ─────────────────────────────────────────────────


def _find_record_index(record_id: str) -> int | None:
    """Return the list index of the record with the given id."""
    for i, r in enumerate(st.session_state.pipeline_data):
        if r["id"] == record_id:
            return i
    return None


def _update_stage(idx: int, new_stage: str) -> None:
    """Update a record's stage (and derived fields) in place."""
    st.session_state.pipeline_data[idx]["stage"] = new_stage
    stage_index = PIPELINE_STAGES.index(new_stage)
    st.session_state.pipeline_data[idx]["stage_index"] = stage_index
    st.session_state.pipeline_data[idx]["last_updated"] = datetime.now().strftime(
        "%Y-%m-%d"
    )
    if is_supabase_mode():
        try:
            display_id = st.session_state.pipeline_data[idx].get("id", "")
            update_pipeline_stage_db(display_id, new_stage, stage_index)
        except Exception:
            pass


def _sync_editor_changes(
    original_df: pd.DataFrame, edited_df: pd.DataFrame
) -> None:
    """Detect stage changes made via the data_editor and persist them."""
    if "stage" not in edited_df.columns or "stage" not in original_df.columns:
        return

    for row_idx in range(min(len(original_df), len(edited_df))):
        old_stage = original_df.iloc[row_idx]["stage"]
        new_stage = edited_df.iloc[row_idx]["stage"]
        if old_stage != new_stage and new_stage in PIPELINE_STAGES:
            record_id = original_df.iloc[row_idx].get("id", "")
            list_idx = _find_record_index(record_id)
            if list_idx is not None:
                _update_stage(list_idx, new_stage)
                _log_action(
                    "pipeline_stage_edit",
                    f"{record_id}: {old_stage} → {new_stage} (inline edit)",
                )
