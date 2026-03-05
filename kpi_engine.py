"""
GSK CTC Analytics – Modelling & KPI Engine
Phase 3: Modelling
Builds KPI scorecards, trend models, and a simple sales forecast.
"""

import pandas as pd
import numpy as np
from scipy import stats
import warnings, os
warnings.filterwarnings("ignore")


# ── 1. KPI Scorecard ──────────────────────────────────────────────────────────
def build_kpi_scorecard(ims_df, sku_df, dist_df):
    """Produces a brand-level KPI scorecard for the latest available period."""
    latest = ims_df["date"].max()
    prev_q = latest - pd.DateOffset(months=3)

    # IMS recent vs previous quarter
    ims_latest = ims_df[ims_df["date"] == latest][["brand", "ims_units", "market_share", "yoy_growth_pct"]]
    ims_prev   = ims_df[ims_df["date"] == prev_q][["brand", "ims_units"]].rename(
        columns={"ims_units": "ims_prev"})

    scorecard = ims_latest.merge(ims_prev, on="brand", how="left")
    scorecard["qoq_growth_pct"] = (
        (scorecard["ims_units"] - scorecard["ims_prev"]) / scorecard["ims_prev"] * 100
    ).round(2)

    # Stock coverage from SKU (latest month)
    stock_avg = sku_df[sku_df["date"] == latest].groupby("brand")["stock_avail_pct"].mean().round(1)
    scorecard = scorecard.merge(stock_avg.rename("avg_stock_pct"), on="brand", how="left")

    # Rx growth from SKU
    rx = sku_df[sku_df["date"] == latest].groupby("brand")["rx_growth_pct"].mean().round(2)
    scorecard = scorecard.merge(rx.rename("rx_growth_pct"), on="brand", how="left")

    # Score each KPI (0-100)
    def score(series, low, high):
        return ((series - low) / (high - low) * 100).clip(0, 100).round(1)

    scorecard["score_ims_growth"]  = score(scorecard["yoy_growth_pct"],  -10, 30)
    scorecard["score_market_share"]= score(scorecard["market_share"],      5, 35)
    scorecard["score_stock"]       = score(scorecard["avg_stock_pct"],    60, 100)
    scorecard["score_rx"]          = score(scorecard["rx_growth_pct"],    -5, 20)

    scorecard["composite_kpi"] = (
        scorecard["score_ims_growth"]   * 0.35 +
        scorecard["score_market_share"] * 0.25 +
        scorecard["score_stock"]        * 0.25 +
        scorecard["score_rx"]           * 0.15
    ).round(1)

    scorecard["kpi_grade"] = pd.cut(
        scorecard["composite_kpi"],
        bins=[0, 40, 60, 75, 90, 101],
        labels=["D", "C", "B", "A", "S"]
    )

    scorecard = scorecard.sort_values("composite_kpi", ascending=False).reset_index(drop=True)
    print(f"[✓] KPI Scorecard built: {len(scorecard)} brands")
    return scorecard


# ── 2. Trend Analysis ─────────────────────────────────────────────────────────
def analyze_trends(ims_df):
    """Linear trend analysis per brand over the full 3-year window."""
    results = []
    for brand, grp in ims_df.groupby("brand"):
        grp = grp.sort_values("date")
        x = np.arange(len(grp))
        y = grp["ims_units"].values

        slope, intercept, r, p, se = stats.linregress(x, y)
        trend_pct = (slope / np.mean(y) * 100) if np.mean(y) > 0 else 0

        results.append({
            "brand":      brand,
            "slope":      round(slope, 1),
            "r_squared":  round(r**2, 3),
            "p_value":    round(p, 4),
            "trend_pct_monthly": round(trend_pct, 3),
            "trend_direction": "↑ Growth" if slope > 0 else "↓ Decline",
            "significant": p < 0.05,
        })

    df = pd.DataFrame(results).sort_values("trend_pct_monthly", ascending=False)
    print(f"[✓] Trend analysis: {len(df)} brands")
    return df


# ── 3. Simple Forecast (Linear Extrapolation + Seasonal) ─────────────────────
def forecast_ims(ims_df, brand, months_ahead=6):
    """Holt-Winters-lite forecast for a single brand."""
    grp = ims_df[ims_df["brand"] == brand].sort_values("date").copy()
    grp["t"] = np.arange(len(grp))

    # Fit linear trend
    slope, intercept, *_ = stats.linregress(grp["t"], grp["ims_units"])

    # Seasonal indices (monthly)
    grp["detrended"] = grp["ims_units"] - (slope * grp["t"] + intercept)
    seasonal_idx = grp.groupby("month")["detrended"].mean()

    # Forecast
    last_t = grp["t"].max()
    last_date = grp["date"].max()
    rows = []
    for i in range(1, months_ahead + 1):
        future_date = last_date + pd.DateOffset(months=i)
        t = last_t + i
        trend_val = slope * t + intercept
        seas      = seasonal_idx.get(future_date.month, 0)
        forecast  = max(0, trend_val + seas)
        ci        = forecast * 0.12  # ±12% confidence band

        rows.append({
            "date":       future_date,
            "brand":      brand,
            "forecast":   round(forecast),
            "ci_lower":   round(max(0, forecast - ci)),
            "ci_upper":   round(forecast + ci),
            "is_forecast": True,
        })

    # Actuals portion
    hist = grp[["date", "brand", "ims_units"]].copy()
    hist.rename(columns={"ims_units": "forecast"}, inplace=True)
    hist["is_forecast"] = False
    hist["ci_lower"] = hist["forecast"]
    hist["ci_upper"] = hist["forecast"]

    return pd.concat([hist, pd.DataFrame(rows)], ignore_index=True)


def build_all_forecasts(ims_df, months_ahead=6):
    all_fc = []
    for brand in ims_df["brand"].unique():
        fc = forecast_ims(ims_df, brand, months_ahead)
        all_fc.append(fc)
    df = pd.concat(all_fc, ignore_index=True)
    print(f"[✓] Forecasts built: {len(df)} rows ({months_ahead} months ahead)")
    return df


# ── 4. Distributor Clustering ─────────────────────────────────────────────────
def cluster_distributors(dist_df):
    """Segment distributors into 4 performance clusters using simple k-means-lite."""
    latest_year = dist_df["year"].max()
    agg = dist_df[dist_df["year"] == latest_year].groupby("distributor_id").agg(
        avg_achievement   = ("achievement_pct",    "mean"),
        avg_coverage      = ("outlet_coverage_pct","mean"),
        avg_otd           = ("on_time_delivery_pct","mean"),
        avg_returns       = ("return_rate_pct",    "mean"),
        avg_composite     = ("composite_score",    "mean"),
    ).reset_index()

    # Simple quantile-based clustering
    agg["cluster"] = pd.qcut(
        agg["avg_composite"],
        q=4,
        labels=["Underperformer", "Developing", "Performer", "Champion"]
    )

    print(f"[✓] Distributor clusters: {agg['cluster'].value_counts().to_dict()}")
    return agg


# ── 5. Decilo-Meter Insights ──────────────────────────────────────────────────
def decilometer_insights(decile_df):
    """Pareto + concentration metrics on top decile pharmacies."""
    by_decile = decile_df.groupby("decile").agg(
        total_outlets   = ("total_outlets",   "sum"),
        total_sales_pkr = ("total_sales_pkr", "sum"),
        avg_brands      = ("avg_brands",      "mean"),
        active_pct      = ("active_pct",      "mean"),
    ).reset_index()

    total_sales = by_decile["total_sales_pkr"].sum()
    by_decile["sales_share_pct"]   = (by_decile["total_sales_pkr"] / total_sales * 100).round(2)
    by_decile["cumul_sales_pct"]   = by_decile["sales_share_pct"].cumsum().round(2)

    top2_share = by_decile[by_decile["decile"] >= 9]["sales_share_pct"].sum()
    print(f"[✓] Decilo-meter: Top 2 deciles = {top2_share:.1f}% of total sales (Pareto insight)")
    return by_decile


# ── Main ──────────────────────────────────────────────────────────────────────
def run_modelling():
    print("\n🟠 PHASE 3 – MODELLING\n" + "=" * 45)

    ims_df  = pd.read_csv("data/processed/ims_tms_clean.csv",    parse_dates=["date"])
    sku_df  = pd.read_csv("data/processed/sku_clean.csv",        parse_dates=["date"])
    dist_df = pd.read_csv("data/processed/distributor_clean.csv",parse_dates=["date"])
    dec_df  = pd.read_csv("data/processed/decilometer.csv")

    scorecard  = build_kpi_scorecard(ims_df, sku_df, dist_df)
    trends     = analyze_trends(ims_df)
    forecasts  = build_all_forecasts(ims_df, months_ahead=6)
    clusters   = cluster_distributors(dist_df)
    decilo     = decilometer_insights(dec_df)

    os.makedirs("data/processed", exist_ok=True)
    scorecard.to_csv("data/processed/kpi_scorecard.csv",  index=False)
    trends.to_csv("data/processed/trend_analysis.csv",    index=False)
    forecasts.to_csv("data/processed/ims_forecasts.csv",  index=False)
    clusters.to_csv("data/processed/dist_clusters.csv",   index=False)
    decilo.to_csv("data/processed/decilo_insights.csv",   index=False)

    print("\n[✓] All modelling outputs saved.")
    return scorecard, trends, forecasts, clusters, decilo


if __name__ == "__main__":
    run_modelling()
