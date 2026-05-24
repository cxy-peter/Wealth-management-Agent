# Compliance Boundary

This repository is a research-assistant demo, not a trading or advisory system.

## Allowed

- Research assistance.
- Risk summaries.
- Product benchmarking.
- Markdown report generation.
- Sample/mock data analysis.
- Human review and audit trace.

## Not Allowed

- Trade direction outputs.
- Return guarantees.
- Deterministic price-path claims.
- Real customer data.
- Private product documents.
- API keys or model weights committed to the repository.

## Data Policy

- Default inputs are the CSV files under `data/`.
- Live adapters must be configured outside the repo through environment variables.
- Tool outputs must carry `tool_call_id` and `evidence_ids`.
- Numeric report statements must come from tool output and pass verifier checks.
