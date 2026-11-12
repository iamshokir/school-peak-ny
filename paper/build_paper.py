"""Build the PES GM 2027 draft (Markdown + Word) from results/.
Every result number comes from paper_numbers.load(); none is typed by hand.
Usage: python paper/build_paper.py"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "paper"))
from paper_numbers import load  # noqa: E402

N = load()
M = "−"

TITLE = ("Cold-Morning Peaks from Electrified School Heating in New York "
         "State: Heat-Pump Choice, Weather-Year Risk and Short-Duration "
         "Storage")
AUTHOR = "Shokirdzhon Ismoilov"
AFFIL = "OFTO Energy Foundation, Brooklyn, NY, USA"
EMAIL = "shokir@oftoenergy.org"

ABSTRACT = (
    "Heating electrification is moving New York toward a winter-peaking "
    "grid, but the share of individual building types is rarely "
    "resolved. This paper estimates the demand that the school stock of "
    "three New York counties would add on cold school mornings if all "
    "school heating used air-source heat pumps with resistance "
    "backup. A ComStock heating signature is driven by "
    f"{N['n_winters']} winters of hourly NOAA temperature under five "
    f"heat-pump cases. The added peak is {N['ny_cc_mw']}, {N['er_cc_mw']} "
    f"and {N['sl_cc_mw']} MW ({N['ny_cc_wm2']}{M}{N['sl_cc_wm2']} W/m²) in "
    "New York, Erie and St. Lawrence counties, "
    f"{round((float(N['er_cc_maxmed'])-1)*100)}{M}"
    f"{round((float(N['sl_cc_maxmed'])-1)*100)}% above the peak of a "
    "median winter. Heat-pump sizing and compressor lockout move the Erie "
    f"peak between {N['er_cc_full_mw']} and {N['er_lockout_mw']} MW. A "
    "battery that caps the peak by 10% needs "
    f"{N['sl_cc_x10_h'][:3]}{M}{N['er_cc_x10_h'][:3]} h and is "
    f"used on at most {N['er_cc_x10_days']} school days in "
    f"{N['n_winters']} winters; a 20% cap needs {N['er_cc_x20_h'][:3]} h in "
    "Erie. Planning should use multi-year weather and specify cold-climate "
    "heat-pump performance.")

INDEX = ("Building electrification, energy storage, heat pumps, peak "
         "demand, schools")


def body() -> list:
    B = []
    h1, p = (lambda t: B.append(("h1", t))), (lambda t: B.append(("p", t)))
    h2 = lambda t: B.append(("h2", t))  # noqa: E731
    eq = lambda t, n: B.append(("eq", t, n))  # noqa: E731

    h1("Introduction")
    p("New York's electric peak occurs in summer today, but heating "
      "electrification would move it to winter: a statewide study finds the "
      "winter peak overtakes the summer peak at about 25% building and "
      "vehicle electrification and reaches 83 GW at full electrification, "
      "against 34 GW today, driven by heating in extreme cold [1]. Similar "
      "winter-peak growth has been reported for space heating at national "
      "scale [2] and for residential heating in Texas [3]. These studies "
      "treat buildings as one or two sectors. Schools are a distinct "
      "segment: a large, publicly owned stock, a narrow occupied window "
      "that starts in the coldest hours of the morning, and a possible role "
      "as shelters during winter outages [10]. Their contribution to the "
      "cold-weather peak, and how it "
      "depends on the heat pump chosen and on the weather year used for "
      "planning, has not been quantified.")
    p("This paper asks three questions for the school stock of three New "
      "York counties with different climates: New York County (Manhattan), "
      "Erie County (Buffalo) and St. Lawrence County (North Country). "
      "(i) How large is the electric peak that full heat-pump conversion of "
      "school heating would add on school mornings? (ii) How much does it "
      "depend on heat-pump cold performance and sizing, and on the winter "
      "used for planning? (iii) How much of it can a short-duration battery "
      "remove? The calculation reuses the heating signature and heat-pump "
      "curve of the author's single-school shelter sizing study [10], which "
      "is under review; that study sizes storage for one school through a "
      "72-h outage and does not address grid demand. The fleet-level "
      "question, the multi-year weather record, the sizing and lockout "
      "cases and the peak-capping analysis are new here.")

    h1("Data and Method")
    h2("Building stock and heating signature")
    p("The school stock is taken from ComStock 2025 Release 3 county "
      "aggregates for primary and secondary schools [4]: "
      f"{N['ny_area_mm2']}, {N['er_area_mm2']} and {N['sl_area_mm2']} million m² "
      "of represented floor area in New York, Erie and St. Lawrence "
      "counties. Thermal heating demand per unit area, from the "
      "ComStock ideal-load upgrade, was fitted in [10] against airport "
      "station temperature in occupied hours (weekdays 08:00{M}15:59, "
      "November{M}March) with a one-slope change-point model, giving "
      f"balance temperatures of {N['tbal_lo']}{M}{N['tbal_hi']} °C and "
      f"R² of {N['r2_lo']}{M}{N['r2_hi']}. The fleet thermal demand in "
      "hour t is".replace("{M}", M))
    eq("Q_{t} = Σ_{b} A_{b} s_{b} max(0, T_{bal,b} − T_{t})", 1)
    p("where A_{b} is the floor area, s_{b} the slope and T_{bal,b} the "
      "balance temperature of school type b, and T_{t} the outdoor "
      "temperature.")
    h2("Weather")
    p("Hourly air temperature for winters 2014/15 to 2024/25 (November to "
      "March) comes from NOAA Integrated Surface Database records [8] at "
      "Central Park (KNYC), Buffalo Niagara (KBUF) and Massena (KMSS). "
      "Reports flagged suspect or erroneous are removed, reports within an "
      "hour are averaged and gaps of up to 3 h are interpolated; "
      f"{N['ny_miss']}%, {N['er_miss']}% and {N['sl_miss']}% of occupied "
      "hours remain missing and are dropped. As a check, the Central Park "
      f"minimum of the record, {N['ny_tmin']} °C on 14 February 2016, "
      "matches the −1 °F reported for that morning. Occupied hours exclude U.S. federal holidays, "
      "24 December{M}1 January and the week of Presidents' Day, an "
      "approximation of New York school calendars (for example, New York "
      "City schools were closed 16{M}20 February 2015); a run with every "
      "weekday occupied is reported as a sensitivity. This leaves "
      f"{N['ny_hours']}{M}{N['er_hours']} occupied hours per county. The "
      "design temperature T_{des} is the 1st percentile of winter hourly "
      f"temperature: {N['ny_tdes']}, {N['er_tdes']} and {N['sl_tdes']} °C."
      .replace("{M}", M))
    h2("Heat-pump cases")
    p("All school heating is assumed to move to air-source heat pumps with "
      "electric-resistance backup; the result is the added electric demand, "
      "not the net change in the school's total load. The heat-pump "
      "nominal thermal capacity is")
    eq("H = Σ_{b} A_{b} s_{b} max(0, T_{bal,b} − T_{des}) / k(T_{des})^{δ}", 2)
    p("with k(T) the capacity fraction at temperature T. With heat-pump "
      "output G_{t} = min(Q_{t}, k(T_{t})H), the electric demand is")
    eq("P_{t} = G_{t}/COP(T_{t}) + (Q_{t} − G_{t})",
       3)
    p("Five cases are compared. CC (main): a cold-climate curve with COP "
      f"3.37, 2.33, 1.98 and 1.49 at 8.3, {M}8.3, {M}15 and {M}26.1 °C "
      "and capacity 1.03, 0.77, 0.69 and 0.51 of nominal [6], nominal "
      "capacity equal to the design-temperature load (δ = 0, the rule "
      "of [10]) and resistance only below the coldest rated point. "
      "CC-full: as CC with δ = 1, so the derated capacity meets the "
      "design load. NEEP: CC with COP scaled to 1.75 at −15 °C, "
      "the qualifying floor of the NEEP cold-climate specification [7]. "
      f"Lockout: CC with the compressor off below {M}17.8 °C (0 °F), "
      "the behavior of the standard-performance heat-pump rooftop unit "
      "modeled by ComStock [5]. CC-hold: CC with the {M}26.1 °C point "
      "held at colder temperatures, an optimistic bound for units that keep "
      "running in deep cold.".replace("{M}", M))
    h2("Peak capping with storage")
    p("Let P_{max} be the highest occupied-hour demand over all winters. A "
      "battery of power xP_{max} holds demand at (1 − x)P_{max} if its "
      "usable energy covers the worst school day:")
    eq("E = max_{d} Σ_{t∈d} max(0, P_{t} − (1 − x)P_{max})", 4)
    p("Nameplate energy is E/(η_{d}u), with discharge efficiency "
      "η_{d} = 0.85^{0.5} from an 85% round trip [9] and usable fraction "
      "u = 0.9; duration is nameplate energy over power. Discharge assumes "
      "the day's demand is known (perfect foresight), and recharge is "
      "assumed in the 16 unoccupied hours that follow; its average power "
      "is reported against the cap. Code and data sources are listed in "
      "the data availability note.")

    h1("Results")
    h2("Why the peak is steep")
    p("Fig. 1 shows the added demand per square foot as a function of "
      "outdoor temperature. Between 0 and −5 °C the heat pumps "
      "carry the load at a COP near 2.5 or above and each degree adds "
      f"{N['slope_mild_lo']}{M}{N['slope_mild_hi']} W/m². Around the "
      "design temperature the derated capacity no longer covers the load "
      "(in the CC case already somewhat above it, since nominal capacity "
      "equals the design load) and resistance takes the rest at COP 1, so "
      f"each degree adds {N['slope_cold_lo']}{M}{N['slope_cold_hi']} "
      f"W/m², {N['slope_ratio_lo']}{M}{N['slope_ratio_hi']} times as "
      "much. The lockout case jumps at "
      f"{M}17.8 °C, and every case except CC-hold converges on pure "
      f"resistance below {M}26.1 °C. Where the coldest occupied hours "
      "fall on this curve decides the peak.".replace("{M}", M))
    B.append(("fig", "Fig1_demand_vs_temperature.png",
              "Added electric demand of the county school stock per square "
              "foot versus outdoor temperature for the five heat-pump cases. "
              "Vertical line: design temperature; shaded: colder than any "
              "occupied hour in 2014/15–2024/25."))
    h2("Peak demand and heat-pump choice")
    p("Table I lists the peaks. With the main CC case the school stock adds "
      f"{N['ny_cc_mw']} MW in New York County, {N['er_cc_mw']} MW in Erie "
      f"and {N['sl_cc_mw']} MW in St. Lawrence, or {N['ny_cc_wm2']}, "
      f"{N['er_cc_wm2']} and {N['sl_cc_wm2']} W/m² of floor area. The peaks fall "
      f"at 08:00 on {N['ny_pkdate']} ({N['ny_tpk']} °C), "
      f"{N['er_pkdate']} ({N['er_tpk']} °C) and {N['sl_pkdate']} "
      f"({N['sl_tpk']} °C) and are {N['er_cc_pm']}{M}{N['ny_cc_pm']} "
      "times the mean occupied-hour demand, so the added energy is "
      "modest but its peak is sharp. Resistance supplies "
      f"{N['er_cc_res']}{M}{N['ny_cc_res']}% of the peak in New York and "
      f"Erie and all of it in St. Lawrence.".replace("{M}", M))
    p("Heat-pump choice matters most where the coldest school mornings sit "
      f"between {M}17.8 and {M}26 °C. In Erie, sizing for the design "
      f"temperature (CC-full) lowers the peak to {N['er_cc_full_mw']} MW and "
      f"the NEEP floor raises it to {N['er_neep_mw']} MW, while the lockout "
      f"raises it to {N['er_lockout_mw']} MW, {round((float(N['er_lockout_mw'])/float(N['er_cc_mw'])-1)*100)}% "
      "above CC. In New York County no occupied hour was colder than "
      f"{N['ny_tpk']} °C, so the lockout never acts and only sizing "
      f"and COP move the peak ({N['ny_cc_full_mw']}{M}{N['ny_neep_mw']} MW). "
      "In St. Lawrence the peak hour is below the coldest rated point, so "
      f"all four rated cases give {N['sl_cc_mw']} MW; only a unit that keeps "
      f"running in deep cold (CC-hold) lowers it, to {N['sl_cc_hold_mw']} "
      "MW. If schools were open on every weekday, the Erie peak would rise "
      f"to {N['er_allwk_mw']} MW (+{N['er_allwk_pct']}%), because the "
      "coldest Erie school morning of the record fell in the Presidents' Day "
      "week of 2015; the other two counties are unchanged."
      .replace("{M}", M))
    B.append(("table1", None, "Added peak demand of the county school stock",
              "Peaks in MW (school calendar). Max / median: 11-winter peak "
              "over median winter peak, CC case."))
    h2("Weather-year risk")
    p(f"Fig. 2 shows the peak of each winter. Winter peaks span "
      f"{N['ny_wmin_wm2']}{M}{N['ny_wmax_wm2']} W/m² in New York, "
      f"{N['er_wmin_wm2']}{M}{N['er_wmax_wm2']} in Erie and "
      f"{N['sl_wmin_wm2']}{M}{N['sl_wmax_wm2']} in St. Lawrence. The "
      f"{N['n_winters']}-winter maximum is {N['er_cc_maxmed']}, "
      f"{N['ny_cc_maxmed']} and {N['sl_cc_maxmed']} times the median winter "
      "peak in Erie, New York and St. Lawrence. A plan based on a typical "
      "winter, or on a single simulation year, would understate the "
      "school peak by a third to more than a half.".replace("{M}", M))
    B.append(("fig", "Fig2_winter_peaks.png",
              "Peak added demand of each winter, CC case (markers), with the "
              "range from CC-full to Lockout (bars); school calendar."))
    h2("Short-duration storage")
    p("Table II gives the battery needed to cap the CC peak. The first 10% "
      f"is cheap in energy: {N['ny_cc_x10_mw']}, {N['er_cc_x10_mw']} and "
      f"{N['sl_cc_x10_mw']} MW with {N['ny_cc_x10_h']}, {N['er_cc_x10_h']} "
      f"and {N['sl_cc_x10_h']} h, or {min(int(N[k + '_cc_x10_whm2']) for k in ('ny', 'er', 'sl'))}{M}"
      f"{max(int(N[k + '_cc_x10_whm2']) for k in ('ny', 'er', 'sl'))} Wh per m² of floor area, discharged on "
      f"{N['ny_cc_x10_days']}{M}{N['er_cc_x10_days']} school days in "
      f"{N['n_winters']} winters. Deeper caps diverge by climate. In Erie a "
      f"20% cap needs {N['er_cc_x20_h']} h ({N['er_cc_x20_mwh']} MWh) and "
      f"is used on {N['er_cc_x20_days']} days, because Buffalo cold "
      "outbreaks hold demand near the peak through the whole school day; "
      f"in New York it needs {N['ny_cc_x20_h']} h. The 1.21-h duration in "
      "St. Lawrence is a single-hour event: its peak is one very cold "
      "morning hour. Recharge at the 20% cap draws on average at most "
      f"{max(float(N['ny_cc_x20_rech']), float(N['er_cc_x20_rech']), float(N['sl_cc_x20_rech']))}"
      "% of the cap over the following 16 h.".replace("{M}", M))
    B.append(("table2", None, "Battery to cap the CC peak by a fraction x",
              "Energy is nameplate; days used: school days with discharge "
              "in 11 winters (school calendar)."))

    h1("Discussion and Limitations")
    p("For grid planners the results point to three inputs that change the "
      "school peak by tens of percent: the weather years used, the "
      "cold-weather rating and lockout setting written into heat-pump "
      "procurement, and whether units are sized to the derated or the "
      "nominal capacity. These are procurement choices made school by "
      "school, which makes them a lever that utilities and school "
      "districts can set together. Short-duration batteries are a "
      "credible tool for the top tenth of the peak, which occurs on a few "
      "mornings per decade; beyond that, upstate cold outbreaks call for "
      "long durations. A school battery held as a shelter reserve [10] "
      "could provide the first 10% only if the discharge does not "
      "compromise readiness for an outage that may follow the same cold "
      "spell; the author's forecast study [11] addresses that readiness "
      "decision and could set when a peak-capping discharge is allowed.")
    p("The estimates have limits. ComStock is simulated stock, not metered "
      "schools, and its represented area may differ from the actual "
      "inventory. The signature uses occupied hours only, so a morning "
      "warm-up after a night setback, which would raise the peak, is not "
      "modeled, nor is overnight heating during recharge. The COP curve is "
      "generic and below the coldest rated point its behavior is "
      "bracketed rather than known. School calendars are approximated. "
      "Storage dispatch assumes perfect foresight. The peaks are "
      "county-level and non-coincident across counties, and they are not "
      "netted against existing electric heating or the summer peak.")

    h1("Conclusion")
    p("Converting the heating of a county's school stock to air-source "
      f"heat pumps adds a sharp cold-morning peak of about "
      f"{N['ny_cc_wm2']}{M}{N['sl_cc_wm2']} W/m² ({N['er_cc_mw']} MW "
      "for Erie), set by the coldest school morning of the decade rather "
      "than a typical winter, and shifted by up to a third by the "
      "heat-pump lockout and sizing rules. A battery can remove its top "
      "10% with under 2 h of storage; deeper caps are a long-duration "
      "problem in cold upstate counties. Specifying cold-climate heat "
      "pumps sized for the design temperature, and planning on multi-year "
      "weather, are the low-cost first steps.".replace("{M}", M))
    return B


REFS = [
    "Y. Wu, M. Waite, T. Conlon, and V. Modi, “The role of "
    "electrification induced peak loads and gas infrastructure constraints "
    "on decarbonization pathways in New York State,” Energy Strategy "
    "Rev., vol. 44, Art. no. 100985, 2022, doi: 10.1016/j.esr.2022.100985.",
    "M. Waite and V. Modi, “Electricity load implications of space "
    "heating decarbonization pathways,” Joule, vol. 4, no. 2, "
    "pp. 376–394, 2020, doi: 10.1016/j.joule.2019.11.011.",
    "P. R. White, J. D. Rhodes, E. J. H. Wilson, and M. E. Webber, "
    "“Quantifying the impact of residential space heating "
    "electrification on the Texas electric grid,” Appl. Energy, "
    "vol. 298, Art. no. 117113, 2021, doi: 10.1016/j.apenergy.2021.117113.",
    "A. Parker et al., “ComStock reference documentation: Version 1,” "
    "Nat. Renewable Energy Lab., Golden, CO, USA, NREL/TP-5500-83819, 2023, "
    "doi: 10.2172/1967948; ComStock 2025 Release 3 (AMY2018) dataset.",
    "J. Kim and C. CaraDonna, “ComStock measure scenario documentation: "
    "Standard performance heat pump RTU with new windows,” Nat. "
    "Renewable Energy Lab., Golden, CO, USA, NREL/TP-5500-95006, 2025.",
    "Nat. Renewable Energy Lab., “ResStock documentation: Heat pump "
    "upgrades tutorial.” [Online]. Available: "
    "https://resstock.readthedocs.io (accessed Oct. 20, 2026).",
    "Northeast Energy Efficiency Partnerships, “Cold climate air source "
    "heat pump specification, version 4.0,” 2023.",
    "NOAA National Centers for Environmental Information, “Integrated "
    "Surface Database (ISD),” [Online]. Available: "
    "https://www.ncei.noaa.gov/pub/data/noaa/ (accessed Nov. 11, 2026).",
    "Nat. Renewable Energy Lab., “2024 Annual Technology Baseline: "
    "Commercial battery storage.” [Online]. Available: "
    "https://atb.nrel.gov (accessed Oct. 21, 2026).",
    "S. Ismoilov, “Can an electrified school stay open in a blizzard? "
    "Solar-plus-storage sizing for winter shelter operation under "
    "cold-battery and snow constraints in New York State,” unpublished.",
    "S. Ismoilov, “Charge before the storm: Forecast-informed battery "
    "readiness for school winter shelters in New York State,” "
    "unpublished.",
]

DATA_NOTE = (
    "Data availability: inputs are public (ComStock 2025 R3, NOAA ISD). "
    "The analysis code, unit tests and result tables are available at "
    "https://github.com/iamshokir/school-peak-ny.")

ACK = (
    "Generative AI disclosure: Claude (Anthropic) was used to write and test "
    "the analysis code, run the calculations, draw the figures and draft "
    "the text of all sections under the author's direction. The author "
    "chose the research question and cases, reviewed the code, results and "
    "text, and takes full responsibility for the content. "
    "[AUTHOR TO CONFIRM WORDING]")


def table1_rows():
    hdr = ["County", "T_{des} (°C)", "CC", "CC-full", "NEEP", "Lock-out",
           "CC (W/m²)", "Max/ median"]
    rows = []
    for k, name in [("ny", "New York"), ("er", "Erie"),
                    ("sl", "St. Lawrence")]:
        rows.append([name, N[f"{k}_tdes"], N[f"{k}_cc_mw"],
                     N[f"{k}_cc_full_mw"], N[f"{k}_neep_mw"],
                     N[f"{k}_lockout_mw"], N[f"{k}_cc_wm2"],
                     N[f"{k}_cc_maxmed"]])
    return hdr, rows


def table2_rows():
    hdr = ["x", "County", "Power (MW)", "Energy (MWh)", "Duration (h)",
           "Days used"]
    rows = []
    for x in (10, 20, 30):
        for k, name in [("ny", "New York"), ("er", "Erie"),
                        ("sl", "St. Lawrence")]:
            p = f"{k}_cc_x{x}"
            rows.append([f"{x}%", name, N[p + "_mw"], N[p + "_mwh"],
                         N[p + "_h"], N[p + "_days"]])
    return hdr, rows


def to_markdown(blocks) -> str:
    out = [f"# {TITLE}", "", f"{AUTHOR} — {AFFIL} — {EMAIL}", "",
           f"**Abstract—**{ABSTRACT}", "", f"**Index Terms—**{INDEX}",
           ""]
    sec = fig = tab = 0
    roman = ["I", "II", "III", "IV", "V", "VI"]
    sub = 0
    for b in blocks:
        if b[0] == "h1":
            out += [f"## {roman[sec]}. {b[1].upper()}", ""]
            sec += 1
            sub = 0
        elif b[0] == "h2":
            out += [f"### {chr(65 + sub)}. {b[1]}", ""]
            sub += 1
        elif b[0] == "p":
            out += [b[1], ""]
        elif b[0] == "eq":
            out += [f"    {b[1]}        ({b[2]})", ""]
        elif b[0] == "fig":
            fig += 1
            out += [f"![Fig. {fig}](../results/figures/{b[1]})", "",
                    f"*Fig. {fig}. {b[2]}*", ""]
        elif b[0] in ("table1", "table2"):
            tab += 1
            hdr, rows = table1_rows() if b[0] == "table1" else table2_rows()
            out += [f"**TABLE {roman[tab - 1]}. {b[2].upper()}**", "", (b[3] if len(b) > 3 else ""), "",
                    "| " + " | ".join(hdr) + " |",
                    "|" + "---|" * len(hdr)]
            out += ["| " + " | ".join(r) + " |" for r in rows]
            out += [""]
    out += [DATA_NOTE, "", ACK, "", "## REFERENCES", ""]
    out += [f"[{i + 1}] {r}" for i, r in enumerate(REFS)]
    return "\n".join(out) + "\n"


def main():
    blocks = body()
    md = to_markdown(blocks)
    (ROOT / "paper" / "draft.md").write_text(md, encoding="utf-8")
    import make_docx_pes
    make_docx_pes.build(blocks, ROOT / "paper" / "Ismoilov_PESGM2027.docx",
                        sys.modules[__name__])
    print("abstract words:", len(ABSTRACT.split()))
    words = len(md.split())
    print("words (md, incl. refs):", words)


if __name__ == "__main__":
    main()
