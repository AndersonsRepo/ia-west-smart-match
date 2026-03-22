"""Features package for IA West Smart Match CRM."""

from features.match_approval import (
    init_match_state,
    log_action,
    get_decision_badge,
    render_match_actions,
    render_decision_summary,
)

from features.interactive_pipeline import (
    init_pipeline_state,
    get_pipeline_df,
    render_add_to_pipeline_form,
    render_pipeline_controls,
    add_to_pipeline_from_match,
)

from features.outreach_tracking import (
    init_outreach_state,
    render_outreach_actions,
    render_outreach_dashboard,
    auto_create_draft,
)

from features.discovery_sim import (
    init_discovery_state,
    render_discovery_scan_button,
    render_discovery_add_to_pipeline,
)

__all__ = [
    "init_match_state", "log_action", "get_decision_badge",
    "render_match_actions", "render_decision_summary",
    "init_pipeline_state", "get_pipeline_df",
    "render_add_to_pipeline_form", "render_pipeline_controls",
    "add_to_pipeline_from_match",
    "init_outreach_state", "render_outreach_actions",
    "render_outreach_dashboard", "auto_create_draft",
    "init_discovery_state", "render_discovery_scan_button",
    "render_discovery_add_to_pipeline",
]
