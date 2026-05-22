# Prototype App Design Package

## Scope
This package supports the first two use cases from the uploaded executive summary:
1. AI-Powered Pre-Call Briefing Assistant
2. AI-Driven HCP Targeting and Next-Best-Action

The package contains **source-only synthetic data**. It does **not** include transformed, modeled, or pre-aggregated outputs.

## Product design principle
Build two apps on top of the same commercial data foundation:
- **Rep Copilot** for pre-call briefing
- **Targeting Copilot** for prioritization and next-best-action

Both apps should read from the same raw source tables and produce different outputs through separate pipelines.



---

# NEW CROSS-APPLICATION COMMERCIAL KPI

## Engagement → Conversion Rate (ConversionRate_30d)

### Business purpose
This KPI measures the real commercial effectiveness of field engagement activities by tracking how many HCP interactions result in a meaningful downstream conversion event within 30 days.

This metric should become a shared performance layer across:
- Rep Copilot
- Targeting Copilot
- Commercial leadership dashboards
- Coaching and field effectiveness workflows

---

## KPI Definition

### Metric Name
`ConversionRate_30d`

### Definition
Percentage of HCP engagements (calls) that result in a defined conversion within 30 days.

### Example conversion events
- Prescription increase
- New prescription start
- Sample request
- Follow-up meeting accepted
- Webinar registration
- Medical information request
- Access discussion initiated

### Formula
```text
ConversionRate_30d =
100 *
(Number of calls in period that had conversion within 30 days)
/
(Total calls in period)
```

---

## KPI Ownership

### Business owner
Commercial Analytics / Field Leadership

### Primary usage
- Program effectiveness measurement
- Rep coaching prioritization
- Message optimization
- Territory effectiveness tracking
- Therapy-area performance benchmarking
- Campaign effectiveness evaluation

---

## Target thresholds

| Metric | Example Baseline | Target |
|---|---|---|
| Calls → Conversion | 8–12% | +2% QoQ uplift |
| High-performing reps | >15% | Maintain/improve |
| Low-performing segments | <6% | Coaching intervention |

---

## Visualization and dashboard design

### A. KPI Cards

#### Primary KPI card
- Current 30-day conversion %
- Absolute change vs previous period
- Relative uplift %
- Trend indicator arrow
- QoQ uplift status

Example:
```text
Target: 12%
Achieved: 14%
Target uplift: +2% QoQ
```

---

### B. Conversion Trend Chart

#### Visualization
Dual-line time-series chart:
- Total HCP calls
- Calls resulting in conversion

#### Features
- Rolling 7-day smoothing
- Rolling 30-day smoothing
- Breakdown filters:
  - Rep
  - Territory
  - Therapy area
  - Brand
  - Account type
- Hover drill-down
- Threshold highlighting
- Trend projection line

#### Suggested analytics overlays
- Campaign launch markers
- Publication release markers
- Competitor event markers
- Market access event markers

#### AI Forecasting
- Time series forecast up to 10 data points using prophet

---

### C. Conversion Effectiveness Heatmap

#### Dimensions
- Rep vs therapy area
- Territory vs product
- Account type vs conversion

#### Purpose
Quickly identify:
- underperforming regions
- high-performing messaging clusters
- coaching opportunities
- strong therapy-response combinations

---

### D. Rep Coaching Dashboard

#### Metrics shown
- Calls made
- Conversion percentage
- Top-performing message themes
- Lowest-performing objections
- Best-performing HCP segments
- Rep ranking percentile

#### AI insights
Examples:
- “Cardiology conversions increased after efficacy-focused messaging.”
- “Rep adoption of publication-led conversations correlates with +3.1% conversion uplift.”
- “Low conversion in dermatology linked to reduced follow-up cadence.”


---

## 1) AI-Powered Pre-Call Briefing Assistant

### User goal
A rep opens an HCP record 10 minutes before a call and gets a compact but evidence-rich briefing.

### Core screens
**A. Rep Home**
- Today's prioritized calls
- Unfinished follow-ups
- High-risk accounts
- Recent market events affecting their territory

**B. HCP Snapshot**
- Specialty and affiliation
- Recent prescriptions by brand
- Recent calls and objections
- Publication activity
- Recent congress/event appearances
- Digital engagement trend
- Consent and contact preference

**C. Pre-Call Brief**
- 60-second summary
- 3 recommended discussion angles
- 2 likely objections with response suggestions
- 1 compliance-safe talking point
- recent evidence citations
- follow-up tasks

**D. Source Explorer**
- Raw claims
- Raw notes
- Raw publication abstracts
- Raw event notes
- Raw digital touchpoints

### Feature-level design
1. **HCP identity resolution**
   - Match rep-selected HCP to master data
   - Pull affiliated account, specialty, territory
   - Resolve missing IDs using name/facility fallback

2. **Recent activity timeline**
   - Last 90/180/365-day interactions
   - Latest publication/event mentions
   - Latest claims trend
   - Latest digital engagement

3. **Signal extraction**
   - Topic labels from raw notes
   - Claims trend acceleration
   - Publication relevance
   - Engagement intensity
   - Market event impacts

4. **Brief generation**
   - LLM summary constrained to approved sources only
   - Must cite the source record IDs used
   - Must avoid off-label recommendations
   - Must separate facts from suggestions

5. **Call coaching**
   - Suggested opening line
   - Suggested evidence point
   - Suggested objection handling
   - Suggested next step

6. **Compliance controls**
   - Approved label knowledge base only
   - No claims beyond source data
   - Audit trail of every generated sentence
   - PHI masking on the UI

### Data needed
- HCP master
- Account master
- Product master
- Claims source
- Field interactions source
- Publication source
- Event source
- Digital engagement source
- Market events source
- Conversion events source
- Rep master
- Rep quota source
- KOL master
- KOL relationship source

---

## 2) AI-Driven HCP Targeting and Next-Best-Action

### User goal
A manager wants to know who should be visited, why, and what action should be taken next.

### Core screens
**A. Territory Prioritization**
- Rank HCPs by opportunity score
- Filter by territory, specialty, brand, rep, and recency
- Explain the score drivers

**B. Account Heatmap**
- High-potential accounts
- Under-covered accounts
- Brand potential vs current penetration
- Event-driven urgency

**C. Next-Best-Action Panel**
- Visit now
- Send clinical update
- Route to MSL
- Hold due to consent/access issue
- Reassign to another rep

**D. Scenario Simulator**
- What if competitor event hits?
- What if we increase digital touchpoints?
- What if rep coverage changes?
- What if a new publication appears?

### Feature-level design
1. **Opportunity scoring**
   - historical prescribing trajectory
   - recent engagement
   - specialty fit
   - product growth stage
   - publication influence
   - event-triggered urgency
   - account access and consent constraints

2. **Rank explanation**
   - show top 5 score drivers
   - show suppressors
   - show source records behind each driver

3. **NBA recommendation engine**
   - if recent negative sentiment + high potential -> MSL follow-up
   - if new publication + high digital activity -> rep visit
   - if access issue -> route to access team
   - if stable high prescriber -> maintain cadence

4. **Territory balancing**
   - identify over-covered and under-covered accounts
   - align coverage to opportunity bands
   - flag travel inefficiency

5. **Feedback loop**
   - capture rep acceptance/rejection
   - capture reason codes
   - retrain model on outcomes
   - monitor drift

---

## Source-only data model

### Raw entity tables
- `hcp_master`
- `account_master`
- `product_master`
- `field_interactions_source`
- `prescription_claims_source`
- `publication_source`
- `event_source`
- `digital_engagement_source`
- `market_events_source`
- `conversion_events_source`
- `rep_master`
- `rep_quota_source`
- `kol_master`
- `kol_relationship_source`

### Why source-only matters
Keep raw inputs separate from derived tables so the prototype can prove:
- traceability
- auditability
- model reproducibility
- better compliance review
- easier refresh logic

---

## DSA / processing / ML / AI design

### A. Data engineering steps
1. Ingest source CSV/API feeds
2. Standardize IDs and dates
3. Validate required fields
4. Detect duplicates
5. Resolve HCP-account-product links
6. Mask sensitive fields
7. Write curated bronze tables
8. Build silver feature tables
9. Build gold app-serving views

### B. Algorithms and methods
**For briefing assistant**
- Retrieval-Augmented Generation over approved source records
- Text summarization with constrained prompting
- Topic classification for notes/publications/events
- Recency-weighted scoring
- Similarity matching for relevance filtering

**For targeting/NBA**
- Gradient boosted trees or logistic regression for response / uptake likelihood
- Learning-to-rank model for priority ordering
- Rules layer for compliance and access constraints
- SHAP or feature contribution logic for explainability
- Optional bandit framework later for cadence optimization

### C. Practical model stack
**Baseline**
- Logistic regression for opportunity propensity
- TF-IDF + cosine similarity for note/publication matching
- Rule-based NBA engine

**Better**
- XGBoost / LightGBM for ranking and propensity
- Sentence embeddings for note and publication relevance
- RAG with approved knowledge base for pre-call briefs
- Temporal feature engineering on claims and engagement

**Advanced**
- Learning-to-rank model for HCP prioritization
- Multi-armed bandit for action selection
- Drift monitoring on engagement and prescribing shifts

### D. Evaluation metrics
**Briefing assistant**
- Time saved per prep
- Brief relevance rating
- Source citation coverage
- Hallucination rate
- Compliance review pass rate

**Targeting/NBA**
- Precision@K
- Lift in accepted recommendations
- Incremental Rx / NRx
- Coverage efficiency
- Rep adoption rate
- Drift and stability metrics

---

## Synthetic data guidance
Use the source tables in this package as the only starting point.
Do **not** use any transformed app tables as input samples. All model-ready outputs should be derived at runtime.

### Good synthetic data properties
- realistic HCP/account/product mix
- mixed channels
- mixed consent statuses
- varying publication and digital intensity
- monthly claims across multiple brands
- market events that can change model priorities
- raw notes with enough text for NLP tests

---

## Build recommendation
Start with one shared source layer and then create two separate app modules:
- **Rep Copilot**
- **Targeting Copilot**

That keeps the prototype fast but still realistic.



---

## New source data required for forecasting and commercial trend analysis

To support the updated KPI and forecast-oriented use cases, the prototype now also includes:
- `rep_master`: static field-force profile and territory assignment data
- `rep_quota_source`: monthly rep targets and planning constraints
- `kol_master`: KOL profile data linked back to HCP master
- `kol_relationship_source`: KOL network graph edges for influence modeling
- `conversion_events_source`: downstream outcome events used for `ConversionRate_30d`

These tables remain source-only. The app should derive trend, forecast, and conversion logic at runtime.
