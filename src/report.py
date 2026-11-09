"""Render README.md from README.template.md, results/metrics.json and the query tables, so every
number in the README comes from the last run."""
import json
import os

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
m = json.load(open(os.path.join(RES, "metrics.json")))
t = {n: pd.read_csv(os.path.join(RES, "tables", f"{n}.csv"))
     for n in ("kpi_summary", "rfm_segments", "top_products")}
cur, prev, g = m["fy2011"], m["fy2010"], m["growth"]


def pct(x, signed=False):
    return f"{x:+.1%}" if signed else f"{x:.1%}"


def gbp(x):
    return f"£{x / 1e6:.2f}M" if abs(x) >= 1e6 else f"£{x / 1e3:,.0f}K" if abs(x) >= 1e4 else f"£{x:,.2f}"


kpi_rows = "\n".join(
    f"| {label} | {fmt(prev[k])} | {fmt(cur[k])} | {pct(g[k], True)} |"
    for label, k, fmt in [
        ("Revenue", "revenue", gbp),
        ("Orders", "orders", lambda v: f"{v:,.0f}"),
        ("Customers (known)", "customers", lambda v: f"{v:,.0f}"),
        ("Average order value", "avg_order_value", lambda v: f"£{v:,.2f}"),
        ("Orders per customer", "orders_per_customer", lambda v: f"{v:.2f}"),
        ("Revenue per customer", "revenue_per_customer", lambda v: f"£{v:,.0f}"),
    ])

rfm_rows = "\n".join(
    f"| {r.segment[2:]} | {r.customers:,} ({pct(r.customer_share)}) | {r.avg_recency_days:.0f} | {r.avg_orders:.1f} "
    f"| {gbp(r.avg_revenue)} | {gbp(r.revenue)} ({pct(r.revenue_share)}) |"
    for r in t["rfm_segments"].itertuples())

prod_rows = "\n".join(
    f"| {r.revenue_rank} | {r.description.title()} | {gbp(r.revenue)} | {r.units:,} | {pct(r.share)} |"
    for r in t["top_products"].head(5).itertuples())

ret, rfm, conc = m["retention"], m["rfm"], m["concentration"]
driver = ("bigger baskets, not more orders" if g["orders"] < 0 < g["avg_order_value"]
          else "more orders" if g["orders"] > 0 else "a mix of order count and basket size")
findings = "\n".join([
    f"1. **Revenue grew {pct(g['revenue'], True)} to {gbp(cur['revenue'])}, and the growth came from {driver}.** "
    f"Orders moved {pct(g['orders'], True)} and orders per customer {pct(g['orders_per_customer'], True)}, "
    f"while average order value rose {pct(g['avg_order_value'], True)} to £{cur['avg_order_value']:,.2f}.",
    f"2. **The business runs on repeat buyers.** Returning customers brought {pct(m['returning_revenue_share_fy2011'])} "
    f"of FY2011 revenue from known customers. Yet only {pct(ret['month_1_first_year_cohorts'])} of a typical 2010 "
    f"cohort ordered again the next month and {pct(ret['month_12_first_year_cohorts'])} a year later, so "
    f"first-to-second order conversion is the cheapest lever.",
    f"3. **Revenue is concentrated.** The top 10% of customers spent {pct(conc['top10pct_share'])} of FY2011 revenue "
    f"and the top 20% spent {pct(conc['top20pct_share'])}. RFM Champions are {pct(rfm['champions_customer_share'])} "
    f"of customers, {pct(rfm['champions_revenue_share'])} of revenue, at {rfm['champions_avg_orders']:.1f} orders each.",
    f"4. **{rfm['at_risk_customers']:,} customers are At risk**: they ordered often in FY2011 but not in the last few months. They spent "
    f"{gbp(rfm['at_risk_revenue'])} in FY2011, which makes them the first win-back list.",
    f"5. **The year is back-loaded.** September to November brought {pct(m['sep_nov_share_fy2011'])} of FY2011 revenue; "
    f"the peak month was {m['peak_month']['month']} at {gbp(m['peak_month']['revenue'])}. The UK is "
    f"{pct(m['countries']['uk_share'])} of known-customer revenue across {m['countries']['count']} countries, and "
    f"returns cost {pct(m['return_rate_fy2011'])} of gross sales.",
])

e = m["etl"]
fill = {
    "FINDINGS": findings, "KPI_TABLE": kpi_rows, "RFM_TABLE": rfm_rows, "PRODUCT_TABLE": prod_rows,
    "RAW": f"{e['raw_lines']:,}", "DUPES": f"{e['duplicates_dropped']:,}", "NONPROD": f"{e['non_product_lines_dropped']:,}",
    "OTHER": f"{e['other_lines_dropped']:,}", "ORDERS": f"{e['rows_fact_orders']:,}", "LINES": f"{e['rows_fact_order_lines']:,}", "RETURNS": f"{e['rows_fact_returns']:,}",
    "CUSTOMERS": f"{e['rows_dim_customer']:,}", "PRODUCTS": f"{e['rows_dim_product']:,}",
    "DEC_SIZE": f"{ret['dec2009_cohort_size']:,}", "DEC_12": pct(ret["dec2009_month_12"]),
    "TOP15": pct(m["top_product"]["top15_share"]),
}
text = open(os.path.join(ROOT, "README.template.md")).read()
for k, v in fill.items():
    text = text.replace("{{" + k + "}}", v)
assert "{{" not in text, "unfilled placeholder in README.template.md"
open(os.path.join(ROOT, "README.md"), "w").write(text)
print("README.md rendered")
