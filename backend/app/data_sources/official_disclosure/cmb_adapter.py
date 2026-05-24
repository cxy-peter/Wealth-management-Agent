from __future__ import annotations


def adapter_status() -> dict[str, str]:
    return {
        "source_type": "official_disclosure_sample",
        "source_name": "CMB disclosure adapter placeholder",
        "adapter_status": "unsupported_or_optional",
        "reason": "Demo keeps the integration point without scraping dynamic or protected pages.",
    }

