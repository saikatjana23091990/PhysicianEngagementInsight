# Commercial Analytics Platform — PRD

## Original Problem Statement
Build a production-quality, demo-ready, enterprise-scalable commercial analytics platform for pharmaceutical / life-sciences commercial operations.

## Architecture
- **Frontend**: React (CRA) + MUI + Recharts + react-force-graph-2d, Kiwi palette, SSE streaming chat, PDF download
- **Backend**: FastAPI with modular API / service / data / ai / ml layers
- **Data layer**: In-memory pandas DataStore (raw) + MongoDB (AI outputs, audit logs, vector chunks)
- **AI layer**: AWS Bedrock primary + Emergent LLM (Claude Sonnet 4.5) fallback; SSE streaming; Mongo-backed vector store (Atlas $vectorSearch compatible)
- **ML layer**: XGBoost opportunity propensity blended with rule-based scoring; Holt-Winters forecast with robust IQR-based confidence bands

## User Personas
- **Executive**: KPI overview, AI narratives, KOL summary, territory & therapy benchmarks, PDF brief export
- **Manager**: Field force coaching, NBA targeting, conversion drill-downs, scenario simulator
- **Rep**: HCP directory, 360° HCP detail, pre-call briefing, opportunity panel

## Core Requirements
1. ConversionRate_30d engine with audit trail ✓
2. Pre-Call Briefing with source citation ✓
3. NBA / HCP targeting with explainable drivers + XGBoost propensity ✓
4. KOL analytics with co-author network ✓
5. Conversational analytics with Bedrock streaming + Emergent fallback ✓
6. Source explorer ✓
7. MongoDB persistence for AI outputs + audit logs ✓
8. MongoDB Atlas Vector Search-compatible RAG ✓
9. PDF export of executive brief ✓
10. Compliance guardrails on every AI output ✓

## Implemented
### Iteration 1 (2026-05-22)
- 12 frontend pages, all live and data-bound
- 14 backend routers, 30+ API endpoints
- ConversionRate_30d engine with explicit + derived attribution
- Opportunity scoring with 6 explainable drivers + rule-based NBA
- KOL dashboard, network graph, topic momentum
- Pre-call briefing service with full source assembly + RAG
- Conversational analytics with structured dossier + RAG context
- AWS Bedrock provider with bearer token + Emergent fallback
- Kiwi-themed UI (#028174 / #0AB68B / #92DE8B / #FFE3B3)

### Iteration 3 (2026-05-22)
- **Interactive Executive Dashboard filters** — Specialty / Territory / Region / Time window dropdowns; `/api/exec/dashboard` accepts query params and recomputes KPIs, trend, breakdowns, and top opportunities; reset icon + active-filter chip count
- **Dual-line forecast** — `/api/conversion/forecast` now forecasts both `total_calls` and `converted_calls` with Holt-Winters + confidence bands; convergence analysis (current gap, forecast min gap, direction = narrowing / widening / stable); new chart renders both lines with forecast region tint and reference line at min-gap week
- **SHAP in NBA drawer** — XGBoost `pred_contribs` exposes per-HCP feature contributions on `/api/nba/explain/{hcp_id}`; new SHAP card in the drawer with horizontal bar chart (teal=positive lift, red=negative drag), ML/Rule score chips, model AUC and log-odds shown

### Iteration 2 (2026-05-22)
- **Mongo persistence** for AI outputs (chat, briefing, narrative) + audit_logs collection with TTL indexes
- **Mongo-backed vector store** (Atlas $vectorSearch compatible) with 295 chunks at startup
- **Embeddings abstraction** — LocalSVD (default) + BedrockTitan (production)
- **XGBoost opportunity propensity** blended with rule scores (60/40), exposes `ml_propensity`, `rule_score`, `model_status`
- **Holt-Winters forecast** with IQR-robust confidence bands (replacing EWM)
- **Bedrock SSE streaming** for `/api/chat/ask_stream` with keep-alive heartbeats and Emergent chunked fallback
- **PDF export** — `/api/export/exec_brief_pdf` generates board-ready brief via reportlab (KPI cards, AI narrative, therapy/territory/rep breakdowns, top opportunities, compliance footer)
- **Audit endpoints** — `/api/audit/ai_outputs` (with preview), `/api/audit/logs`
- **Admin UI** — Recent AI Outputs panel with citations

## Validation
- Iteration 1: 35/35 backend tests passed
- Iteration 2: 53/53 backend tests passed (35 regression + 18 new)

## Backlog
- **P1**: Cognito auth replacing role switcher; full multi-tenant support
- **P2**: Rate limiting on LLM endpoints; 5-min narrative cache
- **P2**: Drift monitoring on opportunity model; SHAP plots in NBA drawer
- **P3**: Real Atlas Vector Search deployment guide with `$vectorSearch` index spec
- **P3**: Multi-armed bandit for action selection

## Next Tasks
- Frontend test pass (UI flows, role switcher, chart rendering, streaming chat UX, PDF download)
