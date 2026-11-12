"""Every number quoted in the paper, read from results/ (no hand-typed
results). Used by build_paper.py; `python paper/paper_numbers.py` prints all."""
from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "results" / "tables"
FT2_PER_M2 = 10.7639          # 1 m2 = 10.7639 ft2 (W/ft2 -> W/m2)
SHORT = {"New York": "ny", "Erie": "er", "St. Lawrence": "sl"}


def f(x, d=1):
    s = f"{x:.{d}f}"
    return s


def load() -> dict:
    pk = pd.read_csv(T / "peaks.csv")
    st = pd.read_csv(T / "storage.csv")
    ck = pd.read_csv(T / "data_check.csv")
    sig = pd.read_csv(ROOT / "vendor" / "comstock_heating_signature.csv")
    N = {}
    sch = pk[pk.calendar == "school"]
    for county, k in SHORT.items():
        c = ck[ck.county == county].iloc[0]
        N[f"{k}_tdes"] = f(c.t_design_c_p1)
        N[f"{k}_miss"] = f(c.occupied_missing_pct, 2)
        N[f"{k}_tmin"] = f(c.t_min_c)
        for case in ["cc", "cc_full", "neep", "lockout", "cc_hold"]:
            r = sch[(sch.county == county) & (sch.case == case)].iloc[0]
            N[f"{k}_{case}_mw"] = f(r.peak_mw, 0)
            N[f"{k}_{case}_wft2"] = f(r.peak_w_ft2)
            N[f"{k}_{case}_wm2"] = f(r.peak_w_ft2 * FT2_PER_M2, 0)
            N[f"{k}_{case}_res"] = f(100 * r.resistance_share_at_peak, 0)
            N[f"{k}_{case}_maxmed"] = f(r.peak_mw / r.median_winter_peak_mw, 2)
            N[f"{k}_{case}_maxmin"] = f(r.peak_mw / r.min_winter_peak_mw, 2)
            N[f"{k}_{case}_pm"] = f(r.peak_over_mean)
            if case == "cc":
                N[f"{k}_area"] = f(r.area_mft2)
                N[f"{k}_area_mm2"] = f(r.area_mft2 / FT2_PER_M2, 2)
                N[f"{k}_tpk"] = f(r.t_at_peak_c)
                N[f"{k}_pkdate"] = pd.Timestamp(r.peak_time).strftime(
                    "%-d %B %Y")
                N[f"{k}_med_mw"] = f(r.median_winter_peak_mw, 0)
                w = ast.literal_eval(r.winter_peaks_mw)
                N[f"{k}_wmin_wft2"] = f(min(w.values()) / r.area_mft2)
                N[f"{k}_wmax_wft2"] = f(max(w.values()) / r.area_mft2)
                N[f"{k}_wmin_wm2"] = f(min(w.values()) / r.area_mft2
                                       * FT2_PER_M2, 0)
                N[f"{k}_wmax_wm2"] = f(max(w.values()) / r.area_mft2
                                       * FT2_PER_M2, 0)
                N[f"{k}_hours"] = f"{int(r.occupied_hours):,}"
        aw = pk[(pk.calendar == "no_recess") & (pk.county == county)
                & (pk.case == "cc")].iloc[0]
        N[f"{k}_allwk_mw"] = f(aw.peak_mw, 0)
        N[f"{k}_allwk_date"] = pd.Timestamp(aw.peak_time).strftime("%-d %B %Y")
        N[f"{k}_allwk_t"] = f(aw.t_at_peak_c)
        N[f"{k}_allwk_pct"] = f(100 * (aw.peak_mw / float(
            sch[(sch.county == county) & (sch.case == "cc")].peak_mw.iloc[0])
            - 1), 0)
        for case in ["cc", "cc_full", "lockout"]:
            for x in [0.1, 0.2, 0.3, 0.4]:
                r = st[(st.county == county) & (st.case == case)
                       & (st.calendar == "school")
                       & np.isclose(st.x, x)].iloc[0]
                p = f"{k}_{case}_x{int(x * 100)}"
                N[p + "_mw"] = f(r.power_mw, 1)
                N[p + "_mwh"] = f(r.nameplate_mwh, 0)
                N[p + "_h"] = f(r.duration_h, 2)
                N[p + "_days"] = str(int(r.days_over))
                N[p + "_hrs"] = str(int(r.hours_over))
                N[p + "_kwhk"] = f(r.nameplate_kwh_per_kft2, 1)
                N[p + "_whm2"] = f(r.nameplate_kwh_per_kft2 * FT2_PER_M2, 0)
                N[p + "_rech"] = f(100 * r.recharge_mw_16h / r.cap_mw, 1)
    # marginal demand per degree (CC), W/ft2/K: mild (0 to -5 C) and
    # around the design temperature (T_des +5 to -5 C)
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    import fleet
    mild, cold = [], []
    for county, k in SHORT.items():
        rows = sig[sig.county == county]
        area = rows.floor_area_ft2.sum()
        td = float(ck[ck.county == county].t_design_c_p1.iloc[0])

        def P(t):
            s = pd.Series([float(t)])
            return sum(fleet.heating_split(s, r.floor_area_ft2,
                                           r.occ_slope_w_ft2_k, r.occ_t_bal_c,
                                           td, "cc").p_el.iloc[0]
                       for _, r in rows.iterrows()) / area * 1e6
        mild.append((P(-5) - P(0)) / 5)
        cold.append((P(td - 1) - P(td + 1)) / 2)    # local, at T_des
    mild = [m * FT2_PER_M2 for m in mild]
    cold = [c * FT2_PER_M2 for c in cold]
    N["slope_mild_lo"], N["slope_mild_hi"] = f(min(mild), 1), f(max(mild), 1)
    N["slope_cold_lo"], N["slope_cold_hi"] = f(min(cold), 1), f(max(cold), 1)
    ratio = [c / m for c, m in zip(cold, mild)]
    N["slope_ratio_lo"], N["slope_ratio_hi"] = f(min(ratio)), f(max(ratio))
    # item 1: neighbor-station check
    nb = pd.read_csv(T / "neighbor_check.csv")
    N["nb_p1_maxdiff"] = f((nb.p1_station_c - nb.p1_neighbor_c).abs().max())
    N["nb_corr_min"] = f(nb["corr"].min(), 3)
    N["nb_corr_max"] = f(nb["corr"].max(), 3)
    N["nb_mae_max"] = f(nb.mae_c.max())
    # items 3-5: warm-up, uncertainty, hourly SOC
    wu = pd.read_csv(T / "warmup.csv")
    un = pd.read_csv(T / "uncertainty.csv")
    sc = pd.read_csv(T / "soc_check.csv")
    for county, k in SHORT.items():
        for b in (0.15, 0.30, 0.50):
            r = wu[(wu.county == county) & (wu.case == "cc")
                   & np.isclose(wu.boost8, b)].iloc[0]
            N[f"{k}_wu{int(b * 100)}_pct"] = f(r.change_pct, 0)
            N[f"{k}_wu{int(b * 100)}_mw"] = f(r.peak_mw, 0)
            N[f"{k}_wu{int(b * 100)}_x20h"] = f(r.x20_duration_h, 2)
            N[f"{k}_wu{int(b * 100)}_maxmed"] = f(r.max_over_median, 2)
        for prm, v in [("load_factor", 0.8), ("load_factor", 1.2),
                       ("load_factor", 0.9), ("load_factor", 1.1),
                       ("dtbal", -2.0), ("dtbal", 2.0),
                       ("cop_factor", 0.9), ("cop_factor", 1.1),
                       ("cap_factor", 0.9), ("cap_factor", 1.1)]:
            r = un[(un.county == county) & (un.param == prm)
                   & np.isclose(un.value, v)].iloc[0]
            N[f"{k}_{prm}_{v}"] = f(r.change_pct, 0)
    wcc = wu[(wu.case == "cc") & (wu.boost8 > 0)]
    N["wu_maxmed_lo"] = f(wcc.max_over_median.min(), 2)
    N["wu_maxmed_hi"] = f(wcc.max_over_median.max(), 2)
    N["wu_x20h_max"] = f(wcc.x20_duration_h.max(), 2)
    rel = (sc["hourly_soc_mwh_charge1.0"] / sc.daily_method_mwh - 1) * 100
    N["soc_maxdiff_pct"] = f(rel.max(), 1)
    N["soc_charge_same"] = str(bool(np.allclose(
        sc["hourly_soc_mwh_charge1.0"], sc["hourly_soc_mwh_charge0.25"])))
    N["soc_daily_ok"] = str(bool(sc.daily_method_ok.all()))
    # external comparison: Shonder et al. (2000), ORNL/TM-2000/80
    N["ornl_wm2"] = f(255e3 / (69000 / FT2_PER_M2), 0)
    N["r2_lo"] = f(sig.occ_r2.min(), 2)
    N["r2_hi"] = f(sig.occ_r2.max(), 2)
    N["tbal_lo"] = f(sig.occ_t_bal_c.min())
    N["tbal_hi"] = f(sig.occ_t_bal_c.max())
    N["n_winters"] = "11"
    return N


if __name__ == "__main__":
    for k, v in load().items():
        print(f"{k:28s} {v}")
