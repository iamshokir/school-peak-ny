"""Item 2: results reproduce, units are right, headline numbers are pinned.
Needs results/ from scripts/run_all.py (skips if absent)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import fleet  # noqa: E402

T = ROOT / "results" / "tables"
PKL = ROOT / "results" / "series.pkl"
need = pytest.mark.skipif(not PKL.exists(), reason="run scripts/run_all.py")
SIG = pd.read_csv(ROOT / "vendor" / "comstock_heating_signature.csv")


def test_unit_conversion():
    # 1 m2 = 10.7639 ft2 exactly enough: (0.3048 m)^2
    assert 1 / 0.3048 ** 2 == pytest.approx(10.7639, abs=1e-4)


@need
def test_headline_peaks_pinned():
    pk = pd.read_csv(T / "peaks.csv")
    s = pk[(pk.case == "cc") & (pk.calendar == "school")].set_index("county")
    assert s.loc["New York", "peak_mw"] == pytest.approx(322.27, abs=0.01)
    assert s.loc["Erie", "peak_mw"] == pytest.approx(391.62, abs=0.01)
    assert s.loc["St. Lawrence", "peak_mw"] == pytest.approx(49.21, abs=0.01)


@need
def test_erie_peak_by_hand():
    """Independent re-derivation of the Erie CC peak from eqs (1)-(3)."""
    pk = pd.read_csv(T / "peaks.csv")
    r = pk[(pk.county == "Erie") & (pk.case == "cc")
           & (pk.calendar == "school")].iloc[0]
    t, td = r.t_at_peak_c, r.t_design_c
    s = SIG[SIG.county == "Erie"]
    a_s = (s.floor_area_ft2 * s.occ_slope_w_ft2_k).sum() / 1e6     # MW/K
    f = (t + 26.1) / (26.1 - 15.0)
    k, cop = 0.507 + f * (0.688 - 0.507), 1.49 + f * (1.98 - 1.49)
    q, h = a_s * (15.5 - t), a_s * (15.5 - td)
    g = min(q, k * h)
    assert g / cop + q - g == pytest.approx(r.peak_mw, rel=1e-6)


@need
def test_peaks_per_area_consistent():
    pk = pd.read_csv(T / "peaks.csv")
    area = SIG.groupby("county").floor_area_ft2.sum()
    for _, r in pk.iterrows():
        assert r.peak_w_ft2 == pytest.approx(r.peak_mw * 1e6
                                             / area[r.county], rel=1e-9)


@need
def test_storage_identities():
    st = pd.read_csv(T / "storage.csv")
    assert np.allclose(st.power_mw, st.x * (st.cap_mw / (1 - st.x)))
    assert np.allclose(st.nameplate_mwh, st.usable_mwh
                       / (fleet.ETA_D * fleet.USABLE))
    assert np.allclose(st.duration_h, st.nameplate_mwh / st.power_mw)


@need
def test_case_ordering():
    """Physical ordering: CC-full <= CC <= NEEP and CC <= Lockout."""
    pk = pd.read_csv(T / "peaks.csv")
    for (c, cal), g in pk.groupby(["county", "calendar"]):
        v = g.set_index("case").peak_mw
        assert v["cc_full"] <= v["cc"] + 1e-9 <= v["neep"] + 2e-9
        assert v["cc"] <= v["lockout"] + 1e-9
        assert v["cc_hold"] <= v["cc"] + 1e-9


@need
def test_rerun_reproduces_table():
    d = pd.read_pickle(PKL)
    pk = pd.read_csv(T / "peaks.csv")
    for (county, case, cal), s in d["series"].items():
        r = pk[(pk.county == county) & (pk.case == case)
               & (pk.calendar == cal)].iloc[0]
        assert s.p_el.max() == pytest.approx(r.peak_mw, rel=1e-12)
