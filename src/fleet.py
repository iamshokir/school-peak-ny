"""County school fleet: electric heating demand if all school heating is
served by air-source heat pumps with resistance backup, and the battery
needed to cap its peak.

Method (stated):
  1. Thermal demand of the county's ComStock school stock in occupied
     hours: Q = A * s * max(0, T_bal - T_out) (vendor/load_remap.py,
     signature from ComStock 2025 R3 upgrade 27, occupied hours).
  2. Heat pumps sized to the thermal demand at the design temperature
     T_des (1st percentile of winter hourly station temperature over the
     study period - same rule as the companion sizing study);
     capacity derates with temperature; the rest is resistance (COP 1).
  3. Three heat-pump cases: 'cc' cold-climate curve (load_remap.CC_CURVE);
     'neep' the same curve scaled so COP(-15 C) = 1.75 (NEEP v4 floor);
     'lockout' the cc curve above -17.8 C and resistance only below
     (ComStock standard HP RTU lockout at 0 F); 'cc_full' the cc curve
     with nominal capacity raised so that the derated capacity at T_des
     equals the design demand (in the other cases nominal = design
     demand, the companion study's rule).
  4. Peak capping: cap = (1 - x) * P_max, P_max the highest occupied-hour
     demand over all winters. Battery power = x * P_max; usable energy =
     the largest single-day sum of demand above the cap; nameplate =
     usable / (eta_d * usable_fraction). Recharge assumed in the 16
     unoccupied hours that follow.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
import load_remap as lr  # noqa: E402

NEEP_SCALE = 1.75 / 1.98
LOCKOUT_C = -17.8
WINTER = [1, 2, 3, 11, 12]
ETA_RT = 0.85                  # NREL ATB 2024b round trip
ETA_D = ETA_RT ** 0.5
USABLE = 0.90                  # SOC 10-100 %


def curve(case: str) -> dict:
    if case == "neep":
        return {t: (c * NEEP_SCALE, k) for t, (c, k) in lr.CC_CURVE.items()}
    return lr.CC_CURVE


def closed_days(idx: pd.DatetimeIndex) -> np.ndarray:
    """Approximate New York school closures (stated, not district-exact):
    US federal holidays, 24 Dec-1 Jan, and the Monday-Friday week of
    Presidents' Day (mid-winter recess; e.g. NYC 16-20 Feb 2015)."""
    from pandas.tseries.holiday import USFederalHolidayCalendar
    d = idx.normalize()
    hol = USFederalHolidayCalendar().holidays(d.min(), d.max())
    xmas = ((idx.month == 12) & (idx.day >= 24)) | ((idx.month == 1)
                                                    & (idx.day == 1))
    pres = hol[(hol.month == 2) & (hol.dayofweek == 0)]
    recess = np.zeros(len(idx), dtype=bool)
    for p in pres:
        recess |= (d >= p) & (d <= p + pd.Timedelta(days=4))
    return np.asarray(d.isin(hol)) | np.asarray(xmas) | recess


def federal_holidays(idx: pd.DatetimeIndex) -> np.ndarray:
    from pandas.tseries.holiday import USFederalHolidayCalendar
    d = idx.normalize()
    hol = USFederalHolidayCalendar().holidays(d.min(), d.max())
    return np.asarray(d.isin(hol))


def occupied_mask(idx: pd.DatetimeIndex, calendar=True) -> np.ndarray:
    """calendar=True: school calendar (closed_days); "holidays": federal
    holidays only removed (recess weeks and winter break counted as
    school days); False: every weekday."""
    m = (np.isin(idx.month, WINTER) & (idx.dayofweek < 5)
         & (idx.hour >= 8) & (idx.hour <= 15))
    if calendar == "holidays":
        return m & ~federal_holidays(idx)
    return m & ~closed_days(idx) if calendar else m


def winter_label(idx: pd.DatetimeIndex) -> np.ndarray:
    y = np.where(idx.month >= 11, idx.year, idx.year - 1)
    return np.array([f"{a}/{str(a + 1)[2:]}" for a in y])


def heating_split(t_out: pd.Series, area_ft2: float, slope_w_ft2_k: float,
                  t_bal: float, t_des: float, case: str,
                  load_factor: float = 1.0, dtbal: float = 0.0,
                  cop_factor: float = 1.0, cap_factor: float = 1.0,
                  boost8: float = 0.0) -> pd.DataFrame:
    """Thermal demand, heat-pump electric and resistance electric, MW.

    Sensitivity arguments (defaults = main case). The heat pump is always
    sized on the base signature, so they act as errors in the load the
    units were sized for: load_factor scales the true thermal demand;
    dtbal shifts the true balance temperature (K); cop_factor and
    cap_factor scale the COP and capacity curves; boost8 adds a morning
    warm-up of boost8 x the 08:00 demand at 08:00 (stated assumption,
    not a measurement)."""
    sig = {"slope_kw_per_k": slope_w_ft2_k * area_ft2 / 1e6, "t_bal_c": t_bal}
    true = {"slope_kw_per_k": sig["slope_kw_per_k"] * load_factor,
            "t_bal_c": t_bal + dtbal}
    q = lr.shelter_heat(t_out, true, 1.0)                    # MW thermal
    if boost8:
        q = q * np.where(t_out.index.hour == 8, 1.0 + boost8, 1.0)
    hp_th_nom = sig["slope_kw_per_k"] * max(0.0, t_bal - t_des)
    if case == "cc_full":       # derated capacity at T_des meets demand
        k_des = lr.cop_curve(pd.Series([t_des]), curve(case))["cap_frac"][0]
        hp_th_nom = hp_th_nom / k_des
    cc = lr.cop_curve(t_out, curve(case))
    cop, cap = cc["cop"].values.copy(), cc["cap_frac"].values.copy()
    if case == "lockout":
        off = t_out.values < LOCKOUT_C
        cop[off], cap[off] = 0.0, 0.0
    if case == "cc_hold":       # bound: coldest point held below -26.1 C
        t0 = min(lr.CC_CURVE)
        low = t_out.values < t0
        cop[low], cap[low] = lr.CC_CURVE[t0]
    cop, cap = cop * cop_factor, cap * cap_factor
    hp_th = np.minimum(q.values, hp_th_nom * cap)
    with np.errstate(divide="ignore", invalid="ignore"):
        hp_el = np.where(hp_th > 0, hp_th / cop, 0.0)
    res_el = q.values - hp_th
    return pd.DataFrame({"t_c": t_out.values, "q_th": q.values,
                         "hp_el": hp_el, "res_el": res_el,
                         "p_el": hp_el + res_el}, index=t_out.index)


def cap_storage(p: pd.Series, x: float, p_max: float | None = None) -> dict:
    """Battery to hold occupied-hour demand p (MW, hourly) at (1-x)*p_max."""
    p_max = float(p.max()) if p_max is None else p_max
    cap = (1.0 - x) * p_max
    over = (p - cap).clip(lower=0.0)
    daily = over.groupby(over.index.date).sum()              # MWh
    e_use = float(daily.max())
    return {"x": x, "cap_mw": cap, "power_mw": x * p_max,
            "usable_mwh": e_use,
            "nameplate_mwh": e_use / (ETA_D * USABLE),
            "duration_h": e_use / (ETA_D * USABLE) / (x * p_max) if x > 0
            else np.nan,
            "hours_over": int((over > 0).sum()),
            "days_over": int((daily > 0).sum()),
            "recharge_mw_16h": e_use / ETA_D / ETA_RT ** 0.5 / 16.0}


def simulate_soc(p_occ: pd.Series, all_hours: pd.DatetimeIndex, x: float,
                 nameplate_mwh: float, charge_frac: float = 1.0,
                 p_max: float | None = None) -> dict:
    """Hourly state of charge over every winter hour. Occupied hours:
    discharge max(0, P_t - cap) up to the power rating xP_max. Other hours
    (nights, weekends, holidays): recharge at up to charge_frac x power
    rating. Starts full. Returns the energy the battery failed to deliver
    (MWh) and the lowest state of charge."""
    p_max = float(p_occ.max()) if p_max is None else p_max
    cap, pw = (1.0 - x) * p_max, x * p_max
    e_max = USABLE * nameplate_mwh
    occ = pd.Series(p_occ, index=p_occ.index).reindex(all_hours)
    soc, short, low = e_max, 0.0, e_max
    for v in occ.values:
        if not np.isnan(v):
            need = min(max(0.0, v - cap), pw)
            short += max(0.0, v - cap) - need
            take = min(need / ETA_D, soc)
            short += need - take * ETA_D
            soc -= take
        else:
            soc = min(e_max, soc + charge_frac * pw * ETA_D)
        low = min(low, soc)
    return {"shortfall_mwh": short, "min_soc_frac": low / e_max}


def min_nameplate(p_occ, all_hours, x, charge_frac=1.0, tol=0.01) -> float:
    """Smallest nameplate (MWh) with zero shortfall, by bisection."""
    lo, hi = 0.0, 1.0
    while simulate_soc(p_occ, all_hours, x, hi, charge_frac)[
            "shortfall_mwh"] > 1e-6:
        hi *= 2
    while hi - lo > tol * hi:
        mid = (lo + hi) / 2
        if simulate_soc(p_occ, all_hours, x, mid, charge_frac)[
                "shortfall_mwh"] > 1e-6:
            lo = mid
        else:
            hi = mid
    return hi
