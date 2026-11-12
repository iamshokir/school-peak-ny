"""Hourly air temperature from NOAA ISD fixed-width files (.gz).

Field positions (1-based, ISD format document, NCEI): date 16-23
(YYYYMMDD), time 24-27 (HHMM, UTC), report type 42-46, air temperature
88-92 (signed, degC x10; +9999 = missing), its quality code 93.

Stated choices:
  - quality codes kept: 0, 1, 4, 5, 9 (passed / not checked);
    2, 3, 6, 7 (suspect or erroneous) are dropped;
  - every report in a UTC hour is averaged to one hourly value
    (routine and special reports alike);
  - gaps of up to 3 h are filled by linear interpolation, longer gaps
    stay missing.
"""
from __future__ import annotations

import gzip
from pathlib import Path

import numpy as np
import pandas as pd

GOOD_Q = set("01459")


def parse_lines(lines) -> pd.Series:
    t, v = [], []
    for ln in lines:
        if len(ln) < 93:
            continue
        raw = ln[87:92]
        if raw == "+9999" or ln[92] not in GOOD_Q:
            continue
        t.append(ln[15:27])
        v.append(int(raw) / 10.0)
    idx = pd.to_datetime(pd.Series(t), format="%Y%m%d%H%M", utc=True)
    return pd.Series(v, index=pd.DatetimeIndex(idx), name="t_c").sort_index()


def read_file(path: Path) -> pd.Series:
    with gzip.open(path, "rt", encoding="ascii", errors="replace") as f:
        return parse_lines(f)


def hourly(obs: pd.Series, max_gap_h: int = 3) -> pd.Series:
    h = obs.groupby(obs.index.floor("h")).mean()
    full = pd.date_range(h.index.min(), h.index.max(), freq="h", tz="UTC")
    h = h.reindex(full)
    miss = h.isna()
    run_id = (~miss).cumsum()
    run_len = miss.groupby(run_id).transform("sum")
    filled = h.interpolate(limit_area="inside")
    return filled.where(~(miss & (run_len > max_gap_h)))


def station_hourly(folder: Path, station: str, years) -> pd.Series:
    parts = [read_file(folder / f"{station}-{y}.gz") for y in years]
    obs = pd.concat(parts)
    obs = obs[~obs.index.duplicated()]
    return hourly(obs)


def to_local_standard(s: pd.Series) -> pd.Series:
    """UTC -> local standard time (UTC-5, no daylight saving), naive."""
    out = s.copy()
    out.index = (s.index - pd.Timedelta(hours=5)).tz_localize(None)
    return out
