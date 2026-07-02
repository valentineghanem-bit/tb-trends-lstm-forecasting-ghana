# Trends, Treatment Gaps and LSTM Forecasting of Tuberculosis in Ghana, with District-Level Structural Risk Stratification

[![CI](https://github.com/valentineghanem-bit/tb-trends-lstm-forecasting-ghana/actions/workflows/ci.yml/badge.svg)](https://github.com/valentineghanem-bit/tb-trends-lstm-forecasting-ghana/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 1. Overview

A 25-year (2000-2024) national analysis of Ghana's tuberculosis epidemiology — trends, forecasting, and the multidrug-resistant TB (MDR-TB) treatment-cascade gap — paired with a district-level (261 MMDA) structural risk-stratification layer. The two analytic tracks are deliberately decoupled: no district-level TB surveillance data exists anywhere in Ghana's public reporting, so the district layer characterises general structural deprivation, not observed TB burden.

## 2. Key findings

- National TB incidence declined 42% (216 → 126 per 100,000; Sen's slope −4.0/year, p<0.0001), 2000-2024.
- ARIMA substantially outperformed LSTM and XGBoost for national incidence forecasting (MAE 0.37 vs. 3.71 and 4.07), a finding robust to random seed and to matching model-selection protocols.
- MDR-TB testing and treatment-initiation capacity expanded significantly, but treatment success showed no significant trend (p=0.13) over 2010-2022.
- The district TB-Vulnerability Index (TVI) shows strong spatial clustering (Moran's I=0.80, p=0.001) concentrated in northern Ghana — a general structural-deprivation construct, not validated TB-specific risk.

## 3. Study design

Dual-track design: (1) a national, longitudinal (2000-2024) time-series analysis of WHO Global Health Observatory TB indicators; (2) a district-level (n=261), cross-sectional (2021) structural-deprivation index. Reported per STROBE, RECORD, and TRIPOD-adapted forecasting items.

## 4. Data sources

- WHO Global Health Observatory: tuberculosis, HIV, health financing, health workforce, global health estimates indicators (public domain).
- WHO Global Tuberculosis Report 2024.
- Ghana Statistical Service 2021 Population & Housing Census (district frame).
- Ghana district boundary GeoJSON (260-polygon set, with a 261→260 crosswalk for the one merged district).

All sources are public-domain, aggregate, secondary data. No individual-level records.

## 5. Repository structure

```
analysis/       Python pipeline (data build, forecasting, spatial stats, figures, assembly)
outputs/
  data/         Intermediate analysis outputs (locked hyperparameters, forecast folds, etc.)
  tables/       Manuscript tables (CSV)
  figures/      Manuscript figures (300 dpi PNG)
  release/      FAIR-compliant master CSV release + data dictionary
dashboard/      Bespoke interactive HTML dashboard (vanilla JS + inline SVG, <60KB)
poster/         Bespoke A0 poster (HTML, print-ready)
qa/             QA protocol script + badge
tests/          Reproducibility test suite (pytest)
docs/           Stage-by-stage methodology documentation
```

## 6. Methods / pipeline

Run in order:
```
python analysis/build_master.py              # national panel + district vulnerability master CSVs
python analysis/build_vulnerability_index.py  # TB-Vulnerability Index (PCA + equal-weight)
python analysis/lock_hyperparameters.py       # pre-registered LSTM/XGBoost hyperparameter lock (fold-1 only)
python analysis/mann_kendall_trends.py        # trend tests, all Track A series
python analysis/forecast_rolling_origin.py    # LSTM/ARIMA/XGBoost rolling-origin CV forecasting
python analysis/mdr_subanalysis.py            # MDR-TB cascade shorter-window sub-analysis
python analysis/spatial_analysis.py           # Moran's I / Getis-Ord Gi* / LISA on district TVI
python analysis/shap_decomposition.py         # SHAP feature importance, XGBoost forecast
python analysis/build_figures.py              # 6 manuscript figures
python analysis/build_release_package.py      # FAIR master CSV release + data dictionary
python analysis/build_dashboard.py            # interactive dashboard
python analysis/build_poster.py               # A0 poster
python analysis/assemble_docx.py              # manuscript assembly (requires manuscript/*.md, not in repo)
```

## 7. Reproducibility

- Python 3.11, dependencies pinned in `requirements.txt`.
- CI (`.github/workflows/ci.yml`) rebuilds the master datasets and runs the test suite on every push.
- All model hyperparameters are pre-registered and locked (`outputs/data/locked_hyperparameters.json`) — no post-hoc tuning.

## 8. Outputs

- 6 manuscript figures (`outputs/figures/`, 300 dpi, colourblind-safe Okabe-Ito palette).
- 5 manuscript tables (`outputs/tables/`).
- FAIR master CSV release (`outputs/release/`) with a full data dictionary.

## 9. Dashboard & poster — view or download

| Deliverable | View | Download |
|---|---|---|
| Dashboard | [`dashboard/TB_Trends_Ghana_Dashboard.html`](dashboard/TB_Trends_Ghana_Dashboard.html) | Open raw file in browser |
| Poster (A0) | [`poster/TB_Trends_Ghana_Poster.html`](poster/TB_Trends_Ghana_Poster.html) | Open raw file in browser or print to PDF at 841×1189mm |

Both are self-contained (vanilla JS + inline SVG, no external libraries/CDNs), colourblind-safe, and under 60KB.

## 10. Data dictionary

See `outputs/release/variable_provenance.csv` — every variable in the two release CSVs documented with definition, source, years covered, unit, and data type (41 variables total).

## 11. Analytical verification

- `qa/qa_6pass.py` — 13-panel QA protocol (data integrity, statistical trace, figure/table quality, references, writing quality, cross-referencing, reporting standards, declarations). Badge: `qa/QA_PASSED_2026-07-01.txt`.
- `tests/test_pipeline.py` — reproducibility sanity tests, run in CI.

## 12. Citation

See `CITATION.cff`. Suggested citation:

> Ghanem VG. Trends, Treatment Gaps and LSTM Forecasting of Tuberculosis in Ghana, with District-Level Structural Risk Stratification. 2026. https://github.com/valentineghanem-bit/tb-trends-lstm-forecasting-ghana

## 13. License & ethics

Code and data: MIT License (`LICENSE`). This study analyses publicly available, de-identified, aggregate secondary data; no individual-level records or human participants are involved. Exempt from full ethical review under Ghana Health Service Ethics Review Committee guidance on secondary analysis of anonymised public data.

## 14. Acknowledgements & contact

Valentine Golden Ghanem, COCOBOD Cocoa Clinic / University of Cape Coast. ORCID: [0009-0002-8332-0220](https://orcid.org/0009-0002-8332-0220). Contact: valentineghanem@gmail.com.

Data acknowledgements: WHO Global Health Observatory, Ghana Statistical Service.
