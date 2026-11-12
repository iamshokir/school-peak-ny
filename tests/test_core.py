import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import fleet  # noqa: E402
import isd  # noqa: E402


def _line(date, hhmm, temp, q="1"):
    s = [" "] * 105
    s[15:23] = list(date)
    s[23:27] = list(hhmm)
    s[87:92] = list(temp)
    s[92] = q
    return "".join(s)


def test_isd_parse_and_quality():
    lines = [_line("20220101", "0051", "-0123"),
             _line("20220101", "0055", "-0103"),
             _line("20220101", "0151", "+9999"),
             _line("20220101", "0251", "+0050", q="3"),
             _line("20220101", "0351", "+0010")]
    obs = isd.parse_lines(lines)
    assert len(obs) == 3
    h = isd.hourly(obs)
    assert h.iloc[0] == pytest.approx(-11.3)            # mean of two reports
    assert h.iloc[3] == pytest.approx(1.0)
    assert h.iloc[1] == pytest.approx(-11.3 + (1.0 + 11.3) / 3)  # filled


def test_isd_gap_longer_than_limit_stays_missing():
    lines = [_line("20220101", "0000", "+0000"),
             _line("20220101", "0500", "+0050")]
    h = isd.hourly(isd.parse_lines(lines), max_gap_h=3)
    assert h.isna().sum() == 4


def test_local_standard_time():
    s = pd.Series([1.0], index=pd.DatetimeIndex(["2022-01-01 13:00"], tz="UTC"))
    assert isd.to_local_standard(s).index[0] == pd.Timestamp("2022-01-01 08:00")


def _t(vals):
    return pd.Series(vals, index=pd.date_range("2022-01-03 08:00",
                                               periods=len(vals), freq="h"))


def test_no_heat_above_balance_point():
    d = fleet.heating_split(_t([20.0, 16.0]), 1e6, 0.4, 15.5, -15.0, "cc")
    assert d.p_el.sum() == 0.0


def test_mild_weather_uses_heat_pump_cop():
    # 8.3 C: COP 3.37, capacity 1.028 of nominal; demand < capacity
    d = fleet.heating_split(_t([8.3]), 1e6, 0.4, 15.5, -15.0, "cc")
    q = 0.4 * 1e6 / 1e6 * (15.5 - 8.3)
    assert d.q_th.iloc[0] == pytest.approx(q)
    assert d.p_el.iloc[0] == pytest.approx(q / 3.37)
    assert d.res_el.iloc[0] == 0.0


def test_below_design_temperature_resistance_takes_rest():
    d = fleet.heating_split(_t([-20.0]), 1e6, 0.4, 15.5, -15.0, "cc")
    nom = 0.4 * (15.5 + 15.0)
    k = np.interp(-20.0, [-26.1, -15.0], [0.507, 0.688])
    c = np.interp(-20.0, [-26.1, -15.0], [1.49, 1.98])
    q = 0.4 * (15.5 + 20.0)
    assert d.res_el.iloc[0] == pytest.approx(q - nom * k)
    assert d.hp_el.iloc[0] == pytest.approx(nom * k / c)


def test_lockout_is_all_resistance_and_neep_is_higher():
    t = _t([-18.0, -5.0])
    lo = fleet.heating_split(t, 1e6, 0.4, 15.5, -15.0, "lockout")
    cc = fleet.heating_split(t, 1e6, 0.4, 15.5, -15.0, "cc")
    ne = fleet.heating_split(t, 1e6, 0.4, 15.5, -15.0, "neep")
    assert lo.p_el.iloc[0] == pytest.approx(lo.q_th.iloc[0])
    assert lo.p_el.iloc[1] == pytest.approx(cc.p_el.iloc[1])
    assert (ne.p_el > cc.p_el).all()


def test_cc_full_covers_design_demand_without_resistance():
    d = fleet.heating_split(_t([-15.0, -20.0]), 1e6, 0.4, 15.5, -15.0,
                            "cc_full")
    assert d.res_el.iloc[0] == pytest.approx(0.0, abs=1e-12)
    cc = fleet.heating_split(_t([-20.0]), 1e6, 0.4, 15.5, -15.0, "cc")
    assert d.p_el.iloc[1] < cc.p_el.iloc[0]


def test_cap_storage_known_answer():
    idx = pd.to_datetime(["2022-01-03 08:00", "2022-01-03 09:00",
                          "2022-01-04 08:00"])
    p = pd.Series([10.0, 8.0, 9.0], index=idx)
    r = fleet.cap_storage(p, 0.2)          # cap 8 MW
    assert r["cap_mw"] == pytest.approx(8.0)
    assert r["power_mw"] == pytest.approx(2.0)
    assert r["usable_mwh"] == pytest.approx(2.0)
    assert r["days_over"] == 2 and r["hours_over"] == 2
    assert r["nameplate_mwh"] == pytest.approx(2.0 / (0.85 ** 0.5 * 0.9))


def test_occupied_mask():
    idx = pd.to_datetime(["2022-01-03 08:00", "2022-01-03 16:00",
                          "2022-01-08 10:00", "2022-06-06 10:00"])
    assert list(fleet.occupied_mask(idx)) == [True, False, False, False]


def test_calendar_closures():
    idx = pd.to_datetime(["2015-02-16 08:00", "2015-02-20 08:00",
                          "2015-02-23 08:00", "2014-12-29 09:00",
                          "2015-01-19 09:00", "2015-01-20 09:00"])
    # Presidents' Day week, its Friday, next Monday, winter break, MLK day
    assert list(fleet.occupied_mask(idx)) == [False, False, True, False,
                                              False, True]
    assert fleet.occupied_mask(idx, calendar=False).all()
