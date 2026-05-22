"""
Pharma Commercial Analytics Backend Tests
Tests all 12 routers + AI integrations (Emergent LLM provider)
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://commercial-ops-ai.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

SHORT = 30
LONG = 120  # for LLM calls (PDF w/ narrative can take ~40s)


@pytest.fixture(scope="session")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------------- Health ----------------
class TestHealth:
    def test_health(self, client):
        r = client.get(f"{API}/health", timeout=SHORT)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "row_counts" in data
        rc = data["row_counts"]
        # 14 expected source tables
        assert len(rc) >= 10, f"Expected ~14 source tables, got {len(rc)}: {list(rc.keys())}"
        # spot check important tables
        for t in ["hcp_master", "rep_master", "field_interactions_source"]:
            assert t in rc, f"missing {t} in row_counts"


# ---------------- KPI ----------------
class TestKPI:
    def test_kpi_overview(self, client):
        r = client.get(f"{API}/kpi/overview", timeout=SHORT)
        assert r.status_code == 200, r.text
        d = r.json()
        # Validate totals (allow some flexibility)
        for k in ["hcps", "reps", "interactions", "conversions"]:
            # try totals.k or top level
            assert k in d or ("totals" in d and k in d["totals"]), f"missing {k}"


# ---------------- Conversion ----------------
class TestConversion:
    def test_overview(self, client):
        r = client.get(f"{API}/conversion/overview", timeout=SHORT)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "conversion_rate" in d
        assert "target" in d
        # uplift may be 'uplift' or computed
        assert isinstance(d["conversion_rate"], (int, float))

    def test_trend(self, client):
        r = client.get(f"{API}/conversion/trend", params={"freq": "W"}, timeout=SHORT)
        assert r.status_code == 200, r.text
        d = r.json()
        arr = d if isinstance(d, list) else d.get("data") or d.get("trend") or d.get("points")
        assert isinstance(arr, list) and len(arr) > 0
        sample = arr[0]
        assert "bucket" in sample or "date" in sample or "period" in sample

    @pytest.mark.parametrize("dim", ["specialty_group", "territory", "rep_name"])
    def test_breakdown(self, client, dim):
        r = client.get(f"{API}/conversion/breakdown/{dim}", timeout=SHORT)
        assert r.status_code == 200, r.text
        d = r.json()
        arr = d if isinstance(d, list) else d.get("data") or d.get("breakdown")
        assert isinstance(arr, list) and len(arr) > 0

    def test_heatmap(self, client):
        r = client.get(f"{API}/conversion/heatmap", timeout=SHORT)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "rows" in d and "columns" in d and "matrix" in d

    def test_audit(self, client):
        r = client.get(f"{API}/conversion/audit/INT00117", timeout=SHORT)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "attribution_link" in d or "attribution" in d or "interaction_id" in d

    def test_forecast(self, client):
        r = client.get(f"{API}/conversion/forecast", params={"weeks_ahead": 8}, timeout=SHORT)
        assert r.status_code == 200, r.text
        d = r.json()
        arr = d if isinstance(d, list) else d.get("forecast") or d.get("data") or d.get("points")
        assert isinstance(arr, list)
        assert len(arr) == 8, f"expected 8 forecast points, got {len(arr)}"


# ---------------- HCP ----------------
class TestHCP:
    def test_list(self, client):
        r = client.get(f"{API}/hcp/list", timeout=SHORT)
        assert r.status_code == 200, r.text
        d = r.json()
        items = d.get("items") if isinstance(d, dict) else d
        assert items is not None and len(items) > 0

    def test_list_filter(self, client):
        r = client.get(f"{API}/hcp/list", params={"territory": "T01"}, timeout=SHORT)
        assert r.status_code == 200, r.text

    def test_detail(self, client):
        r = client.get(f"{API}/hcp/HCP0001", timeout=SHORT)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ["hcp", "account", "claims", "calls"]:
            assert k in d, f"missing {k} in HCP detail"

    def test_opportunity(self, client):
        r = client.get(f"{API}/hcp/HCP0001/opportunity", timeout=SHORT)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "score" in d or "opportunity_score" in d
        assert "drivers" in d or "recommendation" in d


# ---------------- Rep ----------------
class TestRep:
    def test_list(self, client):
        r = client.get(f"{API}/rep/list", timeout=SHORT)
        assert r.status_code == 200, r.text

    def test_detail(self, client):
        r = client.get(f"{API}/rep/REP001", timeout=SHORT)
        assert r.status_code == 200, r.text

    def test_leaderboard(self, client):
        r = client.get(f"{API}/rep/leaderboard", timeout=SHORT)
        assert r.status_code == 200, r.text


# ---------------- Territory ----------------
class TestTerritory:
    def test_list(self, client):
        r = client.get(f"{API}/territory/list", timeout=SHORT)
        assert r.status_code == 200, r.text

    def test_heatmap(self, client):
        r = client.get(f"{API}/territory/heatmap", timeout=SHORT)
        assert r.status_code == 200, r.text

    def test_detail(self, client):
        r = client.get(f"{API}/territory/T01", timeout=SHORT)
        assert r.status_code == 200, r.text


# ---------------- KOL ----------------
class TestKOL:
    def test_dashboard(self, client):
        r = client.get(f"{API}/kol/dashboard", timeout=SHORT)
        assert r.status_code == 200, r.text

    def test_list(self, client):
        r = client.get(f"{API}/kol/list", timeout=SHORT)
        assert r.status_code == 200, r.text

    def test_network(self, client):
        r = client.get(f"{API}/kol/network", timeout=SHORT)
        assert r.status_code == 200, r.text

    def test_topics(self, client):
        r = client.get(f"{API}/kol/topics", timeout=SHORT)
        assert r.status_code == 200, r.text

    def test_detail(self, client):
        r = client.get(f"{API}/kol/KOL0001", timeout=SHORT)
        assert r.status_code == 200, r.text


# ---------------- NBA ----------------
class TestNBA:
    def test_ranked(self, client):
        r = client.get(f"{API}/nba/ranked", timeout=SHORT)
        assert r.status_code == 200, r.text
        d = r.json()
        arr = d if isinstance(d, list) else d.get("items") or d.get("data")
        assert isinstance(arr, list) and len(arr) > 0

    def test_simulate(self, client):
        r = client.get(f"{API}/nba/simulate",
                       params={"hcp_id": "HCP0001", "scenario": "competitor_event"},
                       timeout=SHORT)
        assert r.status_code == 200, r.text


# ---------------- Briefing ----------------
class TestBriefing:
    def test_context(self, client):
        r = client.get(f"{API}/briefing/context/HCP0001", timeout=SHORT)
        assert r.status_code == 200, r.text

    def test_generate(self, client):
        r = client.post(f"{API}/briefing/generate",
                        json={"hcp_id": "HCP0001"}, timeout=LONG)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ["brief_markdown", "provider", "compliance_audit"]:
            assert k in d, f"missing {k}: keys={list(d.keys())}"
        assert len(d["brief_markdown"]) > 50


# ---------------- Sources ----------------
class TestSources:
    def test_tables(self, client):
        r = client.get(f"{API}/sources/tables", timeout=SHORT)
        assert r.status_code == 200, r.text

    def test_table_data(self, client):
        r = client.get(f"{API}/sources/table/hcp_master",
                       params={"page": 1, "page_size": 10}, timeout=SHORT)
        assert r.status_code == 200, r.text


# ---------------- Chat ----------------
class TestChat:
    def test_suggested(self, client):
        r = client.get(f"{API}/chat/suggested", timeout=SHORT)
        assert r.status_code == 200, r.text
        d = r.json()
        arr = d if isinstance(d, list) else d.get("questions") or d.get("suggested")
        assert isinstance(arr, list)
        assert len(arr) == 6, f"expected 6 suggested, got {len(arr)}"

    def test_ask(self, client):
        r = client.post(f"{API}/chat/ask",
                        json={"question": "Which therapy area has the highest conversion rate?"},
                        timeout=LONG)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "answer_markdown" in d or "answer" in d
        ans = d.get("answer_markdown") or d.get("answer")
        assert ans and len(ans) > 20


# ---------------- Exec Dashboard ----------------
class TestExec:
    def test_dashboard(self, client):
        r = client.get(f"{API}/exec/dashboard", timeout=SHORT)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ["conversion", "trend", "by_specialty", "by_territory",
                  "top_reps", "top_opportunities"]:
            assert k in d, f"missing {k} in exec/dashboard"

    def test_narrative(self, client):
        r = client.post(f"{API}/exec/narrative", json={}, timeout=LONG)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "narrative_markdown" in d or "narrative" in d



# =====================================================================
# Iteration 2: Mongo persistence, Vector RAG, XGBoost+HW, PDF, Streaming
# =====================================================================

# ---------------- Health (iteration 2 — rag_chunks expected) ----------------
class TestHealthV2:
    def test_health_has_14_tables_and_mongo(self, client):
        r = client.get(f"{API}/health", timeout=SHORT)
        assert r.status_code == 200, r.text
        d = r.json()
        rc = d.get("row_counts", {})
        assert len(rc) >= 14, f"expected >=14 source tables, got {len(rc)}"


# ---------------- Audit / Mongo persistence ----------------
class TestAudit:
    def test_audit_logs_endpoint(self, client):
        r = client.get(f"{API}/audit/logs", timeout=SHORT)
        assert r.status_code == 200, r.text
        d = r.json()
        # Either {items, total} or list — accept both
        if isinstance(d, dict):
            assert "items" in d
            assert isinstance(d["items"], list)
        else:
            assert isinstance(d, list)

    def test_audit_ai_outputs_chat_filter(self, client):
        r = client.get(f"{API}/audit/ai_outputs", params={"type": "chat"}, timeout=SHORT)
        assert r.status_code == 200, r.text
        d = r.json()
        items = d.get("items") if isinstance(d, dict) else d
        assert isinstance(items, list)
        # Every returned record should be of type chat (if any)
        for it in items:
            assert it.get("type") == "chat"


# ---------------- Vector RAG: /api/chat/ask returns audit_id + sources ----
class TestChatRAG:
    def test_ask_persists_audit_and_sources(self, client):
        payload = {"question": "Top conversion territories?"}
        r = client.post(f"{API}/chat/ask", json=payload, timeout=LONG)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("audit_id"), f"missing audit_id in response: keys={list(d.keys())}"
        # retrieved_sources should be present (may be named differently)
        sources = d.get("retrieved_sources") or d.get("sources") or d.get("citations")
        assert isinstance(sources, list), f"expected retrieved_sources array, got {type(sources)}"
        ans = d.get("answer_markdown") or d.get("answer")
        assert ans and len(ans) > 20

    def test_audit_chat_log_persisted(self, client):
        # Run AFTER test_ask_persists_audit_and_sources — should see at least 1
        r = client.get(f"{API}/audit/ai_outputs", params={"type": "chat"}, timeout=SHORT)
        assert r.status_code == 200, r.text
        d = r.json()
        items = d.get("items") if isinstance(d, dict) else d
        assert len(items) >= 1, "expected at least 1 chat log persisted in Mongo"
        first = items[0]
        # citations field present
        assert "citations" in first or "retrieved_sources" in first or "payload" in first
        # created_at present (could be at top-level or inside payload)
        assert "created_at" in first or "ts" in first or "timestamp" in first or \
            (isinstance(first.get("payload"), dict))


# ---------------- ML: XGBoost-blended NBA scores ----------------
class TestMLScoring:
    def test_ranked_blended_scores(self, client):
        r = client.get(f"{API}/nba/ranked", params={"limit": 5}, timeout=SHORT)
        assert r.status_code == 200, r.text
        d = r.json()
        arr = d if isinstance(d, list) else d.get("items") or d.get("data")
        assert isinstance(arr, list) and len(arr) > 0
        for item in arr[:5]:
            score = item.get("opportunity_score") or item.get("score")
            assert score is not None, f"missing opportunity_score in {item}"
            assert 0 <= float(score) <= 100, f"score {score} out of [0,100]"
            conf = item.get("score_confidence") or item.get("confidence")
            if conf is not None:
                assert 0 <= float(conf) <= 1, f"confidence {conf} out of [0,1]"


# ---------------- Forecasting: Holt-Winters ----------------
class TestForecast:
    def test_forecast_holt_winters(self, client):
        r = client.get(f"{API}/conversion/forecast", params={"weeks_ahead": 8}, timeout=SHORT)
        assert r.status_code == 200, r.text
        d = r.json()
        arr = d if isinstance(d, list) else d.get("forecast") or d.get("data")
        assert isinstance(arr, list) and len(arr) == 8
        non_zero = 0
        for pt in arr:
            assert "forecast_rate" in pt
            assert "confidence_low" in pt
            assert "confidence_high" in pt
            if float(pt["forecast_rate"]) > 0:
                non_zero += 1
            # CI invariant
            assert pt["confidence_low"] <= pt["forecast_rate"] <= pt["confidence_high"] + 1e-6
        assert non_zero >= 6, f"expected most forecast rates non-zero, got {non_zero}/8"


# ---------------- PDF Export ----------------
class TestPDFExport:
    def test_pdf_no_narrative(self, client):
        r = client.post(f"{API}/export/exec_brief_pdf",
                        json={"include_narrative": False}, timeout=SHORT)
        assert r.status_code == 200, r.text[:200]
        ct = r.headers.get("content-type", "")
        assert "application/pdf" in ct, f"expected pdf, got {ct}"
        body = r.content
        assert body[:4] == b"%PDF", f"PDF magic missing: {body[:8]}"
        assert len(body) > 3 * 1024, f"PDF too small: {len(body)} bytes"

    def test_pdf_with_narrative(self, client):
        r = client.post(f"{API}/export/exec_brief_pdf",
                        json={"include_narrative": True}, timeout=LONG)
        assert r.status_code == 200, r.text[:200]
        ct = r.headers.get("content-type", "")
        assert "application/pdf" in ct
        body = r.content
        assert body[:4] == b"%PDF"
        assert len(body) > 4 * 1024, f"PDF w/ narrative too small: {len(body)} bytes"


# ---------------- Briefing: audit_id field ----------------
class TestBriefingV2:
    def test_briefing_returns_audit_id(self, client):
        r = client.post(f"{API}/briefing/generate",
                        json={"hcp_id": "HCP0001"}, timeout=LONG)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("audit_id"), f"missing audit_id in briefing response: keys={list(d.keys())}"
        assert d.get("brief_markdown") and len(d["brief_markdown"]) > 50


# ---------------- Exec narrative now persists ----------------
class TestExecNarrativePersist:
    def test_narrative_returns_audit_id(self, client):
        r = client.post(f"{API}/exec/narrative", json={}, timeout=LONG)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("audit_id"), f"missing audit_id in narrative response: keys={list(d.keys())}"

    def test_narrative_persisted_in_audit(self, client):
        r = client.get(f"{API}/audit/ai_outputs", params={"type": "narrative"}, timeout=SHORT)
        assert r.status_code == 200, r.text
        d = r.json()
        items = d.get("items") if isinstance(d, dict) else d
        assert isinstance(items, list)
        assert len(items) >= 1, "expected at least 1 narrative audit entry"


# ---------------- Streaming SSE ----------------
class TestStreaming:
    def test_chat_ask_stream(self, client):
        import requests as rq
        url = f"{API}/chat/ask_stream"
        with rq.post(url,
                     json={"question": "Which therapy has highest conversion?"},
                     stream=True, timeout=60) as r:
            assert r.status_code == 200, r.text[:200]
            ct = r.headers.get("content-type", "")
            assert "text/event-stream" in ct, f"expected SSE, got {ct}"
            saw_meta = False
            saw_delta = False
            buf = ""
            for raw in r.iter_lines(decode_unicode=True):
                if raw is None:
                    continue
                buf += (raw or "") + "\n"
                if "event: meta" in buf:
                    saw_meta = True
                if "event: delta" in buf:
                    saw_delta = True
                if saw_meta and saw_delta:
                    break
            assert saw_meta, f"no 'event: meta' in stream. buf head:\n{buf[:400]}"
            assert saw_delta, f"no 'event: delta' in stream. buf head:\n{buf[:400]}"


# ---------------- Top-level regression ----------------
class TestTopLevelRegression:
    @pytest.mark.parametrize("path", [
        "/kpi/overview",
        "/exec/dashboard",
        "/kol/dashboard",
        "/hcp/HCP0001",
        "/territory/T01",
    ])
    def test_endpoint_200(self, client, path):
        r = client.get(f"{API}{path}", timeout=SHORT)
        assert r.status_code == 200, f"{path} failed: {r.text[:200]}"
