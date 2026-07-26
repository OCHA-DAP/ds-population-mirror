"""Audit pop.population_admin p-codes against the team boundary reference.

Reports, per country and admin level: how many distinct pcodes match
public.polygon (prod, the canonical pcode spine) exactly, and lists the
misses. Also reports polygon countries with NO population rows at all
(candidates for a WorldPop zonal-stats phase 2), and checks the adm1
coverage of the partial-IPC countries the seas5 HNRP tab needs most.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

import ocha_stratus as stratus  # noqa: E402
import pandas as pd  # noqa: E402

from src import storage  # noqa: E402

KEY_COUNTRIES = ["PAK", "BEN", "YEM", "UGA", "BGD", "TGO", "KEN", "MDG", "MOZ", "SDN"]


def main():
    pop = storage.read_population_admin()
    poly = pd.read_sql(
        "SELECT pcode, name, adm_level, iso3 FROM public.polygon "
        "WHERE adm_level IN (1,2)",
        stratus.get_engine(stage="prod"),
    )
    ref = set(poly["pcode"])

    print("== pop pcodes vs public.polygon (prod) ==")
    rows = []
    for lvl in (1, 2):
        code_col = f"admin{lvl}_code"
        sub = pop[pop["admin_level"] == lvl][["location_code", code_col]]
        sub = sub.dropna(subset=[code_col]).drop_duplicates()
        for iso3, g in sub.groupby("location_code"):
            codes = set(g[code_col])
            missing = sorted(codes - ref)
            rows.append(
                {
                    "iso3": iso3,
                    "adm_level": lvl,
                    "pcodes": len(codes),
                    "matched": len(codes) - len(missing),
                    "missing": len(missing),
                    "examples": ", ".join(missing[:4]),
                }
            )
    report = pd.DataFrame(rows).sort_values(
        ["missing", "iso3"], ascending=[False, True]
    )
    print(report.to_string(index=False))
    total = report[["pcodes", "matched"]].sum()
    print(
        f"\nTOTAL: {total.matched}/{total.pcodes} distinct pcodes matched "
        f"({100 * total.matched / total.pcodes:.1f}%)"
    )

    print("\n== polygon countries with NO population rows (phase-2 candidates) ==")
    have = set(pop["location_code"])
    missing_iso = sorted(set(poly["iso3"]) - have)
    print(", ".join(missing_iso) or "(none)")

    print("\n== key partial-IPC countries: adm1 units in mirror ==")
    adm1 = pop[pop["admin_level"] == 1].copy()
    # HAPI uses *-XXX placeholder codes where COD-PS lacks pcodes (e.g. MDG);
    # those units are still usable by name, so count units by name there.
    placeholder = adm1["admin1_code"].str.endswith("-XXX", na=True)
    adm1["unit"] = adm1["admin1_code"].where(~placeholder, adm1["admin1_name"])
    for iso3 in KEY_COUNTRIES:
        g = adm1[adm1["location_code"] == iso3]
        n = g["unit"].nunique()
        n_ph = g[placeholder]["unit"].nunique()
        n_poly = poly[(poly["iso3"] == iso3) & (poly["adm_level"] == 1)][
            "pcode"
        ].nunique()
        note = " MISSING" if n == 0 else (f" ({n_ph} name-only)" if n_ph else "")
        print(f"{iso3}: {n} adm1 units in mirror vs {n_poly} in polygon{note}")


if __name__ == "__main__":
    main()
