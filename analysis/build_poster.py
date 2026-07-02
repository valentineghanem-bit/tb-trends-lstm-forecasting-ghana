"""
Stage 14 — Bespoke A0 Poster. Vanilla HTML/CSS + inline SVG only, no external
libs/CDNs, target <=60KB, colourblind-safe, A0 @page in explicit mm (never a
named CSS page size, per Project 18 lesson), print-ready.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_dashboard import svg_line_chart, svg_bar_chart, OI, years, incidence, tx_years, tx_success, \
    mdr_labels, mdr_slopes, top10

ROOT = Path(__file__).resolve().parent.parent

chart_incidence = svg_line_chart(years, incidence, width=700, height=280, color=OI["blue"], y_label="TB incidence per 100,000", title_id="p1")
chart_tx = svg_line_chart(tx_years, tx_success, width=700, height=280, color=OI["green"], y_label="Treatment success (%)", title_id="p2")
chart_mdr = svg_bar_chart(mdr_labels, mdr_slopes, width=700, height=300, color=OI["orange"], y_label="MDR-TB cascade trend magnitude", title_id="p3")
chart_tvi = svg_bar_chart(top10["district"].tolist(), top10["tvi_pca"].tolist(), width=700, height=300, color=OI["red"], y_label="Top 10 most-vulnerable districts", title_id="p4")

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>TB Trends & Forecasting Ghana — A0 Poster</title>
<style>
  @page {{ size: 841mm 1189mm; margin: 0; }}
  @media print {{ body {{ width: 841mm; height: 1189mm; margin: 0; }} }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, "Segoe UI", Arial, sans-serif; margin: 0; width: 841mm; min-height: 1189mm;
          background: #fff; color: #1a1a1a; }}
  .poster {{ padding: 30mm; display: grid; grid-template-rows: auto auto 1fr auto; gap: 12mm; height: 100%; }}
  header {{ background: #6c3483; color: #fff; padding: 14mm 20mm; border-radius: 6mm; }}
  header h1 {{ margin: 0 0 6mm; font-size: 34pt; line-height: 1.15; }}
  header .authors {{ font-size: 16pt; margin: 0 0 2mm; }}
  header .affil {{ font-size: 13pt; opacity: 0.9; }}
  .banner {{ background: #0072B2; color: #fff; padding: 8mm 14mm; border-radius: 6mm; font-size: 20pt; text-align: center; font-weight: 600; }}
  .grid3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10mm; }}
  .col {{ display: flex; flex-direction: column; gap: 10mm; }}
  .panel {{ background: #fafafa; border: 1px solid #ddd; border-radius: 5mm; padding: 10mm; }}
  .panel h2 {{ font-size: 18pt; margin: 0 0 5mm; color: #6c3483; border-bottom: 2px solid #6c3483; padding-bottom: 2mm; }}
  .panel p, .panel li {{ font-size: 13pt; line-height: 1.5; }}
  .panel svg {{ width: 100%; height: auto; }}
  .limitations {{ background: #fff3e0; border: 2px solid #E69F00; border-radius: 5mm; padding: 8mm; font-size: 12.5pt; }}
  .limitations h2 {{ font-size: 16pt; margin: 0 0 4mm; }}
  .methods-strip {{ display: flex; gap: 6mm; flex-wrap: wrap; font-size: 11.5pt; }}
  .methods-strip span {{ background: #eee; padding: 3mm 6mm; border-radius: 20mm; }}
  footer {{ display: flex; justify-content: space-between; align-items: center; font-size: 11pt; color: #555; border-top: 2px solid #ddd; padding-top: 6mm; }}
  .qr {{ width: 30mm; height: 30mm; background: #eee; border: 1px solid #ccc; display: flex; align-items: center; justify-content: center; font-size: 9pt; color: #777; text-align: center; }}
  .stat {{ font-size: 26pt; font-weight: 700; color: #0072B2; }}
</style>
</head>
<body>
<div class="poster">
  <header>
    <h1>Trends, Treatment Gaps and LSTM Forecasting of Tuberculosis in Ghana, with District-Level Structural Risk Stratification</h1>
    <div class="authors">Valentine Golden Ghanem</div>
    <div class="affil">COCOBOD Cocoa Clinic &middot; University of Cape Coast &middot; ORCID 0009-0002-8332-0220</div>
  </header>

  <div class="banner">National TB incidence declined 42% (2000&ndash;2024), but the MDR-TB treatment-success gap has not closed &mdash; and classical ARIMA outperforms deep learning for small-N annual forecasting.</div>

  <div class="grid3">
    <div class="col">
      <div class="panel">
        <h2>Background &amp; Objectives</h2>
        <p>Ghana's TB control faces two compounding challenges: COVID-19 disrupted case detection worldwide, and MDR-TB treatment success remains below WHO targets across sub-Saharan Africa. No district-level TB surveillance data exists in Ghana's public reporting.</p>
        <ul>
          <li>Characterise 25-year national TB trends &amp; forecast future trajectory</li>
          <li>Quantify the MDR-TB treatment cascade gap</li>
          <li>Compare LSTM, ARIMA, XGBoost for small-N forecasting</li>
          <li>Map district structural TB-vulnerability (not observed burden)</li>
        </ul>
      </div>
      <div class="panel">
        <h2>Methods</h2>
        <div class="methods-strip">
          <span>WHO-GHO 2000&ndash;2024</span><span>Mann-Kendall</span><span>Rolling-origin CV</span>
          <span>LSTM+ARIMA+XGBoost</span><span>Fold-1 hyperparameter lock</span>
          <span>PCA TB-Vulnerability Index</span><span>Moran's I / Gi* / LISA</span><span>SHAP</span>
        </div>
        <p style="margin-top:6mm">Dual-track design: (1) national temporal analysis (2000&ndash;2024, genuine data); (2) district cross-sectional structural-deprivation index (2021 census, single timepoint) &mdash; explicitly not TB-specific.</p>
      </div>
    </div>

    <div class="col">
      <div class="panel">
        <h2>Results: National Trends</h2>
        <p><span class="stat">-42%</span> incidence decline (216&rarr;126/100k, Sen's slope &minus;4.0/yr, p&lt;0.0001)</p>
        {chart_incidence}
      </div>
      <div class="panel">
        <h2>Forecasting Comparison</h2>
        <p>ARIMA (MAE=0.37) vastly outperformed LSTM (3.71) and XGBoost (4.07) &mdash; robust to seed (SD=0.17) and to matching ARIMA's protocol to the other models' (MAE=0.41).</p>
        {chart_tx}
      </div>
    </div>

    <div class="col">
      <div class="panel">
        <h2>MDR-TB Treatment Gap</h2>
        <p>Testing &amp; treatment-initiation capacity expanded significantly, but treatment success showed <strong>no significant trend</strong> (p=0.13). Regional evidence (81.6% success, 9-country cohort) shows this gap is addressable via regimen standardisation.</p>
        {chart_mdr}
      </div>
      <div class="panel">
        <h2>District Structural Risk</h2>
        <p>Strong spatial clustering (Moran's I=0.80, p=0.001; robustness r=0.987) concentrated in northern Ghana &mdash; a general deprivation index, not validated TB risk.</p>
        {chart_tvi}
      </div>
    </div>
  </div>

  <div class="limitations">
    <h2>Interpretation &amp; Limitations</h2>
    <p>National forecasts use N&asymp;25 annual points &mdash; small by published TB-forecasting standards; addressed via pre-registered fold-1-only hyperparameter locking and co-primary (not LSTM-primary) model reporting. The district TB-Vulnerability Index is a <strong>general structural-deprivation/health-access construct</strong>, not observed or validated TB burden &mdash; no district-level TB case data exists anywhere in Ghana's public reporting to validate it against. Ghana's post-2021 COVID-recovery trajectory is undocumented in peer-reviewed literature, unlike comparator African settings (Zambia, Malawi).</p>
  </div>

  <footer>
    <div>Data: WHO Global Health Observatory &middot; Ghana Statistical Service 2021 PHC &middot; Target journal: Int J Tuberculosis &amp; Lung Disease</div>
    <div class="qr">QR:<br>repo link<br>(pending)</div>
  </footer>
</div>
</body>
</html>"""

out = ROOT / "poster" / "TB_Trends_Ghana_Poster.html"
out.parent.mkdir(exist_ok=True)
out.write_text(html, encoding="utf-8")
kb = len(html.encode("utf-8")) / 1024
print(f"Poster saved: {out} ({kb:.1f} KB)")
assert kb <= 60, f"Poster exceeds 60KB cap: {kb:.1f}KB"
print("60KB cap: PASS")
