"""DB layer: pop schema on the team Postgres via ocha-stratus.

Stage is selected with the STAGE env var (default "dev"). Writers need the
*_UID_WRITE / *_PW_WRITE credentials; PGSSLMODE=require is enforced here.
"""

import logging
import os
from datetime import datetime, timezone

os.environ.setdefault("PGSSLMODE", "require")

import ocha_stratus as stratus
import pandas as pd
from sqlalchemy import text

logger = logging.getLogger(__name__)

SCHEMA = "pop"
STAGE = os.environ.get("STAGE", "dev")

POPULATION_COLS = [
    "location_code", "location_name", "admin1_code", "admin1_name",
    "admin2_code", "admin2_name", "admin_level", "gender", "age_range",
    "population", "reference_period_start", "reference_period_end",
    "resource_hdx_id",
]


def get_engine(write=False):
    return stratus.get_engine(stage=STAGE, write=write)


def ensure_tables():
    ddl = f"""
    CREATE SCHEMA IF NOT EXISTS {SCHEMA};
    CREATE TABLE IF NOT EXISTS {SCHEMA}.population_admin (
        location_code text,
        location_name text,
        admin1_code text,
        admin1_name text,
        admin2_code text,
        admin2_name text,
        admin_level integer,
        gender text,
        age_range text,
        population bigint,
        reference_period_start date,
        reference_period_end date,
        resource_hdx_id text,
        refreshed_at timestamptz
    );
    CREATE INDEX IF NOT EXISTS population_admin_key_idx
        ON {SCHEMA}.population_admin (location_code, admin_level);
    """
    with get_engine(write=True).begin() as conn:
        conn.execute(text(ddl))


def replace_population_admin(df, guard=0.5):
    """Full transactional replace, refusing to shrink the table by > guard."""
    df = df[POPULATION_COLS].copy()
    df["refreshed_at"] = datetime.now(timezone.utc)
    engine = get_engine(write=True)
    with engine.begin() as conn:
        existing = conn.execute(
            text(f"SELECT count(*) FROM {SCHEMA}.population_admin")
        ).scalar()
        if existing and len(df) < existing * guard:
            raise RuntimeError(
                f"population_admin: refusing to replace {existing} rows with "
                f"{len(df)} (partial pull?)"
            )
        conn.execute(text(f"DELETE FROM {SCHEMA}.population_admin"))
        df.to_sql(
            "population_admin",
            conn,
            schema=SCHEMA,
            if_exists="append",
            index=False,
            chunksize=10_000,
            method="multi",
        )
    logger.info("Replaced %s.population_admin with %s rows", SCHEMA, len(df))


def read_population_admin():
    return pd.read_sql(f"SELECT * FROM {SCHEMA}.population_admin", get_engine())
