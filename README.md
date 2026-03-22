# IA West Smart Match CRM

AI-powered volunteer-to-opportunity matching system for the Insights Association West Chapter. Built for the CPP AI Hackathon 2026.

## What It Does

Smart Match solves the volunteer coordination problem for professional associations engaging with universities. Instead of relying on personal connections and spreadsheets, the system:

1. **Ingests** speaker profiles and university opportunity data
2. **Recommends** optimal volunteer-to-opportunity matches using a 6-factor weighted scoring algorithm
3. **Generates** personalized outreach communications
4. **Tracks** the engagement-to-membership pipeline (Match Found → New IA Member)
5. **Discovers** new opportunities via live web scraping of university event pages
6. **Analyzes** ROI projections, coverage gaps, and volunteer engagement at the executive level

## Matching Algorithm

The AI matching engine uses **TF-IDF cosine similarity** with bigram features (scikit-learn) to score topic relevance, combined with 5 additional deterministic factors:

```
MATCH_SCORE = 0.30 × Topic Relevance       (TF-IDF cosine similarity with bigrams)
            + 0.25 × Role Fit              (expertise-to-role keyword alignment)
            + 0.20 × Geographic Proximity   (metro region clustering + adjacency)
            + 0.10 × Calendar Fit           (IA regional event schedule overlap)
            + 0.05 × Experience Bonus       (seniority heuristic from expertise tags)
            + 0.10 × Student Interest       (enrollment capacity / audience signal)
```

Every match includes a full human-readable explanation with score breakdown and radar chart visualization — no black-box decisions.

## Setup

### Prerequisites
- Python 3.9+
- pip

### Install & Run

```bash
# Clone the repo
git clone https://github.com/AndersonsRepo/ia-west-smart-match.git
cd ia-west-smart-match

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run app.py
```

The app will open at `http://localhost:8501`.

### Optional: Supabase Persistence

The app works fully in **demo mode** with CSV data. To enable persistent CRM state (volunteer registration, match decisions, pipeline tracking):

1. Create a Supabase project and run `scripts/migration.sql`
2. Add credentials to `.streamlit/secrets.toml`:
   ```toml
   SUPABASE_URL = "https://your-project.supabase.co"
   SUPABASE_KEY = "your-anon-key"
   ```

## Project Structure

```
ia-west-smart-match/
├── app.py                        # Streamlit dashboard (7 tabs)
├── pages/
│   └── 1_Volunteer_Portal.py     # Self-service volunteer registration
├── src/
│   ├── data_loader.py            # CSV loading and normalization
│   ├── matching_engine.py        # TF-IDF + 6-factor composite scoring
│   ├── outreach_generator.py     # Personalized email generation
│   ├── discovery.py              # University opportunity discovery simulation
│   ├── university_scraper.py     # Live web scraping engine (requests + BeautifulSoup)
│   ├── pipeline_tracker.py       # 8-stage membership pipeline tracking
│   ├── executive_analytics.py    # ROI projections, coverage analysis, engagement scores
│   └── db.py                     # Supabase data access layer (CSV fallback)
├── features/
│   ├── match_approval.py         # Approve/shortlist/reject workflow
│   ├── interactive_pipeline.py   # Pipeline stage management UI
│   ├── outreach_tracking.py      # Outreach send/response tracking
│   └── discovery_sim.py          # Live scraping UI + discovery scan
├── data/
│   ├── speaker_profiles.csv      # 18 IA West board members
│   ├── cpp_events.csv            # 15 CPP events and programs
│   ├── event_calendar.csv        # 9 IA West 2026 regional events
│   └── cpp_courses.csv           # 35 CPP marketing course sections
├── docs/
│   ├── growth_strategy.md        # Multi-phase expansion plan
│   ├── measurement_plan.md       # KPIs and tracking framework
│   ├── responsible_ai.md         # Ethical AI guidelines
│   └── demo_script.md            # 5-minute demo walkthrough
├── scripts/
│   ├── migration.sql             # Supabase schema (7 tables)
│   └── seed_supabase.py          # CSV → Supabase import
├── requirements.txt
└── README.md
```

## Dashboard Tabs

| Tab | Description |
|-----|-------------|
| **Speaker Profiles** | Browse IA West board members with expertise tags, regions, and top matches |
| **Opportunities** | Explore CPP events, course sections, and the IA regional event calendar |
| **Smart Matches** | Ranked recommendations with score breakdowns, radar charts, annotated heatmap, and approve/shortlist/reject workflow |
| **Outreach** | Generate personalized email drafts with outreach tracking |
| **Pipeline** | 8-stage membership funnel (Match Found → New IA Member) with bottleneck analysis and KPIs |
| **Discovery** | Live web scraping of university event pages + expansion roadmap |
| **Executive Analytics** | ROI projections, coverage analysis, volunteer engagement scores, and strategic insights |

## Data Sources

- **Speaker profiles** — 18 IA West board members with expertise tags, metro regions, and company affiliations
- **CPP events** — 15 published event listings from Cal Poly Pomona departments and student orgs
- **Event calendar** — 9 IA West 2026 regional events across the West Coast with lecture window suggestions
- **Course schedule** — 35 CPP marketing department course sections with guest lecture fit ratings

## Tech Stack

- **Python** — Core language
- **Streamlit** — Interactive dashboard + Streamlit Cloud deployment
- **scikit-learn** — TF-IDF vectorization and cosine similarity
- **pandas / NumPy** — Data manipulation
- **Plotly** — Interactive charts, annotated heatmaps, funnels, and radar charts
- **requests + BeautifulSoup** — Live university event page scraping
- **Supabase** — Optional PostgreSQL persistence for CRM state

## Deliverables

- [Growth Strategy](docs/growth_strategy.md) — Multi-phase expansion from CPP to 20+ universities
- [Measurement Plan](docs/measurement_plan.md) — KPIs, tracking framework, and success criteria
- [Responsible AI Note](docs/responsible_ai.md) — Ethical guidelines, bias mitigation, transparency commitments

## Team

Built by Anderson Edmond for the CPP AI Hackathon 2026 — IA West Smart Match Challenge.
