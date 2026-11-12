"""Item 1: input check table. ComStock areas and signature fits (vendor
file, hash-checked against the source repository), NOAA hourly temperature
coverage, occupied-hour counts, and a neighbor-station comparison for each
study station. Writes results/tables/input_check.csv and neighbor_check.csv.
Usage: python scripts/check_inputs.py"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import fleet  # noqa: E402
import isd  # noqa: E402
from run_all import COUNTIES, END, RAW, START  # noqa: E402

NEIGHBORS = {  # study station -> (neighbor ICAO, ISD stem, first year)
    "KNYC": ("KLGA", "725030-14732", 2014),
    "KBUF": ("KIAG", "725287-04724", 2014),
    "KMSS": ("KOGS", "725186-99999", 2016),   # KOGS ISD files start 2016
}
SOURCE_SHA = {  # vendor/SHA256_source.txt, school-shelter-ny@23d8d0b
    "comstock_heating_signature.csv":
    "dec14590998a71a4805e693f48880c74c10acbf5ef247d7ba3c7921ce82b8f8b"}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def winter(t: pd.Series) -> pd.Series:
    return t[np.isin(t.index.month, fleet.WINTER)]


def main() -> None:
    out = ROOT / "results" / "tables"
    sigf = ROOT / "vendor" / "comstock_heating_signature.csv"
    assert sha(sigf) == SOURCE_SHA[sigf.name], "signature file changed"
    sig = pd.read_csv(sigf)
    rows, nb = [], []
    for county, (icao, stem) in COUNTIES.items():
        t = isd.to_local_standard(isd.station_hourly(RAW, stem,
                                                     range(2014, 2026)))
        t = t.loc[START:END]
        w = winter(t)
        s = sig[sig.county == county]
        rows.append({
            "county": county, "station": icao,
            "area_primary_ft2": int(s[s.school == "primaryschool"]
                                    .floor_area_ft2.iloc[0]),
            "area_secondary_ft2": int(s[s.school == "secondaryschool"]
                                      .floor_area_ft2.iloc[0]),
            "area_total_m2": round(s.floor_area_ft2.sum() / 10.7639),
            "slope_w_ft2_k": "/".join(f"{v:.3f}" for v in s.occ_slope_w_ft2_k),
            "t_bal_c": "/".join(f"{v:.1f}" for v in s.occ_t_bal_c),
            "r2": "/".join(f"{v:.2f}" for v in s.occ_r2),
            "winter_hours": len(w),
            "missing_pct": round(100 * w.isna().mean(), 2),
            "occupied_hours_school_calendar":
            int(fleet.occupied_mask(w.dropna().index).sum()),
            "occupied_hours_all_weekdays":
            int(fleet.occupied_mask(w.dropna().index, calendar=False).sum()),
            "t_min_c": float(w.min()), "t_min_time": str(w.idxmin()),
            "t_p1_c": round(float(np.nanpercentile(w, 1)), 1)})
        nicao, nstem, y0 = NEIGHBORS[icao]
        n = isd.to_local_standard(isd.station_hourly(RAW, nstem,
                                                     range(y0, 2026)))
        n = winter(n.loc[START:END])
        j = pd.concat([w.rename("a"), n.rename("b")], axis=1).dropna()
        d = j.a - j.b
        nb.append({"station": icao, "neighbor": nicao,
                   "common_winter_hours": len(j),
                   "mean_diff_c": round(d.mean(), 2),
                   "mae_c": round(d.abs().mean(), 2),
                   "corr": round(j.a.corr(j.b), 3),
                   "p1_station_c": round(np.percentile(j.a, 1), 1),
                   "p1_neighbor_c": round(np.percentile(j.b, 1), 1),
                   "min_station_c": j.a.min(), "min_neighbor_c": j.b.min()})
    r = pd.DataFrame(rows)
    r.to_csv(out / "input_check.csv", index=False)
    n = pd.DataFrame(nb)
    n.to_csv(out / "neighbor_check.csv", index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(r.to_string(index=False))
        print(n.to_string(index=False))
    # consistency with the main run
    dc = pd.read_csv(out / "data_check.csv")
    for _, x in r.iterrows():
        y = dc[dc.county == x.county].iloc[0]
        assert x.t_p1_c == y.t_design_c_p1 and x.t_min_c == y.t_min_c
    print("input check consistent with run_all data_check.csv")


if __name__ == "__main__":
    main()
