from __future__ import annotations

from typing import Any

from backend.app.data_sources.real_adapters.official_disclosure.citic_wealth_disclosure_adapter import fetch_disclosures
from backend.app.data_sources.real_adapters.official_nav.boc_nav_adapter import fetch_public_nav
from backend.app.data_sources.real_adapters.reference_rates.deposit_rate_adapter import fetch_deposit_rates
from backend.app.data_sources.real_adapters.reference_rates.us_treasury_adapter import fetch_us_treasury_rates
from backend.app.data_sources.real_adapters.registry.registry_lookup_adapter import lookup_registry_code


def run_external_sources(product_code: str, registry_code: str | None = None) -> dict[str, Any]:
    results = {
        "official_public_nav": fetch_public_nav(product_code),
        "official_disclosure_sample": fetch_disclosures(product_code),
        "registry_lookup_sample": lookup_registry_code(registry_code or product_code, product_code),
        "public_reference_rate_api": fetch_us_treasury_rates(),
        "deposit_rate_sample": fetch_deposit_rates(),
    }
    return {key: value.to_dict() for key, value in results.items()}
