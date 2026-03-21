# IA West Smart Match CRM

AI-powered volunteer-to-opportunity matching system for the Insights Association West Chapter. Built for the CPP AI Hackathon 2026.

## What It Does

Smart Match solves the volunteer coordination problem for professional associations engaging with universities. Instead of relying on personal connections and spreadsheets, the system:

1. **Ingests** speaker profiles and university opportunity data
2. **Recommends** optimal volunteer-to-opportunity matches using a weighted scoring algorithm
3. **Generates** personalized outreach communications
4. **Tracks** the engagement-to-membership pipeline
5. **Discovers** new opportunities at universities across the West Coast

## Matching Algorithm

```
MATCH_SCORE = 0.30 × Topic Relevance      (TF-IDF cosine similarity)
            + 0.25 × Role Fit             (expertise-to-role alignment)
            + 0.20 × Geographic Proximity  (metro region clustering)
            + 0.15 × Calendar Fit          (IA event schedule overlap)
            + 0.10 × Historical Bonus      (past engagement record)
```

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

## Project Structure

```
ia-west-smart-match/
├── app.py                    # Streamlit dashboard (6 tabs)
├── src/
│   ├── data_loader.py        # CSV loading and normalization
│   ├── matching_engine.py    # TF-IDF + composite scoring algorithm
│   ├── outreach_generator.py # Email template generation
│   ├── discovery.py          # University opportunity discovery simulator
│   └── pipeline_tracker.py   # Engagement pipeline tracking
├── data/
│   ├── speaker_profiles.csv  # 17 IA West board members
│   ├── cpp_events.csv        # 15 CPP events and programs
│   ├── event_calendar.csv    # 9 IA West 2026 regional events
│   └── cpp_courses.csv       # 35 CPP marketing course sections
├── docs/
│   ├── growth_strategy.md    # Multi-phase expansion plan
│   ├── measurement_plan.md   # KPIs and tracking framework
│   └── responsible_ai.md     # Ethical AI guidelines
├── requirements.txt
└── README.md
```

## Dashboard Tabs

| Tab | Description |
|-----|-------------|
| **Speaker Profiles** | Browse IA West board members with expertise tags, regions, and top matches |
| **Opportunities** | Explore CPP events, course sections, and the IA regional event calendar |
| **Smart Matches** | View ranked recommendations with score breakdowns and radar charts |
| **Outreach** | Generate personalized email drafts for top matches |
| **Pipeline** | Track engagement funnel from identification to membership conversion |
| **Discovery** | Simulate automated opportunity discovery at new universities |

## Data Sources

- **Speaker profiles** — IA West board roster with expertise tags
- **CPP events** — Published event listings from Cal Poly Pomona departments and student orgs
- **Event calendar** — IA West 2026 regional event schedule with lecture window suggestions
- **Course schedule** — CPP marketing department course sections with guest lecture fit ratings

## Tech Stack

- **Python** — Core language
- **Streamlit** — Interactive dashboard
- **scikit-learn** — TF-IDF vectorization and cosine similarity
- **pandas** — Data manipulation
- **Plotly** — Interactive charts and visualizations

## Deliverables

- [Growth Strategy](docs/growth_strategy.md) — Multi-phase expansion from CPP to 20+ universities
- [Measurement Plan](docs/measurement_plan.md) — KPIs, tracking framework, and success criteria
- [Responsible AI Note](docs/responsible_ai.md) — Ethical guidelines, bias mitigation, transparency commitments

## Team

Built by Anderson Edmond for the CPP AI Hackathon 2026 — IA West Smart Match Challenge.
