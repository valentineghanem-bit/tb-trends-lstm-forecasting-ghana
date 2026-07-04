# Trends, Treatment Gaps and LSTM Forecasting of Tuberculosis in Ghana, with District-Level Structural Risk Stratification

**A 25-year national forecasting study (2000-2024) paired with a 261-district structural TB-vulnerability index**

[![CI](https://github.com/valentineghanem-bit/tb-trends-lstm-forecasting-ghana/actions/workflows/ci.yml/badge.svg)](https://github.com/valentineghanem-bit/tb-trends-lstm-forecasting-ghana/actions/workflows/ci.yml)
&nbsp;Reporting: STROBE + RECORD + TRIPOD &nbsp;·&nbsp; License: MIT &nbsp;·&nbsp; [ORCID 0009-0002-8332-0220](https://orcid.org/0009-0002-8332-0220)

---

## 1. Overview

This repository contains the full, reproducible analysis behind a 25-year (2000-2024) national study of Ghana's
tuberculosis epidemiology — trends, co-primary forecasting (ARIMA, LSTM, XGBoost), and the multidrug-resistant TB
(MDR-TB) treatment-cascade gap — paired with a district-level (261 MMDA) structural risk-stratification layer. The
two analytic tracks are deliberately decoupled: no district-level TB surveillance data exists anywhere in Ghana's
public reporting, so the district layer characterises general structural deprivation, not observed TB burden.

**Author:** Valentine Golden Ghanem · COCOBOD Cocoa Clinic, Accra, Ghana / University of Cape Coast · ORCID 0009-0002-8332-0220.

## 2. Key findings

- National TB incidence declined **42%** (216 → 126 per 100,000; Sen's slope **−4.0/year, p<0.0001**), 2000-2024.
- **ARIMA substantially outperformed LSTM and XGBoost** for national incidence forecasting (mean absolute error
  **0.37** vs. **3.71** and **4.07**), a finding robust to random seed (5-seed LSTM check, MAE range 3.71-4.24) and
  to matching model-selection protocols (fold-1-locked ARIMA order).
- MDR-TB testing and treatment-initiation capacity expanded significantly, but treatment success showed **no
  significant improving trend (p=0.13)** over 2010-2022.
- The district TB-Vulnerability Index (TVI) shows strong spatial clustering (**Moran's I=0.80, p=0.001**;
  Gi*/PCA agreement r=0.987) concentrated in northern Ghana — a general structural-deprivation construct, not
  validated TB-specific risk.

## 3. Study design

Dual-track ecological design: **Track A** — a national, longitudinal (2000-2024) time-series analysis of WHO
Global Health Observatory TB indicators, using pre-registered, fold-1-only hyperparameter locking and co-primary
(ARIMA/LSTM/XGBoost) rolling-origin cross-validation forecasting; **Track B** — a district-level (n=261),
cross-sectional (2021) PCA-based structural-deprivation index with Global Moran's I / Getis-Ord Gi* / LISA spatial
statistics. Reported per STROBE (observational studies), RECORD (routinely-collected health data), and a
TRIPOD-adapted forecasting checklist. The TVI is not validated against district TB outcomes — no such data exists
in Ghana's public reporting — and is declared throughout as a structural-deprivation screening tool, not a TB risk
predictor.

## 4. Data sources

| Source | Unit | Used for |
|---|---|---|
| WHO Global Health Observatory | Country, annual | TB incidence/notification/MDR/HIV-coinfection indicators, health financing, health workforce, global health estimates (2000-2024) |
| WHO Global Tuberculosis Report 2024 | Country | Corroborating national estimates and MDR-TB context |
| Ghana Statistical Service 2021 Population & Housing Census | District (261) | Poverty, literacy, insurance, employment, demography for the TB-Vulnerability Index |
| Ghana district boundary GeoJSON | 260 polygons | Choropleth + spatial weights (261→260 crosswalk; one merged district) |

All inputs are public-domain, aggregate, secondary data; no individual-level records.

## 5. Repository structure

```
.
├── analysis/         build_master · build_vulnerability_index · lock_hyperparameters · mann_kendall_trends
│                     · forecast_rolling_origin · mdr_subanalysis · spatial_analysis · shap_decomposition
│                     · build_figures · build_release_package · _labels
├── outputs/
│   ├── data/         intermediate analysis outputs (locked hyperparameters, forecast folds, etc.)
│   ├── tables/        manuscript tables (table1a, table1b, table2, table3, table4, CSV)
│   ├── figures/        manuscript figures (figure1–figure6, 300 dpi, colourblind-safe)
│   └── release/        FAIR-compliant master CSVs + variable_provenance.csv (data dictionary)
├── dashboard/        TB_Trends_Ghana_Dashboard.html (self-contained, inline ECharts)
├── poster/           TB_Trends_Ghana_Poster.html (A0, print-ready)
├── qa/               qa_6pass.py · QA_PASSED_2026-07-01.txt
├── tests/            test_pipeline.py (5 reproducibility tests)
├── docs/             stage-by-stage methodology documentation
├── .github/workflows/ci.yml
├── CITATION.cff · LICENSE · README.md · requirements.txt · .gitignore
```

## 6. Methods / pipeline

1. **Master datasets** (`build_master.py`) — WHO-GHO exact-indicator extraction (2000-2024 national panel) +
   GSS census → 261-district structural covariates.
2. **Vulnerability index** (`build_vulnerability_index.py`) — TB-Vulnerability Index via PCA (PC1) and an
   equal-weight comparator, both retained for robustness comparison.
3. **Hyperparameter lock** (`lock_hyperparameters.py`) — LSTM/XGBoost architecture and hyperparameters
   pre-registered on fold 1 only, then frozen for all subsequent folds to prevent overfitting-via-architecture-search.
4. **Trend + forecasting** (`mann_kendall_trends.py`, `forecast_rolling_origin.py`) — Mann-Kendall/Sen's slope
   trend tests across all Track A series; rolling-origin (walk-forward) cross-validation comparing ARIMA, LSTM
   and XGBoost as co-primary models, with COVID-era (2020-2021) sensitivity comparison.
5. **MDR-TB cascade + spatial** (`mdr_subanalysis.py`, `spatial_analysis.py`) — shorter-window cascade
   sub-analysis, individually continuity-verified per series; queen contiguity, Global Moran's I, Getis-Ord Gi*,
   FDR-adjusted Local Moran's I (LISA) on district TVI.
6. **Interpretation + release** (`shap_decomposition.py`, `build_figures.py`, `build_release_package.py`) —
   SHAP feature importance for the XGBoost forecast; 6 manuscript figures; the FAIR master CSV release.

## 7. Reproducibility

```bash
pip install -r requirements.txt                # CI-installable (Python 3.11+)
python analysis/build_master.py                # national panel + district vulnerability master CSVs
python analysis/build_vulnerability_index.py   # TB-Vulnerability Index (PCA + equal-weight)
python analysis/lock_hyperparameters.py        # pre-registered LSTM/XGBoost hyperparameter lock (fold-1 only)
python analysis/mann_kendall_trends.py         # trend tests, all Track A series
python analysis/forecast_rolling_origin.py     # LSTM/ARIMA/XGBoost rolling-origin CV forecasting
python analysis/mdr_subanalysis.py             # MDR-TB cascade shorter-window sub-analysis
python analysis/spatial_analysis.py            # Moran's I / Getis-Ord Gi* / LISA on district TVI
python analysis/shap_decomposition.py          # SHAP feature importance, XGBoost forecast
python analysis/build_figures.py               # 6 manuscript figures
python analysis/build_release_package.py       # FAIR master CSV release + data dictionary
python qa/qa_6pass.py                          # 16-panel QA protocol (requires local manuscript, not in repo)
pytest tests/ -v                                # 5 reproducibility tests
```

Random seed fixed throughout. Software: Python 3.11, pandas, statsmodels, scikit-learn, TensorFlow/Keras (LSTM),
XGBoost, SHAP, libpysal, esda. Continuous integration (`.github/workflows/ci.yml`) installs dependencies, compiles
all scripts, rebuilds the master datasets, and runs the test suite on every push.

## 8. Outputs

- `outputs/figures/` — 6 manuscript figures (incidence trend, forecast comparison, MDR-TB cascade, TVI
  choropleth, LISA clusters, SHAP importance; 300 dpi, colourblind-safe Okabe-Ito palette).
- `outputs/tables/` — 5 manuscript tables (national panel summary, Mann-Kendall trends, MDR sub-analysis,
  district vulnerability summary, SHAP importance).
- `outputs/release/` — FAIR master CSV release (national panel + district vulnerability) with a full data
  dictionary.

## 9. Dashboard & poster — view or download

Both are self-contained offline HTML files (**inline ECharts + inline district geometry** — no CDN, no server),
colourblind-safe, and interactive (zoomable TVI choropleth + LISA cluster map, cluster/metric/focus-district
filters, threshold flagging, CSV/PNG export).

| Artefact | View on GitHub | Live preview | Direct download (raw HTML) |
|---|---|---|---|
| Interactive dashboard | [View](https://github.com/valentineghanem-bit/tb-trends-lstm-forecasting-ghana/blob/main/dashboard/TB_Trends_Ghana_Dashboard.html) | [Preview](https://htmlpreview.github.io/?https://github.com/valentineghanem-bit/tb-trends-lstm-forecasting-ghana/blob/main/dashboard/TB_Trends_Ghana_Dashboard.html) | [Download](https://raw.githubusercontent.com/valentineghanem-bit/tb-trends-lstm-forecasting-ghana/main/dashboard/TB_Trends_Ghana_Dashboard.html) |
| Conference poster (A0, HTML) | [View](https://github.com/valentineghanem-bit/tb-trends-lstm-forecasting-ghana/blob/main/poster/TB_Trends_Ghana_Poster.html) | [Preview](https://htmlpreview.github.io/?https://github.com/valentineghanem-bit/tb-trends-lstm-forecasting-ghana/blob/main/poster/TB_Trends_Ghana_Poster.html) | [Download](https://raw.githubusercontent.com/valentineghanem-bit/tb-trends-lstm-forecasting-ghana/main/poster/TB_Trends_Ghana_Poster.html) |

> **Tip:** both files are fully self-contained — ECharts and the district map geometry are inlined — so they
> render **offline** with no server or network. The poster is print-ready at A0 (841 × 1189 mm). Open a
> downloaded copy with `start dashboard\TB_Trends_Ghana_Dashboard.html` (Windows), `open …` (macOS) or
> `xdg-open …` (Linux). Built with the bespoke HI-EI pipeline (inline ECharts + inline SVG; supersedes the
> legacy 60 KB ceiling).

## 10. Data dictionary

See [`outputs/release/variable_provenance.csv`](outputs/release/variable_provenance.csv) — definition, source,
years covered, unit and data type for all 41 variables across the two release CSVs.

## 11. Analytical verification

- `pytest tests/` — 5 reproducibility sanity tests on the rebuilt master datasets, run in CI.
- `python qa/qa_6pass.py` — 16-panel QA protocol (data integrity, statistical trace, figure/table quality,
  ascending-order figure/table citation check in Results, orphaned-reference check, references, writing
  quality, cross-referencing, reporting standards, declarations); badge
  [`qa/QA_PASSED_2026-07-01.txt`](qa/QA_PASSED_2026-07-01.txt).
- Dashboard and poster were render-verified headlessly. All headline numbers (42%, 216, 126, −4.0, 0.37, 3.71,
  4.07, 0.80, 0.987) are reconciled across the manuscript, the master CSV release, the dashboard, and the poster.

## 12. Citation

See [`CITATION.cff`](CITATION.cff). Ghanem VG. *Trends, Treatment Gaps and LSTM Forecasting of Tuberculosis in
Ghana, with District-Level Structural Risk Stratification.* 2026. ORCID 0009-0002-8332-0220. **Target journal:**
*The International Journal of Tuberculosis and Lung Disease* (Q1).

## 13. License & ethics

MIT License (see [`LICENSE`](LICENSE)); source datasets retain their original terms. This study analyses publicly
available, de-identified, aggregate secondary data; no individual-level records or human participants are
involved. Exempt from full ethical review under Ghana Health Service Ethics Review Committee guidance on
secondary analysis of anonymised public data.

## 14. Acknowledgements & contact

WHO Global Health Observatory and the Ghana Statistical Service for open data. Forecasting used statsmodels,
TensorFlow/Keras and XGBoost; spatial analysis used esda and libpysal.
Contact: Valentine Golden Ghanem — valentineghanem@gmail.com · ORCID 0009-0002-8332-0220.
