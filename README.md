# school-peak-ny

Code and results for *Cold-Morning Peaks from Electrified School Heating in
New York State: Heat-Pump Choice, Weather-Year Risk and Short-Duration
Storage* (Shokirdzhon Ismoilov, OFTO Energy Foundation; draft for IEEE PES
GM 2027).

## Reproduce

```
python scripts/run_all.py           # data check, peaks, storage (results/tables)
python scripts/check_inputs.py      # input table + neighbor-station check
python scripts/run_checks.py        # warm-up, uncertainty, hourly state-of-charge
python -m pytest -q                 # 20 tests (unit, regression, hand check)
python scripts/make_figures.py      # results/figures
python paper/build_paper.py         # paper/draft.md and .docx (needs the PES PG4 template converted to template/pg4.docx; not committed)
```

Weather input: NOAA ISD fixed-width files, stations 725280-14733 (KBUF),
725053-94728 (KNYC), 726223-94725 (KMSS), 2014-2025; neighbors for the
check: 725030-14732 (KLGA), 725287-04724 (KIAG), 725186-99999 (KOGS, 2016-2025), downloaded from
https://www.ncei.noaa.gov/pub/data/noaa/{year}/{station}-{year}.gz on
2026-11-11 (data/SHA256SUMS_isd.txt). Raw files are not committed.

## Reused (read-only, hashes in vendor/SHA256_source.txt)

- `vendor/load_remap.py` — copied unchanged from
  iamshokir/school-shelter-ny@23d8d0b (COP curve, signature functions).
- `vendor/comstock_heating_signature.csv` — the same repository's
  ComStock 2025 R3 county school signatures (results/data_checks).

## Generative-AI use log

| Date | Tool | What AI did | Author |
|---|---|---|---|
| 2026-11-11/12 | Claude (Anthropic), Opus 5.5, cloud container | Proposed three contribution options (author chose A); downloaded NOAA ISD; wrote src/, scripts/, tests; ran all calculations; drew figures; drafted all paper text and the submission pack; checked IEEE/PES policies. | Chose option A; review of code, text, conclusions and the submission decision pending. |
