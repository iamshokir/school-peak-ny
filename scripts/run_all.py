"""All results for the PES GM 2027 paper: data check, fleet peaks,
peak-capping storage, figures. Usage: python scripts/run_all.py"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import fleet  # noqa: E402
import isd  # noqa: E402

RAW = ROOT / "data" / "raw" / "isd"
OUT = ROOT / "results"
YEARS = range(2014, 2026)
START, END = "2014-11-01", "2025-03-31 23:00"
COUNTIES = {  # county: (station ICAO, ISD file stem)
    "Erie": ("KBUF", "725280-14733"),
    "St. Lawrence": ("KMSS", "726223-94725"),
    "New York": ("KNYC", "725053-94728"),
}
CASES = ["cc", "cc_full", "neep", "lockout", "cc_hold"]
CALENDARS = {"school": True, "all_weekdays": False}
XS = [0.1, 0.2, 0.3, 0.4]


def load_temps() -> dict[str, pd.Series]:
    out = {}
    for county, (icao, stem) in COUNTIES.items():
        s = isd.to_local_standard(isd.station_hourly(RAW, stem, YEARS))
        out[county] = s.loc[START:END]
    return out


def data_check(temps) -> pd.DataFrame:
    rows = []
    for county, t in temps.items():
        w = t[np.isin(t.index.month, fleet.WINTER)]
        occ = w[fleet.occupied_mask(w.index)]
        lab = fleet.winter_label(w.index)
        mins = w.groupby(lab).min()
        rows.append({"county": county, "station": COUNTIES[county][0],
                     "winter_hours": len(w),
                     "missing_pct": round(100 * w.isna().mean(), 2),
                     "occupied_missing_pct": round(100 * occ.isna().mean(), 2),
                     "t_design_c_p1": round(float(np.nanpercentile(w, 1)), 1),
                     "t_min_c": float(w.min()), "winter_of_min":
                     mins.idxmin(), "min_by_winter": mins.round(1).to_dict()})
    return pd.DataFrame(rows)


def fleet_series(temps, sig, t_des) -> dict:
    """{(county, case): DataFrame of occupied-hour MW, all school types}"""
    res = {}
    for county, t in temps.items():
      w0 = t[np.isin(t.index.month, fleet.WINTER)].dropna()
      for cal, flag in CALENDARS.items():
        w = w0[fleet.occupied_mask(w0.index, calendar=flag)]
        for case in CASES:
            tot = None
            for _, s in sig[sig.county == county].iterrows():
                d = fleet.heating_split(w, s.floor_area_ft2,
                                        s.occ_slope_w_ft2_k / 1.0,
                                        s.occ_t_bal_c, t_des[county], case)
                d = d.drop(columns="t_c")
                tot = d if tot is None else tot + d
            tot["t_c"] = w.values
            res[(county, case, cal)] = tot
    return res


def peak_table(series, sig, t_des) -> pd.DataFrame:
    rows = []
    for (county, case, cal), d in series.items():
        area = sig[sig.county == county].floor_area_ft2.sum()
        lab = fleet.winter_label(d.index)
        wpk = d.p_el.groupby(lab).max()
        i = d.p_el.idxmax()
        rows.append({
            "county": county, "case": case, "calendar": cal,
            "occupied_hours": len(d), "area_mft2": area / 1e6,
            "t_design_c": t_des[county],
            "peak_mw": d.p_el.max(), "peak_w_ft2": d.p_el.max() / area * 1e6,
            "peak_time": str(i), "t_at_peak_c": d.t_c[i],
            "resistance_share_at_peak": d.res_el[i] / d.p_el[i],
            "median_winter_peak_mw": float(wpk.median()),
            "min_winter_peak_mw": float(wpk.min()),
            "mean_occupied_mw": d.p_el.mean(),
            "peak_over_mean": d.p_el.max() / d.p_el.mean(),
            "winter_peaks_mw": wpk.round(2).to_dict()})
    return pd.DataFrame(rows)


def storage_table(series, sig) -> pd.DataFrame:
    rows = []
    for (county, case, cal), d in series.items():
        area = sig[sig.county == county].floor_area_ft2.sum()
        for x in XS:
            r = fleet.cap_storage(d.p_el, x)
            r.update({"county": county, "case": case, "calendar": cal,
                      "nameplate_kwh_per_kft2": r["nameplate_mwh"] / area
                      * 1e6})
            rows.append(r)
    return pd.DataFrame(rows)


def main() -> None:
    (OUT / "tables").mkdir(parents=True, exist_ok=True)
    sig = pd.read_csv(ROOT / "vendor" / "comstock_heating_signature.csv")
    temps = load_temps()
    chk = data_check(temps)
    chk.to_csv(OUT / "tables" / "data_check.csv", index=False)
    print(chk.drop(columns="min_by_winter").to_string(index=False))
    t_des = dict(zip(chk.county, chk.t_design_c_p1))
    series = fleet_series(temps, sig, t_des)
    pk = peak_table(series, sig, t_des)
    pk.to_csv(OUT / "tables" / "peaks.csv", index=False)
    st = storage_table(series, sig)
    st.to_csv(OUT / "tables" / "storage.csv", index=False)
    pd.to_pickle({"series": series, "temps": temps, "t_des": t_des},
                 OUT / "series.pkl")
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(pk.drop(columns="winter_peaks_mw").round(3).to_string(index=False))
        print(st.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
