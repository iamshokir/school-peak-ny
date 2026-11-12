# Copied unchanged from iamshokir/school-shelter-ny@23d8d0b2c5573f04684e1565da494a51c72232e3, src/load_remap.py (2026-11-11).
"""Stage 4: carry ComStock school heating onto other weather (decision Q4a).

ComStock profiles are simulated on 2018 weather only; the design event is
December 2022. Q4a: take ComStock's dependence of heating demand on
outdoor temperature and apply it to station temperature of another
period. Method (docs/model-spec.md section 5, stated here):

1. Heating signature. Over occupied hours, hourly heating demand Q (kW,
   thermal: ComStock upgrade 27 "ideal thermal air loads", or fuel use x
   efficiency) is fitted as Q = s * max(0, T_bal - T_out): a one-slope
   change-point model; T_bal is chosen on a 0.5 degC grid by least
   squares, s by least squares given T_bal.
2. Shelter heat demand for any temperature series:
   Q_shelter = f_zone * s * max(0, T_bal + dT_set - T_out), with
   f_zone = shelter-zone floor share (Q1) and dT_set = shelter set point
   minus ComStock's occupied set point (both inputs, sourced in
   docs/assumptions.md).
3. Electric heating = Q_shelter / COP(T_out) up to capacity, resistance
   (COP 1) for the rest (cold-climate curve, docs/assumptions.md).

The signature ignores solar and occupant gains varying by hour; the fit's
R^2 is returned so the loss is reported, not hidden.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def fit_signature(q_kw: pd.Series, t_out: pd.Series,
                  occupied: pd.Series | None = None,
                  grid=np.arange(5.0, 25.01, 0.5)) -> dict:
    """Return {'slope_kw_per_k', 't_bal_c', 'r2', 'n'} of the change-point
    fit over occupied hours (all hours if occupied is None)."""
    d = pd.DataFrame({"q": q_kw, "t": t_out}).dropna()
    if occupied is not None:
        d = d[occupied.reindex(d.index).fillna(False).astype(bool)]
    if len(d) < 10:
        raise ValueError("too few hours to fit")
    best = None
    for tb in grid:
        x = np.maximum(0.0, tb - d["t"].values)
        xx = float(x @ x)
        if xx == 0:
            continue
        s = float(x @ d["q"].values) / xx
        sse = float(((d["q"].values - s * x) ** 2).sum())
        if best is None or sse < best[0]:
            best = (sse, tb, s)
    sse, tb, s = best
    sst = float(((d["q"] - d["q"].mean()) ** 2).sum())
    return {"slope_kw_per_k": s, "t_bal_c": float(tb),
            "r2": 1 - sse / sst if sst > 0 else float("nan"), "n": len(d)}


def shelter_heat(t_out: pd.Series, sig: dict, f_zone: float,
                 dt_set: float = 0.0) -> pd.Series:
    """Thermal heat demand (kW) of the shelter zone at the shelter set
    point, for any temperature series."""
    if not 0 < f_zone <= 1:
        raise ValueError("f_zone must be in (0, 1]")
    q = f_zone * sig["slope_kw_per_k"] * np.maximum(
        0.0, sig["t_bal_c"] + dt_set - t_out)
    return pd.Series(q, index=t_out.index, name="q_heat_kw")


def cop_curve(t_out: pd.Series, points: dict[float, tuple[float, float]]
              ) -> pd.DataFrame:
    """COP and capacity fraction by linear interpolation between
    {temp_c: (cop, capacity_fraction)}; held flat above the warmest point;
    below the coldest point the heat pump is off (COP 0, capacity 0) so
    resistance takes all the load."""
    ts = np.array(sorted(points))
    cop = np.array([points[t][0] for t in ts])
    cap = np.array([points[t][1] for t in ts])
    t = t_out.values
    c = np.interp(t, ts, cop)
    k = np.interp(t, ts, cap)
    off = t < ts[0]
    c[off], k[off] = 0.0, 0.0
    return pd.DataFrame({"cop": c, "cap_frac": k}, index=t_out.index)


def electric_heating(q_heat: pd.Series, t_out: pd.Series, hp_kw_th: float,
                     points: dict[float, tuple[float, float]]) -> pd.Series:
    """Electric kW to meet q_heat with a heat pump of nominal thermal size
    hp_kw_th (capacity derated by the curve) plus resistance backup."""
    cc = cop_curve(t_out, points)
    hp_th = np.minimum(q_heat.values, hp_kw_th * cc["cap_frac"].values)
    with np.errstate(divide="ignore", invalid="ignore"):
        hp_el = np.where(hp_th > 0, hp_th / cc["cop"].values, 0.0)
    resist_el = q_heat.values - hp_th
    return pd.Series(hp_el + resist_el, index=q_heat.index,
                     name="p_heat_kw")


# Cold-climate curve, docs/assumptions.md (ResStock example values;
# candidate). Keys degC; values (COP, capacity fraction of nominal).
CC_CURVE = {
    -26.1: (1.49, 0.507),
    -15.0: (1.98, 0.688),
    -8.3: (2.33, 0.766),
    8.3: (3.37, 1.028),
}
