"""Items 3-5: morning warm-up scenarios, one-at-a-time uncertainty and an
hourly state-of-charge battery check. Main case: CC, school calendar.
Writes results/tables/warmup.csv, uncertainty.csv, soc_check.csv.
Usage: python scripts/run_checks.py   (after scripts/run_all.py)"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import fleet  # noqa: E402

OUT = ROOT / "results" / "tables"
SIG = pd.read_csv(ROOT / "vendor" / "comstock_heating_signature.csv")
D = pd.read_pickle(ROOT / "results" / "series.pkl")
TEMPS, TDES = D["temps"], D["t_des"]
COUNTIES = ["New York", "Erie", "St. Lawrence"]


def occ_temps(county):
    t = TEMPS[county]
    w = t[np.isin(t.index.month, fleet.WINTER)].dropna()
    return w[fleet.occupied_mask(w.index)]


def fleet_p(county, case="cc", **kw) -> pd.Series:
    w = occ_temps(county)
    tot = 0.0
    for _, r in SIG[SIG.county == county].iterrows():
        tot = tot + fleet.heating_split(w, r.floor_area_ft2,
                                        r.occ_slope_w_ft2_k, r.occ_t_bal_c,
                                        TDES[county], case, **kw).p_el
    return tot


def warmup() -> pd.DataFrame:
    rows = []
    for county in COUNTIES:
        for case in ("cc", "cc_full"):
            base = fleet_p(county, case).max()
            for b in (0.0, 0.15, 0.30, 0.50):
                p = fleet_p(county, case, boost8=b)
                pk = p.max()
                wpk = p.groupby(fleet.winter_label(p.index)).max()
                s10 = fleet.cap_storage(p, 0.1)
                s20 = fleet.cap_storage(p, 0.2)
                rows.append({"county": county, "case": case, "boost8": b,
                             "peak_mw": pk, "change_pct": 100 * (pk / base - 1),
                             "max_over_median": pk / wpk.median(),
                             "x10_duration_h": s10["duration_h"],
                             "x10_days": s10["days_over"],
                             "x20_duration_h": s20["duration_h"]})
    return pd.DataFrame(rows)


def uncertainty() -> pd.DataFrame:
    var = ([("load_factor", v) for v in (0.8, 0.9, 1.1, 1.2)]
           + [("dtbal", v) for v in (-2.0, -1.0, 1.0, 2.0)]
           + [("cop_factor", v) for v in (0.9, 1.1)]
           + [("cap_factor", v) for v in (0.9, 1.1)])
    rows = []
    for county in COUNTIES:
        base = fleet_p(county).max()
        rows.append({"county": county, "param": "base", "value": np.nan,
                     "peak_mw": base, "change_pct": 0.0})
        for k, v in var:
            pk = fleet_p(county, **{k: v}).max()
            rows.append({"county": county, "param": k, "value": v,
                         "peak_mw": pk, "change_pct": 100 * (pk / base - 1)})
    return pd.DataFrame(rows)


def soc_check() -> pd.DataFrame:
    st = pd.read_csv(OUT / "storage.csv")
    rows = []
    for county in COUNTIES:
        p = fleet_p(county)
        t = TEMPS[county]
        all_h = t[np.isin(t.index.month, fleet.WINTER)].index
        for x in (0.1, 0.2, 0.3):
            daily = st[(st.county == county) & (st.case == "cc")
                       & (st.calendar == "school") & np.isclose(st.x, x)
                       ].nameplate_mwh.iloc[0]
            r = {"county": county, "x": x, "power_mw": x * p.max(),
                 "daily_method_mwh": daily}
            for cf in (1.0, 0.25):
                e = fleet.min_nameplate(p, all_h, x, charge_frac=cf)
                r[f"hourly_soc_mwh_charge{cf}"] = e
            r["daily_method_ok"] = fleet.simulate_soc(
                p, all_h, x, daily)["shortfall_mwh"] < 1e-6
            rows.append(r)
    return pd.DataFrame(rows)


def main():
    w, u, s = warmup(), uncertainty(), soc_check()
    w.to_csv(OUT / "warmup.csv", index=False)
    u.to_csv(OUT / "uncertainty.csv", index=False)
    s.to_csv(OUT / "soc_check.csv", index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        for df in (w, u, s):
            print(df.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
