"""
Stage 14 — Bespoke HI-EI Dashboard. Vanilla JS + inline SVG only, no external
libraries/CDNs, target <=60KB, colourblind-safe (Okabe-Ito), anti-slop
(no pie/3D/dual-axis), accessible (contrast, keyboard, reduced-motion),
mandatory interpretation/limitations caveat box (per DASH-028 pattern).
"""
import json
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
panel = pd.read_csv(ROOT / "outputs/data/master_tb_national_panel.csv")
panel = panel[panel["year"].between(2000, 2024)].reset_index(drop=True)
district = pd.read_csv(ROOT / "outputs/data/master_district_vulnerability.csv")
mdr = pd.read_csv(ROOT / "outputs/tables/table3_mdr_subanalysis.csv")

OI = {"blue": "#0072B2", "orange": "#E69F00", "green": "#009E73", "red": "#D55E00",
      "purple": "#CC79A7", "grey": "#8c8c8c"}


def svg_line_chart(x, y, width=760, height=260, color=OI["blue"], y_label="", title_id="chart1"):
    pad_l, pad_r, pad_t, pad_b = 55, 20, 20, 35
    w, h = width - pad_l - pad_r, height - pad_t - pad_b
    xmin, xmax = min(x), max(x)
    ymin, ymax = 0, max(y) * 1.1
    def px(xv): return pad_l + (xv - xmin) / (xmax - xmin) * w
    def py(yv): return pad_t + h - (yv - ymin) / (ymax - ymin) * h
    pts = " ".join(f"{px(xi):.1f},{py(yi):.1f}" for xi, yi in zip(x, y))
    # gridlines + y ticks
    yticks = [ymin + i * (ymax - ymin) / 4 for i in range(5)]
    grid = "".join(
        f'<line x1="{pad_l}" y1="{py(t):.1f}" x2="{width-pad_r}" y2="{py(t):.1f}" stroke="#e5e5e5" stroke-width="1"/>'
        f'<text x="{pad_l-8}" y="{py(t)+4:.1f}" font-size="10" text-anchor="end" fill="#555">{t:.0f}</text>'
        for t in yticks
    )
    xticks = [x[0], x[len(x)//2], x[-1]]
    xaxis = "".join(
        f'<text x="{px(t):.1f}" y="{height-pad_b+18}" font-size="10" text-anchor="middle" fill="#555">{t}</text>'
        for t in xticks
    )
    circles = "".join(f'<circle cx="{px(xi):.1f}" cy="{py(yi):.1f}" r="2.5" fill="{color}"/>' for xi, yi in zip(x, y))
    return f'''<svg viewBox="0 0 {width} {height}" role="img" aria-labelledby="{title_id}" style="width:100%;height:auto">
<title id="{title_id}">{y_label} trend, {xmin}-{xmax}</title>
{grid}
<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.5"/>
{circles}
{xaxis}
</svg>'''


def svg_bar_chart(labels, values, width=760, height=260, color=OI["orange"], title_id="chart2", y_label=""):
    pad_l, pad_r, pad_t, pad_b = 55, 20, 20, 70
    w, h = width - pad_l - pad_r, height - pad_t - pad_b
    vmax = max(values) * 1.15 if values else 1
    n = len(labels)
    bw = w / n * 0.6
    gap = w / n
    bars, xlabels = [], []
    for i, (lab, val) in enumerate(zip(labels, values)):
        bh = (val / vmax) * h
        bx = pad_l + i * gap + (gap - bw) / 2
        by = pad_t + h - bh
        bars.append(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{color}"/>')
        bars.append(f'<text x="{bx+bw/2:.1f}" y="{by-4:.1f}" font-size="10" text-anchor="middle" fill="#333">{val:.0f}</text>')
        xlabels.append(f'<text x="{bx+bw/2:.1f}" y="{height-pad_b+14}" font-size="9" text-anchor="end" fill="#555" transform="rotate(-35 {bx+bw/2:.1f} {height-pad_b+14})">{lab}</text>')
    return f'''<svg viewBox="0 0 {width} {height}" role="img" aria-labelledby="{title_id}" style="width:100%;height:auto">
<title id="{title_id}">{y_label}</title>
<line x1="{pad_l}" y1="{pad_t+h}" x2="{width-pad_r}" y2="{pad_t+h}" stroke="#999"/>
{''.join(bars)}
{''.join(xlabels)}
</svg>'''


years = panel["year"].tolist()
incidence = panel["tb_incidence_per100k"].tolist()
tx_success = panel["tx_success_new_pct"].dropna().tolist()
tx_years = panel.loc[panel["tx_success_new_pct"].notna(), "year"].tolist()

mdr_labels = [r["variable"].replace("_", " ") for _, r in mdr.iterrows()]
mdr_slopes = [abs(r["sens_slope"]) for _, r in mdr.iterrows()]

top10 = district.nlargest(10, "tvi_pca")[["district", "tvi_pca"]]
bot10 = district.nsmallest(10, "tvi_pca")[["district", "tvi_pca"]]

chart_incidence = svg_line_chart(years, incidence, color=OI["blue"], y_label="TB incidence per 100,000", title_id="c1")
chart_tx = svg_line_chart(tx_years, tx_success, color=OI["green"], y_label="Treatment success, new cases (%)", title_id="c2")
chart_mdr = svg_bar_chart(mdr_labels, mdr_slopes, color=OI["orange"], y_label="MDR-TB cascade: |Sen's slope| per year", title_id="c3")
chart_tvi = svg_bar_chart(top10["district"].tolist(), top10["tvi_pca"].tolist(), color=OI["red"], y_label="Top 10 most-vulnerable districts (TVI-PCA)", title_id="c4")

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TB Trends & Forecasting Ghana — Dashboard</title>
<style>
  :root {{
    --primary: #6c3483; --ink: #1a1a1a; --bg: #fafafa; --card-bg: #ffffff;
    --border: #e0e0e0; --accent: #0072B2; --warn-bg: #fff3e0; --warn-border: #E69F00;
  }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, "Segoe UI", Arial, sans-serif; margin: 0; background: var(--bg); color: var(--ink); line-height: 1.5; }}
  header {{ background: var(--primary); color: #fff; padding: 24px 32px; }}
  header h1 {{ margin: 0 0 4px; font-size: 1.5rem; }}
  header p {{ margin: 0; opacity: 0.9; font-size: 0.9rem; }}
  main {{ max-width: 1200px; margin: 0 auto; padding: 24px 16px 48px; }}
  .hero {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 10px; padding: 24px; margin-bottom: 24px; text-align: center; }}
  .hero .metric {{ font-size: 3rem; font-weight: 700; color: var(--accent); }}
  .hero .label {{ font-size: 1rem; color: #555; margin-top: 4px; }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }}
  .kpi-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 10px; padding: 16px; }}
  .kpi-card .value {{ font-size: 1.6rem; font-weight: 700; }}
  .kpi-card .delta {{ font-size: 0.85rem; margin-top: 2px; }}
  .delta.down {{ color: #009E73; }}
  .delta.up {{ color: #D55E00; }}
  .kpi-card .desc {{ font-size: 0.8rem; color: #666; margin-top: 6px; }}
  .chart-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 20px; margin-bottom: 24px; }}
  .chart-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 10px; padding: 16px; }}
  .chart-card h2 {{ font-size: 1rem; margin: 0 0 12px; }}
  .caveat {{ background: var(--warn-bg); border: 1px solid var(--warn-border); border-radius: 10px; padding: 16px; margin-bottom: 24px; font-size: 0.9rem; }}
  .caveat h2 {{ margin: 0 0 8px; font-size: 1rem; }}
  footer {{ text-align: center; font-size: 0.75rem; color: #888; padding: 16px; }}
  button.tab {{ background: #f0f0f0; border: 1px solid var(--border); padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 0.9rem; margin-right: 8px; }}
  button.tab[aria-selected="true"] {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
  button.tab:focus-visible {{ outline: 3px solid #005a9c; outline-offset: 2px; }}
  .track {{ display: none; }}
  .track.active {{ display: block; }}
  @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; transition: none !important; }} }}
</style>
</head>
<body>
<header>
  <h1>Tuberculosis in Ghana: Trends, Treatment Gaps &amp; Forecasting</h1>
  <p>National TB epidemiology (2000&ndash;2024) and district-level structural risk stratification (2021)</p>
</header>
<main>
  <div class="hero">
    <div class="metric">-42%</div>
    <div class="label">National TB incidence decline, 2000&ndash;2024 (216 &rarr; 126 per 100,000; Sen's slope &minus;4.0/yr, p&lt;0.0001)</div>
  </div>

  <div class="kpi-grid">
    <div class="kpi-card"><div class="value">126</div><div class="delta down">&darr; from 216 in 2000</div><div class="desc">TB incidence per 100,000 (2024)</div></div>
    <div class="kpi-card"><div class="value">0.37</div><div class="delta down">vs 3.71 (LSTM), 4.07 (XGBoost)</div><div class="desc">ARIMA forecast MAE (rolling-origin CV)</div></div>
    <div class="kpi-card"><div class="value">p=0.13</div><div class="delta up">no significant trend</div><div class="desc">MDR-TB treatment success, 2010&ndash;2022</div></div>
    <div class="kpi-card"><div class="value">0.80</div><div class="delta up">p=0.001, n=255 districts</div><div class="desc">District TVI Moran's I (spatial clustering)</div></div>
  </div>

  <div role="tablist" aria-label="Dashboard view">
    <button class="tab" role="tab" aria-selected="true" aria-controls="trackA" id="tabA" onclick="showTrack('A')">National Trends &amp; Forecasting</button>
    <button class="tab" role="tab" aria-selected="false" aria-controls="trackB" id="tabB" onclick="showTrack('B')">District Structural Risk</button>
  </div>

  <div id="trackA" class="track active" role="tabpanel" aria-labelledby="tabA">
    <div class="chart-grid">
      <div class="chart-card"><h2>National TB incidence, 2000&ndash;2024</h2>{chart_incidence}</div>
      <div class="chart-card"><h2>Treatment success, new TB cases (%)</h2>{chart_tx}</div>
      <div class="chart-card" style="grid-column:1/-1"><h2>MDR-TB cascade: trend magnitude by series (|Sen's slope|/year)</h2>{chart_mdr}</div>
    </div>
  </div>

  <div id="trackB" class="track" role="tabpanel" aria-labelledby="tabB">
    <div class="chart-grid">
      <div class="chart-card" style="grid-column:1/-1"><h2>Top 10 most-vulnerable districts (TB-Vulnerability Index, PCA)</h2>{chart_tvi}</div>
    </div>
  </div>

  <div class="caveat">
    <h2>Interpretation &amp; limitations</h2>
    <p><strong>National trends (left tab)</strong> are genuine 25-year observed/forecast data from WHO Global Health Observatory. <strong>District risk (right tab)</strong> is a general structural-deprivation index (poverty, illiteracy, insurance, dependency; 2021 census, single timepoint) &mdash; it is <em>NOT</em> observed or validated TB burden. No district-level TB case data exists anywhere in Ghana's public reporting; the district layer is a resource-prioritisation screening tool only, pending future TB-specific validation. Do not interpret district rankings as measured TB incidence.</p>
  </div>
</main>
<footer>
  Data: WHO Global Health Observatory &middot; Ghana Statistical Service 2021 PHC &middot; Generated {pd.Timestamp.now().strftime('%Y-%m-%d')}
</footer>
<script>
function showTrack(t) {{
  document.getElementById('trackA').classList.toggle('active', t==='A');
  document.getElementById('trackB').classList.toggle('active', t==='B');
  document.getElementById('tabA').setAttribute('aria-selected', t==='A');
  document.getElementById('tabB').setAttribute('aria-selected', t==='B');
}}
</script>
</body>
</html>"""

out = ROOT / "dashboard" / "TB_Trends_Ghana_Dashboard.html"
out.parent.mkdir(exist_ok=True)
out.write_text(html, encoding="utf-8")
kb = len(html.encode("utf-8")) / 1024
print(f"Dashboard saved: {out} ({kb:.1f} KB)")
assert kb <= 60, f"Dashboard exceeds 60KB cap: {kb:.1f}KB"
print("60KB cap: PASS")
