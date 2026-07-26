"""HDX HAPI baseline population: UNFPA COD-PS derived, p-coded admin 0-2.

Totals only (gender=all, age_range=all) — HAPI also carries sex/age
disaggregation but at ~54x the row count (~1M rows vs ~21k); the totals are
the product. Endpoint moved in HAPI v2 from population-social/population to
geography-infrastructure/baseline-population.

HAPI requires an app identifier (base64 of "app-name:email", no registration).
Set HAPI_APP_IDENTIFIER in the environment.
"""

import logging
import os
import time

import requests

logger = logging.getLogger(__name__)

BASE = "https://hapi.humdata.org/api/v2"
PAGE_SIZE = 10_000


def app_identifier():
    ident = os.environ.get("HAPI_APP_IDENTIFIER")
    if not ident:
        raise RuntimeError("HAPI_APP_IDENTIFIER env var is required")
    return ident


def fetch_population():
    """All totals rows from geography-infrastructure/baseline-population."""
    rows = []
    offset = 0
    while True:
        for attempt in range(3):
            try:
                r = requests.get(
                    f"{BASE}/geography-infrastructure/baseline-population",
                    params={
                        "gender": "all",
                        "age_range": "all",
                        "limit": PAGE_SIZE,
                        "offset": offset,
                        "output_format": "json",
                        "app_identifier": app_identifier(),
                    },
                    timeout=180,
                )
                r.raise_for_status()
                page = r.json()["data"]
                break
            except (requests.RequestException, ValueError, KeyError):
                if attempt == 2:
                    raise
                time.sleep(10 * (attempt + 1))
        rows.extend(page)
        logger.info("HAPI baseline-population: %s rows so far", len(rows))
        if len(page) < PAGE_SIZE:
            return rows
        offset += PAGE_SIZE
