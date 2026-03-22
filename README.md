# IA West Smart Match CRM

**AI-powered volunteer-to-opportunity matching for the Insights Association West Chapter.**

Built for the CPP AI Hackathon 2026 — IA West Smart Match Challenge ($2K prize).

> *18 board members. 50 opportunities. 900 scored matches. Zero spreadsheets.*

---

## The Problem

IA West has 18+ board member volunteers and hundreds of university engagement opportunities across the West Coast. Today, matching is manual — someone reads a spreadsheet, guesses who might fit, and sends a generic email. Opportunities are missed, volunteers are underutilized, and membership growth stalls.

## The Solution

Smart Match is an AI-powered CRM that:

1. **Scores** every volunteer against every opportunity using a 6-factor weighted algorithm (TF-IDF + cosine similarity)
2. **Explains** every recommendation with human-readable breakdowns and radar charts
3. **Generates** personalized outreach emails with contact lookup and one-click send
4. **Tracks** the full journey from match → outreach → event → membership conversion
5. **Discovers** new opportunities via live web scraping of university event pages
6. **Projects** ROI with 3-year membership revenue and labor savings forecasts
7. **Lets you tune** the algorithm in real time with an interactive weight slider

## Matching Algorithm

```
MATCH_SCORE = 0.30 × Topic Relevance       (TF-IDF cosine similarity with bigrams)
            + 0.25 × Role Fit              (expertise-to-role keyword taxonomy)
            + 0.20 × Geographic Proximity   (metro region clustering + adjacency)
            + 0.10 × Calendar Fit           (IA regional event schedule overlap)
            + 0.10 × Student Interest       (enrollment capacity / audience signal)
            + 0.05 × Experience Bonus       (seniority heuristic from title parsing)
```

**Key properties:**
- Fully deterministic — no LLM in the scoring loop; reproducible results
- Explainable — every score includes a component breakdown
- Configurable — interactive weight tuner lets stakeholders adjust priorities in real time

## Quick Start

```bash
git clone https://github.com/AndersonsRepo/ia-west-smart-match.git
cd ia-west-smart-match
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`. Works immediately in **demo mode** with bundled CSV data — no API keys or database setup required.

### Optional: Supabase Persistence

For persistent CRM state (volunteer registration, match decisions, pipeline tracking):

1. Create a Supabase project
2. Run `supabase/migrations/20260322000000_initial_schema.sql` and `supabase/migrations/20260322010000_outreach_enhancements.sql`
3. Add credentials to `.streamlit/secrets.toml`:
   ```toml
   SUPABASE_URL = "https://your-project.supabase.co"
   SUPABASE_KEY = "your-anon-key"
   ```

## Dashboard Tabs

| Tab | What It Does |
|-----|-------------|
| **Volunteers** | Browse 18 IA West board members with expertise tag pills, region filters, and top-3 match previews |
| **Opportunities** | Explore 15 CPP events, 35 course sections, and the full IA 2026 regional calendar with timeline chart |
| **Smart Matches** | Ranked recommendations with score distribution, radar charts, annotated heatmap, approve/reject workflow, volunteer comparison tool, weight tuner, and CSV export |
| **Outreach** | Command center with contact finder, personalized email generation, mailto send, response monitoring, and outreach funnel KPIs |
| **Pipeline** | 8-stage membership funnel (Match Found → New IA Member) with bottleneck analysis, per-volunteer/region/event-type breakdowns, and stage management |
| **Discovery** | Live web scraping of university event pages, scraping templates for 6 universities, and a phased expansion roadmap |
| **Executive** | 3-year ROI projections, opportunity coverage analysis, volunteer engagement leaderboard, pipeline trends, and deterministic strategic insights |

**Bonus:** Volunteer Self-Service Portal (`/Volunteer_Portal`) for self-registration, profile updates, and personal match viewing.

## Key Features for Judges

| Feature | Why It Matters |
|---------|---------------|
| **Weight Tuner** | Drag 6 sliders to re-rank all 900 matches in real time — proves the algorithm is transparent and configurable |
| **Volunteer Comparison** | Side-by-side radar overlay for any two volunteers on any opportunity — makes the recommendation actionable |
| **Outreach Command Center** | Contact lookup → email generation → mailto send → response tracking — complete outreach workflow |
| **Bottleneck Analysis** | Shows exactly WHERE prospects drop off in the pipeline — color-coded by severity vs. benchmarks |
| **ROI Projections** | 3-year stacked bar chart: membership revenue + engagement value + labor savings, with transparent assumptions |
| **Architecture Diagram** | Expandable system flow showing Supply → Demand → Match Engine → Pipeline with tech detail cards |

## Project Structure

```
ia-west-smart-match/
├── app.py                          # Main dashboard (7 tabs, ~1900 lines)
├── pages/1_Volunteer_Portal.py     # Self-service volunteer registration
├── src/
│   ├── matching_engine.py          # TF-IDF + 6-factor composite scoring
│   ├── outreach_generator.py       # Email templates + mailto URL generation
│   ├── pipeline_tracker.py         # 8-stage funnel with conversion benchmarks
│   ├── executive_analytics.py      # ROI, coverage, engagement, insights
│   ├── university_scraper.py       # Live web scraping engine
│   ├── discovery.py                # Opportunity discovery simulation
│   ├── data_loader.py              # CSV loading and normalization
│   └── db.py                       # Supabase DAL with CSV fallback
├── features/
│   ├── match_approval.py           # Approve/shortlist/reject workflow
│   ├── interactive_pipeline.py     # Pipeline stage management UI
│   ├── outreach_tracking.py        # Contact finder + response monitor
│   └── discovery_sim.py            # Live scraping UI + scan button
├── data/                           # 4 CSV datasets (speakers, events, courses, calendar)
├── docs/                           # Growth strategy, measurement plan, responsible AI, demo script
├── supabase/migrations/            # PostgreSQL schema (2 migration files)
├── tests/test_matching.py          # 8 matching engine tests
└── requirements.txt
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Streamlit (wide layout, custom CSS, glassmorphism cards) |
| **Matching** | scikit-learn TF-IDF vectorizer + cosine similarity |
| **Visualization** | Plotly (radar, heatmap, funnel, histogram, timeline, bar, pie) |
| **Data** | pandas + NumPy |
| **Scraping** | requests + BeautifulSoup4 |
| **Persistence** | Supabase (PostgreSQL) with CSV fallback |
| **Deployment** | Streamlit Cloud / Codespaces (devcontainer included) |

## Data Sources

- **18 IA West board members** — names, roles, companies, metro regions, expertise tags (from IA West board roster)
- **15 CPP events** — hackathons, symposiums, career programs, and student org events
- **35 course sections** — CPP marketing department schedule with guest lecture fit ratings
- **9 regional events** — IA West 2026 calendar across LA, SF, Seattle, Portland, San Diego

## Deliverables

- [Growth Strategy](docs/growth_strategy.md) — 4-phase expansion from CPP pilot to national platform
- [Measurement Plan](docs/measurement_plan.md) — KPIs, tracking framework, and Year 1 success criteria
- [Responsible AI](docs/responsible_ai.md) — Ethical guidelines, bias mitigation, transparency commitments
- [Demo Script](docs/demo_script.md) — 5-minute walkthrough with talking points and Q&A prep

## Running Tests

```bash
python tests/test_matching.py
```

Verifies: all volunteers matched, known-good pairings (Dr. Lin → AI Hackathon), geographic scoring, score bounds, explanation structure, and deduplication.

---

Built by Anderson Edmond · CPP AI Hackathon 2026 · IA West Smart Match Challenge
