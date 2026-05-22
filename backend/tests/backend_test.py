"""
Pharma Commercial Analytics Backend Tests
Tests all 12 routers + AI integrations (Emergent LLM provider)
"""
import os
import pytest
import requests

BASE_URL = "https://52fc47d2-22c3-4873-8e08-8e873065f130.preview.emergentagent.com"
API = f"{BASE_URL}/api"

SHORT = 30
LONG = 90  # for LLM calls


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
