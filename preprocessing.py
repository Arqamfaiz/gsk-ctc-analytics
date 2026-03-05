"""
GSK CTC Analytics – Data Preparation & Preprocessing
Phase 2: Preparation
Cleans raw data, engineers features, and exports processed datasets.
"""

import pandas as pd
import numpy as np
import os

def load_raw():
    print("\n🟡 PHASE 2 – DATA PREPARATION\n" + "=" * 45)
    dfs = {}
    files = {
        "ims_tms":     "data/raw/ims_tms_monthly.csv",
        "sku":         "data/raw/brand_sku_performance.csv",
        "distributor": "data/raw/distributor_performance.csv",
        "outlets":     "data/raw/outlet_data.csv",
        "pasbaan":     "data/raw/pasbaan_launch_kpis.csv",
    }
    for key, path in files.items():
        df = pd.read_csv(path, parse_dates=["date"] if "date" in pd.read_csv(path, nrows=0).columns else [])
        dfs[key] = df
        print(f"[✓] Loaded {key}: {df.shape}")
    return dfs


def clean_ims_tms(df):
    df = df.copy()
    # Remove negative values (data entry errors)
    for col in ["ims_units", "tms_units", "ims_value_pkr", "tms_value_pkr"]:
        df[col] = df[col].clip(lower=0)

    # Add derived time features
    df["year"]    = df["date"].dt.year
    df["month"]   = df["date"].dt.month
    df["quarter"] = df["date"].dt.quarter
    df["ym"]      = df["date"].dt.to_period("M")

    # Rolling 3-month average
    df = df.sort_values(["brand", "date"])
    df["ims_roll3"] = df.groupby("brand")["ims_units"].transform(
        lambda x: x.rolling(3, min_periods=1).mean()
    ).round(0)

    # YoY growth
    df["ims_lag12"] = df.groupby("brand")["ims_units"].shift(12)
    df["yoy_growth_pct"] = ((df["ims_units"] - df["ims_lag12"]) / df["ims_lag12"] * 100).round(2)

    # Value index (relative to brand average)
    avg = df.groupby("brand")["ims_units"].transform("mean")
    df["value_index"] = (df["ims_units"] / avg * 100).round(1)

    print(f"[✓] IMS/TMS cleaned: {df.shape} | Missing yoy: {df['yoy_growth_pct'].isna().sum()}")
    return df


def clean_sku(df):
    df = df.copy()
    df["year"]    = df["date"].dt.year
    df["month"]   = df["date"].dt.month
    df["quarter"] = df["date"].dt.quarter

    # Flag low stock
    df["low_stock_flag"] = df["stock_avail_pct"] < 80

    # Brand-level rank within month
    brand_monthly = df.groupby(["date", "brand"])["units_sold"].sum().reset_index()
    brand_monthly["brand_rank"] = brand_monthly.groupby("date")["units_sold"].rank(ascending=False)
    df = df.merge(brand_monthly[["date", "brand", "brand_rank"]], on=["date", "brand"], how="left")

    print(f"[✓] SKU cleaned: {df.shape}")
    return df


def clean_distributor(df):
    df = df.copy()
    df["year"]    = df["date"].dt.year
    df["quarter"] = df["date"].dt.quarter

    # Performance tier
    df["perf_tier"] = pd.cut(
        df["achievement_pct"],
        bins=[0, 85, 95, 105, 999],
        labels=["Below Target", "Near Target", "On Target", "Overachiever"]
    )

    # Composite score (equal weight)
    df["composite_score"] = (
        df["achievement_pct"] * 0.40 +
        df["outlet_coverage_pct"] * 0.30 +
        df["on_time_delivery_pct"] * 0.20 +
        (100 - df["return_rate_pct"] * 10) * 0.10
    ).round(1)

    df["composite_tier"] = pd.cut(
        df["composite_score"],
        bins=[0, 70, 80, 90, 999],
        labels=["Low", "Medium", "High", "Elite"]
    )

    print(f"[✓] Distributor cleaned: {df.shape}")
    return df


def engineer_decilometer(outlets_df, ims_df):
    """Build decile-level analytics joining outlet and IMS data."""
    # Outlet aggregates by decile & region
    dec = outlets_df.groupby(["region", "decile"]).agg(
        total_outlets   = ("outlet_id", "count"),
        active_outlets  = ("is_active", "sum"),
        avg_sales_pkr   = ("monthly_sales_pkr", "mean"),
        total_sales_pkr = ("monthly_sales_pkr", "sum"),
        avg_brands      = ("gsm_brands_carried", "mean"),
    ).reset_index()

    dec["active_pct"]  = (dec["active_outlets"] / dec["total_outlets"] * 100).round(1)
    dec["sales_share"] = (dec["total_sales_pkr"] / dec["total_sales_pkr"].sum() * 100).round(2)

    # Classify top decile
    dec["is_top_decile"] = dec["decile"] >= 9

    print(f"[✓] Decilo-meter engineered: {dec.shape}")
    return dec


def save_processed(dfs_clean, decile_df):
    os.makedirs("data/processed", exist_ok=True)
    dfs_clean["ims_tms"].to_csv("data/processed/ims_tms_clean.csv", index=False)
    dfs_clean["sku"].to_csv("data/processed/sku_clean.csv", index=False)
    dfs_clean["distributor"].to_csv("data/processed/distributor_clean.csv", index=False)
    dfs_clean["outlets"].to_csv("data/processed/outlets_clean.csv", index=False)
    dfs_clean["pasbaan"].to_csv("data/processed/pasbaan_clean.csv", index=False)
    decile_df.to_csv("data/processed/decilometer.csv", index=False)
    print("\n[✓] All processed files saved to data/processed/")


def run_preparation():
    raw = load_raw()

    cleaned = {
        "ims_tms":     clean_ims_tms(raw["ims_tms"]),
        "sku":         clean_sku(raw["sku"]),
        "distributor": clean_distributor(raw["distributor"]),
        "outlets":     raw["outlets"],
        "pasbaan":     raw["pasbaan"],
    }

    decile = engineer_decilometer(raw["outlets"], raw["ims_tms"])
    save_processed(cleaned, decile)

    # Data quality report
    print("\n📋 DATA QUALITY SUMMARY")
    print("-" * 45)
    for name, df in cleaned.items():
        miss = df.isnull().sum().sum()
        print(f"  {name:<15} rows: {len(df):>6,}  nulls: {miss:>4}")

    return cleaned, decile


if __name__ == "__main__":
    run_preparation()
