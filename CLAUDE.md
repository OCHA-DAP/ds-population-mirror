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
- Known upstream data-quality bug (2026-07): **PAK adm1 rows are mis-p-coded
  by HAPI** — 5 rows with a duplicate PK7 and populations shifted one unit
  against their names/codes (PK2 "Balochistan" carries KP's 35.5M, PK5 "KP"
  carries Islamabad's 2.0M; verified vs the 2017 census; resource
  16394872-79a8-4292-bc7c-037bb7038084). Mirrored raw per doctrine —
  consumers must distrust PAK adm1 (seas5-skill excludes it explicitly).
  Worth reporting to the HDX HAPI team.
- **NAM adm1 rows are ~10% of reality** (sum 284k vs 3.0M census 2023) — the
  true figures sit in its adm2 (constituency) rows; aggregate those instead.
- Known coverage holes (2026-07): **YEM absent entirely** from HAPI baseline
  population; ~20 `public.polygon` countries missing overall (SYR, MMR, UKR,
  LBN…). Run `scripts/pcode_audit.py` for the current gap list.
- **Recommended fallback for missing/distrusted countries** (before reaching
  for WorldPop; the seas5-skill HNRP tab uses this layering): (1) this
  mirror → (2) **HNO/JIAF baseline in `hpc.needs_admin`** (ds-hnrp-mirror;
  `population_status='all' AND lower(category) IN ('total','')`) — current
  planning-year totals for 17 HRP countries incl. YEM/UKR/MMR and the
  old-census countries → (3) per-country HDX datasets HAPI never ingested
  (`cod-ps-mmr`/`-ukr`/`-gmb`, OCHA CO estimates for LBN/YEM/LBY) → (4)
  WorldPop zonal stats, only for the residue (SYR, COG, GNB). Full detail on
  the KB page.
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
