"""
GSK CTC Analytics – Synthetic Data Generator
Phase 1: Development
Generates realistic pharmaceutical sales data for Pakistan market.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(42)

# ── Constants ────────────────────────────────────────────────────────────────
BRANDS = {
    "Panadol":      {"category": "Analgesic",       "priority": "A", "base_sales": 12000},
    "Augmentin":    {"category": "Antibiotic",       "priority": "A", "base_sales": 9800},
    "Ventolin":     {"category": "Respiratory",      "priority": "A", "base_sales": 7500},
    "Zantac":       {"category": "GI",               "priority": "B", "base_sales": 4200},
    "Voltaren":     {"category": "Anti-inflammatory","priority": "B", "base_sales": 3900},
    "Calpol":       {"category": "Analgesic",        "priority": "B", "base_sales": 3500},
    "Piriton":      {"category": "Antihistamine",    "priority": "C", "base_sales": 2100},
    "Betnovate":    {"category": "Dermatology",      "priority": "C", "base_sales": 1800},
    "Nasonex":      {"category": "Respiratory",      "priority": "C", "base_sales": 1600},
    "Seretide":     {"category": "Respiratory",      "priority": "C", "base_sales": 1400},
    "Amoxil":       {"category": "Antibiotic",       "priority": "C", "base_sales": 1300},
    "Flixonase":    {"category": "Respiratory",      "priority": "C", "base_sales": 1100},
    "PASBAAN":      {"category": "Analgesic",        "priority": "B", "base_sales": 2800},  # New launch
    "Clavulin":     {"category": "Antibiotic",       "priority": "C", "base_sales": 950},
}

SKU_MAP = {
    "Panadol":   ["Panadol 500mg Tab 10s", "Panadol CF Tab 10s", "Panadol Ext 665mg Tab 8s"],
    "Augmentin": ["Augmentin 625mg Tab 6s", "Augmentin 1g Tab 4s", "Augmentin 375mg Tab 6s"],
    "Ventolin":  ["Ventolin Inhaler 100mcg", "Ventolin Syrup 100ml", "Ventolin Neb 2.5mg"],
    "Zantac":    ["Zantac 150mg Tab 20s", "Zantac 300mg Tab 10s"],
    "Voltaren":  ["Voltaren 50mg Tab 20s", "Voltaren Gel 100g"],
    "Calpol":    ["Calpol 120mg Susp 100ml", "Calpol 250mg Susp 100ml"],
    "Piriton":   ["Piriton 4mg Tab 20s", "Piriton Syrup 100ml"],
    "Betnovate": ["Betnovate Cream 30g", "Betnovate-N Cream 30g"],
    "Nasonex":   ["Nasonex 50mcg Nasal Spray"],
    "Seretide":  ["Seretide 25/250 Inhaler", "Seretide 25/125 Inhaler"],
    "Amoxil":    ["Amoxil 500mg Cap 12s", "Amoxil 250mg Susp 100ml"],
    "Flixonase": ["Flixonase 50mcg Nasal Spray"],
    "PASBAAN":   ["PASBAAN 500mg Tab 10s", "PASBAAN 250mg Tab 20s"],
    "Clavulin":  ["Clavulin 312mg Susp 100ml"],
}

REGIONS = {
    "Karachi":    {"zone": "South", "outlets": 18500, "weight": 0.34},
    "Lahore":     {"zone": "Central","outlets": 14200, "weight": 0.26},
    "Islamabad":  {"zone": "North", "outlets": 6800,  "weight": 0.12},
    "Faisalabad": {"zone": "Central","outlets": 5900,  "weight": 0.11},
    "Peshawar":   {"zone": "North", "outlets": 4100,  "weight": 0.07},
    "Quetta":     {"zone": "West",  "outlets": 3200,  "weight": 0.06},
    "Multan":     {"zone": "Central","outlets": 2300,  "weight": 0.04},
}

DISTRIBUTORS = [f"Dist_{str(i).zfill(2)}" for i in range(1, 33)]

DIST_REGION = {d: list(REGIONS.keys())[i % len(REGIONS)] for i, d in enumerate(DISTRIBUTORS)}


def make_monthly_dates(start="2022-01", end="2024-12"):
    return pd.date_range(start=start, end=end, freq="MS")


# ── 1. IMS / TMS Monthly Data ────────────────────────────────────────────────
def generate_ims_tms(save=True):
    dates = make_monthly_dates()
    rows = []

    for brand, meta in BRANDS.items():
        base = meta["base_sales"]
        trend = 0.008 if meta["priority"] in ("A", "B") else 0.003
        seasonal_amp = 0.12 if meta["category"] == "Respiratory" else 0.06

        for i, dt in enumerate(dates):
            seasonal = 1 + seasonal_amp * np.sin(2 * np.pi * (dt.month - 1) / 12)
            growth   = (1 + trend) ** i
            noise    = np.random.normal(1.0, 0.04)

            # PASBAAN launched Dec 2024 – ramp up
            if brand == "PASBAAN":
                if dt < pd.Timestamp("2024-12-01"):
                    ims = 0
                else:
                    months_post = (dt.year - 2024) * 12 + dt.month - 12
                    ims = base * (0.3 + 0.15 * months_post) * noise
            else:
                ims = base * seasonal * growth * noise

            market_share = np.random.uniform(0.18, 0.35) if meta["priority"] == "A" else \
                           np.random.uniform(0.08, 0.20) if meta["priority"] == "B" else \
                           np.random.uniform(0.03, 0.10)
            tms = ims / market_share

            rows.append({
                "date":         dt,
                "brand":        brand,
                "category":     meta["category"],
                "priority":     meta["priority"],
                "ims_units":    round(ims),
                "tms_units":    round(tms),
                "market_share": round(market_share * 100, 2),
            })

    df = pd.DataFrame(rows)
    df["ims_value_pkr"] = (df["ims_units"] * np.random.uniform(80, 650, len(df))).round(0)
    df["tms_value_pkr"] = (df["tms_units"] * np.random.uniform(80, 650, len(df))).round(0)
    if save:
        df.to_csv("data/raw/ims_tms_monthly.csv", index=False)
        print(f"[✓] IMS/TMS: {len(df)} rows → data/raw/ims_tms_monthly.csv")
    return df


# ── 2. Brand SKU Performance ──────────────────────────────────────────────────
def generate_brand_sku(save=True):
    dates = make_monthly_dates()
    rows = []
    for brand, skus in SKU_MAP.items():
        meta = BRANDS[brand]
        for sku in skus:
            sku_share = np.random.uniform(0.25, 0.55)
            for i, dt in enumerate(dates):
                trend   = (1.007) ** i
                noise   = np.random.normal(1.0, 0.05)
                units   = meta["base_sales"] * sku_share * trend * noise
                stock   = np.random.uniform(0.70, 0.99)

                if brand == "PASBAAN" and dt < pd.Timestamp("2024-12-01"):
                    units, stock = 0, 0

                rows.append({
                    "date":            dt,
                    "brand":           brand,
                    "sku":             sku,
                    "category":        meta["category"],
                    "priority":        meta["priority"],
                    "units_sold":      round(units),
                    "stock_avail_pct": round(stock * 100, 1),
                    "rx_growth_pct":   round(np.random.normal(5, 3), 2),
                })
    df = pd.DataFrame(rows)
    if save:
        df.to_csv("data/raw/brand_sku_performance.csv", index=False)
        print(f"[✓] SKU: {len(df)} rows → data/raw/brand_sku_performance.csv")
    return df


# ── 3. Distributor Performance ───────────────────────────────────────────────
def generate_distributor(save=True):
    dates = make_monthly_dates()
    rows = []
    for dist in DISTRIBUTORS:
        region   = DIST_REGION[dist]
        rw       = REGIONS[region]["weight"]
        base_rev = np.random.uniform(1_200_000, 4_500_000) * rw * 6

        for i, dt in enumerate(dates):
            noise      = np.random.normal(1.0, 0.07)
            growth     = (1.006) ** i
            revenue    = base_rev * growth * noise
            target     = revenue * np.random.uniform(0.90, 1.15)
            coverage   = np.random.uniform(0.72, 0.97)
            on_time    = np.random.uniform(0.75, 0.98)
            returns    = np.random.uniform(0.01, 0.05)

            rows.append({
                "date":               dt,
                "distributor_id":     dist,
                "region":             region,
                "zone":               REGIONS[region]["zone"],
                "actual_revenue_pkr": round(revenue),
                "target_revenue_pkr": round(target),
                "achievement_pct":    round((revenue / target) * 100, 1),
                "outlet_coverage_pct":round(coverage * 100, 1),
                "on_time_delivery_pct":round(on_time * 100, 1),
                "return_rate_pct":    round(returns * 100, 2),
            })

    df = pd.DataFrame(rows)
    if save:
        df.to_csv("data/raw/distributor_performance.csv", index=False)
        print(f"[✓] Distributors: {len(df)} rows → data/raw/distributor_performance.csv")
    return df


# ── 4. Outlet / Pharmacy Data ────────────────────────────────────────────────
def generate_outlets(save=True):
    total = 55000
    rows = []
    outlet_types = ["Pharmacy", "Hospital Pharmacy", "Clinic", "Wholesale"]
    type_weights = [0.65, 0.15, 0.12, 0.08]

    for region, meta in REGIONS.items():
        n = int(total * meta["weight"])
        for j in range(n):
            otype  = np.random.choice(outlet_types, p=type_weights)
            active = np.random.random() > 0.08
            decile = np.random.choice(range(1, 11), p=np.array([
                0.05, 0.06, 0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.13, 0.13
            ]))
            rows.append({
                "outlet_id":       f"{region[:3].upper()}{j+1:05d}",
                "region":          region,
                "zone":            meta["zone"],
                "outlet_type":     otype,
                "is_active":       active,
                "decile":          decile,
                "monthly_sales_pkr": round(np.random.lognormal(11, 1.2)),
                "gsm_brands_carried": np.random.randint(2, len(BRANDS) + 1),
            })

    df = pd.DataFrame(rows)
    if save:
        df.to_csv("data/raw/outlet_data.csv", index=False)
        print(f"[✓] Outlets: {len(df)} rows → data/raw/outlet_data.csv")
    return df


# ── 5. PASBAAN Launch KPIs ────────────────────────────────────────────────────
def generate_pasbaan_kpis(save=True):
    dates = pd.date_range("2024-10-01", "2025-04-01", freq="MS")
    rows = []
    for i, dt in enumerate(dates):
        months_since = i  # Oct = 0
        rx_growth = max(0, -5 + 8 * months_since + np.random.normal(0, 2))
        stock_cov  = min(99, 45 + 8 * months_since + np.random.normal(0, 3))
        acq_rate   = min(95, 20 + 12 * months_since + np.random.normal(0, 4))
        sales_idx  = max(0, 85 + 15 * months_since + np.random.normal(0, 5))

        rows.append({
            "date":                  dt,
            "month_label":           dt.strftime("%b %Y"),
            "rx_growth_pct":         round(rx_growth, 1),
            "stock_coverage_pct":    round(stock_cov, 1),
            "acquisition_rate_pct":  round(acq_rate, 1),
            "sales_index":           round(sales_idx, 1),
            "target_rx_growth":      round(5 + 7 * i, 1),
            "target_stock_cov":      70.0,
            "target_acq_rate":       round(30 + 10 * i, 1),
        })

    df = pd.DataFrame(rows)
    if save:
        df.to_csv("data/raw/pasbaan_launch_kpis.csv", index=False)
        print(f"[✓] PASBAAN KPIs: {len(df)} rows → data/raw/pasbaan_launch_kpis.csv")
    return df


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

    print("\n🔵 PHASE 1 – DATA GENERATION\n" + "=" * 45)
    ims   = generate_ims_tms()
    skus  = generate_brand_sku()
    dists = generate_distributor()
    outs  = generate_outlets()
    pasb  = generate_pasbaan_kpis()
    print("\n[✓] All raw datasets generated successfully.\n")
