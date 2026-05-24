from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.agents.planner_agent import planner_agent
from backend.app.agents.risk_guardrail_agent import FORBIDDEN_PHRASES, sanitize_text
from backend.app.agents.verifier_agent import verify_result
from backend.app.agents.workflow import ResearchRequest, run_workflow
from backend.app.main import app
from backend.app.mcp.client import local_mcp_config, mcp_available
from backend.app.optimization.context_features import extract_context
from backend.app.optimization.contextual_bandit import LinUCBPolicy
from backend.app.optimization.reward import compute_reward
from backend.app.optimization.router_policy import ACTION_TO_REQUEST, EpsilonGreedyRouter
from backend.app.tools.data_loader import load_product_nav, load_product_risk_events, load_products
from backend.app.tools.tool_registry import execute_tool, get_registered_tool_names
from backend.app.weekly_report.generators.benchmark_report_generator import peer_benchmark, weekly_product_detail
from backend.app.weekly_report.generators.weekly_report_generator import generate_weekly_report, weekly_summary
from backend.app.weekly_report.weekly_report_verifier import verify_weekly_report
from backend.app.dpo.dpo_dataset_validator import validate_dpo_dataset


def test_tool_registry_has_required_tools() -> None:
    names = set(get_registered_tool_names())
    assert {
        "load_price_series",
        "calculate_metrics",
        "load_fundamental_snapshot",
        "load_valuation_snapshot",
        "load_news",
        "classify_news_risk",
        "product_benchmark",
    }.issubset(names)


def test_tool_call_record_shape() -> None:
    record = execute_tool("load_price_series", symbol="600519")
    assert record["success"] is True
    assert record["tool_call_id"].startswith("tc_load_price_series_")
    assert record["evidence_ids"]
    assert record["latency_ms"] >= 0


def test_calculate_metrics_tool_output() -> None:
    record = execute_tool("calculate_metrics", symbol="600519")
    metrics = record["output"]["metrics"]
    assert metrics["observations"] == 25
    assert "sharpe_ratio" in metrics


def test_planner_risk_route_skips_product_tool() -> None:
    state = {"request": {"symbol": "600519", "company": "贵州茅台", "analysis_type": "risk", "risk_preference": "balanced"}}
    plan = planner_agent(state)["planner_plan"]
    assert plan["task_type"] == "risk_only"
    assert "product_benchmark" in plan["skipped_tools"]


def test_workflow_standard_has_verification_and_trace() -> None:
    result = run_workflow(ResearchRequest(symbol="600519", company="贵州茅台"), persist=False)
    assert result["verification_result"]["pass"] is True
    assert result["tool_calls"]
    assert all("tool_call_id" in call for call in result["tool_calls"])
    assert "tool_call_id=" in result["report_markdown"]


def test_workflow_risk_route_does_not_run_product_tool() -> None:
    result = run_workflow(ResearchRequest(symbol="600519", company="贵州茅台", analysis_type="risk"), persist=False)
    tool_names = [call["tool_name"] for call in result["tool_calls"]]
    assert "product_benchmark" not in tool_names
    assert "classify_news_risk" in tool_names


def test_workflow_product_route_runs_product_tool() -> None:
    result = run_workflow(ResearchRequest(symbol="600519", company="贵州茅台", analysis_type="product"), persist=False)
    tool_names = [call["tool_name"] for call in result["tool_calls"]]
    assert "product_benchmark" in tool_names
    assert result["peer_summary"]["product_count"] >= 80
    assert "calmar_ratio" in result["peer_summary"]["table"][0]
    assert result["peer_summary"]["table"][0]["source_tool_call_id"].startswith("tc_product_benchmark_")


def test_verifier_detects_missing_evidence() -> None:
    verification = verify_result(
        {
            "report_markdown": "合规说明 数据与工具调用摘要 核心量化指标 基本面与估值摘要 技术面风险观察 同业产品对标样例 新闻情绪与风险信号 风险提示与可追溯结论",
            "metrics": {"total_return": 0, "annualized_volatility": 0, "max_drawdown": 0, "sharpe_ratio": 0},
            "news_signals": [{"title": "sample"}],
            "peer_summary": {"table": [{}]},
        }
    )
    assert verification["pass"] is False
    assert verification["missing_evidence"]


def test_guardrail_sanitizes_configured_terms() -> None:
    text = f"abc {FORBIDDEN_PHRASES[0]} xyz"
    assert FORBIDDEN_PHRASES[0] not in sanitize_text(text)


def test_reward_penalizes_forbidden_hit() -> None:
    clean = compute_reward(
        {
            "tool_call_success": 1,
            "metric_consistency": 1,
            "risk_warning_coverage": 1,
            "evidence_coverage": 1,
            "report_format_pass": 1,
            "latency_ms": 0,
            "forbidden_wording_hit": 0,
        }
    )
    blocked = compute_reward(
        {
            "tool_call_success": 1,
            "metric_consistency": 1,
            "risk_warning_coverage": 1,
            "evidence_coverage": 1,
            "report_format_pass": 1,
            "latency_ms": 0,
            "forbidden_wording_hit": 1,
        }
    )
    assert blocked < clean


def test_router_policy_updates_values() -> None:
    router = EpsilonGreedyRouter(epsilon=0, seed=1)
    action = router.select_action()
    router.update(action, 0.8)
    assert router.counts[action] == 1
    assert ACTION_TO_REQUEST[action]["analysis_type"]


def test_api_job_report_and_review_flow() -> None:
    client = TestClient(app)
    response = client.post("/api/analyze/jobs", json={"symbol": "600519", "company": "贵州茅台", "analysis_type": "risk"})
    assert response.status_code == 200
    run_id = response.json()["run_id"]
    assert client.get(f"/api/analyze/jobs/{run_id}").status_code == 200
    assert client.get(f"/api/analyze/jobs/{run_id}/events").json()["tool_calls"]
    assert client.get(f"/api/reports/{run_id}").json()["report_markdown"]
    assert client.post(f"/api/reviews/{run_id}/approve", json={"reviewer": "pytest"}).json()["status"] == "approved"


def test_mcp_client_config_is_available() -> None:
    assert "wealth_research_local" in local_mcp_config()
    assert isinstance(mcp_available(), bool)


def test_synthetic_product_universe_files_are_loaded() -> None:
    products = load_products()
    nav = load_product_nav()
    events = load_product_risk_events()
    assert 80 <= len(products) <= 120
    assert products["asset_class"].nunique() >= 9
    assert products["risk_level"].nunique() == 5
    assert len(nav) > len(products) * 20
    assert {"信用利差走阔", "权益回撤", "估值波动"}.intersection(set(events["event_type"]))


def test_product_api_detail_nav_and_events() -> None:
    client = TestClient(app)
    products = client.get("/api/products").json()
    product_id = products["products"][0]["product_id"]
    detail = client.get(f"/api/products/{product_id}").json()
    nav = client.get(f"/api/products/{product_id}/nav").json()
    events = client.get(f"/api/products/{product_id}/risk-events").json()
    assert detail["metrics"]["metric_evidence_id"].startswith("ev_product_metric_")
    assert nav["records"]
    assert "records" in events


def test_linucb_policy_select_update_and_snapshot() -> None:
    context = extract_context(
        {
            "analysis_type": "product",
            "risk_preference": "balanced",
            "product_pool_size": 108,
            "product_risk_level": "R3",
            "latency_budget_ms": 800,
        }
    )
    policy = LinUCBPolicy(alpha=0.5, ridge_lambda=1.0, seed=1)
    action, scores = policy.select_action(context)
    policy.update(action, context, 0.8)
    snapshot = policy.snapshot()
    assert action in scores
    assert snapshot["A"][action]


def test_weekly_summary_uses_synthetic_universe() -> None:
    summary = weekly_summary()
    assert summary["product_count"] == 96
    assert summary["kpis"]["total_scale_bn"] > 0
    assert summary["scale_change_rank"]
    assert summary["market_issuance"]["new_product_count"] > 0
    assert summary["evidence_ids"]


def test_weekly_product_detail_and_peer_benchmark() -> None:
    detail = weekly_product_detail("WP0001")
    assert detail is not None
    assert detail["nav"]
    assert detail["percentile"]["evidence_id"].startswith("ev_percentile_")
    peer = peer_benchmark("WP0001")
    assert peer["peer_count"] > 0
    assert peer["table"]


def test_weekly_report_verifier_passes_generated_report() -> None:
    report = generate_weekly_report()
    verification = verify_weekly_report(report)
    assert verification["pass"] is True
    assert verification["metric_mismatches"] == []


def test_weekly_api_endpoints() -> None:
    client = TestClient(app)
    dates = client.get("/api/weekly-report/dates").json()
    assert dates["latest"]
    summary = client.get("/api/weekly-report/summary", params={"report_date": dates["latest"]}).json()
    products = client.get("/api/weekly-report/products", params={"report_date": dates["latest"]}).json()
    assert summary["product_count"] == products["count"]
    product_code = products["products"][0]["product_code"]
    assert client.get(f"/api/weekly-report/products/{product_code}", params={"report_date": dates["latest"]}).status_code == 200
    assert client.post("/api/weekly-report/generate", json={"report_date": dates["latest"]}).json()["verification_result"]["pass"] is True


def test_weekly_benchmark_api_endpoints() -> None:
    client = TestClient(app)
    peer = client.post("/api/benchmark/peer", json={"product_code": "WP0001"}).json()
    channel = client.post("/api/benchmark/channel", json={}).json()
    top = client.post("/api/benchmark/top-peers", json={}).json()
    assert peer["peer_count"] > 0
    assert channel["peer_count"] > 0
    assert top["count"] > 0


def test_dpo_dataset_validator() -> None:
    result = validate_dpo_dataset()
    assert result["valid"] is True
    assert result["pair_count"] >= 20
