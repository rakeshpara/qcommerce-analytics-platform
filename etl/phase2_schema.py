"""
PHASE 2 — Star Schema Builder
QCommerce Analytics Platform

Reads cleaned CSVs and outputs 6 tables:
  data/schema/dim_customer.csv
  data/schema/dim_product.csv
  data/schema/dim_date.csv
  data/schema/dim_warehouse.csv
  data/schema/fact_orders.csv
  data/schema/fact_inventory.csv
"""

import pandas as pd
import numpy as np
import random
import os
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

CLEANED = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned')
SCHEMA  = os.path.join(os.path.dirname(__file__), '..', 'data', 'schema')
os.makedirs(SCHEMA, exist_ok=True)

def print_section(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")

# LOAD CLEANED DATA

print_section("Loading Cleaned Data")

df1 = pd.read_csv(os.path.join(CLEANED, 'clean_orders.csv'), parse_dates=['OrderDate','DueDate','ShipDate'])
df2 = pd.read_csv(os.path.join(CLEANED, 'clean_inventory.csv'), parse_dates=['InvoiceDate'])

print(f"clean_orders.csv    : {len(df1):,} rows")
print(f"clean_inventory.csv : {len(df2):,} rows")

# DIM_CUSTOMER

print_section("Building dim_customer")

dim_customer = df1[[
    'CustomerName', 'MaritalStatus', 'Gender',
    'EmailAddress', 'YearlyIncome', 'CommuteDistance'
]].drop_duplicates(subset=['EmailAddress']).copy()

dim_customer.reset_index(drop=True, inplace=True)
dim_customer.insert(0, 'customer_id', range(1, len(dim_customer) + 1))

# Income bucket for segmentation
def income_bucket(income):
    if income < 30000:   return 'Low'
    elif income < 70000: return 'Medium'
    elif income < 120000:return 'High'
    else:                return 'Very High'

dim_customer['income_segment'] = dim_customer['YearlyIncome'].apply(income_bucket)

print(f"Unique customers : {len(dim_customer):,}")
print(f"Income segments  : {dim_customer['income_segment'].value_counts().to_dict()}")
print(f"Gender split     : {dim_customer['Gender'].value_counts().to_dict()}")

out = os.path.join(SCHEMA, 'dim_customer.csv')
dim_customer.to_csv(out, index=False)
print(f"\n Saved dim_customer.csv — {len(dim_customer):,} rows")

# DIM_PRODUCT

print_section("Building dim_product")

# From Dataset 1 — sales products
p1 = df1[[
    'ProductName', 'ProductCategory', 'ProductSubcategory',
    'Color', 'StandardCost', 'ReorderPoint'
]].drop_duplicates(subset=['ProductName']).copy()
p1['source_system'] = 'sales'
p1['stock_code']    = None
p1['unit_price']    = p1['StandardCost']

# From Dataset 2 — inventory products
p2 = df2[[
    'StockCode', 'Description', 'UnitPrice'
]].drop_duplicates(subset=['StockCode']).copy()
p2.rename(columns={
    'StockCode'  : 'stock_code',
    'Description': 'ProductName',
    'UnitPrice'  : 'unit_price'
}, inplace=True)
p2['ProductCategory']    = 'Retail'
p2['ProductSubcategory'] = 'General'
p2['Color']              = 'Not Specified'
p2['StandardCost']       = p2['unit_price']
p2['ReorderPoint']       = 50
p2['source_system']      = 'inventory'

# Combine
dim_product = pd.concat([p1, p2], ignore_index=True)
dim_product.insert(0, 'product_id', range(1, len(dim_product) + 1))

print(f"Products from sales system     : {len(p1):,}")
print(f"Products from inventory system : {len(p2):,}")
print(f"Total dim_product rows         : {len(dim_product):,}")
print(f"Categories : {dim_product['ProductCategory'].value_counts().to_dict()}")

out = os.path.join(SCHEMA, 'dim_product.csv')
dim_product.to_csv(out, index=False)
print(f"\n Saved dim_product.csv — {len(dim_product):,} rows")

# DIM_DATE

print_section("Building dim_date")

# Collect all unique dates from both datasets
dates_d1 = pd.concat([
    df1['OrderDate'].dt.normalize(),
    df1['ShipDate'].dt.normalize()
])
dates_d2 = df2['InvoiceDate'].dt.normalize()

all_dates = pd.concat([dates_d1, dates_d2]).drop_duplicates().sort_values()
all_dates = all_dates.reset_index(drop=True)

dim_date = pd.DataFrame({'date': all_dates})
dim_date.insert(0, 'date_id', range(1, len(dim_date) + 1))
dim_date['day']        = dim_date['date'].dt.day
dim_date['month']      = dim_date['date'].dt.month
dim_date['month_name'] = dim_date['date'].dt.strftime('%B')
dim_date['quarter']    = dim_date['date'].dt.quarter
dim_date['year']       = dim_date['date'].dt.year
dim_date['weekday']    = dim_date['date'].dt.day_name()
dim_date['is_weekend'] = dim_date['date'].dt.dayofweek >= 5
dim_date['week_of_year'] = dim_date['date'].dt.isocalendar().week.astype(int)

print(f"Date range : {dim_date['date'].min().date()} → {dim_date['date'].max().date()}")
print(f"Total dates: {len(dim_date):,}")

out = os.path.join(SCHEMA, 'dim_date.csv')
dim_date.to_csv(out, index=False)
print(f"\n Saved dim_date.csv — {len(dim_date):,} rows")

# DIM_WAREHOUSE

print_section("Building dim_warehouse")

# Use actual regions from Dataset 1 as warehouse zones
regions_countries = {
    'Southwest'     : 'United States',
    'Northwest'     : 'United States',
    'Central'       : 'United States',
    'Southeast'     : 'United States',
    'Northeast'     : 'United States',
    'France'        : 'France',
    'Australia'     : 'Australia',
    'Canada'        : 'Canada',
    'Germany'       : 'Germany',
    'United Kingdom': 'United Kingdom',
}

warehouses = []
wh_id = 1
for region, country in regions_countries.items():
    for store_num in [1, 2]:
        warehouses.append({
            'warehouse_id'      : f'WH{wh_id:03d}',
            'warehouse_name'    : f'{region} Dark Store {store_num}',
            'region'            : region,
            'country'           : country,
            'capacity'          : random.randint(500, 2000),
            'max_orders_per_day': random.randint(200, 800),
            'is_active'         : True
        })
        wh_id += 1

dim_warehouse = pd.DataFrame(warehouses)

print(f"Total warehouses : {len(dim_warehouse)}")
print(f"Countries        : {dim_warehouse['country'].unique().tolist()}")

out = os.path.join(SCHEMA, 'dim_warehouse.csv')
dim_warehouse.to_csv(out, index=False)
print(f"\n Saved dim_warehouse.csv — {len(dim_warehouse)} rows")

# FACT_ORDERS

print_section("Building fact_orders")

fact = df1.copy()

# --- Map customer_id
cust_map = dim_customer.set_index('EmailAddress')['customer_id']
fact['customer_id'] = fact['EmailAddress'].map(cust_map)

# --- Map product_id
prod_map = dim_product[dim_product['source_system'] == 'sales'] \
               .set_index('ProductName')['product_id']
fact['product_id'] = fact['ProductName'].map(prod_map)

# --- Map date_id (on OrderDate)
date_map = dim_date.set_index(dim_date['date'].dt.normalize())['date_id']
fact['date_id'] = fact['OrderDate'].dt.normalize().map(date_map)

# --- Assign warehouse_id based on SalesTerritoryRegion
wh_map = dim_warehouse.groupby('region')['warehouse_id'].apply(list).to_dict()
def assign_warehouse(region):
    options = wh_map.get(region, ['WH001'])
    return random.choice(options)
fact['warehouse_id'] = fact['SalesTerritoryRegion'].apply(assign_warehouse)

# --- Select final columns
fact_orders = fact[[
    'customer_id', 'product_id', 'date_id', 'warehouse_id',
    'SalesTerritoryRegion', 'SalesTerritoryCountry', 'SalesTerritoryGroup',
    'PromotionType', 'ProductCategory', 'ProductSubcategory',
    'SalesAmount', 'StandardCost', 'TaxAmt', 'Freight',
    'profit', 'profit_margin_pct', 'total_cost',
    'promised_days', 'actual_days', 'delay_days', 'is_delayed',
    'OrderDate', 'DueDate', 'ShipDate'
]].copy()

fact_orders.insert(0, 'order_id', range(1, len(fact_orders) + 1))

# Verify no nulls in foreign keys
fk_nulls = fact_orders[['customer_id','product_id','date_id']].isnull().sum()
print(f"Foreign key nulls: {fk_nulls.to_dict()}")
print(f"Total orders     : {len(fact_orders):,}")
print(f"Revenue total    : ${fact_orders['SalesAmount'].sum():,.0f}")
print(f"Delayed orders   : {fact_orders['is_delayed'].sum():,} ({fact_orders['is_delayed'].mean()*100:.1f}%)")

out = os.path.join(SCHEMA, 'fact_orders.csv')
fact_orders.to_csv(out, index=False)
print(f"\n Saved fact_orders.csv — {len(fact_orders):,} rows")

# FACT_INVENTORY

print_section("Building fact_inventory")

inv = df2.copy()

# --- Map product_id from inventory system
inv_prod_map = dim_product[dim_product['source_system'] == 'inventory'] \
                   .set_index('stock_code')['product_id']
inv['product_id'] = inv['StockCode'].map(inv_prod_map)

# --- Map date_id
inv_date = inv['InvoiceDate'].dt.normalize()
inv['date_id'] = inv_date.map(date_map)

# --- Assign warehouse based on Country
country_wh_map = dim_warehouse.groupby('country')['warehouse_id'].apply(list).to_dict()
def assign_wh_by_country(country):
    # Map Online Retail countries to our warehouse countries
    mapping = {
        'United Kingdom': 'United Kingdom',
        'France'        : 'France',
        'Germany'       : 'Germany',
        'Australia'     : 'Australia',
        'Canada'        : 'Canada',
    }
    mapped = mapping.get(country, 'United States')
    options = country_wh_map.get(mapped, ['WH001'])
    return random.choice(options)

inv['warehouse_id'] = inv['Country'].apply(assign_wh_by_country)

# --- Final columns
fact_inventory = inv[[
    'product_id', 'date_id', 'warehouse_id',
    'InvoiceNo', 'StockCode', 'Description',
    'Quantity', 'UnitPrice', 'revenue',
    'CustomerID', 'Country',
    'invoice_month', 'invoice_year'
]].copy()

fact_inventory.insert(0, 'inventory_id', range(1, len(fact_inventory) + 1))

# Fill any unmapped date_ids with nearest available
null_dates = fact_inventory['date_id'].isnull().sum()
if null_dates > 0:
    fact_inventory['date_id'] = fact_inventory['date_id'].fillna(1)
    print(f"  Note: Filled {null_dates} unmapped date_ids with default")

print(f"Total inventory rows : {len(fact_inventory):,}")
print(f"Total revenue        : ${fact_inventory['revenue'].sum():,.0f}")
print(f"Unique products      : {fact_inventory['StockCode'].nunique():,}")
print(f"Unique customers     : {fact_inventory['CustomerID'].nunique():,}")

out = os.path.join(SCHEMA, 'fact_inventory.csv')
fact_inventory.to_csv(out, index=False)
print(f"\n Saved fact_inventory.csv — {len(fact_inventory):,} rows")


# FINAL SUMMARY

print_section("PHASE 2 COMPLETE — Schema Summary")

files = {
    'dim_customer.csv' : len(dim_customer),
    'dim_product.csv'  : len(dim_product),
    'dim_date.csv'     : len(dim_date),
    'dim_warehouse.csv': len(dim_warehouse),
    'fact_orders.csv'  : len(fact_orders),
    'fact_inventory.csv': len(fact_inventory),
}

for fname, rows in files.items():
    print(f"  {fname:<25} {rows:>10,} rows")

