"""
PHASE 3 — Snowflake Data Loader
QCommerce Analytics Platform

Loads all 6 schema CSVs into Snowflake tables.
Requires .env file in project root with credentials.
"""

import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
import os
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'schema')

def print_section(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")

# CONNECT TO SNOWFLAKE

print_section("Connecting to Snowflake")

conn = snowflake.connector.connect(
    user      = os.getenv('SNOWFLAKE_USER'),
    password  = os.getenv('SNOWFLAKE_PASSWORD'),
    account   = os.getenv('SNOWFLAKE_ACCOUNT'),
    database  = os.getenv('SNOWFLAKE_DATABASE'),
    schema    = os.getenv('SNOWFLAKE_SCHEMA'),
    warehouse = os.getenv('SNOWFLAKE_WAREHOUSE'),
)

print(f" Connected to Snowflake")
print(f"   Account  : {os.getenv('SNOWFLAKE_ACCOUNT')}")
print(f"   Database : {os.getenv('SNOWFLAKE_DATABASE')}")
print(f"   Schema   : {os.getenv('SNOWFLAKE_SCHEMA')}")

# LOADER FUNCTION

def load_table(csv_filename, table_name, dtype_map=None):
    """Load a CSV into a Snowflake table using write_pandas."""
    path = os.path.join(SCHEMA_DIR, csv_filename)
    df = pd.read_csv(path, dtype=dtype_map)

    # Snowflake expects uppercase column names
    df.columns = [c.upper() for c in df.columns]

    # Truncate existing data before loading
    cursor = conn.cursor()
    cursor.execute(f"TRUNCATE TABLE {table_name}")
    cursor.close()

    success, nchunks, nrows, _ = write_pandas(
        conn=conn,
        df=df,
        table_name=table_name,
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema=os.getenv('SNOWFLAKE_SCHEMA'),
        quote_identifiers=False,
    )

    if success:
        print(f"  {table_name:<20} → {nrows:>10,} rows loaded")
    else:
        print(f"  {table_name} — FAILED")

    return nrows

# LOAD ALL 6 TABLES

print_section("Loading Tables into Snowflake")

total_rows = 0

total_rows += load_table('dim_customer.csv',  'DIM_CUSTOMER')
total_rows += load_table('dim_product.csv',   'DIM_PRODUCT')
total_rows += load_table('dim_date.csv',      'DIM_DATE')
total_rows += load_table('dim_warehouse.csv', 'DIM_WAREHOUSE')
total_rows += load_table('fact_orders.csv',   'FACT_ORDERS')
total_rows += load_table('fact_inventory.csv','FACT_INVENTORY',
                          dtype_map={'CustomerID': str})

# VERIFY WITH COUNTS

print_section("Verifying Row Counts in Snowflake")

tables = [
    'DIM_CUSTOMER', 'DIM_PRODUCT', 'DIM_DATE',
    'DIM_WAREHOUSE', 'FACT_ORDERS', 'FACT_INVENTORY'
]

cursor = conn.cursor()
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"  {table:<25} {count:>10,} rows")
cursor.close()

# CREATE ANALYTICAL VIEWS

print_section("Creating Analytical Views")

views = {

'V_DAILY_REVENUE': """
CREATE OR REPLACE VIEW V_DAILY_REVENUE AS
SELECT
    d.DATE, d.MONTH_NAME, d.YEAR, d.QUARTER, d.IS_WEEKEND,
    f.SALESTERRITORYREGION   AS region,
    f.SALESTERRITORYGROUP    AS territory_group,
    f.PRODUCTCATEGORY        AS category,
    f.PROMOTIONTYPE          AS promotion,
    SUM(f.SALESAMOUNT)       AS revenue,
    SUM(f.PROFIT)            AS profit,
    COUNT(f.ORDER_ID)        AS orders,
    AVG(f.PROFIT_MARGIN_PCT) AS avg_margin
FROM FACT_ORDERS f
JOIN DIM_DATE d ON f.DATE_ID = d.DATE_ID
GROUP BY 1,2,3,4,5,6,7,8,9
""",

'V_DELIVERY_PERFORMANCE': """
CREATE OR REPLACE VIEW V_DELIVERY_PERFORMANCE AS
SELECT
    f.SALESTERRITORYREGION              AS region,
    f.SALESTERRITORYGROUP               AS territory_group,
    f.PRODUCTCATEGORY                   AS category,
    d.YEAR,
    d.MONTH_NAME,
    COUNT(f.ORDER_ID)                   AS total_orders,
    AVG(f.ACTUAL_DAYS)                  AS avg_delivery_days,
    AVG(f.PROMISED_DAYS)                AS avg_promised_days,
    AVG(f.DELAY_DAYS)                   AS avg_delay_days,
    SUM(CASE WHEN f.IS_DELAYED THEN 1 ELSE 0 END) AS delayed_orders,
    ROUND(SUM(CASE WHEN f.IS_DELAYED THEN 1 ELSE 0 END) * 100.0
          / COUNT(*), 2)                AS pct_delayed
FROM FACT_ORDERS f
JOIN DIM_DATE d ON f.DATE_ID = d.DATE_ID
GROUP BY 1,2,3,4,5
""",

'V_INVENTORY_RISK': """
CREATE OR REPLACE VIEW V_INVENTORY_RISK AS
SELECT
    i.STOCKCODE,
    i.DESCRIPTION,
    i.COUNTRY,
    i.INVOICE_YEAR,
    i.INVOICE_MONTH,
    SUM(i.QUANTITY)       AS total_units_sold,
    SUM(i.REVENUE)        AS total_revenue,
    AVG(i.UNITPRICE)      AS avg_unit_price,
    COUNT(DISTINCT i.INVOICENO) AS invoice_count,
    CASE
        WHEN SUM(i.QUANTITY) > 1000 THEN 'High Movement'
        WHEN SUM(i.QUANTITY) > 300  THEN 'Medium Movement'
        ELSE 'Low Movement / Stockout Risk'
    END AS stock_status
FROM FACT_INVENTORY i
GROUP BY 1,2,3,4,5
""",

'V_CUSTOMER_SEGMENTS': """
CREATE OR REPLACE VIEW V_CUSTOMER_SEGMENTS AS
SELECT
    c.CUSTOMER_ID,
    c.CUSTOMERNAME,
    c.GENDER,
    c.MARITALSTATUS,
    c.INCOME_SEGMENT,
    c.YEARLYINCOME,
    COUNT(f.ORDER_ID)    AS order_count,
    SUM(f.SALESAMOUNT)   AS lifetime_value,
    AVG(f.SALESAMOUNT)   AS avg_order_value,
    SUM(f.PROFIT)        AS total_profit,
    CASE
        WHEN COUNT(f.ORDER_ID) >= 10 THEN 'VIP'
        WHEN COUNT(f.ORDER_ID) >= 5  THEN 'Regular'
        ELSE 'New'
    END AS customer_segment
FROM FACT_ORDERS f
JOIN DIM_CUSTOMER c ON f.CUSTOMER_ID = c.CUSTOMER_ID
GROUP BY 1,2,3,4,5,6
""",

'V_PROMOTION_IMPACT': """
CREATE OR REPLACE VIEW V_PROMOTION_IMPACT AS
SELECT
    PROMOTIONTYPE,
    PRODUCTCATEGORY,
    COUNT(ORDER_ID)        AS total_orders,
    SUM(SALESAMOUNT)       AS total_revenue,
    AVG(SALESAMOUNT)       AS avg_order_value,
    AVG(PROFIT_MARGIN_PCT) AS avg_margin,
    SUM(PROFIT)            AS total_profit
FROM FACT_ORDERS
GROUP BY 1,2
""",

'V_DEMAND_VS_SUPPLY': """
CREATE OR REPLACE VIEW V_DEMAND_VS_SUPPLY AS
SELECT
    fo.PRODUCTCATEGORY   AS sales_category,
    d.YEAR,
    d.MONTH_NAME,
    SUM(fo.SALESAMOUNT)  AS sales_revenue,
    COUNT(fo.ORDER_ID)   AS sales_orders,
    SUM(fi.QUANTITY)     AS inventory_units_moved,
    SUM(fi.REVENUE)      AS inventory_revenue
FROM FACT_ORDERS fo
JOIN DIM_DATE d ON fo.DATE_ID = d.DATE_ID
LEFT JOIN FACT_INVENTORY fi ON d.YEAR = fi.INVOICE_YEAR
    AND d.MONTH = fi.INVOICE_MONTH
GROUP BY 1,2,3
"""

}

cursor = conn.cursor()
for view_name, sql in views.items():
    try:
        cursor.execute(sql)
        print(f"  {view_name} created")
    except Exception as e:
        print(f"  {view_name} failed: {e}")
cursor.close()

# DONE

conn.close()

print_section("PHASE 3 COMPLETE")
print(f"  Total rows loaded : {total_rows:,}")
print(f"  Tables            : 6")
print(f"  Analytical views  : {len(views)}")
