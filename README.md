# Commercial Analytics Platform — Kiwi

> Production-quality enterprise prototype for pharmaceutical commercial analytics with AI-powered briefings, HCP targeting, conversion intelligence, KOL analytics, and AWS Bedrock conversational analytics.

![Stack](https://img.shields.io/badge/stack-FastAPI%20%2B%20React%20%2B%20MUI%20%2B%20MongoDB%20%2B%20Bedrock-028174)

## ✨ What's inside

| Module | Description |
|---|---|
| **Executive Dashboard** | KPI cards · weekly trend · therapy/territory/rep breakdowns · AI-generated executive narrative |
| **Pre-Call Briefing** | RAG over CRM notes, claims, publications, events; source-cited markdown briefs; compliance audit |
| **NBA / HCP Targeting** | Opportunity scoring with explainable drivers · rule-based recommendations · scenario simulator |
| **Conversion Analytics** | Real `ConversionRate_30d` engine with attribution audit, heatmap, 8-week forecast |
| **KOL Analytics** | Influence dashboard · co-author network graph · topic momentum |
| **Conversational Analytics** | Ask-data chat backed by AWS Bedrock or Emergent LLM with source-grounded answers |
| **Source Explorer** | Inspect the raw layer — all 14 source tables paginated/searchable |
| **Rep Dashboard / Territory / Settings** | Field effectiveness, territory benchmarking, platform configuration |

## 🏗 Architecture

```
                 ┌─────────────────────────────────────┐
                 │           React (MUI + Recharts)     │
                 └────────────────┬────────────────────┘
                                  │ /api
                 ┌────────────────▼────────────────────┐
                 │             FastAPI                  │
                 │                                      │
                 │  api ─► services ─► ml/ai ─► data    │
                 │           │                          │
                 │           └─► RAG (TF-IDF) + LLM     │
                 └─────────┬─────────────────┬──────────┘
                           │                 │
                ┌──────────▼─────┐    ┌──────▼────────────┐
                │  In-memory     │    │  AWS Bedrock      │
                │  DataStore     │    │  (Claude) +       │
                │  (pandas)      │    │  Emergent fallback│
                └──────────┬─────┘    └───────────────────┘
                           │
                ┌──────────▼──────────┐
                │   /app/data/raw     │
                │   14 source CSVs    │
                └─────────────────────┘
```

**Layers preserved (per the design):**
1. **Raw** — Source CSVs in `/app/data/raw/data/` (never mutated)
2. **Processed** — Date coercion, identity resolution, audit-trail-ready (`DataStore._post_process`)
3. **Feature** — Computed at runtime by `OpportunityEngine`, `ConversionEngine`, `KOLEngine`
4. **Serving** — FastAPI routers under `/api/*`

## 🚀 Local Quickstart

This repo is wired to run on Emergent's managed cluster (supervisor + Mongo). For local dev outside that environment:

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
cp .env.example .env  # or use the provided .env
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend

```bash
cd frontend
yarn install
yarn start  # serves on :3000
```

Set `REACT_APP_BACKEND_URL=http://localhost:8001` in `frontend/.env` for local dev.

### Data

The 14 source CSVs are auto-loaded from `DATA_DIR` (default `/app/data/raw/data`) on backend startup.
No seeding step needed — the DataStore lazy-builds processed/feature views on first request.

To seed into MongoDB instead (optional, for persistence/audit):
```bash
python scripts/seed_mongo.py
```

## 🔌 Configuration

`backend/.env`:

```ini
MONGO_URL=mongodb://localhost:27017
DB_NAME=commercial_analytics
CORS_ORIGINS=*

# LLM provider selection: emergent | bedrock
LLM_PROVIDER=emergent

# Emergent universal LLM key (Claude Sonnet 4.5)
EMERGENT_LLM_KEY=sk-emergent-...

# AWS Bedrock (short-term bearer token from console)
AWS_REGION=us-east-1
AWS_BEARER_TOKEN_BEDROCK=bedrock-api-key-<base64>
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
BEDROCK_EMBEDDING_MODEL=amazon.titan-embed-text-v2:0

DATA_DIR=/app/data/raw/data
```

Switch to Bedrock-primary by setting `LLM_PROVIDER=bedrock`.
The platform auto-falls back to whichever provider is configured if the primary fails.

## 🔎 API Surface (selected)

```
GET  /api/health
GET  /api/kpi/overview
GET  /api/exec/dashboard
POST /api/exec/narrative                       — AI executive narrative
GET  /api/conversion/{overview|trend|breakdown/{dim}|heatmap|forecast|audit/{id}}
GET  /api/hcp/list?q=&specialty=&territory=
GET  /api/hcp/{id}                             — 360° HCP detail
GET  /api/hcp/{id}/opportunity
POST /api/briefing/generate                    — AI pre-call brief
GET  /api/nba/ranked?specialty=&rep_id=
GET  /api/nba/simulate?hcp_id=&scenario=
GET  /api/kol/{dashboard|list|network|topics|{id}}
POST /api/chat/ask                             — Conversational analytics
GET  /api/sources/tables, /api/sources/table/{name}
GET  /api/rep/{list|leaderboard|{id}}
GET  /api/territory/{list|heatmap|{id}}
```

## 🧠 The ConversionRate_30d Engine

- **Definition:** % of HCP calls with a downstream conversion event within 30 days.
- **Attribution:**
  1. Use `conversion_events_source.linked_call_id` when present (explicit).
  2. Else, for each call, find the **nearest** conversion for the same HCP within the 30-day window.
  3. Track audit trail: explicit vs derived link, confidence, days-to-conversion.
- **Surface:** `/api/conversion/*` (overview, trend with rolling 7d/30d, breakdown, heatmap, forecast, audit per call).

## 🛡 AI Guardrails

Every AI response goes through `app/ai/guardrails.py`:
- Source citation required (`[INT00012]`, `[PUB0034]`, `[CONV00007]`)
- Off-label medical claims blocked
- Facts vs inferences separated
- All retrieved sources logged in `compliance_audit` field of the response

## 📂 Repository Layout

```
/app
├── backend/
│   ├── server.py                  # FastAPI entry
│   ├── requirements.txt
│   └── app/
│       ├── api/                   # routers (health, kpi, hcp, rep, ...)
│       ├── services/              # business logic (conversion, opp, kol, briefing, ask_data)
│       ├── ai/                    # llm.py, rag.py, guardrails.py
│       ├── data/                  # store.py (in-memory pandas-backed)
│       └── ml/                    # (future) advanced models
├── frontend/
│   └── src/
│       ├── pages/                 # 12 pages
│       ├── components/            # layout, kpi card, ...
│       ├── theme/kiwiTheme.js     # Kiwi palette (#028174, #0AB68B, #92DE8B, #FFE3B3)
│       └── services/api.js
├── data/raw/data/                 # 14 source CSVs
├── docs/
│   ├── design.md
│   ├── data_dictionary.csv
│   └── AWS_DEPLOYMENT.md
├── scripts/seed_mongo.py
└── README.md
```

## 🌩 AWS Deployment

See [docs/AWS_DEPLOYMENT.md](docs/AWS_DEPLOYMENT.md) for the full architecture, IAM, and CI/CD guide.

TL;DR:
- **Frontend** → S3 + CloudFront
- **Backend** → Lambda + Mangum OR ECS Fargate
- **DB** → MongoDB Atlas (or DynamoDB / RDS)
- **GenAI** → Bedrock (Claude + Titan)
- **Secrets** → Secrets Manager
- **CI/CD** → GitHub Actions

## 🧪 Demo Highlights

- 50 synthetic HCPs across 5 specialties · 18 reps · 12 accounts · 10 brands
- 200 field interactions, 769 claim rows, 34 conversion events
- 30 publications, 40 events, 25 market events, 80 digital touchpoints
- 18 KOLs with 41 co-author relationships
- **Real** ConversionRate_30d engine — no toy numbers
