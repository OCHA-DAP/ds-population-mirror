"""Refresh the population mirror: HAPI baseline population, totals only."""

import logging
import sys

sys.path.insert(0, ".")

import pandas as pd
from dotenv import load_dotenv

from src import hapi, storage

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger("refresh_pop")


def main():
    load_dotenv()
    storage.ensure_tables()

    rows = hapi.fetch_population()
    df = pd.DataFrame(rows)
    for col in ("reference_period_start", "reference_period_end"):
        df[col] = pd.to_datetime(df[col]).dt.date
    storage.replace_population_admin(df)

    summary = df.groupby("admin_level").size()
    logger.info("Rows by admin level:\n%s", summary.to_string())
    logger.info("Countries: %s", df["location_code"].nunique())
    logger.info("Refresh complete")


if __name__ == "__main__":
    main()
