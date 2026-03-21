---
name: streamlit-dashboard
description: "Use for ALL Streamlit tasks on the IA West Smart Match CRM: editing pages, fixing bugs, adding visualizations, improving design, optimizing performance. Triggers: streamlit, st., dashboard, app.py, chart, dataframe, plotly, tab, sidebar, layout, style, slow, cache, deploy."
user-invocable: true
argument-hint: "[beautify | optimize | debug | add-chart | help]"
---

# IA West Smart Match — Streamlit Dashboard Skill

This skill provides Streamlit best practices tailored to the IA West Smart Match CRM dashboard. Based on the official [Streamlit Agent Skills](https://github.com/streamlit/agent-skills).

## Project Context

- **App**: `app.py` — single-file Streamlit dashboard with 6 tabs
- **Data**: CSV-backed via `src/data_loader.py` (speakers, CPP events, courses, IA event calendar)
- **Matching**: TF-IDF cosine similarity engine in `src/matching_engine.py`
- **Charts**: Plotly Express + Plotly Graph Objects (not Altair)
- **Deploy**: Streamlit Cloud (GitHub-connected, auto-deploys on push to `main`)
- **Python**: 3.14 on Streamlit Cloud — beware compatibility issues

## Known Gotchas

### pandas Styler is broken on Python 3.14
`df.style.background_gradient()` crashes with `_compute()` error on Streamlit Cloud (Python 3.14). **Never use pandas Styler with `st.dataframe()`**. Use `column_config` instead:

```python
# BAD — crashes on Python 3.14
st.dataframe(df.style.background_gradient(subset=["score"], cmap="YlGn"))

# GOOD — native Streamlit, works everywhere
st.dataframe(df, column_config={
    "score": st.column_config.ProgressColumn("Score", format="%.0f%%", min_value=0, max_value=1),
})
```

### Streamlit Cloud quirks
- Python version is controlled by Streamlit Cloud, not `runtime.txt` — currently 3.14
- `requirements.txt` must pin compatible versions for 3.14
- Large file uploads and heavy computation may timeout (30s default)
- Secrets go in Streamlit Cloud dashboard, not `.env` files

## Dashboard Layout Patterns

### KPI Rows
Use horizontal containers for responsive metric rows:

```python
with st.container(horizontal=True):
    st.metric("Revenue", "$1.2M", "-7%", border=True)
    st.metric("Users", "762k", "+12%", border=True)
    st.metric("Orders", "1.4k", "+5%", border=True)
```

### Cards with Borders
```python
with st.container(border=True):
    st.subheader("Sales Overview")
    st.line_chart(sales_data)
```

### Sidebar Filters
Put filters in sidebar to maximize dashboard space. This app already does this well.

## Data Display Best Practices

### column_config (preferred over Styler)
```python
st.dataframe(df, column_config={
    "revenue": st.column_config.NumberColumn("Revenue", format="$%.2f"),
    "completion": st.column_config.ProgressColumn("Progress", min_value=0, max_value=100),
    "url": st.column_config.LinkColumn("Website"),
    "created_at": st.column_config.DatetimeColumn("Created", format="MMM DD, YYYY"),
    "internal_id": None,  # Hide column
}, hide_index=True)
```

### Column types available
`NumberColumn`, `ProgressColumn`, `LinkColumn`, `ImageColumn`, `DatetimeColumn`, `DateColumn`, `TimeColumn`, `CheckboxColumn`, `SelectboxColumn`, `TextColumn`, `ListColumn`, `JSONColumn`, `LineChartColumn`, `BarChartColumn`, `AreaChartColumn`

### Pinned columns
```python
st.dataframe(df, column_config={
    "name": st.column_config.TextColumn(pinned=True),
})
```

## Performance

### Caching (already used in this app)
```python
@st.cache_data
def load_data():
    return load_all()

# With TTL for live data:
@st.cache_data(ttl="5m")
def get_metrics():
    return api.fetch()
```

### Cache anti-patterns
- Don't put widgets inside cached functions
- Cache the expensive part (data loading), filter separately
- Set `ttl` or `max_entries` for user-specific caches

### Fragments for partial reruns
```python
@st.fragment
def live_metrics():
    st.metric("Users", get_count())
    st.button("Refresh")
```

### Conditional rendering
Tabs always render all content. For expensive tabs, use `st.segmented_control` with conditional logic:
```python
view = st.segmented_control("View", ["Light", "Heavy"])
if view == "Heavy":
    expensive_chart()  # Only computed when selected
```

## Visual Design

### Icons over emojis
```python
st.markdown(":material/settings:")
st.markdown(":material/analytics:")
```
Find icons: https://fonts.google.com/icons

### Badges for status
```python
st.badge("Active", icon=":material/check:", color="green")
st.badge("Pending", icon=":material/schedule:", color="orange")
# Inline: :green-badge[Active] :orange-badge[Pending]
```

### Spacing
Remove heavy `st.divider()` calls — default spacing is usually enough. Use `st.space("small"|"medium"|"large")` when needed.

### Sentence casing
```python
st.title("Upload your data")     # GOOD
st.title("Upload Your Data")     # BAD — too shouty
```

### Captions over info boxes
```python
st.caption("Data last updated 5 minutes ago")  # Light
st.info("Important instructions here")          # Heavy — use sparingly
```

## Plotly Patterns (this app uses Plotly, not Altair)

### Consistent styling
```python
fig.update_layout(
    height=400,
    margin=dict(l=10, r=10, t=30, b=10),
    showlegend=False,
)
```

### Color maps used in this project
- Score gradients: `YlGn` (yellow-green)
- Categories: `Blues`
- Fit levels: `{"High": "#28a745", "Medium": "#ffc107", "Low": "#dc3545"}`
- Primary accent: `#007bff`

## Tab Structure (current app)

| Tab | Content |
|-----|---------|
| Speaker Profiles | Board member cards with expertise tags + region chart |
| Opportunities | CPP Events, Courses, IA Calendar (3 sub-tabs) |
| Smart Matches | Score distribution, top matches table, radar charts, heatmap |
| Outreach | Email generator with download buttons |
| Pipeline | Funnel chart, conversion rates, per-speaker/event/region metrics |
| Discovery | Opportunity finder, scraping templates, expansion roadmap |

## Deployment Checklist

1. Test locally: `streamlit run app.py`
2. Commit and push to `main`
3. Streamlit Cloud auto-deploys (watch for build errors in Manage App)
4. If deploy fails, check Python 3.14 compatibility in logs
