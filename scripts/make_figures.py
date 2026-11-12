"""Figures for the PES GM paper from results/ (run scripts/run_all.py first)."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import fleet  # noqa: E402

FIG = ROOT / "results" / "figures"
COL = {"cc": "#2a78d6", "cc_full": "#1baf7a", "neep": "#eda100",
       "lockout": "#eb6834", "cc_hold": "#2a78d6"}
LS = {"cc": "-", "cc_full": "--", "neep": "-.", "lockout": ":",
      "cc_hold": (0, (1, 1))}
NAME = {"cc": "Cold-climate HP, nominal = design load",
        "cc_full": "Cold-climate HP, sized for design temp.",
        "neep": "NEEP-floor COP",
        "lockout": "Lockout below -17.8 °C",
        "cc_hold": "HP kept on below -26 °C"}
COUNTY_COL = {"Erie": "#2a78d6", "St. Lawrence": "#eb6834",
              "New York": "#1baf7a"}
COUNTY_MK = {"Erie": "o", "St. Lawrence": "s", "New York": "^"}
plt.rcParams.update({"font.size": 7, "font.family": "serif",
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.linewidth": 0.6, "xtick.major.width": 0.6,
                     "ytick.major.width": 0.6, "axes.grid": True,
                     "grid.color": "#e4e4e0", "grid.linewidth": 0.5})


def fig1(sig, t_des, temps):
    fig, axes = plt.subplots(1, 3, figsize=(3.5, 2.35), sharey=True)
    tg = pd.Series(np.arange(-34.0, 16.01, 0.1))
    for ax, county in zip(axes, ["New York", "Erie", "St. Lawrence"]):
        rows = sig[sig.county == county]
        area = rows.floor_area_ft2.sum()
        for case in ["cc", "cc_full", "neep", "lockout", "cc_hold"]:
            p = sum(fleet.heating_split(tg, r.floor_area_ft2,
                                        r.occ_slope_w_ft2_k, r.occ_t_bal_c,
                                        t_des[county], case).p_el.values
                    for _, r in rows.iterrows()) / area * 1e6
            if case == "cc_hold":
                m = tg.values <= -26.1
                ax.plot(tg[m], p[m], color=COL[case], ls=LS[case], lw=1.0,
                        label=NAME[case])
            else:
                ax.plot(tg, p, color=COL[case], ls=LS[case], lw=1.2,
                        label=NAME[case])
        t = temps[county]
        w = t[np.isin(t.index.month, fleet.WINTER)].dropna()
        tmin = float(w[fleet.occupied_mask(w.index)].min())
        ax.axvline(t_des[county], color="#6b6b66", lw=0.6)
        ax.axvspan(-34, tmin, color="#f0efec", lw=0)
        ax.text(t_des[county] + 0.8, 25.2, "design", rotation=90,
                va="top", fontsize=6, color="#4a4a46")
        ax.set_title(county, fontsize=7)
        ax.set_xlim(-34, 16)
        ax.set_xticks([-30, -15, 0, 15])
    axes[0].set_ylabel("Added electric demand (W/ft²)")
    axes[1].set_xlabel("Outdoor temperature (°C)")
    axes[0].set_ylim(0, 26)
    h, l = axes[2].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=2, fontsize=5.6, frameon=False,
               handlelength=2.6, bbox_to_anchor=(0.5, -0.01))
    fig.tight_layout(rect=(0, 0.17, 1, 1), w_pad=0.4)
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"Fig1_demand_vs_temperature.{ext}", dpi=600)
    plt.close(fig)


def fig2(pk):
    fig, ax = plt.subplots(figsize=(3.5, 2.0))
    main = pk[(pk.case == "cc") & (pk.calendar == "school")]
    lo = pk[(pk.case == "cc_full") & (pk.calendar == "school")]
    hi = pk[(pk.case == "lockout") & (pk.calendar == "school")]
    off = {"New York": -0.22, "Erie": 0.0, "St. Lawrence": 0.22}
    for county in ["New York", "Erie", "St. Lawrence"]:
        r = main[main.county == county].iloc[0]
        area = r.area_mft2
        w = eval(r.winter_peaks_mw)          # dict written by run_all.py
        wl = eval(lo[lo.county == county].iloc[0].winter_peaks_mw)
        wh = eval(hi[hi.county == county].iloc[0].winter_peaks_mw)
        keys = sorted(w)
        x = np.arange(len(keys)) + off[county]
        y = np.array([w[k] for k in keys]) / area
        ax.vlines(x, [wl[k] / area for k in keys],
                  [wh[k] / area for k in keys], color=COUNTY_COL[county],
                  lw=0.9, alpha=0.6)
        ax.plot(x, y, ls="none", marker=COUNTY_MK[county], ms=3.4,
                color=COUNTY_COL[county], mec="white", mew=0.5, label=county)
    ax.set_xticks(np.arange(len(keys)))
    ax.set_xticklabels([k[2:] for k in keys], rotation=45, fontsize=6)
    ax.set_xlabel("Winter")
    ax.set_ylabel("Winter peak (W/ft²)")
    ax.set_ylim(0, 20)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), fontsize=6,
              frameon=False, ncol=3, handletextpad=0.2, columnspacing=0.8)
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(FIG / f"Fig2_winter_peaks.{ext}", dpi=600)
    plt.close(fig)


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    sig = pd.read_csv(ROOT / "vendor" / "comstock_heating_signature.csv")
    d = pd.read_pickle(ROOT / "results" / "series.pkl")
    pk = pd.read_csv(ROOT / "results" / "tables" / "peaks.csv")
    fig1(sig, d["t_des"], d["temps"])
    fig2(pk)


if __name__ == "__main__":
    main()
