"""
PHASE 1 — Data Cleaning
QCommerce Analytics Platform

Reads both raw datasets, cleans them, and saves:
  data/cleaned/clean_orders.csv
  data/cleaned/clean_inventory.csv
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

RAW     = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
CLEANED = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned')
os.makedirs(CLEANED, exist_ok=True)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def excel_serial_to_date(n):
    """Convert Excel serial date integer to Python datetime."""
    return datetime(1899, 12, 30) + timedelta(days=int(n))

def print_section(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")

# ─────────────────────────────────────────────
# DATASET 1 — Adventures Online Sales
# ─────────────────────────────────────────────

print_section("DATASET 1 — Adventures Online Sales")

df1 = pd.read_excel(os.path.join(RAW, 'Adventures-Online-Sales.xlsx'))
print(f"Loaded: {len(df1):,} rows, {df1.shape[1]} columns")

# --- Fix 1: Excel serial dates → real dates
print("\n[1] Converting Excel serial dates...")
for col in ['OrderDate', 'DueDate', 'ShipDate']:
    df1[col] = df1[col].apply(excel_serial_to_date)
print(f"    OrderDate range: {df1['OrderDate'].min().date()} → {df1['OrderDate'].max().date()}")

# --- Fix 2: Drop rows with missing MaritalStatus / Gender (only 10)
before = len(df1)
df1 = df1.dropna(subset=['MaritalStatus', 'Gender'])
print(f"\n[2] Dropped {before - len(df1)} rows with missing MaritalStatus/Gender")

# --- Fix 3: Fill missing Color
df1['Color'] = df1['Color'].fillna('Not Specified')
print(f"[3] Filled {(df1['Color'] == 'Not Specified').sum():,} missing Color values")

# --- Fix 4: Engineer delivery features
print("\n[4] Engineering delivery features...")
df1['promised_days'] = (df1['DueDate']  - df1['OrderDate']).dt.days
df1['actual_days']   = (df1['ShipDate'] - df1['OrderDate']).dt.days
df1['delay_days']    = df1['actual_days'] - df1['promised_days']
df1['is_delayed']    = df1['delay_days'] > 0
pct_delayed = df1['is_delayed'].mean() * 100
print(f"    Promised avg: {df1['promised_days'].mean():.1f} days")
print(f"    Actual avg:   {df1['actual_days'].mean():.1f} days")
print(f"    % Delayed:    {pct_delayed:.1f}%")

# --- Fix 5: Profit metrics
print("\n[5] Calculating profit metrics...")
df1['profit']             = df1['SalesAmount'] - df1['StandardCost']
df1['profit_margin_pct']  = (df1['profit'] / df1['SalesAmount'] * 100).round(2)
df1['total_cost']         = df1['StandardCost'] + df1['TaxAmt'] + df1['Freight']
print(f"    Total Revenue: ${df1['SalesAmount'].sum():,.0f}")
print(f"    Total Profit:  ${df1['profit'].sum():,.0f}")
print(f"    Avg Margin:    {df1['profit_margin_pct'].mean():.1f}%")

# --- Fix 6: Standardize text columns
df1['Gender']        = df1['Gender'].map({'M': 'Male', 'F': 'Female'}).fillna(df1['Gender'])
df1['MaritalStatus'] = df1['MaritalStatus'].map({'S': 'Single', 'M': 'Married'}).fillna(df1['MaritalStatus'])

# --- Save
out1 = os.path.join(CLEANED, 'clean_orders.csv')
df1.to_csv(out1, index=False)
print(f"\n✅ Saved clean_orders.csv — {len(df1):,} rows")

# ─────────────────────────────────────────────
# DATASET 2 — Online Retail (Inventory)
# ─────────────────────────────────────────────

print_section("DATASET 2 — Online Retail (Inventory)")

df2 = pd.read_excel(os.path.join(RAW, 'Online Retail.xlsx'))
print(f"Loaded: {len(df2):,} rows, {df2.shape[1]} columns")

# --- Fix 1: Remove returns (negative quantity)
before = len(df2)
df2 = df2[df2['Quantity'] > 0]
print(f"\n[1] Removed {before - len(df2):,} return/cancellation rows (Quantity ≤ 0)")

# --- Fix 2: Remove zero/negative prices
before = len(df2)
df2 = df2[df2['UnitPrice'] > 0]
print(f"[2] Removed {before - len(df2):,} zero-price rows")

# --- Fix 3: Remove guest checkouts (no CustomerID)
before = len(df2)
df2 = df2[df2['CustomerID'].notna()]
print(f"[3] Removed {before - len(df2):,} guest checkout rows (no CustomerID)")

# --- Fix 4: Fix types
df2['CustomerID'] = df2['CustomerID'].astype(int).astype(str)
df2['InvoiceNo']  = df2['InvoiceNo'].astype(str)
df2['StockCode']  = df2['StockCode'].astype(str)
df2['InvoiceDate'] = pd.to_datetime(df2['InvoiceDate'])

# --- Fix 5: Fill missing Description
df2['Description'] = df2['Description'].fillna('Unknown Product')

# --- Fix 6: Revenue per line
df2['revenue'] = (df2['Quantity'] * df2['UnitPrice']).round(2)

# --- Fix 7: Date parts
df2['invoice_date_only'] = df2['InvoiceDate'].dt.normalize()
df2['invoice_month']     = df2['InvoiceDate'].dt.month
df2['invoice_year']      = df2['InvoiceDate'].dt.year

print(f"\n[4-7] Engineered revenue, date parts, fixed types")
print(f"    Date range: {df2['InvoiceDate'].min().date()} → {df2['InvoiceDate'].max().date()}")
print(f"    Total Revenue: ${df2['revenue'].sum():,.0f}")
print(f"    Unique Products: {df2['StockCode'].nunique():,}")
print(f"    Unique Customers: {df2['CustomerID'].nunique():,}")
print(f"    Countries: {df2['Country'].nunique()}")

# --- Save
out2 = os.path.join(CLEANED, 'clean_inventory.csv')
df2.to_csv(out2, index=False)
print(f"\n✅ Saved clean_inventory.csv — {len(df2):,} rows")

# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

print_section("PHASE 1 COMPLETE")
print(f"  clean_orders.csv    → {len(df1):,} rows")
print(f"  clean_inventory.csv → {len(df2):,} rows")
print(f"\n  Next: Run etl/phase2_schema.py to build dimension & fact tables")
