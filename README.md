# QCommerce Analytics Intelligence Platform

An end-to-end data analytics platform simulating a quick commerce ecosystem (Blinkit/Zepto-style), built with Snowflake, Python, Power BI, and Streamlit.

---

## Architecture

```
Raw Data (Excel)
      ↓
Python ETL Pipeline (Pandas)
      ↓
Snowflake Data Warehouse (Constellation Schema)
      ↓
SQL Analytical Views (6 KPI views)
      ↓
┌─────────────────┬──────────────────────┐
│   Power BI      │   Streamlit Web App  │
│   Dashboard     │   (Intelligence Layer│
│   (4 pages)     │    + What-If Engine) │
└─────────────────┴──────────────────────┘
```

---

## Dashboard Pages (Power BI)

| Page | Description |
|---|---|
| Executive Overview | Revenue trend, category split, regional performance |
| Delivery Performance | Delay rates, avg delivery days by region |
| Inventory Intelligence | Stock movement, stockout risk classification |
| Customer Insights | Segments (VIP/Regular/New), income vs spend, promotion impact |

---

## Streamlit App Features

| Feature | Description |
|---|---|
| Live KPIs | Real-time metrics from Snowflake |
| Auto Insights | 7 rule-based insights generated from live data |
| Anomaly Detection | Z-score detection on revenue, delivery, inventory |
| What-If Simulator | 3 scenario sliders projecting revenue impact |

---

## Data Model (Constellation Schema)

```
             DIM_DATE
            /        \
DIM_CUSTOMER—FACT_ORDERS   FACT_INVENTORY—DIM_WAREHOUSE
            \        /
            DIM_PRODUCT
```

| Table | Rows | Source |
|---|---|---|
| DIM_CUSTOMER | 18,479 | Adventures Online Sales |
| DIM_PRODUCT | 3,795 | Both datasets merged |
| DIM_DATE | 1,439 | Generated from both datasets |
| DIM_WAREHOUSE | 20 | Synthetically generated |
| FACT_ORDERS | 60,382 | Adventures Online Sales |
| FACT_INVENTORY | 397,884 | Online Retail dataset |

---

## Tech Stack

| Layer | Tool |
|---|---|
| Data Warehouse | Snowflake (AWS ap-southeast-7) |
| ETL Pipeline | Python, Pandas, openpyxl |
| Data Modeling | SQL (Star/Constellation Schema) |
| Dashboard | Power BI Desktop |
| Web Application | Streamlit |
| Anomaly Detection | SciPy (Z-score) |
| Data Generation | Faker, NumPy |

---

## Project Structure

```
qcommerce_platform/
├── data/
│   ├── raw/              ← original Excel files (gitignored)
│   ├── cleaned/          ← cleaned CSVs (gitignored)
│   └── schema/           ← dimension & fact CSVs (gitignored)
├── etl/
│   ├── phase1_clean.py   ← data cleaning pipeline
│   ├── phase2_schema.py  ← star schema builder
│   └── phase3_snowflake.py ← Snowflake loader + view creation
├── app/
│   └── streamlit_app.py  ← web application
├── sql/
│   └── create_tables.sql ← Snowflake DDL
├── dashboard/
│   └── screenshots/      ← Power BI dashboard screenshots
├── .env                  ← credentials (gitignored)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## How to Run Locally

**1. Clone the repo**
```bash
git clone https://github.com/YOUR_USERNAME/qcommerce-analytics-platform.git
cd qcommerce-analytics-platform
```

**2. Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up .env file**
```
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_DATABASE=QCOMMERCE_DB
SNOWFLAKE_SCHEMA=ANALYTICS
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
```

**5. Run ETL pipeline**
```bash
python etl/phase1_clean.py
python etl/phase2_schema.py
python etl/phase3_snowflake.py
```

**6. Launch Streamlit app**
```bash
streamlit run app/streamlit_app.py
```

---

## Key Business KPIs

- **Total Revenue:** $29.3M across 60,382 orders
- **Avg Profit Margin:** 53.3%
- **Delivery Performance:** 99.5% on-time rate
- **Inventory Coverage:** 397,884 stock movements across 3,665 SKUs
- **Customer Base:** 18,479 customers across 6 countries

---

## Intelligence Features

**Anomaly Detection**
Uses Z-score (threshold = 2.0) to flag:
- Unusual revenue drops or spikes on any given day
- Regions with abnormally high delivery delay rates
- Products with dangerously low stock movement

**What-If Simulator**
Three interactive scenarios:
1. Reducing delivery time → projects customer retention lift and revenue uplift
2. Increasing promotion coverage → projects order volume vs margin trade-off
3. Restocking low-inventory products → projects recovered missed sales

---

## Author

**Rakesh Para**
Data Analytics | Python | SQL | Power BI | Snowflake

---

## License

MIT License
