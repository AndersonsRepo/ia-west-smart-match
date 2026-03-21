# IA West Smart Match CRM — 5-Minute Demo Script

**Duration:** 5 minutes
**Presenter Setup:** Run `streamlit run app.py` before demo starts. Have the dashboard loaded with the Smart Matches tab visible.

---

## Opening (30 seconds)

> "IA West has 18 board members and hundreds of volunteer opportunities across universities. Right now, matching is manual — someone reads a spreadsheet, guesses who might fit, and sends a generic email. Smart Match replaces that with AI-powered matching that scores every speaker against every opportunity in seconds."

**Key stat to mention:** "We scored 900 speaker-opportunity pairs using TF-IDF cosine similarity and a 5-factor composite algorithm."

---

## Tab 1: Speaker Profiles (45 seconds)

**Navigate to:** Speaker Profiles tab

- Show the 18 board members with their expertise tags rendered as pills
- **Demo action:** Click on "Dr. Yufan Lin" — highlight that his top 3 matches appear automatically
- **Demo action:** Use the region filter to show only "Los Angeles" members — point out the geographic clustering
- Scroll to the region distribution chart

> "Every board member has structured expertise tags that the AI uses for matching. Dr. Yufan Lin specializes in econometrics and generative AI — watch how the algorithm connects him to the right opportunities."

**Judging criteria hit:** Feasibility (real data, works today), Adoption (simple for coordinators)

---

## Tab 2: Opportunities (30 seconds)

**Navigate to:** Opportunities tab

- Quickly show the 3 sub-tabs: CPP Events (15 real events), CPP Courses (35 sections), IA Calendar (9 regional events)
- **Demo action:** In CPP Courses, filter to "High" fit only — show the instructor names and scheduling details
- Briefly show the IA Event Timeline chart

> "We loaded real data from Cal Poly Pomona — 15 events from their hackathon to career center programs, 35 course sections with guest lecture fit ratings, and the full IA West 2026 regional calendar."

**Judging criteria hit:** Impact (addresses a real operational pain point)

---

## Tab 3: Smart Matches (90 seconds) — THE CORE DEMO

**Navigate to:** Smart Matches tab

### Show the Algorithm (15 seconds)
- Point to the formula in the sidebar: `SCORE = 0.35 * Topic + 0.25 * Role + 0.20 * Geo + 0.10 * Calendar + 0.10 * Experience`
- Mention: "Five weighted factors, computed with scikit-learn TF-IDF and cosine similarity"

### Score Distribution (15 seconds)
- Show the histogram — overlay of event vs. course scores
- Point out the bell curve shape: most matches are moderate, a few are exceptional

### Top Matches Table (20 seconds)
- Show the top 20 matches with the green gradient coloring
- **Demo action:** Point out "Rob Kaiser → College of Science Research Symposium (94%)" as the top match
- Note that LA speakers dominate the top because CPP events are in LA (geographic proximity = 1.0)

### Match Explanations (30 seconds)
- **Demo action:** Expand "Dr. Yufan Lin → AI for a Better Future Hackathon (72%)"
- Walk through the "Why this match?" explanation:
  - Topic Relevance: econometrics and generative AI align with the hackathon
  - Role Fit: Can serve as Judge (matched on analytics) and Guest Speaker (matched on AI)
  - Geographic Proximity: Same region (Los Angeles — East)
  - Calendar Fit: IA event in the LA area creates a natural travel window
- Show the radar chart visualization of the 5 score components

> "This isn't a black box. Every match comes with a full explanation — which tags drove the topic score, which volunteer roles the speaker qualifies for, and why the logistics work."

### Heatmap (10 seconds)
- Scroll to the Speaker-Opportunity Match Heatmap
- Point out the visual pattern: some speakers (Rob Kaiser, Dr. Yufan Lin) are bright green across many opportunities

**Judging criteria hit:** Innovation (TF-IDF + multi-factor scoring), Storytelling (visual explanations), Feasibility (deterministic, reproducible)

---

## Tab 4: Outreach (30 seconds)

**Navigate to:** Outreach tab

- **Demo action:** Select "Dr. Yufan Lin" as speaker, "event" as type
- Show the generated email — personalized with his title, company, expertise tags, and match score
- Point out the "Why this match works" bullet points pulled from the matching algorithm
- Show the download button

> "Once a match is approved, the system generates a personalized outreach email. No more copy-paste templates — every email references the specific expertise overlap and logistics."

**Judging criteria hit:** Adoption (ready-to-use output), Impact (saves hours of manual writing)

---

## Tab 5: Pipeline (45 seconds)

**Navigate to:** Pipeline tab

### Funnel Chart (15 seconds)
- Show the conversion funnel: Identified → Outreach → Engaged → Scheduled → Completed → Follow-Up → Lead → Member
- Point out the conversion rate KPI and the realistic 2-3% end-to-end conversion

### Conversion Rates (15 seconds)
- Show the stage-to-stage conversion rate chart with observed vs. benchmark lines
- "Our observed rates track close to industry benchmarks — 85% get outreach, 40% engage, but only 25% of follow-ups become membership leads"

### Breakdowns (15 seconds)
- **Demo action:** Click "By Region" sub-tab — show how LA dominates the pipeline
- **Demo action:** Click "By Event Type" — show which event categories convert best

> "This pipeline tracker shows the full member journey. IA West can see exactly where prospects drop off and which regions or event types produce the best conversions."

**Judging criteria hit:** Impact (data-driven membership growth), Feasibility (uses realistic conversion benchmarks)

---

## Tab 6: Discovery (45 seconds)

**Navigate to:** Discovery tab

### Discovered Opportunities (15 seconds)
- Show the 54 real opportunities found from CSV data across 25 universities
- Point out High-fit vs. Medium-fit breakdown

### Scraping Templates (15 seconds)
- **Demo action:** Expand "Cal Poly Pomona" template — show the real URLs and HTML selectors
- "Each university has a configured template. In production, these run automatically to discover new events."
- Show the queued scan targets

### Expansion Roadmap (15 seconds)
- Show the 5 phases from SoCal to Pacific Northwest
- "Phase 1 is ready to deploy — UCLA, USC, SDSU. We already have scraping templates built."

> "This is the scaling path. Start with CPP, expand to every university in IA West's footprint. The scraping templates mean adding a new school takes minutes, not weeks."

**Judging criteria hit:** Innovation (automated discovery), Adoption (clear expansion path), Storytelling (phased roadmap)

---

## Close (15 seconds)

> "Smart Match turns IA West's volunteer matching from a manual spreadsheet exercise into an AI-powered CRM. 18 board members, 900 scored matches, personalized outreach, pipeline tracking, and automated university discovery — all in one dashboard. This is ready to deploy today and scale across IA West's entire regional footprint."

---

## Backup Q&A Talking Points

**"How does the matching algorithm work?"**
- TF-IDF vectorization of expertise tags and opportunity descriptions
- Cosine similarity for topic relevance, weighted with role fit, geography, calendar overlap, and experience
- Bigram features capture "generative AI", "focus groups" as single concepts
- Normalized scores ensure fair comparison across event types

**"What data did you use?"**
- Real CSV datasets: 18 IA West board members, 15 CPP events, 35 course sections, 9 regional events
- All speaker expertise tags and event descriptions come from actual IA West data

**"How would you deploy this?"**
- Streamlit Cloud for immediate hosting (free tier)
- Connect to IA West's existing CRM (Salesforce/HubSpot) via API
- Add Brightdata web scraping for automated university discovery
- OAuth integration for email outreach from the platform

**"What makes this different from just using a spreadsheet?"**
- Automated scoring eliminates guesswork — every match has a quantified reason
- Explanations build trust — coordinators understand WHY a match was recommended
- Pipeline tracking shows ROI — connect volunteer engagement to membership growth
- Discovery engine finds opportunities humans would miss

**"What about privacy and responsible AI?"**
- No personal data beyond publicly available board member profiles
- Algorithm is fully deterministic and explainable (no black-box LLM decisions)
- See `docs/responsible_ai.md` for our full responsible AI framework
