# IA West Smart Match — Measurement Plan

## Overview

This measurement plan defines how we track the effectiveness of Smart Match across three dimensions: matching quality, engagement outcomes, and membership growth.

## Key Performance Indicators (KPIs)

### 1. Matching Quality Metrics

| Metric | Definition | Target | Measurement Method |
|--------|-----------|--------|-------------------|
| Match Acceptance Rate | % of recommended matches accepted by coordinators | >60% | Pipeline stage tracking (Outreach Sent → Engaged) |
| Match Score Accuracy | Correlation between predicted score and actual engagement quality | r > 0.5 | Post-event survey vs. predicted score |
| Top-3 Hit Rate | % of accepted matches that were in the system's top 3 recommendations | >70% | Compare accepted matches to ranking |
| False Positive Rate | % of high-score matches that result in poor engagement | <15% | Post-event feedback |

### 2. Engagement Metrics

| Metric | Definition | Target (Year 1) | Measurement Method |
|--------|-----------|-----------------|-------------------|
| Total Placements | Number of successful volunteer placements | 25+ | Pipeline: Event Completed stage |
| Guest Lectures Delivered | Number of in-class speaking engagements | 10+ | Event completion tracking |
| University Partners | Number of universities with active opportunities | 5+ | Discovery + Pipeline data |
| Outreach Response Rate | % of outreach emails that receive a response | >30% | Email tracking integration |
| Volunteer Utilization | % of board members with at least 1 placement | >50% | Pipeline speaker uniqueness |

### 3. Membership Pipeline Metrics

| Metric | Definition | Target (Year 1) | Measurement Method |
|--------|-----------|-----------------|-------------------|
| Pipeline Entries | Total contacts entered into membership pipeline | 50+ | Pipeline tracker |
| Conversion Rate | % of pipeline entries that become IA members | >5% | Pipeline: Member stage |
| Time to Conversion | Average days from first contact to membership | <120 days | Pipeline date tracking |
| Engagement Depth | Average number of touchpoints before conversion | 3-5 | Pipeline stage count per contact |

## Measurement Framework

### Data Collection Points

1. **Match Generation** (Automated)
   - Match scores, component breakdowns, speaker-opportunity pairs
   - Logged every time the matching engine runs

2. **Outreach Tracking** (Semi-automated)
   - Email sent date, response received, response sentiment
   - Tracked via pipeline stage transitions

3. **Event Participation** (Manual entry + confirmation)
   - Attendance confirmed, role performed, duration
   - Entered by event coordinator or volunteer

4. **Post-Event Feedback** (Survey)
   - Coordinator satisfaction (1-5 scale)
   - Volunteer satisfaction (1-5 scale)
   - Student impact rating (1-5 scale)
   - Would they engage again? (Y/N)

5. **Membership Tracking** (CRM integration)
   - New member applications attributed to Smart Match
   - Source attribution via pipeline tracking

### Reporting Cadence

| Report | Frequency | Audience | Content |
|--------|-----------|----------|---------|
| Weekly Dashboard | Weekly | IA West Board | Active pipeline, recent matches, outreach stats |
| Monthly Performance | Monthly | Metro Directors | Regional metrics, placement counts, trending opportunities |
| Quarterly Review | Quarterly | IA West Leadership | KPI progress, algorithm tuning recommendations, growth trajectory |
| Annual Impact Report | Annually | IA National + Sponsors | Year-over-year growth, membership impact, ROI analysis |

## Algorithm Tuning Process

The matching algorithm weights should be tuned based on measured outcomes:

1. **Baseline** (Current): Topic 0.30, Role 0.25, Geo 0.20, Calendar 0.10, Experience 0.05, Student Interest 0.10

   > **Note:** Student Interest Signal (enrollment trends, Google Trends) is planned for Phase 2 but not yet implemented in the prototype.
2. **After 25 placements:** Analyze which score components best predict successful placements
3. **Adjust weights** based on correlation analysis
4. **A/B test** adjusted weights on next batch of recommendations
5. **Quarterly review** of weight performance

## Success Criteria (Year 1)

The Smart Match pilot will be considered successful if:

- [ ] 25+ successful volunteer placements completed
- [ ] 5+ university partnerships established
- [ ] Match acceptance rate exceeds 60%
- [ ] At least 3 new IA members attributed to Smart Match pipeline
- [ ] Volunteer satisfaction averages 4.0+ out of 5.0
- [ ] System processes 200+ match recommendations without manual intervention
- [ ] At least 50% of board members have participated in at least one placement

## Data Privacy & Ethics

- All measurement data is aggregated for reporting; individual responses are confidential
- Volunteers can opt out of tracking at any time
- University partner data is used only for matching purposes
- See `responsible_ai.md` for full ethical guidelines
