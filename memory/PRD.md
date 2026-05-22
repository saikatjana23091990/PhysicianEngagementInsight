# Commercial Analytics Platform — PRD

## Original Problem Statement
Build a production-quality, demo-ready, enterprise-scalable commercial analytics platform for pharmaceutical / life-sciences commercial operations.

## Architecture
- **Frontend**: React (CRA) + MUI + Recharts + react-force-graph-2d, Kiwi palette
- **Backend**: FastAPI with modular API / service / data / ai layers
- **Data layer**: In-memory pandas DataStore loading 14 source CSVs at startup; runtime feature engineering (no toy aggregates)
- **AI layer**: AWS Bedrock primary + Emergent LLM (Claude Sonnet 4.5) fallback; TF-IDF RAG over CRM notes / publications / events / market events
- **Storage**: MongoDB-ready (optional seed script); current demo uses in-memory layer

## User Personas
- **Executive**: KPI overview, AI narratives, KOL summary, territory & therapy benchmarks
- **Manager**: Field force coaching, NBA targeting, conversion drill-downs, scenario simulator
- **Rep**: HCP directory, 360° HCP detail, pre-call briefing, opportunity panel

## Core Requirements (static)
1. ConversionRate_30d engine with audit trail
2. Pre-Call Briefing with source citation
3. NBA / HCP targeting with explainable drivers
4. KOL analytics with co-author network
5. Conversational analytics (Ask Data) backed by Bedrock/Emergent
6. Source explorer over raw layer
7. AWS Bedrock integration with graceful Emergent fallback
8. Compliance guardrails on every AI output

## Implemented (Jan 2026 / 2026-05-22)
- 12 frontend pages, all live and data-bound
- 12 backend routers, ~30 API endpoints
- ConversionRate_30d engine with explicit + derived attribution
- Opportunity scoring with 6 explainable drivers + rule-based NBA
- KOL dashboard, network graph, topic momentum
- Pre-call briefing service with full source assembly + RAG
- Conversational analytics service with structured dossier + RAG context
- AWS Bedrock provider with bearer token + Emergent fallback
- Kiwi-themed UI (palette: #028174 / #0AB68B / #92DE8B / #FFE3B3)
- README, AWS deployment guide, Dockerfile, Mongo seed script

## Prioritized Backlog
- **P1**: MongoDB persistence for AI outputs and audit logs
- **P1**: Atlas Vector Search swap-in for RAG (currently TF-IDF)
- **P1**: Streaming responses for chat (Bedrock supports it)
- **P2**: XGBoost opportunity propensity (currently logistic-style weighted)
- **P2**: Prophet/SARIMA forecast (currently EWM exponential smoothing)
- **P2**: Auth (Cognito) replacing role switcher
- **P3**: SHAP plots in NBA drawer

## Next Tasks
- Validate end-to-end via testing subagent
- Tighten any rough edges from test report
- Consider lightweight Bedrock streaming endpoint
