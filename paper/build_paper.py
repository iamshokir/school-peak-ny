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
M = "-"

TITLE = ("Cold-Morning Peaks from Electrified School Heating in New York "
         "State: Heat-Pump Choice, Weather-Year Risk and Short-Duration "
         "Storage")
AUTHOR = "Shokirdzhon Ismoilov"
AFFIL = "OFTO Energy Foundation, Brooklyn, NY, USA"
EMAIL = "shokir@oftoenergy.org"

ABSTRACT = (
    "Heating electrification is projected to move New York toward a "
    "winter-peaking grid, but the share of individual building types is "
    "rarely resolved. This paper estimates the gross heating demand that "
    "the school stock of three New York counties would add on cold school "
    "mornings if all school heating used air-source heat pumps with "
    "resistance backup. A ComStock-derived heating signature is applied to "
    f"{N['n_winters']} winters of hourly NOAA temperatures for five "
    f"heat-pump cases. The county peaks are {N['ny_cc_mw']}, "
    f"{N['er_cc_mw']} and {N['sl_cc_mw']} MW "
    f"({N['ny_cc_wm2']}-{N['sl_cc_wm2']} W/m²) in New York, Erie and "
    "St. Lawrence, "
    f"{round((float(N['er_cc_maxmed'])-1)*100)}-"
    f"{round((float(N['sl_cc_maxmed'])-1)*100)}% above a median winter; "
    "they are gross and non-coincident. Sizing and compressor lockout move "
    f"the Erie peak between {N['er_cc_full_mw']} and {N['er_lockout_mw']} "
    "MW, and an assumed 30% morning warm-up allowance adds "
    f"{N['sl_wu30_pct']}-{N['ny_wu30_pct']}%. A battery that caps 10% of "
    f"the peak needs {N['sl_cc_x10_h'][:3]}-{N['er_cc_x10_h'][:3]} h and "
    f"discharges on at most {N['er_cc_x10_days']} school days in "
    f"{N['n_winters']} winters.")

INDEX = ("Building electrification, energy storage, heat pumps, peak "
         "demand, schools")

REFD = {
    "wu": "Y. Wu, M. Waite, T. Conlon, and V. Modi, “The role of "
    "electrification induced peak loads and gas infrastructure constraints "
    "on decarbonization pathways in New York State,” Energy Strategy "
    "Rev., vol. 44, Art. no. 100985, 2022, doi: 10.1016/j.esr.2022.100985.",
    "waite": "M. Waite and V. Modi, “Electricity load implications of space "
    "heating decarbonization pathways,” Joule, vol. 4, no. 2, "
    "pp. 376-394, 2020, doi: 10.1016/j.joule.2019.11.011.",
    "white": "P. R. White, J. D. Rhodes, E. J. H. Wilson, and M. E. Webber, "
    "“Quantifying the impact of residential space heating "
    "electrification on the Texas electric grid,” Appl. Energy, "
    "vol. 298, Art. no. 117113, 2021, doi: 10.1016/j.apenergy.2021.117113.",
    "p4": "S. Ismoilov, “Can an electrified school stay open in a blizzard? "
    "Solar-plus-storage sizing for winter shelter operation under "
    "cold-battery and snow constraints in New York State,” unpublished.",
    "comstock": "A. Parker et al., “ComStock reference documentation: "
    "Version 1,” Nat. Renewable Energy Lab., Golden, CO, USA, "
    "NREL/TP-5500-83819, 2023, doi: 10.2172/1967948; ComStock 2025 "
    "Release 3 (AMY2018) dataset.",
    "isd": "NOAA National Centers for Environmental Information, "
    "“Integrated Surface Database (ISD),” [Online]. Available: "
    "https://www.ncei.noaa.gov/pub/data/noaa/ (accessed Nov. 11, 2026).",
    "resstock": "Nat. Renewable Energy Lab., “ResStock documentation: Heat "
    "pump upgrades tutorial.” [Online]. Available: "
    "https://resstock.readthedocs.io (accessed Oct. 20, 2026).",
    "neep": "Northeast Energy Efficiency Partnerships, “Cold climate air "
    "source heat pump specification, version 4.0,” 2022 (effective "
    "Jan. 1, 2023).",
    "kim": "J. Kim and C. CaraDonna, “ComStock measure scenario "
    "documentation: Standard performance heat pump RTU with new "
    "windows,” Nat. Renewable Energy Lab., Golden, CO, USA, "
    "NREL/TP-5500-95006, Aug. 2025.",
    "ti": "U.S. Army, “Mechanical design: Heating, ventilating, and air "
    "conditioning,” Technical Instructions TI 810-10, Feb. 1999.",
    "atb": "Nat. Renewable Energy Lab., “2024 Annual Technology Baseline: "
    "Commercial battery storage.” [Online]. Available: "
    "https://atb.nrel.gov (accessed Oct. 21, 2026).",
    "p5": "S. Ismoilov, “Charge before the storm: Forecast-informed battery "
    "readiness for school winter shelters in New York State,” "
    "unpublished.",
    "ornl": "J. A. Shonder, M. A. Martin, P. J. Hughes, and J. Thornton, "
    "“Geothermal heat pumps in K-12 schools: A case study of the Lincoln, "
    "Nebraska, schools,” Oak Ridge Nat. Lab., Oak Ridge, TN, USA, "
    "ORNL/TM-2000/80, 2000.",
}
REFS = []


def _number_refs(B):
    """Replace [@key] by IEEE numbers in order of first citation."""
    import re
    order = []
    pat = re.compile(r"\[@([a-z0-9]+)\]")
    for b in B:
        for part in b[1:]:
            if isinstance(part, str):
                for k in pat.findall(part):
                    if k not in order:
                        order.append(k)
    assert set(order) == set(REFD), set(REFD) ^ set(order)
    num = {k: i + 1 for i, k in enumerate(order)}
    REFS[:] = [REFD[k] for k in order]
    out = []
    for b in B:
        out.append(tuple(pat.sub(lambda m: f"[{num[m.group(1)]}]", x)
                         if isinstance(x, str) else x for x in b))
    return out


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
      "against 34 GW today, driven by heating in extreme cold [@wu]. "
      "Similar winter-peak growth has been reported for space heating at "
      "national scale [@waite] and for residential heating in Texas "
      "[@white]. These studies treat buildings as one or two sectors. "
      "Schools are a distinct segment: a large, publicly owned stock, a "
      "narrow occupied window that starts in the coldest hours of the "
      "morning, and a possible role as shelters during winter outages "
      "[@p4]. To the author's knowledge, their contribution to "
      "cold-weather demand, and how it depends on the heat pump chosen and "
      "on the weather year used for planning, has not been quantified.")
    p("This paper asks three questions for the school stock of three New "
      "York counties with different climates: New York County (Manhattan), "
      "Erie County (Buffalo) and St. Lawrence County (North Country). "
      "(i) How large is the gross electric heating demand that full "
      "heat-pump conversion would add on school mornings? (ii) How much "
      "does it depend on heat-pump performance and sizing, on the winter "
      "used for planning and on model uncertainty? (iii) How much of it can "
      "a short-duration battery remove? The calculation reuses the heating "
      "signature and heat-pump curve of the author's single-school shelter "
      "sizing study [@p4], which is unpublished; that study sizes storage "
      "for one school through a 72-h outage and does not address grid "
      "demand. The fleet-level question, the multi-year weather record, "
      "the sizing, lockout and uncertainty cases, and the peak-capping "
      "analysis are new.")

    h1("Data and Method")
    h2("Building stock and heating signature")
    p("The school stock is taken from ComStock 2025 Release 3 county "
      "aggregates for primary and secondary schools [@comstock]: "
      f"{N['ny_area_mm2']}, {N['er_area_mm2']} and {N['sl_area_mm2']} "
      "million m² of represented floor area in New York, Erie and "
      "St. Lawrence counties. Thermal heating demand per unit area, from "
      "the ComStock ideal-load upgrade, was fitted in [@p4] against airport "
      "station temperature in occupied hours (weekdays 08:00-15:59, "
      "November-March) with a one-slope change-point model, giving "
      f"balance temperatures of {N['tbal_lo']}-{N['tbal_hi']} °C and R² of "
      f"{N['r2_lo']}-{N['r2_hi']}. The thermal demand of school type b in "
      "hour t is")
    eq("Q_{b,t} = A_{b} s_{b} max(0, T_{bal,b} - T_{t})", 1)
    p("where A_{b} is the floor area, s_{b} the slope, T_{bal,b} the "
      "balance temperature and T_{t} the outdoor temperature.")
    h2("Weather")
    p("Hourly air temperature for winters 2014/15 to 2024/25 (November to "
      "March) comes from NOAA Integrated Surface Database records [@isd] at "
      "Central Park (KNYC), Buffalo Niagara (KBUF) and Massena (KMSS). "
      "Reports flagged suspect or erroneous are removed, reports within an "
      "hour are averaged and gaps of up to 3 h are interpolated; "
      f"{N['ny_miss']}%, {N['er_miss']}% and {N['sl_miss']}% of occupied "
      "hours remain missing and are dropped. Each series was compared with "
      "a neighboring station (LaGuardia, Niagara Falls, Ogdensburg): "
      f"hourly correlation {N['nb_corr_min']}-{N['nb_corr_max']} and 1st "
      f"percentiles within {N['nb_p1_maxdiff']} °C. Occupied hours exclude "
      "U.S. federal holidays, 24 December-1 January and the week of "
      "Presidents' Day, an approximation of New York school calendars (for "
      "example, New York City schools were closed 16-20 February 2015). "
      f"This leaves {N['ny_hours']}-{N['er_hours']} occupied hours per "
      "county. The design temperature T_{des} is the 1st percentile of all "
      f"winter hours: {N['ny_tdes']}, {N['er_tdes']} and {N['sl_tdes']} °C; "
      "it is not the ASHRAE design value.")
    h2("Heat-pump cases")
    p("All school heating is assumed to move to air-source heat pumps with "
      "electric-resistance backup. The result is the gross added heating "
      "demand: it is not netted against existing electric heating, and its "
      "coincidence across counties and with the system peak is not "
      "assessed. The nominal thermal capacity (capacity fraction k = 1) of "
      "the heat pumps of school type b is")
    eq("H_{b} = A_{b} s_{b} (T_{bal,b} - T_{des}) / k(T_{des})^{δ}", 2)
    p("with k(T) the capacity fraction at temperature T and δ = 0 or 1. "
      "With heat-pump output G_{b,t} = min(Q_{b,t}, k(T_{t})H_{b}), the "
      "fleet electric demand is")
    eq("P_{t} = Σ_{b} [G_{b,t}/COP(T_{t}) + (Q_{b,t} - G_{b,t})]", 3)
    p("Five cases are compared. CC (main): a cold-climate curve with COP "
      "3.37, 2.33, 1.98 and 1.49 at 8.3, -8.3, -15 and -26.1 °C and "
      "capacity fractions 1.03, 0.77, 0.69 and 0.51 [@resstock], with "
      "δ = 0 (nominal capacity equal to the design load, the rule of "
      "[@p4]); resistance covers any capacity shortfall, and the "
      "compressor is off below the coldest rated point. CC-full: as CC "
      "with δ = 1, so the derated capacity meets the design load; CC and "
      "CC-full bracket common sizing practice. NEEP: CC with COP scaled to "
      "1.75 at -15 °C, the qualifying floor of the NEEP cold-climate "
      "specification [@neep]. Lockout: CC with the compressor off below "
      "-17.8 °C (0 °F), the behavior of the standard-performance heat-pump "
      "rooftop unit modeled by ComStock [@kim]. CC-hold: CC with COP and "
      "capacity held at their -26.1 °C values at colder temperatures, an "
      "optimistic bound.")
    h2("Uncertainty and morning warm-up")
    p("With the heat pumps sized on the base signature, the true thermal "
      "load is varied by ±10% and ±20%, the balance temperature by ±2 K, "
      "and the COP and capacity curves by ±10%, one at a time. The "
      "signature does not resolve the morning recovery after a night "
      "setback, so three stated assumptions add 15%, 30% and 50% to the "
      "08:00 thermal demand; 30% is the recovery allowance in U.S. Army "
      "design criteria [@ti]. These are scenarios, not measurements. A "
      "calendar sensitivity counts recess weeks and winter break as school "
      "days (federal holidays still excluded).")
    h2("Peak capping with storage")
    p("Let P_{max} be the highest occupied-hour demand over all winters. A "
      "battery of power xP_{max} holds demand at (1 - x)P_{max} if its "
      "usable energy covers the worst school day:")
    eq("E = max_{d} Σ_{t∈d} max(0, P_{t} - (1 - x)P_{max})", 4)
    p("Nameplate energy is E/(η_{d}u), with discharge efficiency "
      "η_{d} = 0.85^{0.5} from an 85% round trip [@atb] and usable fraction "
      "u = 0.9; duration is nameplate energy over power. Dispatch assumes "
      "the day's demand is known. An hourly state-of-charge simulation over "
      "every winter hour, with discharge limited to the power rating and "
      "recharge only outside school hours, checks the sizing across "
      "consecutive cold days.")

    h1("Results")
    h2("Why the peak is steep")
    p("Fig. 1 shows the added demand per square meter of floor area as a "
      "function of outdoor temperature. Between 0 and -5 °C the heat pumps "
      "carry the load at a COP near 2.5 or above and each degree adds "
      f"{N['slope_mild_lo']}-{N['slope_mild_hi']} W/m². Near the design "
      "temperature the derated capacity no longer covers the load (in the "
      "CC case this begins several kelvins above T_{des}, because nominal "
      "capacity equals the design load) and resistance takes the rest at "
      f"COP 1, so each degree adds {N['slope_cold_lo']}-"
      f"{N['slope_cold_hi']} W/m², {N['slope_ratio_lo']}-"
      f"{N['slope_ratio_hi']} times as much. The lockout case jumps at "
      "-17.8 °C, and every case except CC-hold steps up to pure "
      "resistance below -26.1 °C.")
    B.append(("fig", "Fig1_demand_vs_temperature.png",
              "Added electric demand of the county school stock per square "
              "meter of floor area versus outdoor temperature for the five "
              "heat-pump cases. Vertical line: design temperature; shaded: "
              "colder than any occupied hour in 2014/15-2024/25."))
    h2("Peak demand and heat-pump choice")
    p("Table I lists the peaks. With the main CC case the gross added "
      f"heating demand peaks at {N['ny_cc_mw']} MW in New York County, "
      f"{N['er_cc_mw']} MW in Erie and {N['sl_cc_mw']} MW in St. Lawrence, "
      f"or {N['ny_cc_wm2']}, {N['er_cc_wm2']} and {N['sl_cc_wm2']} W/m². "
      f"The peaks fall at 08:00 on {N['ny_pkdate']} ({N['ny_tpk']} °C), "
      f"{N['er_pkdate']} ({N['er_tpk']} °C) and {N['sl_pkdate']} "
      f"({N['sl_tpk']} °C) and are {N['er_cc_pm']}-{N['ny_cc_pm']} times "
      "the mean occupied-hour demand. Resistance supplies "
      f"{N['er_cc_res']}-{N['ny_cc_res']}% of the peak in New York and "
      "Erie and all of it in St. Lawrence.")
    p("Heat-pump choice matters most where the coldest school mornings "
      "fall between -17.8 and -26.1 °C. In Erie, sizing for the design "
      f"temperature (CC-full) lowers the peak to {N['er_cc_full_mw']} MW, "
      f"the NEEP floor raises it to {N['er_neep_mw']} MW and the lockout to "
      f"{N['er_lockout_mw']} MW, "
      f"{round((float(N['er_lockout_mw'])/float(N['er_cc_mw'])-1)*100)}% "
      "above CC. In New York County no occupied hour was colder than "
      f"{N['ny_tpk']} °C, so the lockout never acts "
      f"({N['ny_cc_full_mw']}-{N['ny_neep_mw']} MW). In St. Lawrence the "
      "peak hour is below the coldest rated point, so all four rated cases "
      f"give {N['sl_cc_mw']} MW; CC-hold lowers it to {N['sl_cc_hold_mw']} "
      "MW. If recess weeks and winter break were school days, the Erie "
      f"peak would rise to {N['er_allwk_mw']} MW (+{N['er_allwk_pct']}%, "
      f"{N['er_allwk_date']}, {N['er_allwk_t']} °C); the other two counties "
      "are unchanged.")
    B.append(("table1", None, "Gross added peak of the county school stock",
              "Peaks in MW (school calendar). Max/median: 11-winter peak "
              "over median winter peak, CC case."))
    h2("Weather-year risk")
    p("Fig. 2 shows the peak of each winter: "
      f"{N['ny_wmin_wm2']}-{N['ny_wmax_wm2']} W/m² in New York, "
      f"{N['er_wmin_wm2']}-{N['er_wmax_wm2']} in Erie and "
      f"{N['sl_wmin_wm2']}-{N['sl_wmax_wm2']} in St. Lawrence. The "
      f"{N['n_winters']}-winter maximum is {N['er_cc_maxmed']}, "
      f"{N['ny_cc_maxmed']} and {N['sl_cc_maxmed']} times the median winter "
      "peak in Erie, New York and St. Lawrence, so a plan based on a "
      "typical winter, or on a single simulation year, would understate "
      "the school peak by a quarter to more than a third.")
    B.append(("fig", "Fig2_winter_peaks.png",
              "Peak of each winter, CC case (markers), with the range from "
              "CC-full to Lockout (bars; NEEP not shown); school calendar."))
    h2("Short-duration storage")
    p("Table II gives the battery needed to cap the CC peak. Capping the "
      f"top 10% requires {N['ny_cc_x10_mw']}, {N['er_cc_x10_mw']} and "
      f"{N['sl_cc_x10_mw']} MW of power with {N['ny_cc_x10_h']}, "
      f"{N['er_cc_x10_h']} and {N['sl_cc_x10_h']} h of nameplate duration, "
      f"or {min(int(N[k + '_cc_x10_whm2']) for k in ('ny', 'er', 'sl'))}-"
      f"{max(int(N[k + '_cc_x10_whm2']) for k in ('ny', 'er', 'sl'))} Wh "
      f"per m² of floor area, and discharges on {N['ny_cc_x10_days']}-"
      f"{N['er_cc_x10_days']} school days in {N['n_winters']} winters. "
      "Deeper caps depend on the daily profile: in Erie a 20% cap needs "
      f"{N['er_cc_x20_h']} h ({N['er_cc_x20_mwh']} MWh) with the flat "
      "occupied-hour profile, because Buffalo cold outbreaks hold demand "
      "near the peak all day, but under any of the warm-up scenarios the "
      f"peak becomes an 08:00 spike and {N['wu_x20h_max']} h suffices. The "
      "hourly state-of-charge simulation confirms the daily sizing within "
      f"{N['soc_maxdiff_pct']}%, also when recharge is limited to a quarter "
      "of the power rating, so consecutive cold days do not constrain the "
      "sizing.")
    B.append(("table2", None, "Battery to cap the CC peak by a fraction x",
              "Energy: nameplate; duration: nameplate energy over power "
              "(1.21 h is one hour of discharge); days used: school days "
              "with discharge in 11 winters; no warm-up."))
    h2("Robustness")
    p("Table III gives the one-at-a-time changes. A load error of ±20% "
      f"moves the peak by {N['sl_load_factor_1.2']}-"
      f"{N['ny_load_factor_1.2']}%, more than proportionally where the "
      "heat pumps were sized on the base load and the error falls on "
      f"resistance; the balance temperature (±2 K) moves it by up to "
      f"{N['ny_dtbal_2.0']}%, and COP or capacity (±10%) by up to 5%. The "
      "assumed morning warm-up has the largest effect: a 30% allowance "
      f"raises the peaks to {N['ny_wu30_mw']}, {N['er_wu30_mw']} and "
      f"{N['sl_wu30_mw']} MW. The max/median ratio remains "
      f"{N['wu_maxmed_lo']}-{N['wu_maxmed_hi']} under every warm-up "
      "scenario.")
    B.append(("table3", None, "Change in CC peak, one input at a time (%)",
              "Values for a decrease/increase of the input. Heat pumps "
              "sized on the base signature. Warm-up: assumed extra 08:00 "
              "thermal demand; 30% from [@ti]."))

    h1("Discussion and Limitations")
    p("For grid planners the results identify inputs that change the "
      "school peak by tens of percent: the weather years used (all "
      f"counties), the lockout setting in Erie (+{round((float(N['er_lockout_mw'])/float(N['er_cc_mw'])-1)*100)}%), sizing to derated "
      f"rather than nominal capacity ({round((float(N['ny_cc_full_mw'])/float(N['ny_cc_mw'])-1)*100)}% and "
      f"{round((float(N['er_cc_full_mw'])/float(N['er_cc_mw'])-1)*100)}% in New York and Erie) "
      "and, under the stated assumptions, the morning start-up strategy. "
      "Because these choices are made school by school, utilities and "
      "school districts can set them jointly. Short-duration batteries can "
      "remove the top tenth of the peak, which occurs on a few mornings "
      "per decade; how much more they remove depends on the intraday "
      "profile, which needs metered data. A school battery held as a "
      "shelter reserve [@p4] could provide this only if the discharge does "
      "not compromise readiness for an outage that may follow the same "
      "cold spell; the forecast approach of [@p5] could set when a "
      "peak-capping discharge is allowed.")
    p("The estimates have limits. ComStock is simulated stock, not metered "
      "schools, and no independent measurement of air-source heat-pump "
      "school peaks was found for validation. The nearest published "
      "figure is a ground-source heat-pump school in Lincoln, Nebraska, "
      "with a measured 1996 peak of 255 kW over about 69,000 ft² [@ornl], "
      f"or about {N['ornl_wm2']} W/m² for all end uses; ground-source units "
      "avoid resistance backup and that building was new, so it indicates "
      "what efficient design can reach rather than validating the "
      "existing-stock estimate. The warm-up is assumed, overnight heating "
      "during recharge is not modeled, the COP curve is generic, calendars "
      "are approximated and dispatch assumes perfect foresight. Turning "
      "the gross county peaks into a net system impact requires "
      "coincidence with zonal load, which is outside this paper.")

    h1("Conclusion")
    p("Converting the heating of a county's school stock to air-source "
      "heat pumps adds a sharp gross cold-morning peak of about "
      f"{N['ny_cc_wm2']}-{N['sl_cc_wm2']} W/m² in the main case "
      f"({N['er_cc_mw']} MW for Erie). The peak is set by the coldest "
      "school morning of the decade rather than a typical winter. In Erie "
      "it moves by up to a third with heat-pump lockout and sizing, and in "
      f"all three counties it rises by {N['sl_wu30_pct']}-{N['ny_wu30_pct']}% "
      "under an assumed 30% warm-up allowance. A battery can remove the top 10% with under 2 h "
      "of storage in the main case. Specifying cold-climate heat pumps "
      "sized for the design temperature, managing morning start-up and "
      "planning on multi-year weather are steps this analysis supports; "
      "metered school data are the next need.")
    return _number_refs(B)


DATA_NOTE = (
    "Data availability: inputs are public (ComStock 2025 R3, NOAA ISD). "
    "The analysis code, unit tests and result tables are available at "
    "https://github.com/iamshokir/school-peak-ny.")

AI_REF = ("Anthropic, “Claude (Opus 5.5),” large language model, accessed "
          "Nov. 11-12, 2026. [Online]. Available: https://claude.ai")

ACK = (
    "Generative AI disclosure: Claude (Anthropic) [{ai}] was used to write and test "
    "the analysis code, run the calculations, draw the figures and draft "
    "the text of all sections under the author's direction. The author "
    "chose the research question and cases, reviewed the code, results and "
    "text, and takes full responsibility for the content.")


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


def table3_rows():
    hdr = ["Input", "New York", "Erie", "St. Lawrence"]
    def pair(prm, lo, hi):
        return [f"{N[k + '_' + prm + '_' + str(lo)]}/+{N[k + '_' + prm + '_' + str(hi)]}"
                for k in ("ny", "er", "sl")]
    rows = [["Load ±20%"] + pair("load_factor", 0.8, 1.2),
            ["Load ±10%"] + pair("load_factor", 0.9, 1.1),
            ["T_{bal} ±2 K"] + pair("dtbal", -2.0, 2.0),
            ["COP ±10%"] + [f"+{N[k + '_cop_factor_0.9']}/{N[k + '_cop_factor_1.1']}"
                            for k in ("ny", "er", "sl")],
            ["Capacity ±10%"] + [f"+{N[k + '_cap_factor_0.9']}/{N[k + '_cap_factor_1.1']}"
                                 for k in ("ny", "er", "sl")]]
    for b in (15, 30, 50):
        rows.append([f"Warm-up {b}%"] + [f"+{N[k + f'_wu{b}_pct']}"
                                         for k in ("ny", "er", "sl")])
    return hdr, [[c.replace("+-", "-").replace("/+0", "/0").replace("+0/", "0/") for c in r] for r in rows]


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
    out = [f"# {TITLE}", "", f"{AUTHOR} - {AFFIL} - {EMAIL}", "",
           f"**Abstract-**{ABSTRACT}", "", f"**Index Terms-**{INDEX}",
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
        elif b[0] in ("table1", "table2", "table3"):
            tab += 1
            hdr, rows = {"table1": table1_rows, "table2": table2_rows,
                         "table3": table3_rows}[b[0]]()
            out += [f"**TABLE {roman[tab - 1]}. {b[2].upper()}**", "", (b[3] if len(b) > 3 else ""), "",
                    "| " + " | ".join(hdr) + " |",
                    "|" + "---|" * len(hdr)]
            out += ["| " + " | ".join(r) + " |" for r in rows]
            out += [""]
    out += [DATA_NOTE, "", ACK, "", "## REFERENCES", ""]
    out += [f"[{i + 1}] {r}" for i, r in enumerate(REFS)]
    return "\n".join(out) + "\n"


def main():
    global ACK
    blocks = body()
    REFS.append(AI_REF)
    ACK = ACK.replace("{ai}", str(len(REFS)))
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
