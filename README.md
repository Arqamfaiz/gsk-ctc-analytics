# 💊 GSK CTC Analytics — Pakistan Pharmaceutical Sales Intelligence

> **A complete end-to-end analytics project** built on real-world work conducted during a Project Trainee tenure at GSK Pakistan (Oct 2024 – Apr 2025), covering the Consumer Trade Category (CTC) portfolio of distribute-only pharmaceutical brands.

---

## 🗂️ Project Overview

During the GSK tenure, several high-impact analytical projects were executed spanning brand performance tracking, product launch monitoring, BI dashboard development, distributor conference analytics, and top-decile pharmacy insights. This repository recreates that analytical framework as a portfolio-grade data science project.

| Phase | Name | Description |
|-------|------|-------------|
| 1️⃣ | **Development** | Synthetic data generation pipeline for 55K+ outlets, 14 brands, 32 distributors |
| 2️⃣ | **Preparation** | Data cleaning, feature engineering, KPI derivation |
| 3️⃣ | **Modelling** | KPI scoring, trend analysis, sales forecasting, clustering |
| 4️⃣ | **Evaluation** | 8 publication-quality charts + interactive HTML dashboard |

---

## 📊 Live Dashboard

Open `dashboard/index.html` in any browser for the **full interactive dashboard** with 6 tabs:

| Tab | Content |
|-----|---------|
| 📊 Overview | IMS/TMS 2-year trend, category split, priority mix |
| 💊 Brand Performance | KPI scorecard table, market share polar chart |
| 🚀 PASBAAN Launch | 3-KPI launch tracking vs targets |
| 🚚 Distributor Network | Regional performance, cluster segments |
| 📍 Decilo-Meter | Pareto analysis of 55K pharmacy outlets |
| 📈 Forecast | 6-month IMS forecast with confidence intervals |

---

## 🏗️ Project Structure

```
gsk-ctc-analytics/
│
├── data/
│   ├── raw/                        # Generated raw datasets
│   │   ├── ims_tms_monthly.csv     # 3-year IMS/TMS data (14 brands)
│   │   ├── brand_sku_performance.csv
│   │   ├── distributor_performance.csv
│   │   ├── outlet_data.csv         # 55,000 pharmacy outlets
│   │   └── pasbaan_launch_kpis.csv
│   └── processed/                  # Cleaned & engineered datasets
│       ├── ims_tms_clean.csv
│       ├── kpi_scorecard.csv
│       ├── ims_forecasts.csv
│       ├── dist_clusters.csv
│       └── decilometer.csv
│
├── src/
│   ├── data_generator.py           # Phase 1 – Synthetic data engine
│   ├── preprocessing.py            # Phase 2 – Cleaning & feature engineering
│   ├── kpi_engine.py               # Phase 3 – KPI modelling & forecasting
│   └── visualizations.py           # Phase 4 – Matplotlib/Seaborn charts
│
├── dashboard/
│   └── index.html                  # Standalone interactive dashboard (Chart.js)
│
├── reports/
│   └── figures/                    # 8 exported PNG charts
│       ├── 01_ims_tms_trend.png
│       ├── 02_market_share_heatmap.png
│       ├── 03_kpi_scorecard.png
│       ├── 04_pasbaan_launch.png
│       ├── 05_ims_forecast.png
│       ├── 06_distributor_perf.png
│       ├── 07_decilometer_pareto.png
│       └── 08_portfolio_map.png
│
├── run_pipeline.py                 # 🚀 One-click pipeline runner
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation & Usage

### Prerequisites
- Python 3.9+
- pip

### Setup

```bash
git clone https://github.com/<your-username>/gsk-ctc-analytics.git
cd gsk-ctc-analytics
pip install -r requirements.txt
```

### Run the Full Pipeline

```bash
python run_pipeline.py
```

This runs all 4 phases sequentially:

```
🔵 PHASE 1 – DATA GENERATION
🟡 PHASE 2 – DATA PREPARATION
🟠 PHASE 3 – MODELLING
🟢 PHASE 4 – EVALUATION & VISUALIZATIONS
```

### View Dashboard

```bash
# Simply open in browser
open dashboard/index.html
```

---

## 🧠 Analytical Components

### Phase 1 — Data Development

Generates 5 realistic datasets inspired by the GSK Pakistan market:

| Dataset | Rows | Description |
|---------|------|-------------|
| `ims_tms_monthly` | 504 | Monthly IMS/TMS for 14 brands, Jan 2022–Dec 2024 |
| `brand_sku_performance` | 1,008 | SKU-level units, stock availability, Rx growth |
| `distributor_performance` | 1,152 | 32 distributors × 36 months × 5 KPIs |
| `outlet_data` | 55,000 | Full pharmacy outlet universe with decile assignment |
| `pasbaan_launch_kpis` | 7 | Month-by-month PASBAAN launch tracking |

### Phase 2 — Preparation

- Null handling and value clipping
- YoY and QoQ growth calculations
- Rolling 3-month moving averages
- Distributor performance tiers (Composite score = Achievement × 40% + Coverage × 30% + OTD × 20% + Returns × 10%)
- Decilo-meter feature engineering (decile × region aggregation)
- Low stock flags (`stock_avail_pct < 80%`)

### Phase 3 — Modelling

| Model | Method | Output |
|-------|--------|--------|
| **KPI Scorecard** | Weighted multi-KPI index | Brand grades S/A/B/C/D |
| **Trend Analysis** | OLS linear regression per brand | Slope, R², p-value, trend direction |
| **Sales Forecast** | Linear extrapolation + seasonal index | 6-month forecast + 95% CI |
| **Distributor Clusters** | Quantile-based segmentation | Champion / Performer / Developing / Underperformer |
| **Decilo-Meter** | Pareto concentration analysis | Sales share by decile, cumulative curve |

### Phase 4 — Evaluation

Eight charts across all analytical themes:

1. **IMS vs TMS Trend** — Top 5 brands, 3-year line chart
2. **Market Share Heatmap** — Brand × Year matrix
3. **KPI Scorecard** — Horizontal bar chart with grade labels
4. **PASBAAN Launch Dashboard** — 4-panel KPI grid (Rx, Stock, Acquisition, Sales Index)
5. **Sales Forecast** — Actual vs forecast + CI band
6. **Distributor Performance** — Regional composite + KPI breakdown
7. **Decilo-Meter Pareto** — Dual-axis bar + cumulative line
8. **Portfolio Bubble Map** — Market share vs growth, bubble = volume

---

## 📈 Key Insights

- **Panadol & Augmentin** are consistent volume leaders (Priority A), with stable YoY growth of 7–9%
- **PASBAAN** launch in Dec 2024 exceeded stock coverage and Rx targets within 3 months, achieving **+15% sales uplift**
- **Top 2 deciles (D9+D10)** represent ~26% of total pharmacy sales — validating a top-decile-first sales strategy
- **Karachi** leads distributor composite performance (91.2), driven by highest outlet coverage and achievement
- **Respiratory** category shows strongest seasonal trend (Q3–Q4 peaks due to climate)

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.x | Core analysis language |
| Pandas | Data manipulation |
| NumPy | Numerical operations |
| SciPy | Statistical modelling (OLS, linregress) |
| Scikit-learn | Quantile-based clustering |
| Matplotlib | Static chart generation |
| Seaborn | Statistical visualizations |
| Chart.js | Interactive browser dashboard |
| HTML/CSS/JS | Dashboard front-end |

---

## 👤 About

Built by **Arqam Faiz Siddiqui** as a portfolio project reflecting real analytical work conducted during a Project Trainee role at **GlaxoSmithKline (GSK) Pakistan** — Consumer Healthcare division.

- 📧 arqamfaiz4@gmail.com
- 🔗 [LinkedIn](https://linkedin.com/in/arqam-faiz-siddiqui-500826202)
- 🎓 M.Sc. Information Systems — FAU Erlangen-Nürnberg

> ⚠️ **Note:** All data in this repository is synthetically generated to replicate realistic patterns. No proprietary GSK data is included.

---

## 📄 License

MIT License — free to use and adapt with attribution.
