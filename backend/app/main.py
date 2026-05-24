"""FastAPI entrypoint for the wealth research assistant."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.app.agents.workflow import ResearchRequest, run_workflow
from backend.app.evaluation import run_evaluation
from backend.app.tools.data_loader import load_products
from backend.app.tools.product_benchmark import peer_summary

ROOT = Path(__file__).resolve().parents[2]

app = FastAPI(title="wealth-research-agent", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    symbol: str = Field("600519", description="Instrument or product code")
    company: str = Field("贵州茅台", description="Company/product display name")
    analysis_type: str = Field("full", description="full/risk/product")
    output_path: str | None = Field(None, description="Optional markdown report path")


class ProductBenchmarkRequest(BaseModel):
    asset_class: str | None = None
    risk_level: str | None = None
    channel: str | None = None


class EvalRunRequest(BaseModel):
    output_path: str | None = None


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "wealth-research-agent",
        "data_mode": "sample/mock",
        "workflow": "LangGraph with deterministic fallbacks",
    }


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest) -> dict[str, Any]:
    output_path = req.output_path or str(Path("reports") / f"{req.symbol}_research_report.md")
    return run_workflow(
        ResearchRequest(
            symbol=req.symbol,
            company=req.company,
            analysis_type=req.analysis_type,
            output_path=output_path,
        )
    )


@app.post("/api/product-benchmark")
def product_benchmark(req: ProductBenchmarkRequest) -> dict[str, Any]:
    filters = req.model_dump(exclude_none=True)
    return peer_summary(load_products(), filters=filters)


@app.post("/api/eval/run")
def eval_run(req: EvalRunRequest | None = None) -> dict[str, Any]:
    output_path = req.output_path if req else None
    return run_evaluation(output_path=output_path)


@app.post("/analyze")
def analyze_legacy(req: AnalyzeRequest) -> dict[str, Any]:
    return analyze(req)
