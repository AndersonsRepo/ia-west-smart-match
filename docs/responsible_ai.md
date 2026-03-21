# IA West Smart Match — Responsible AI Guidelines

## Purpose

This document outlines the ethical principles, safeguards, and transparency commitments governing the AI-powered matching system used in IA West Smart Match. Our goal is to ensure the system is fair, transparent, and beneficial to all stakeholders.

## Core Principles

### 1. Human-in-the-Loop Decision Making

Smart Match is a **recommendation system, not an autonomous decision maker**. Every critical action requires human approval:

- **Matching:** The system recommends matches; metro directors and coordinators approve them
- **Outreach:** Email drafts are generated as templates; humans review and personalize before sending
- **Pipeline management:** Stage transitions require manual confirmation of real-world events
- **Discovery:** New opportunities are flagged for review, not automatically pursued

The AI augments human judgment — it does not replace it.

### 2. Transparency & Explainability

Every recommendation includes a full explanation:

- **Score breakdown:** Users see exactly how the composite score was calculated (topic relevance, role fit, geographic proximity, calendar fit, historical bonus)
- **Component visibility:** Each sub-score is displayed with its weight and rationale
- **No black boxes:** The TF-IDF + cosine similarity approach is interpretable and auditable
- **Radar charts:** Visual breakdown of match quality across all dimensions

### 3. Fairness & Bias Mitigation

**Potential biases we monitor:**

| Bias Type | Risk | Mitigation |
|-----------|------|------------|
| Geographic bias | LA-based members get more matches due to proximity to CPP | Calendar fit score balances by rewarding regional event alignment |
| Expertise breadth bias | Members with more listed tags score higher | TF-IDF normalization ensures quality of match, not quantity of tags |
| Recency bias | New members with no history score lower | Historical bonus defaults to 0.5 (neutral) until real data exists |
| Gender/demographic bias | Algorithm could inadvertently favor demographic patterns | Matching is based solely on expertise, role, geography, and availability — no demographic features |
| Popularity bias | Well-known speakers could dominate recommendations | Per-speaker view ensures every member gets their top opportunities surfaced |

**What we do NOT use for matching:**
- Age, gender, race, ethnicity, or any protected characteristic
- Social media follower counts or popularity metrics
- Salary, company size, or revenue data
- Personal relationship history or subjective assessments

### 4. Data Privacy & Security

**Data we collect and use:**
- Professional profiles (name, title, company, expertise — from IA West board roster)
- University event and course data (from public university websites)
- Engagement history (volunteer participation records)
- Match scores and recommendations (system-generated)

**Data we do NOT collect:**
- Personal contact information beyond what's publicly available
- Browsing or usage analytics
- Private communications between volunteers and coordinators
- Financial or compensation data

**Data handling:**
- All data is stored locally — no cloud transmission of personal data
- University contact information comes exclusively from published, public sources
- Volunteers can request their profile be removed at any time
- Data retention follows IA West's existing privacy policy

### 5. Consent & Opt-Out

- Board members are informed about the matching system and its use of their professional profiles
- Any volunteer can opt out of the matching system at any time
- University coordinators are informed that outreach is facilitated by a recommendation system
- Opt-out requests are processed immediately with no data retention

### 6. Accountability

- **System owner:** IA West Board (collectively)
- **Algorithm oversight:** Dr. Yufan Lin (Director of New Professionals, CPP faculty)
- **Ethical review:** Amber Jawaid (Director of Inclusion & Diversity)
- **Technical maintenance:** Designated technical contact

### 7. Continuous Improvement

- Quarterly bias audits examining match distribution across demographics and regions
- Feedback loops from coordinators and volunteers to identify systematic issues
- Algorithm weight adjustments based on measured outcomes (see measurement_plan.md)
- Annual review of these guidelines with IA West board

## Limitations

Smart Match is an MVP prototype with known limitations:

1. **No real-time learning:** The current system uses static weights; adaptive ML is a future enhancement
2. **Limited historical data:** The historical bonus is a placeholder (0.5 for all members) until real engagement data accumulates
3. **CPP-focused:** Opportunity data is currently limited to Cal Poly Pomona; expansion planned in phases
4. **Template-based outreach:** Generated emails are templates, not LLM-generated content; this is intentional to maintain human control over communications
5. **Simulated discovery:** The opportunity discovery module uses mock data to demonstrate the concept; production would require web scraping with appropriate rate limits and terms of service compliance

## Commitment

We are committed to building AI that serves the IA West community equitably, transparently, and responsibly. This system exists to make volunteer coordination more efficient and effective — not to make decisions that should remain with people.

Questions or concerns about these guidelines should be directed to the IA West Board.
