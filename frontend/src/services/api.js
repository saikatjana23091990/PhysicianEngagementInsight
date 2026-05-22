import axios from "axios";

const API_URL = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const api = axios.create({
  baseURL: API_URL,
  timeout: 60000,
});

// Convenience wrappers
export const KPI = {
  overview: () => api.get("/kpi/overview").then((r) => r.data),
};

export const Conversion = {
  overview: (params) => api.get("/conversion/overview", { params }).then((r) => r.data),
  trend: (freq = "W") => api.get("/conversion/trend", { params: { freq } }).then((r) => r.data),
  breakdown: (dim) => api.get(`/conversion/breakdown/${dim}`).then((r) => r.data),
  heatmap: () => api.get("/conversion/heatmap").then((r) => r.data),
  audit: (id) => api.get(`/conversion/audit/${id}`).then((r) => r.data),
  forecast: (weeks = 8) => api.get("/conversion/forecast", { params: { weeks_ahead: weeks } }).then((r) => r.data),
};

export const HCPApi = {
  list: (params) => api.get("/hcp/list", { params }).then((r) => r.data),
  specialties: () => api.get("/hcp/specialties").then((r) => r.data),
  detail: (id) => api.get(`/hcp/${id}`).then((r) => r.data),
  opportunity: (id) => api.get(`/hcp/${id}/opportunity`).then((r) => r.data),
};

export const RepApi = {
  list: () => api.get("/rep/list").then((r) => r.data),
  leaderboard: () => api.get("/rep/leaderboard").then((r) => r.data),
  detail: (id) => api.get(`/rep/${id}`).then((r) => r.data),
};

export const Territory = {
  list: () => api.get("/territory/list").then((r) => r.data),
  heatmap: () => api.get("/territory/heatmap").then((r) => r.data),
  detail: (id) => api.get(`/territory/${id}`).then((r) => r.data),
};

export const KOL = {
  dashboard: () => api.get("/kol/dashboard").then((r) => r.data),
  list: (params) => api.get("/kol/list", { params }).then((r) => r.data),
  network: (kol_id) => api.get("/kol/network", { params: kol_id ? { kol_id } : {} }).then((r) => r.data),
  topics: () => api.get("/kol/topics").then((r) => r.data),
  detail: (id) => api.get(`/kol/${id}`).then((r) => r.data),
};

export const Briefing = {
  generate: (hcp_id) => api.post("/briefing/generate", { hcp_id }).then((r) => r.data),
  context: (hcp_id) => api.get(`/briefing/context/${hcp_id}`).then((r) => r.data),
};

export const NBA = {
  ranked: (params) => api.get("/nba/ranked", { params }).then((r) => r.data),
  explain: (hcp_id) => api.get(`/nba/explain/${hcp_id}`).then((r) => r.data),
  simulate: (hcp_id, scenario) => api.get("/nba/simulate", { params: { hcp_id, scenario } }).then((r) => r.data),
};

export const Sources = {
  tables: () => api.get("/sources/tables").then((r) => r.data),
  table: (name, params) => api.get(`/sources/table/${name}`, { params }).then((r) => r.data),
};

export const Chat = {
  ask: (question, history, session_id) =>
    api.post("/chat/ask", { question, history, session_id }).then((r) => r.data),
  suggested: () => api.get("/chat/suggested").then((r) => r.data),
};

export const ExecDash = {
  dashboard: () => api.get("/exec/dashboard").then((r) => r.data),
  narrative: () => api.post("/exec/narrative").then((r) => r.data),
};
