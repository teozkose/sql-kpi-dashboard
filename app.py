"""Streamlit KPI dashboard over data/retail.db. Every panel runs one of the files in sql/.

    streamlit run app.py
"""
import os
import sqlite3

import pandas as pd
import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "data", "retail.db")


@st.cache_data
def query(name: str) -> pd.DataFrame:
    sql = open(os.path.join(ROOT, "sql", f"{name}.sql")).read()
    with sqlite3.connect(DB) as con:
        return pd.read_sql_query(sql, con)


st.set_page_config(page_title="Retail KPIs", layout="wide")
st.title("Retail KPI dashboard")
st.caption("UK online gift retailer, Dec 2009 to Nov 2011. Tiles show FY2011 (Dec 2010 to Nov 2011) against FY2010. "
           "Amounts in GBP.")

if not os.path.exists(DB):
    st.error("data/retail.db not found. Run ./run_all.sh first.")
    st.stop()

kpi = query("01_kpi_summary").set_index("fiscal_year")
cur, prev = kpi.loc["FY2011"], kpi.loc["FY2010"]
cols = st.columns(5)
for col, (label, field, fmt) in zip(cols, [
    ("Revenue", "revenue", "£{:,.0f}"),
    ("Orders", "orders", "{:,.0f}"),
    ("Customers", "customers", "{:,.0f}"),
    ("Avg order value", "avg_order_value", "£{:,.2f}"),
    ("Orders per customer", "orders_per_customer", "{:.2f}"),
]):
    value = f"£{cur[field] / 1e6:.2f}M" if field == "revenue" else fmt.format(cur[field])
    col.metric(label, value, f"{cur[field] / prev[field] - 1:+.1%} vs FY2010")

tab_rev, tab_cust, tab_prod = st.tabs(["Revenue", "Customers", "Products and markets"])

with tab_rev:
    monthly = query("02_monthly_revenue").set_index("order_month")
    st.subheader("Monthly revenue")
    st.bar_chart(monthly["revenue"])
    left, right = st.columns(2)
    left.subheader("Average order value")
    left.line_chart(monthly["avg_order_value"])
    returns = query("08_return_rate").set_index("order_month")
    right.subheader("Return rate (returned value / gross sales)")
    right.line_chart(returns["return_rate"])
    st.dataframe(monthly, width="stretch")

with tab_cust:
    nvr = query("03_new_vs_returning").set_index("order_month")
    st.subheader("Revenue from first-time and returning customers")
    st.bar_chart(nvr[["new_revenue", "returning_revenue"]])

    st.subheader("Cohort retention")
    ret = query("04_cohort_retention")
    max_months = st.slider("Months since first order", 3, 23, 12)
    grid = (ret[ret["months_since"] <= max_months]
            .pivot(index="cohort_month", columns="months_since", values="retention"))
    st.dataframe(grid.style.format("{:.0%}", na_rep="").background_gradient(cmap="Blues", axis=None, vmax=0.5),
                 width="stretch")

    left, right = st.columns(2)
    left.subheader("RFM segments")
    left.dataframe(query("07_rfm_segments"), width="stretch", hide_index=True)
    right.subheader("Revenue by customer decile")
    right.bar_chart(query("09_customer_concentration").set_index("decile")["share"])

with tab_prod:
    st.subheader("Top 15 products, FY2011")
    st.dataframe(query("05_top_products"), width="stretch", hide_index=True)
    countries = query("06_country_revenue")
    n = st.slider("Countries to show", 5, len(countries), 10)
    st.subheader("Revenue by customer country, FY2011")
    st.bar_chart(countries.head(n).set_index("country")["revenue"])
