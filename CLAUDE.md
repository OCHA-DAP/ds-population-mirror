# ds-population-mirror

Canonical **admin-level total-population baseline** in the team **dev**
Postgres, schema **`pop`**. The single denominator for population-share
products (seas5-skill HNRP tab, CERF predictor, exposure work) — stops each
one re-deriving population ad hoc.

## Key facts

- Table: `pop.population_admin` — HDX HAPI baseline population (UNFPA COD-PS
  derived), p-coded admin 0–2, **totals only** (`gender='all'`,
  `age_range='all'`; sex/age disaggregation exists upstream but is ~54× the
  rows — ~1M vs ~21k — and deliberately not mirrored). All reference periods
  kept (history); latest-per-unit is the consumer's job.
- Endpoint: `GET /api/v2/geography-infrastructure/baseline-population` —
  NOTE: moved in HAPI v2 from the older `population-social/population` path.
  Needs `HAPI_APP_IDENTIFIER` (base64 of `app-name:email`, no registration).
- **Mirror raw, reconcile downstream**: p-codes are stored exactly as HAPI
  serves them. Consumers reconcile to the COD vintage via the crosswalk
  pattern in KB `methods/pcode-matching.md` (e.g. `normalize_pcodes()` /
  `REFORM_XWALK` in ds-seas5-skill's `pipeline/export_hnrp_drought.py`).
- Known coverage holes (2026-07): **YEM absent entirely** from HAPI baseline
  population — the brief's Phase 2 (WorldPop zonal stats over our COD
  polygons in the prod `polygon` blob container) is the designed fallback.
  Run `scripts/pcode_audit.py` for the current gap list vs `public.polygon`.
- Full-replace loads guard against partial pulls (refuse to shrink >50%).
- DB access via `ocha_stratus.get_engine(stage=STAGE, write=...)`;
  `PGSSLMODE=require`. STAGE defaults to dev.
- GHA: `DSCI_AZ_DB_*` are OCHA-DAP **org-level** secrets (no per-repo setup);
  repo secret: `HAPI_APP_IDENTIFIER`. Monthly cron + `workflow_dispatch`
  (population vintages change rarely; daily would be waste).
- License: COD-PS via HDX is CC-BY (IGO) — credit UNFPA/OCHA on any
  published page.
- CI pins Python 3.12; installs with `uv pip install --no-sources -e .`.
- KB page: `pipelines/population-mirror.md`.
