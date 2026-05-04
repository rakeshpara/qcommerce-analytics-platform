"""
QCommerce Analytics Platform — Streamlit App
Pages: Overview | Insights | Anomaly Alerts | What-If Simulator
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import snowflake.connector
from scipy import stats
import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="QCommerce Intelligence Platform",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# SNOWFLAKE CONNECTION
# ─────────────────────────────────────────────

@st.cache_resource
def get_connection():
    return snowflake.connector.connect(
        user      = os.getenv('SNOWFLAKE_USER'),
        password  = os.getenv('SNOWFLAKE_PASSWORD'),
        account   = os.getenv('SNOWFLAKE_ACCOUNT'),
        database  = os.getenv('SNOWFLAKE_DATABASE'),
        schema    = os.getenv('SNOWFLAKE_SCHEMA'),
        warehouse = os.getenv('SNOWFLAKE_WAREHOUSE'),
    )

@st.cache_data(ttl=300)
def run_query(sql):
    conn = get_connection()
    return pd.read_sql(sql, conn)

# ─────────────────────────────────────────────
# SIDEBAR NAVIGATION
# ─────────────────────────────────────────────

st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3081/3081559.png", width=60)
st.sidebar.title("QCommerce Platform")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["📊 Overview", "💡 Insights", "🚨 Anomaly Alerts", "🔮 What-If Simulator"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.caption("Data: Snowflake · QCOMMERCE_DB")
st.sidebar.caption("Built with Python + Streamlit")

# ─────────────────────────────────────────────
# PAGE 1 — OVERVIEW
# ─────────────────────────────────────────────

if page == "📊 Overview":

    st.title("📊 Executive Overview")
    st.markdown("Live KPIs pulled directly from Snowflake")

    # --- KPI Cards
    with st.spinner("Loading KPIs..."):
        kpi = run_query("""
            SELECT
                SUM(REVENUE)       AS total_revenue,
                SUM(ORDERS)        AS total_orders,
                AVG(AVG_MARGIN)    AS avg_margin,
                SUM(PROFIT)        AS total_profit
            FROM V_DAILY_REVENUE
        """)

        delivery = run_query("""
            SELECT
                AVG(AVG_DELIVERY_DAYS) AS avg_delivery_days,
                AVG(PCT_DELAYED)       AS avg_pct_delayed
            FROM V_DELIVERY_PERFORMANCE
        """)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("💰 Total Revenue",    f"${kpi['TOTAL_REVENUE'][0]:,.0f}")
    col2.metric("📦 Total Orders",     f"{kpi['TOTAL_ORDERS'][0]:,.0f}")
    col3.metric("📈 Avg Profit Margin",f"{kpi['AVG_MARGIN'][0]:.1f}%")
    col4.metric("🚚 Avg Delivery Days",f"{delivery['AVG_DELIVERY_DAYS'][0]:.1f}")
    col5.metric("⚠️ Delay Rate",       f"{delivery['AVG_PCT_DELAYED'][0]:.1f}%")

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Revenue Trend by Year")
        rev_year = run_query("""
            SELECT YEAR, SUM(REVENUE) AS REVENUE
            FROM V_DAILY_REVENUE
            GROUP BY YEAR ORDER BY YEAR
        """)
        fig = px.line(rev_year, x='YEAR', y='REVENUE',
                      markers=True, color_discrete_sequence=['#378ADD'])
        fig.update_layout(margin=dict(t=10,b=10), height=280)
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Revenue by Product Category")
        rev_cat = run_query("""
            SELECT CATEGORY, SUM(REVENUE) AS REVENUE
            FROM V_DAILY_REVENUE
            GROUP BY CATEGORY ORDER BY REVENUE DESC
        """)
        fig = px.pie(rev_cat, names='CATEGORY', values='REVENUE',
                     hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(margin=dict(t=10,b=10), height=280)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Revenue by Region")
    rev_region = run_query("""
        SELECT REGION, SUM(REVENUE) AS REVENUE
        FROM V_DAILY_REVENUE
        GROUP BY REGION ORDER BY REVENUE DESC
    """)
    fig = px.bar(rev_region, x='REVENUE', y='REGION', orientation='h',
                 color='REVENUE', color_continuous_scale='Blues')
    fig.update_layout(margin=dict(t=10,b=10), height=320, yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────
# PAGE 2 — INSIGHTS
# ─────────────────────────────────────────────

elif page == "💡 Insights":

    st.title("💡 Automated Insights")
    st.markdown("Auto-generated from your Snowflake data")

    with st.spinner("Analyzing data..."):
        rev      = run_query("SELECT REGION, CATEGORY, SUM(REVENUE) AS R, SUM(ORDERS) AS O FROM V_DAILY_REVENUE GROUP BY 1,2")
        delivery = run_query("SELECT REGION, AVG(PCT_DELAYED) AS D, AVG(AVG_DELIVERY_DAYS) AS AD FROM V_DELIVERY_PERFORMANCE GROUP BY 1")
        promo    = run_query("SELECT PROMOTIONTYPE, SUM(TOTAL_REVENUE) AS R, AVG(AVG_MARGIN) AS M FROM V_PROMOTION_IMPACT GROUP BY 1")
        segments = run_query("SELECT CUSTOMER_SEGMENT, COUNT(*) AS C FROM V_CUSTOMER_SEGMENTS GROUP BY 1")
        inv      = run_query("SELECT STOCK_STATUS, COUNT(*) AS C FROM V_INVENTORY_RISK GROUP BY 1")

    # Generate insights
    top_region     = rev.groupby('REGION')['R'].sum().idxmax()
    top_region_rev = rev.groupby('REGION')['R'].sum().max()
    top_cat        = rev.groupby('CATEGORY')['R'].sum().idxmax()
    worst_delivery = delivery.loc[delivery['D'].idxmax(), 'REGION']
    best_delivery  = delivery.loc[delivery['D'].idxmin(), 'REGION']
    best_promo     = promo.loc[promo['R'].idxmax(), 'PROMOTIONTYPE']
    best_promo_rev = promo['R'].max()
    vip_count      = segments[segments['CUSTOMER_SEGMENT'] == 'VIP']['C'].values
    vip_count      = int(vip_count[0]) if len(vip_count) > 0 else 0
    stockout_count = inv[inv['STOCK_STATUS'] == 'Low Movement / Stockout Risk']['C'].values
    stockout_count = int(stockout_count[0]) if len(stockout_count) > 0 else 0

    insights = [
        ("🏆", "Top Revenue Region",
         f"{top_region} is your highest revenue region, generating ${top_region_rev:,.0f} in total sales."),
        ("🛒", "Best Product Category",
         f"{top_cat} is your top-performing product category by revenue."),
        ("⚠️", "Delivery Risk",
         f"{worst_delivery} has the highest order delay rate. Consider prioritizing warehouse capacity there."),
        ("✅", "Best Delivery Region",
         f"{best_delivery} has the lowest delay rate — a model region for operational efficiency."),
        ("🎯", "Most Effective Promotion",
         f"'{best_promo}' is your highest revenue promotion type at ${best_promo_rev:,.0f}."),
        ("👑", "VIP Customers",
         f"You have {vip_count:,} VIP customers (10+ orders). These are your highest retention targets."),
        ("📦", "Stockout Risk",
         f"{stockout_count:,} products are flagged as Low Movement / Stockout Risk. Review inventory levels."),
    ]

    for icon, title, text in insights:
        with st.container():
            st.markdown(f"""
            <div style="background:#f8f9fa;border-left:4px solid #378ADD;
                        padding:14px 18px;border-radius:6px;margin-bottom:12px">
                <div style="font-size:15px;font-weight:600;color:#1a1a2e">{icon} {title}</div>
                <div style="font-size:14px;color:#444;margin-top:4px">{text}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Promotion Effectiveness")
    fig = px.bar(promo.sort_values('R', ascending=True),
                 x='R', y='PROMOTIONTYPE', orientation='h',
                 color='M', color_continuous_scale='Greens',
                 labels={'R': 'Total Revenue', 'M': 'Avg Margin %', 'PROMOTIONTYPE': 'Promotion'})
    fig.update_layout(height=320, margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────
# PAGE 3 — ANOMALY ALERTS
# ─────────────────────────────────────────────

elif page == "🚨 Anomaly Alerts":

    st.title("🚨 Anomaly Detection")
    st.markdown("Z-score based anomaly detection across revenue, delivery, and inventory")

    with st.spinner("Running anomaly detection..."):
        rev_daily = run_query("""
            SELECT DATE, SUM(REVENUE) AS REVENUE, SUM(ORDERS) AS ORDERS
            FROM V_DAILY_REVENUE
            GROUP BY DATE ORDER BY DATE
        """)
        delivery_region = run_query("""
            SELECT REGION, AVG(PCT_DELAYED) AS PCT_DELAYED,
                   AVG(AVG_DELIVERY_DAYS) AS AVG_DAYS
            FROM V_DELIVERY_PERFORMANCE GROUP BY 1
        """)
        inv_data = run_query("""
            SELECT DESCRIPTION, SUM(TOTAL_UNITS_SOLD) AS UNITS
            FROM V_INVENTORY_RISK
            GROUP BY 1 ORDER BY UNITS ASC
            LIMIT 50
        """)

    alerts = []

    # --- Anomaly 1: Revenue Z-score
    rev_daily = rev_daily.dropna(subset=['REVENUE'])
    if len(rev_daily) > 10:
        rev_daily['zscore'] = stats.zscore(rev_daily['REVENUE'])
        rev_anomalies = rev_daily[abs(rev_daily['zscore']) > 2]
        for _, row in rev_anomalies.iterrows():
            direction = "spike" if row['zscore'] > 0 else "drop"
            alerts.append(("🔴", "Revenue Anomaly",
                f"Date {str(row['DATE'])[:10]}: Revenue ${row['REVENUE']:,.0f} — unusual {direction} detected (Z={row['zscore']:.2f})"))

    # --- Anomaly 2: Delivery delay Z-score
    if len(delivery_region) > 3:
        delivery_region['zscore'] = stats.zscore(delivery_region['PCT_DELAYED'])
        del_anomalies = delivery_region[delivery_region['zscore'] > 1.5]
        for _, row in del_anomalies.iterrows():
            alerts.append(("🟡", "Delivery Delay Spike",
                f"{row['REGION']}: {row['PCT_DELAYED']:.1f}% delayed orders — significantly above average"))

    # --- Anomaly 3: Low inventory
    low_inv = inv_data.head(10)
    for _, row in low_inv.iterrows():
        alerts.append(("🟠", "Stockout Risk",
            f"'{row['DESCRIPTION'][:40]}' — only {row['UNITS']:,.0f} units total movement. Potential stockout risk."))

    # Display alerts
    if alerts:
        st.markdown(f"### {len(alerts)} alerts detected")
        for color, title, msg in alerts:
            bg = "#fff5f5" if color == "🔴" else "#fffbf0" if color == "🟡" else "#fff8f0"
            border = "#e74c3c" if color == "🔴" else "#f39c12" if color == "🟡" else "#e67e22"
            st.markdown(f"""
            <div style="background:{bg};border-left:4px solid {border};
                        padding:12px 16px;border-radius:6px;margin-bottom:10px">
                <div style="font-size:14px;font-weight:600;color:#1a1a2e">{color} {title}</div>
                <div style="font-size:13px;color:#555;margin-top:4px">{msg}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ No anomalies detected in current data.")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Revenue Distribution")
        fig = px.histogram(rev_daily, x='REVENUE', nbins=40,
                           color_discrete_sequence=['#378ADD'])
        fig.update_layout(height=280, margin=dict(t=10,b=10))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Delay Rate by Region")
        fig = px.bar(delivery_region.sort_values('PCT_DELAYED', ascending=True),
                     x='PCT_DELAYED', y='REGION', orientation='h',
                     color='PCT_DELAYED', color_continuous_scale='Reds')
        fig.update_layout(height=280, margin=dict(t=10,b=10))
        st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────
# PAGE 4 — WHAT-IF SIMULATOR
# ─────────────────────────────────────────────

elif page == "🔮 What-If Simulator":

    st.title("🔮 What-If Simulator")
    st.markdown("Simulate business decisions and project their impact on revenue and operations")

    with st.spinner("Loading base metrics..."):
        base = run_query("""
            SELECT
                SUM(REVENUE)    AS base_revenue,
                SUM(ORDERS)     AS base_orders,
                AVG(AVG_MARGIN) AS base_margin
            FROM V_DAILY_REVENUE
        """)
        base_revenue = float(base['BASE_REVENUE'][0])
        base_orders  = int(base['BASE_ORDERS'][0])
        base_margin  = float(base['BASE_MARGIN'][0])

        inv_base = run_query("""
            SELECT COUNT(*) AS stockout_products
            FROM V_INVENTORY_RISK
            WHERE STOCK_STATUS = 'Low Movement / Stockout Risk'
        """)
        stockout_products = int(inv_base['STOCKOUT_PRODUCTS'][0])

    st.markdown("---")

    # --- Simulator 1
    st.subheader("📦 Scenario 1 — Reduce Delivery Time")
    col1, col2 = st.columns([1, 2])
    with col1:
        delivery_reduction = st.slider(
            "Reduce avg delivery time by (%)", 0, 40, 10,
            help="Faster delivery improves customer satisfaction and repeat orders"
        )
        retention_lift = delivery_reduction * 0.6
        revenue_impact = base_revenue * (1 + retention_lift / 100)
        extra_revenue  = revenue_impact - base_revenue

    with col2:
        m1, m2, m3 = st.columns(3)
        m1.metric("Projected Revenue",   f"${revenue_impact:,.0f}", f"+${extra_revenue:,.0f}")
        m2.metric("Customer Retention ↑", f"+{retention_lift:.1f}%")
        m3.metric("Delivery Reduction",   f"-{delivery_reduction}%")
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=revenue_impact/1e6,
            delta={'reference': base_revenue/1e6, 'valueformat': '.2f'},
            gauge={'axis': {'range': [base_revenue/1e6 * 0.9, base_revenue/1e6 * 1.5]},
                   'bar': {'color': "#378ADD"}},
            title={'text': "Projected Revenue ($M)"}
        ))
        fig.update_layout(height=200, margin=dict(t=30,b=0,l=30,r=30))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # --- Simulator 2
    st.subheader("🏷️ Scenario 2 — Change Promotion Strategy")
    col1, col2 = st.columns([1, 2])
    with col1:
        promo_boost = st.slider(
            "Increase promotion coverage by (%)", 0, 50, 20,
            help="Applying promotions to more orders can drive volume but reduce margin"
        )
        margin_trade = promo_boost * 0.15
        order_lift   = base_orders * (1 + promo_boost * 0.008)
        new_margin   = max(base_margin - margin_trade, 0)
        new_revenue  = base_revenue * (1 + promo_boost * 0.005)

    with col2:
        m1, m2, m3 = st.columns(3)
        m1.metric("Projected Orders",  f"{order_lift:,.0f}", f"+{order_lift-base_orders:,.0f}")
        m2.metric("Projected Revenue", f"${new_revenue:,.0f}", f"+${new_revenue-base_revenue:,.0f}")
        m3.metric("Margin Impact",     f"{new_margin:.1f}%", f"-{margin_trade:.1f}%", delta_color="inverse")

    st.markdown("---")

    # --- Simulator 3
    st.subheader("📊 Scenario 3 — Inventory Restocking")
    col1, col2 = st.columns([1, 2])
    with col1:
        restock_pct = st.slider(
            "Restock low-inventory products by (%)", 0, 100, 30,
            help="Restocking at-risk products reduces missed sales opportunities"
        )
        products_fixed    = int(stockout_products * restock_pct / 100)
        missed_sales_rec  = products_fixed * 850
        stockout_remaining = stockout_products - products_fixed

    with col2:
        m1, m2, m3 = st.columns(3)
        m1.metric("Products Restocked",      f"{products_fixed}")
        m2.metric("Recovered Missed Sales",  f"${missed_sales_rec:,.0f}")
        m3.metric("Remaining At-Risk",       f"{stockout_remaining}")

        restock_data = pd.DataFrame({
            'Status': ['Restocked', 'Still at Risk'],
            'Count':  [products_fixed, stockout_remaining]
        })
        fig = px.pie(restock_data, names='Status', values='Count',
                     hole=0.5, color_discrete_sequence=['#2ecc71', '#e74c3c'])
        fig.update_layout(height=200, margin=dict(t=10,b=10))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # --- Combined Impact Summary
    st.subheader("📋 Combined Scenario Summary")
    total_projected = revenue_impact + (new_revenue - base_revenue) + missed_sales_rec
    summary = pd.DataFrame({
        'Scenario': [
            'Reduce Delivery Time',
            'Promotion Strategy',
            'Inventory Restocking'
        ],
        'Revenue Impact ($)': [
            extra_revenue,
            new_revenue - base_revenue,
            missed_sales_rec
        ]
    })
    fig = px.bar(summary, x='Scenario', y='Revenue Impact ($)',
                 color='Revenue Impact ($)', color_continuous_scale='Blues',
                 text_auto='.2s')
    fig.update_layout(height=320, margin=dict(t=10,b=10))
    st.plotly_chart(fig, use_container_width=True)
    st.metric("💰 Total Projected Revenue Uplift (all 3 scenarios)",
              f"${total_projected - base_revenue:,.0f}",
              f"+{(total_projected/base_revenue - 1)*100:.1f}% vs baseline")
