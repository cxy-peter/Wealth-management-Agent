from __future__ import annotations

from pathlib import Path

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
from backend.app.weekly_report.generators.benchmark_report_generator import peer_benchmark, top_peers, weekly_product_detail
from backend.app.weekly_report.generators.weekly_report_generator import generate_weekly_report, weekly_summary
from backend.app.weekly_report.weekly_report_verifier import verify_weekly_report
from backend.app.dpo.dpo_dataset_validator import validate_dpo_dataset
from backend.app.data_sources.base import REQUIRED_SOURCE_FIELDS
from backend.app.data_sources.quality.lineage_builder import lineage_for_evidence
from backend.app.models.qwen_risk_adapter import QwenRiskClassifier
from backend.app.product_taxonomy.manual_override_store import create_override
from backend.app.product_taxonomy.series_classifier import classify_products
from backend.app.product_taxonomy.series_performance import compute_series_performance
from backend.app.benchmark.reference_rate_engine import compare_product_to_reference, load_reference_rates
from backend.app.data_sources.real_adapters.official_nav.boc_nav_adapter import fetch_public_nav
from backend.app.data_sources.real_adapters.reference_rates.us_treasury_adapter import _parse_treasury_html
from backend.app.data_sources.real_adapters.registry.registry_lookup_adapter import lookup_registry_code
from backend.app.external_verification.external_verification_agent import run_external_verification
from backend.app.external_verification.source_boundary_guardrail import check_source_boundary
from backend.app.external_verification.verification_score import external_verification_score
from backend.app.skills.harness_validator import HarnessValidator
from backend.app.skills.skill_executor import execute_skill_harness


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


def test_qwen_risk_adapter_is_lightweight_fallback() -> None:
    classifier = QwenRiskClassifier()
    result = classifier.predict("信用利差走阔，净值回撤压力上升", symbol="WP0001")
    assert result["fallback_required"] is True
    assert result["model_mode"] == "rule-based-fallback"
    assert result["risk_score"] >= 3
    assert classifier.metadata.to_dict()["enabled"] is False


def test_data_source_metadata_required() -> None:
    client = TestClient(app)
    payload = client.get("/api/data/freshness").json()
    assert payload["sources"]
    for source in payload["sources"]:
        assert {"source_type", "source_name", "source_url_or_file", "confidence_level", "adapter_status"}.issubset(source)
    assert REQUIRED_SOURCE_FIELDS


def test_synthetic_data_not_labeled_official() -> None:
    client = TestClient(app)
    payload = client.post("/api/data/refresh-demo", json={"as_of_date": "2025-04-11", "base_date": "2025-04-04", "n_products": 8}).json()
    assert payload["source_type"] == "synthetic_weekly_snapshot"
    assert "Synthetic demo data only" in payload["disclaimer"]
    assert "official" not in payload["source_type"].lower()


def test_freshness_api() -> None:
    client = TestClient(app)
    response = client.get("/api/data/freshness")
    assert response.status_code == 200
    rows = response.json()["sources"]
    assert any(row["source_type"] == "synthetic_weekly_snapshot" for row in rows)
    assert any(row["source_type"] == "official_disclosure_sample" for row in rows)


def test_manual_upload_schema_preview() -> None:
    client = TestClient(app)
    csv_text = "report_date,product_code,product_name,product_type,channel,risk_level,product_scale_bn,scale_wow_bn,scale_mom_bn,latest_nav,return_3m,max_drawdown,volatility,sharpe,benchmark_status\n2025-04-04,WPX001,样例,纯固收,个金,R2,1.2,0.1,0.2,1.01,0.01,-0.02,0.03,0.5,in_range\n"
    uploaded = client.post("/api/data/upload", json={"file_name": "weekly.csv", "dataset_scope": "own_company", "text": csv_text, "target_schema": "product_weekly_snapshot"}).json()
    preview = client.get(f"/api/data/upload/{uploaded['upload_id']}/schema-preview").json()
    quality = client.get(f"/api/data/upload/{uploaded['upload_id']}/quality-report").json()
    assert preview["schema_preview"]["parser_status"] == "parsed"
    assert quality["missing_required_fields"] == []


def test_lineage_lookup() -> None:
    lineage = lineage_for_evidence("ev_snapshot_WP0001_20250404")
    assert lineage["found"] is True
    assert lineage["source_type"] == "synthetic_weekly_snapshot"


def test_verifier_blocks_fake_realtime_claim() -> None:
    report = generate_weekly_report()
    report["report_markdown"] += "\n本报告已接入官网实时数据并覆盖真实全市场产品。"
    verification = verify_weekly_report(report)
    assert verification["pass"] is False
    assert "source_overclaim" in verification["failed_checks"]


def test_upload_scope_required() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/data/upload",
        json={"file_name": "weekly.csv", "text": "report_date,product_code,product_name\n2025-04-04,WPX001,测试\n", "target_schema": "product_weekly_snapshot"},
    )
    assert response.status_code == 422


def test_own_company_upload_triggers_series_classification() -> None:
    client = TestClient(app)
    csv_text = "report_date,product_code,product_name,product_type,channel,risk_level\n2025-04-04,WPX101,稳健添利90天持有期A,纯固收,个金,R2\n"
    uploaded = client.post(
        "/api/data/upload",
        json={"file_name": "own.csv", "dataset_scope": "own_company", "text": csv_text, "target_schema": "product_weekly_snapshot"},
    )
    assert uploaded.status_code == 200
    classified = classify_products(
        products=[{"product_code": "WPX101", "product_name": "稳健添利90天持有期A", "product_type": "纯固收", "channel": "个金", "risk_level": "R2"}],
        apply_manual=False,
    )
    assert classified["classified_products"][0]["suggested_series_id"] == "stable_income"


def test_full_market_upload_updates_peer_universe() -> None:
    client = TestClient(app)
    csv_text = "peer_product_code,report_date,return_3m\nPRX001,2025-04-04,0.012\n"
    response = client.post(
        "/api/data/upload",
        json={"file_name": "peer.csv", "dataset_scope": "full_market", "text": csv_text, "target_schema": "peer_product_metrics"},
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["dataset_scope"] == "full_market"
    assert payload["source_type"] == "manual_upload"


def test_reference_rates_upload_updates_benchmark_panel() -> None:
    client = TestClient(app)
    csv_text = "rate_id,as_of_date,currency,rate_type,tenor_days,tenor_label,annual_yield\nRMB_TEST_3M,2025-04-04,CNY,deposit,90,3M,0.015\n"
    response = client.post(
        "/api/data/upload",
        json={"file_name": "rates.csv", "dataset_scope": "reference_rates", "text": csv_text, "target_schema": "reference_rates"},
    )
    assert response.status_code == 200
    assert response.json()["dataset_scope"] == "reference_rates"
    rates = load_reference_rates("2025-04-04")
    assert not rates.empty
    comparison = compare_product_to_reference({"product_code": "WP0001", "return_3m": 0.01, "holding_period_days": 90, "benchmark_lower": 0.02, "benchmark_upper": 0.04})
    assert comparison["comparisons"]


def test_manual_override_changes_series_membership() -> None:
    before = classify_products(products=[{"product_code": "TST_SERIES_1", "product_name": "现金优选日开A", "product_type": "现金管理"}], apply_manual=False)
    assert before["classified_products"][0]["suggested_series_id"] == "cash"
    override = create_override(product_code="TST_SERIES_1", product_name="现金优选日开A", old_series_id="cash", new_series_id="manual_series", action_type="move", reason="pytest")
    after = classify_products(products=[{"product_code": "TST_SERIES_1", "product_name": "现金优选日开A", "product_type": "现金管理"}])
    assert after["classified_products"][0]["suggested_series_id"] == "manual_series"
    assert after["classified_products"][0]["evidence_id"] == override["evidence_id"]


def test_series_performance_recomputed_after_override() -> None:
    create_override(product_code="TST_SERIES_2", product_name="稳健添利90天", old_series_id="stable_income", new_series_id="manual_perf", action_type="move", reason="pytest")
    performance = compute_series_performance(
        products=[
            {"product_code": "TST_SERIES_2", "product_name": "稳健添利90天", "product_type": "纯固收", "product_scale_bn": 10, "return_3m": 0.01, "return_1m": 0.003, "return_6m": 0.02, "max_drawdown": -0.01, "volatility": 0.02, "sharpe": 0.8, "benchmark_status": "in_range"},
            {"product_code": "TST_SERIES_3", "product_name": "多元配置180天", "product_type": "多资产", "product_scale_bn": 5, "return_3m": 0.02, "return_1m": 0.004, "return_6m": 0.03, "max_drawdown": -0.03, "volatility": 0.06, "sharpe": 0.6, "benchmark_status": "below_lower"},
        ]
    )
    row = next(item for item in performance["series"] if item["series_id"] == "manual_perf")
    assert row["product_count"] == 1
    assert row["total_scale_bn"] == 10


def test_product_names_not_ellipsized_snapshot() -> None:
    css = (Path(__file__).resolve().parents[1] / "frontend" / "src" / "styles.css").read_text(encoding="utf-8")
    assert ".product-name-cell" in css
    assert "text-overflow: unset" in css
    assert "white-space: normal" in css


def test_top_peers_global_rank_not_cyclic() -> None:
    payload = top_peers(limit=24)
    ranks = [row["global_rank"] for row in payload["table"]]
    assert ranks == list(range(1, len(ranks) + 1))
    assert max(ranks) > 8


def test_product_selector_uses_filtered_products() -> None:
    source = (Path(__file__).resolve().parents[1] / "frontend" / "src" / "pages" / "ProductBenchmarkWorkbench.jsx").read_text(encoding="utf-8")
    assert "filteredProducts.slice(0, 120)" in source
    assert "setSelectedCode('')" in source


def test_skill_harness_trace_contains_selected_skills() -> None:
    trace = execute_skill_harness("生成产品周报", {"report_date": "2025-04-04"})
    assert trace["selected_skills"]
    assert trace["skill_calls"]
    assert trace["skill_calls"][0]["skill_call_id"].startswith("sc_")
    assert "harness_result" in trace["skill_calls"][0]


def test_harness_blocks_missing_evidence() -> None:
    result = HarnessValidator().validate("近3个月收益 2.10%，最大回撤 -0.50%。", report_type="weekly_report")
    assert result["pass"] is False
    assert "required_evidence_rules" in result["failed_rules"]


def test_dpo_output_goes_through_verifier() -> None:
    trace = execute_skill_harness("生成产品周报", {"report_date": "2025-04-04", "task_type": "weekly_product_summary"})
    skill_names = [call["skill_name"] for call in trace["skill_calls"]]
    assert "dpo_report_skill" in skill_names
    assert "verifier_skill" in skill_names


def test_import_mode_replace_synthetic_for_own_company() -> None:
    client = TestClient(app)
    csv_text = "report_date,product_code,product_name\n2025-04-04,WPX201,上传产品\n"
    response = client.post(
        "/api/data/upload",
        json={
            "file_name": "own.csv",
            "dataset_scope": "own_company",
            "text": csv_text,
            "target_schema": "product_weekly_snapshot",
            "import_mode": "replace_synthetic_for_scope",
            "delete_synthetic": True,
        },
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["synthetic_action"] == "scope_synthetic_disabled"
    assert payload["delete_synthetic"] is True


def test_import_mode_replace_synthetic_for_full_market() -> None:
    client = TestClient(app)
    csv_text = "peer_product_code,report_date,return_3m\nPRX201,2025-04-04,0.01\n"
    response = client.post(
        "/api/data/upload",
        json={
            "file_name": "peer.csv",
            "dataset_scope": "full_market",
            "text": csv_text,
            "target_schema": "peer_product_metrics",
            "import_mode": "replace_synthetic_for_scope",
            "delete_synthetic": True,
        },
    )
    assert response.status_code == 200
    assert response.json()["synthetic_action"] == "scope_synthetic_disabled"


def test_import_mode_replace_synthetic_for_reference_rates() -> None:
    client = TestClient(app)
    csv_text = "rate_id,as_of_date,tenor_days,annual_yield\nR_TEST,2025-04-04,90,0.015\n"
    response = client.post(
        "/api/data/upload",
        json={
            "file_name": "rates.csv",
            "dataset_scope": "reference_rates",
            "text": csv_text,
            "target_schema": "reference_rates",
            "import_mode": "clear_scope_then_import",
            "delete_synthetic": True,
        },
    )
    payload = response.json()
    assert response.status_code == 200
    assert payload["dataset_scope"] == "reference_rates"
    assert payload["synthetic_action"] == "scope_synthetic_disabled"


def test_data_mode_uploaded_only_excludes_synthetic() -> None:
    source = (Path(__file__).resolve().parents[1] / "frontend" / "src" / "sessionDataStore.js").read_text(encoding="utf-8")
    assert "uploaded_only" in source
    assert "isSyntheticDisabled('own_company')" in source
    assert "uploaded_only_empty" in source


def test_official_adapter_failure_does_not_break_demo(monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_REAL_DATA_ADAPTERS", "false")
    result = fetch_public_nav("AF245408")
    assert result.adapter_status == "disabled_sample"
    assert result.records
    assert result.records[0].source_type == "official_public_nav"


def test_external_verification_marks_unknown_registry_not_verified() -> None:
    result = lookup_registry_code("bad code with spaces")
    payload = result.records[0].payload
    assert payload["registry_status"] == "unknown"
    assert payload["verified"] is False


def test_source_boundary_blocks_real_market_claim_for_synthetic() -> None:
    result = check_source_boundary(
        "本产品处于真实全市场排名前列。",
        {"source_types": ["synthetic_weekly_snapshot"], "synthetic_peer_universe": True},
    )
    assert result["pass"] is False
    assert "synthetic_data_real_market_claim" in result["failed_rules"]


def test_lineage_contains_external_source_url() -> None:
    result = run_external_verification("AF245408")
    records = result["external_verification_result"]["official_sources_used"]
    assert records
    assert records[0]["source_url_or_file"]
    assert records[0]["evidence_id"]


def test_external_verification_score_penalizes_conflict() -> None:
    clean = external_verification_score(
        official_nav_coverage=1,
        disclosure_coverage=1,
        reference_rate_coverage=1,
        registry_check_coverage=1,
        source_freshness_score=1,
        conflict_penalty=0,
    )
    conflict = external_verification_score(
        official_nav_coverage=1,
        disclosure_coverage=1,
        reference_rate_coverage=1,
        registry_check_coverage=1,
        source_freshness_score=1,
        conflict_penalty=1,
    )
    assert conflict < clean


def test_report_requires_manual_review_when_official_nav_conflicts() -> None:
    result = run_external_verification("AF245408", uploaded_nav=0.98, report_text="基于用户上传数据生成周报摘要。")
    verification = result["external_verification_result"]
    assert verification["conflicting_fields"]
    assert verification["source_boundary"]["manual_review_required"] is True


def test_health_defaults_to_weekly_product_mode() -> None:
    client = TestClient(app)
    payload = client.get("/health").json()
    assert payload["data_mode"] == "hybrid_demo_uploaded_official_sample"


def test_analyze_default_uses_wealth_product_route() -> None:
    client = TestClient(app)
    payload = client.post("/api/analyze", json={}).json()
    assert payload["planner_plan"]["task_type"] == "product_compare"
    assert payload["verification_result"]["pass"] is True


def test_dpo_planner_selected_skills_override_rule_fallback() -> None:
    trace = execute_skill_harness("请做渠道对标并输出证据编号", {"channel": "个金", "product_type": "纯固收"})
    assert trace["skill_selection_source"] == "dpo_planner"
    assert trace["dpo_planner"]["generated_plan"]["plan_type"] == "channel_benchmark"
    assert trace["selected_skills"][0] == "channel_benchmark_skill"


def test_harness_required_weekly_fields_are_enforced() -> None:
    result = HarnessValidator().validate(
        {"product_count": 12, "kpis": {"total_scale_bn": 100.0}, "evidence_ids": ["ev_unit"]},
        report_type="weekly_report",
        skill_name="weekly_summary_skill",
    )
    assert result["pass"] is False
    assert "required_fields_by_report_type" in result["failed_rules"]
    assert "benchmark_pass_rate" in result["missing_required_fields"]
    assert "attention_count" in result["missing_required_fields"]


def test_harness_numeric_claim_requires_grounding() -> None:
    result = HarnessValidator().validate("近3个月收益 2.10%，最大回撤 -0.50%，市场分位 35%。", report_type="weekly_report")
    assert result["pass"] is False
    assert "numeric_consistency_rules" in result["failed_rules"]


def test_harness_blocks_real_market_claim_for_synthetic_source() -> None:
    result = HarnessValidator().validate(
        "该产品处于真实全市场排名前列。",
        report_type="weekly_report",
        source_context={"source_types": ["synthetic_weekly_snapshot"]},
    )
    assert result["pass"] is False
    assert "source_boundary_rules" in result["failed_rules"]


def test_us_treasury_html_parser_extracts_core_tenors() -> None:
    html = """
    <table>
      <tr><th>Date</th><th>1 Mo</th><th>3 Mo</th><th>6 Mo</th><th>1 Yr</th><th>2 Yr</th><th>10 Yr</th></tr>
      <tr><td>04/03/2025</td><td>4.31</td><td>4.28</td><td>4.16</td><td>3.88</td><td>3.70</td><td>4.10</td></tr>
      <tr><td>04/04/2025</td><td>4.30</td><td>4.27</td><td>4.15</td><td>3.87</td><td>3.69</td><td>4.09</td></tr>
    </table>
    """
    rows = _parse_treasury_html(html)
    by_id = {row["rate_id"]: row for row in rows}
    assert {"USD_TREASURY_1M", "USD_TREASURY_3M", "USD_TREASURY_6M", "USD_TREASURY_1Y", "USD_TREASURY_2Y", "USD_TREASURY_10Y"}.issubset(by_id)
    assert by_id["USD_TREASURY_10Y"]["as_of_date"] == "2025-04-04"
    assert by_id["USD_TREASURY_10Y"]["annual_yield"] == 0.0409
