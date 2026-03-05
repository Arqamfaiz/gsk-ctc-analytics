"""
GSK CTC Analytics – Visualizations
Phase 4: Evaluation
Generates all charts for the final report and dashboard.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import FuncFormatter
import seaborn as sns
import os, warnings
warnings.filterwarnings("ignore")

# ── Style ─────────────────────────────────────────────────────────────────────
GSK_ORANGE  = "#F36F21"
GSK_TEAL    = "#00857C"
GSK_NAVY    = "#00263A"
GSK_LIGHT   = "#F5F5F5"
GSK_GREY    = "#636466"
GSK_GOLD    = "#F7A600"

PALETTE     = [GSK_ORANGE, GSK_TEAL, GSK_NAVY, GSK_GOLD, "#A0522D", "#5F9EA0",
               "#8B4513", "#20B2AA", "#DC143C", "#4682B4", "#DAA520", "#2E8B57",
               "#CD853F", "#708090"]

def fmt_k(x, pos):
    return f"{x/1000:.0f}K" if x >= 1000 else f"{x:.0f}"

sns.set_theme(style="whitegrid", font_scale=1.05)
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "figure.facecolor":  "white",
})

os.makedirs("reports/figures", exist_ok=True)


# ── 1. IMS vs TMS Trend (Top 5 Brands) ───────────────────────────────────────
def plot_ims_tms_trend(ims_df):
    top5 = ims_df.groupby("brand")["ims_units"].sum().nlargest(5).index
    df   = ims_df[ims_df["brand"].isin(top5)].sort_values("date")

    fig, axes = plt.subplots(1, 2, figsize=(16, 6), facecolor="white")
    fig.suptitle("IMS vs TMS Performance – Top 5 Brands (3-Year Trend)",
                 fontsize=16, fontweight="bold", color=GSK_NAVY, y=1.01)

    for ax, metric, title in zip(axes, ["ims_units", "tms_units"],
                                  ["In-Market Sales (IMS)", "Total Market Sales (TMS)"]):
        for i, brand in enumerate(top5):
            sub = df[df["brand"] == brand]
            ax.plot(sub["date"], sub[metric], label=brand, color=PALETTE[i], lw=2.0)
            ax.fill_between(sub["date"], sub[metric], alpha=0.08, color=PALETTE[i])

        ax.set_title(title, fontsize=13, fontweight="bold", color=GSK_NAVY)
        ax.yaxis.set_major_formatter(FuncFormatter(fmt_k))
        ax.set_xlabel("")
        ax.legend(fontsize=9, framealpha=0.5)
        ax.tick_params(axis="x", rotation=30)

    plt.tight_layout()
    fig.savefig("reports/figures/01_ims_tms_trend.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("[✓] Fig 01 – IMS/TMS Trend")


# ── 2. Market Share Heatmap ───────────────────────────────────────────────────
def plot_market_share_heatmap(ims_df):
    pivot = ims_df.pivot_table(index="brand", columns="year",
                                values="market_share", aggfunc="mean").round(1)

    fig, ax = plt.subplots(figsize=(9, 8), facecolor="white")
    sns.heatmap(pivot, annot=True, fmt=".1f", cmap="YlOrRd",
                linewidths=0.5, ax=ax, cbar_kws={"label": "Market Share (%)"})
    ax.set_title("Average Annual Market Share by Brand (%)",
                 fontsize=14, fontweight="bold", color=GSK_NAVY, pad=15)
    ax.set_xlabel("Year", fontsize=11)
    ax.set_ylabel("")
    plt.tight_layout()
    fig.savefig("reports/figures/02_market_share_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("[✓] Fig 02 – Market Share Heatmap")


# ── 3. KPI Scorecard Bar Chart ────────────────────────────────────────────────
def plot_kpi_scorecard(scorecard_df):
    df = scorecard_df.sort_values("composite_kpi", ascending=True)

    grade_colors = {"S": GSK_TEAL, "A": GSK_ORANGE, "B": GSK_GOLD,
                    "C": "#A0A0A0", "D": "#D64550"}
    colors = [grade_colors.get(str(g), "#A0A0A0") for g in df["kpi_grade"]]

    fig, ax = plt.subplots(figsize=(10, 8), facecolor="white")
    bars = ax.barh(df["brand"], df["composite_kpi"], color=colors, height=0.65)

    # Grade labels
    for bar, grade in zip(bars, df["kpi_grade"]):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"  {grade}", va="center", fontsize=10, fontweight="bold",
                color=grade_colors.get(str(grade), "#333"))

    ax.axvline(75, color=GSK_GREY, lw=1.2, ls="--", alpha=0.7, label="Target (75)")
    ax.set_xlim(0, 105)
    ax.set_xlabel("Composite KPI Score", fontsize=11)
    ax.set_title("Brand KPI Scorecard – Composite Score & Grade",
                 fontsize=14, fontweight="bold", color=GSK_NAVY, pad=12)

    legend_patches = [mpatches.Patch(color=c, label=f"Grade {g}")
                      for g, c in grade_colors.items()]
    ax.legend(handles=legend_patches, loc="lower right", fontsize=9, framealpha=0.6)
    plt.tight_layout()
    fig.savefig("reports/figures/03_kpi_scorecard.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("[✓] Fig 03 – KPI Scorecard")


# ── 4. PASBAAN Launch KPI Dashboard ──────────────────────────────────────────
def plot_pasbaan_kpis(pasbaan_df):
    df = pasbaan_df.copy()

    fig = plt.figure(figsize=(16, 10), facecolor="white")
    fig.suptitle("PASBAAN Product Launch – KPI Tracking Dashboard",
                 fontsize=16, fontweight="bold", color=GSK_NAVY)
    gs = GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.35)

    kpis = [
        ("rx_growth_pct",       "target_rx_growth",   "Rx Growth (%)",          GSK_ORANGE),
        ("stock_coverage_pct",  "target_stock_cov",   "Stock Coverage (%)",     GSK_TEAL),
        ("acquisition_rate_pct","target_acq_rate",    "Acquisition Rate (%)",   GSK_GOLD),
        ("sales_index",         None,                  "Sales Index",            GSK_NAVY),
    ]

    for idx, (actual_col, target_col, label, color) in enumerate(kpis):
        ax = fig.add_subplot(gs[idx // 2, idx % 2])
        months = range(len(df))
        ax.bar(months, df[actual_col], color=color, alpha=0.75, width=0.6, label="Actual")

        if target_col and target_col in df.columns:
            ax.step(list(months) + [len(months) - 0.5],
                    list(df[target_col]) + [df[target_col].iloc[-1]],
                    where="post", color="#333", lw=1.8, ls="--", label="Target")
            ax.legend(fontsize=9)

        ax.set_xticks(months)
        ax.set_xticklabels(df["month_label"], rotation=30, ha="right", fontsize=8)
        ax.set_title(label, fontsize=12, fontweight="bold", color=GSK_NAVY)
        ax.set_ylabel(label.split("(")[-1].replace(")", "") if "(" in label else "")

    fig.savefig("reports/figures/04_pasbaan_launch.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("[✓] Fig 04 – PASBAAN Launch KPIs")


# ── 5. Sales Forecast ─────────────────────────────────────────────────────────
def plot_forecast(forecast_df, brands=("Panadol", "Augmentin", "PASBAAN")):
    fig, axes = plt.subplots(1, len(brands), figsize=(18, 5), facecolor="white")
    fig.suptitle("IMS Sales Forecast – 6-Month Horizon",
                 fontsize=15, fontweight="bold", color=GSK_NAVY)

    for ax, brand, color in zip(axes, brands, [GSK_ORANGE, GSK_TEAL, GSK_NAVY]):
        sub = forecast_df[forecast_df["brand"] == brand]
        hist = sub[~sub["is_forecast"]]
        fcast = sub[sub["is_forecast"]]

        ax.plot(hist["date"], hist["forecast"],   color=color, lw=2, label="Actual")
        ax.plot(fcast["date"], fcast["forecast"], color=color, lw=2, ls="--", label="Forecast")
        ax.fill_between(fcast["date"], fcast["ci_lower"], fcast["ci_upper"],
                        color=color, alpha=0.15, label="95% CI")
        ax.axvline(hist["date"].max(), color="#999", lw=1, ls=":")

        ax.set_title(brand, fontsize=12, fontweight="bold", color=GSK_NAVY)
        ax.yaxis.set_major_formatter(FuncFormatter(fmt_k))
        ax.legend(fontsize=9)
        ax.tick_params(axis="x", rotation=30)

    plt.tight_layout()
    fig.savefig("reports/figures/05_ims_forecast.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("[✓] Fig 05 – IMS Forecast")


# ── 6. Distributor Performance Map ────────────────────────────────────────────
def plot_distributor_performance(dist_df):
    latest_year = dist_df["year"].max()
    agg = dist_df[dist_df["year"] == latest_year].groupby("region").agg(
        avg_achievement   = ("achievement_pct",    "mean"),
        avg_coverage      = ("outlet_coverage_pct","mean"),
        avg_otd           = ("on_time_delivery_pct","mean"),
        avg_composite     = ("composite_score",    "mean"),
    ).reset_index().sort_values("avg_composite", ascending=False)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6), facecolor="white")
    fig.suptitle("Distributor Performance Dashboard – Regional View",
                 fontsize=15, fontweight="bold", color=GSK_NAVY)

    # Bar chart
    ax = axes[0]
    bars = ax.bar(agg["region"], agg["avg_composite"],
                  color=[PALETTE[i] for i in range(len(agg))], width=0.6)
    ax.axhline(80, color="red", lw=1.2, ls="--", alpha=0.6, label="Baseline (80)")
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                f"{bar.get_height():.1f}", ha="center", va="bottom", fontsize=9)
    ax.set_title("Composite Score by Region", fontsize=12, fontweight="bold", color=GSK_NAVY)
    ax.set_ylabel("Composite Score")
    ax.tick_params(axis="x", rotation=20)
    ax.legend()

    # Grouped bar
    ax2 = axes[1]
    x  = np.arange(len(agg))
    w  = 0.25
    ax2.bar(x - w, agg["avg_achievement"], width=w, label="Achievement %", color=GSK_ORANGE)
    ax2.bar(x,     agg["avg_coverage"],    width=w, label="Coverage %",    color=GSK_TEAL)
    ax2.bar(x + w, agg["avg_otd"],         width=w, label="On-Time %",     color=GSK_NAVY)
    ax2.set_xticks(x)
    ax2.set_xticklabels(agg["region"], rotation=20)
    ax2.set_title("KPI Breakdown by Region", fontsize=12, fontweight="bold", color=GSK_NAVY)
    ax2.legend(fontsize=9)

    plt.tight_layout()
    fig.savefig("reports/figures/06_distributor_perf.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("[✓] Fig 06 – Distributor Performance")


# ── 7. Decilo-Meter Pareto ────────────────────────────────────────────────────
def plot_decilometer(decilo_df):
    df = decilo_df.sort_values("decile")

    fig, ax1 = plt.subplots(figsize=(12, 6), facecolor="white")
    ax2 = ax1.twinx()

    bars = ax1.bar(df["decile"], df["sales_share_pct"],
                   color=[GSK_ORANGE if d >= 9 else GSK_TEAL for d in df["decile"]],
                   width=0.65, label="Sales Share %")
    ax2.plot(df["decile"], df["cumul_sales_pct"], color=GSK_NAVY,
             lw=2.5, marker="o", ms=5, label="Cumulative %")

    ax1.set_xlabel("Decile", fontsize=11)
    ax1.set_ylabel("Sales Share (%)", color=GSK_TEAL, fontsize=11)
    ax2.set_ylabel("Cumulative Share (%)", color=GSK_NAVY, fontsize=11)
    ax2.set_ylim(0, 110)

    ax1.set_title("Decilo-Meter: Pharmacy Sales Concentration (Pareto Analysis)",
                  fontsize=14, fontweight="bold", color=GSK_NAVY, pad=12)
    ax1.set_xticks(df["decile"])
    ax1.set_xticklabels([f"D{d}" for d in df["decile"]])

    top2_share = df[df["decile"] >= 9]["sales_share_pct"].sum()
    ax1.annotate(f"Top 20% outlets\n= {top2_share:.0f}% of sales",
                 xy=(9.5, top2_share / 2), xytext=(7.5, top2_share * 0.9),
                 fontsize=10, color=GSK_ORANGE, fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color=GSK_ORANGE))

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)

    plt.tight_layout()
    fig.savefig("reports/figures/07_decilometer_pareto.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("[✓] Fig 07 – Decilo-Meter Pareto")


# ── 8. YoY Growth Bubble Chart ────────────────────────────────────────────────
def plot_yoy_bubble(ims_df, scorecard_df):
    latest = ims_df["date"].max()
    df = ims_df[ims_df["date"] == latest].merge(
        scorecard_df[["brand", "composite_kpi", "kpi_grade"]], on="brand"
    )
    df = df.dropna(subset=["yoy_growth_pct"])

    grade_colors = {"S": GSK_TEAL, "A": GSK_ORANGE, "B": GSK_GOLD,
                    "C": "#A0A0A0", "D": "#D64550"}
    colors = [grade_colors.get(str(g), "#999") for g in df["kpi_grade"]]
    sizes  = (df["ims_units"] / df["ims_units"].max() * 1200 + 100).clip(100, 1200)

    fig, ax = plt.subplots(figsize=(13, 8), facecolor="white")
    scatter = ax.scatter(df["market_share"], df["yoy_growth_pct"],
                         s=sizes, c=colors, alpha=0.75, edgecolors="white", lw=1)

    for _, row in df.iterrows():
        ax.annotate(row["brand"], (row["market_share"], row["yoy_growth_pct"]),
                    textcoords="offset points", xytext=(6, 3), fontsize=8, color="#333")

    ax.axhline(0,  color="#999", lw=1,   ls="--", alpha=0.5)
    ax.axvline(15, color="#999", lw=1,   ls="--", alpha=0.5)
    ax.set_xlabel("Market Share (%)",  fontsize=11)
    ax.set_ylabel("YoY IMS Growth (%)", fontsize=11)
    ax.set_title("Brand Portfolio Map – Market Share vs Growth\n(Bubble size = IMS volume)",
                 fontsize=14, fontweight="bold", color=GSK_NAVY, pad=12)

    legend_patches = [mpatches.Patch(color=c, label=f"Grade {g}")
                      for g, c in grade_colors.items()]
    ax.legend(handles=legend_patches, title="KPI Grade", fontsize=9, framealpha=0.6)

    # Quadrant labels
    ax.text(25, df["yoy_growth_pct"].max() * 0.85, "Star Brands →",
            fontsize=9, color=GSK_TEAL, style="italic")
    ax.text(0.5, df["yoy_growth_pct"].min() * 0.85, "← At Risk",
            fontsize=9, color="#D64550", style="italic")

    plt.tight_layout()
    fig.savefig("reports/figures/08_portfolio_map.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("[✓] Fig 08 – Portfolio Bubble Map")


# ── Main ──────────────────────────────────────────────────────────────────────
def run_visualizations():
    print("\n🟢 PHASE 4 – EVALUATION & VISUALIZATIONS\n" + "=" * 45)

    ims_df      = pd.read_csv("data/processed/ims_tms_clean.csv",    parse_dates=["date"])
    pasbaan_df  = pd.read_csv("data/processed/pasbaan_clean.csv",    parse_dates=["date"])
    dist_df     = pd.read_csv("data/processed/distributor_clean.csv",parse_dates=["date"])
    scorecard   = pd.read_csv("data/processed/kpi_scorecard.csv")
    forecast_df = pd.read_csv("data/processed/ims_forecasts.csv",    parse_dates=["date"])
    decilo_df   = pd.read_csv("data/processed/decilo_insights.csv")

    plot_ims_tms_trend(ims_df)
    plot_market_share_heatmap(ims_df)
    plot_kpi_scorecard(scorecard)
    plot_pasbaan_kpis(pasbaan_df)
    plot_forecast(forecast_df)
    plot_distributor_performance(dist_df)
    plot_decilometer(decilo_df)
    plot_yoy_bubble(ims_df, scorecard)

    print(f"\n[✓] All {8} figures saved to reports/figures/")


if __name__ == "__main__":
    run_visualizations()
