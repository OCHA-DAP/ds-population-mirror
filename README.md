# ds-population-mirror

Mirror of the **HDX HAPI baseline population** (UNFPA COD-PS derived, p-coded
admin 0–2, totals only) into the team dev Postgres, schema `pop`. The
canonical total-population denominator for population-share products.

## Table

`pop.population_admin`: `location_code`, `location_name`, `admin1_code`,
`admin1_name`, `admin2_code`, `admin2_name`, `admin_level`, `gender`,
`age_range`, `population`, `reference_period_start`, `reference_period_end`,
`resource_hdx_id`, `refreshed_at`.

All reference periods are kept — pick the latest per unit downstream.
P-codes are mirrored raw; reconcile to your COD vintage downstream (see KB
`methods/pcode-matching.md`).

## Running

```sh
uv venv --python 3.12 && uv pip install --no-sources -e .
cp .env.example .env  # fill in
uv run --no-sync python scripts/refresh_pop.py   # full-replace load (guarded)
uv run --no-sync python scripts/pcode_audit.py   # join-rate audit vs public.polygon
```

Refreshes monthly (3rd, 04:23 UTC) as the Databricks job **Population
Mirror** (`databricks.yml`): the dev DB is reachable only through its private
endpoint, so the refresh cannot run on GitHub runners. The Job Compute policy
injects the `DSCI_AZ_*` secrets; `HAPI_APP_IDENTIFIER` must exist in the
`dsci` secret scope.

```sh
databricks bundle validate -t prod -p DEFAULT
databricks bundle deploy   -t prod -p DEFAULT                 # config changes only; code ships by pushing main
databricks bundle run population_mirror -t prod -p DEFAULT    # on-demand refresh
```

## Attribution

Source data: UNFPA / OCHA Common Operational Datasets — Population
Statistics, via [HDX HAPI](https://hdx-hapi.readthedocs.io/). License:
CC-BY (IGO).
