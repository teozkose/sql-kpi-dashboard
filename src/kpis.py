"""Run every query in sql/ against data/retail.db, save each result as a CSV, collect the headline
numbers in results/metrics.json and draw the figures used in the README."""
import glob
import json
import os
import sqlite3

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "data", "retail.db")
RES = os.path.join(ROOT, "results")
TABLES = os.path.join(RES, "tables")


def run_queries(con) -> dict[str, pd.DataFrame]:
    out = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "sql", "[0-9]*.sql"))):
        name = os.path.basename(path)[3:-4]
        out[name] = pd.read_sql_query(open(path).read(), con)
        out[name].to_csv(os.path.join(TABLES, f"{name}.csv"), index=False)
        print(f"{name:>24}: {len(out[name]):>4} rows")
    return out


def headline(q: dict[str, pd.DataFrame]) -> dict:
    kpi = q["kpi_summary"].set_index("fiscal_year")
    prev, cur = kpi.loc["FY2010"], kpi.loc["FY2011"]
    growth = {c: round(cur[c] / prev[c] - 1, 4) for c in kpi.columns}

    monthly = q["monthly_revenue"]
    peak = monthly.loc[monthly["revenue"].idxmax()]
    nov = monthly.set_index("order_month")
    q4_share = monthly[monthly["order_month"].str[5:].isin(["09", "10", "11"])
                       & (monthly["order_month"] >= "2010-12")]["revenue"].sum() / cur["revenue"]

    ret = q["cohort_retention"]
    first_year = ret[ret["cohort_month"].between("2010-01", "2010-11")]
    sizes = first_year.drop_duplicates("cohort_month").set_index("cohort_month")["cohort_size"]

    def weighted_retention(month: int, cohorts: pd.DataFrame) -> float:
        rows = cohorts[cohorts["months_since"] == month]
        size = cohorts.drop_duplicates("cohort_month").set_index("cohort_month")["cohort_size"]
        eligible = size[size.index.isin(rows["cohort_month"])]
        return round(rows["active_customers"].sum() / eligible.sum(), 4)

    dec = ret[ret["cohort_month"] == "2009-12"].set_index("months_since")["retention"]

    nvr = q["new_vs_returning"]
    nvr_fy = nvr[nvr["order_month"] >= "2010-12"]
    returning_share = (nvr_fy["returning_revenue"].sum()
                       / (nvr_fy["returning_revenue"].sum() + nvr_fy["new_revenue"].sum()))

    rfm = q["rfm_segments"].set_index("segment")
    champs = rfm.loc["1 Champions"]
    at_risk = rfm.loc["4 At risk"]

    conc = q["customer_concentration"].set_index("decile")
    top = q["top_products"]
    countries = q["country_revenue"]
    rr = q["return_rate"]
    rr_fy = rr[rr["order_month"] >= "2010-12"]

    return {
        "period": {"fy2010": "2009-12 to 2010-11", "fy2011": "2010-12 to 2011-11", "data_end": "2011-12-09"},
        "fy2011": {k: (float(v) if isinstance(v, (np.floating, float)) else int(v)) for k, v in cur.items()},
        "fy2010": {k: (float(v) if isinstance(v, (np.floating, float)) else int(v)) for k, v in prev.items()},
        "growth": growth,
        "peak_month": {"month": peak["order_month"], "revenue": float(peak["revenue"])},
        "nov_2011_yoy": float(nov.loc["2011-11", "growth_yoy"]),
        "sep_nov_share_fy2011": round(float(q4_share), 4),
        "retention": {
            "month_1_first_year_cohorts": weighted_retention(1, first_year),
            "month_3_first_year_cohorts": weighted_retention(3, first_year),
            "month_12_first_year_cohorts": weighted_retention(12, first_year),
            "dec2009_cohort_size": int(ret.loc[ret["cohort_month"] == "2009-12", "cohort_size"].iloc[0]),
            "dec2009_month_12": float(dec.loc[12]),
            "dec2009_month_23": float(dec.loc[23]),
        },
        "returning_revenue_share_fy2011": round(float(returning_share), 4),
        "rfm": {
            "champions_customer_share": float(champs["customer_share"]),
            "champions_revenue_share": float(champs["revenue_share"]),
            "champions_avg_orders": float(champs["avg_orders"]),
            "at_risk_customers": int(at_risk["customers"]),
            "at_risk_revenue": float(at_risk["revenue"]),
        },
        "concentration": {"top10pct_share": float(conc.loc[1, "share"]),
                          "top20pct_share": float(conc.loc[2, "cumulative_share"])},
        "top_product": {"description": top.loc[0, "description"], "revenue": float(top.loc[0, "revenue"]),
                        "top15_share": float(top["cumulative_share"].iloc[-1])},
        "countries": {"uk_share": float(countries.loc[countries["country"] == "United Kingdom", "share"].iloc[0]),
                      "count": int(len(countries)),
                      "next": countries.loc[1:3, ["country", "share"]].to_dict("records")},
        "return_rate_fy2011": round(float(rr_fy["returned_value"].sum() / rr_fy["gross_sales"].sum()), 4),
    }


def figures(q: dict[str, pd.DataFrame]) -> None:
    m = q["monthly_revenue"]
    nvr = q["new_vs_returning"]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    x = np.arange(len(m))
    ax.bar(x, nvr["returning_revenue"] / 1e3, color="#3b6ea5", label="Returning customers")
    ax.bar(x, nvr["new_revenue"] / 1e3, bottom=nvr["returning_revenue"] / 1e3, color="#9cc3e6",
           label="First-time customers")
    ax.plot(x, m["revenue"] / 1e3, color="#222", lw=1.5, marker="o", ms=3, label="All revenue (incl. guest checkouts)")
    ax.set_xticks(x[::2], m["order_month"][::2], rotation=45, ha="right")
    ax.set_ylabel("Revenue (GBP thousands)")
    ax.set_title("Monthly revenue, Dec 2009 to Nov 2011")
    ax.legend(frameon=False, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "monthly_revenue.png"), dpi=130)
    plt.close(fig)

    r = q["cohort_retention"]
    grid = r.pivot(index="cohort_month", columns="months_since", values="retention").iloc[:13, :13]
    fig, ax = plt.subplots(figsize=(10, 6))
    shown = grid.copy()
    shown[0] = np.nan  # month 0 is always 100%, which flattens the colour scale
    im = ax.imshow(shown.values, cmap="Blues", vmin=0, vmax=0.5, aspect="auto")
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            v = grid.values[i, j]
            if not np.isnan(v) and j > 0:
                ax.text(j, i, f"{v:.0%}", ha="center", va="center", fontsize=7,
                        color="white" if v > 0.3 else "#222")
    sizes = r.drop_duplicates("cohort_month").set_index("cohort_month")["cohort_size"]
    ax.set_yticks(range(len(grid)), [f"{c}  (n={sizes[c]:,})" for c in grid.index])
    ax.set_xticks(range(grid.shape[1]))
    ax.set_xlabel("Months since first order")
    ax.set_title("Cohort retention: share of each monthly cohort ordering again")
    fig.colorbar(im, ax=ax, fraction=0.03, format=matplotlib.ticker.PercentFormatter(1.0))
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "cohort_retention.png"), dpi=130)
    plt.close(fig)

    s = q["rfm_segments"]
    labels = s["segment"].str[2:]
    fig, ax = plt.subplots(figsize=(8, 4))
    y = np.arange(len(s))
    ax.barh(y - 0.2, s["customer_share"], 0.4, color="#9cc3e6", label="Share of customers")
    ax.barh(y + 0.2, s["revenue_share"], 0.4, color="#3b6ea5", label="Share of revenue")
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.set_title("RFM segments, FY2011")
    ax.legend(frameon=False, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "rfm_segments.png"), dpi=130)
    plt.close(fig)


def main() -> None:
    os.makedirs(TABLES, exist_ok=True)
    con = sqlite3.connect(DB)
    q = run_queries(con)
    con.close()
    metrics = headline(q)
    metrics["etl"] = json.load(open(os.path.join(RES, "etl_stats.json")))
    json.dump(metrics, open(os.path.join(RES, "metrics.json"), "w"), indent=1)
    figures(q)
    print(json.dumps({k: metrics[k] for k in ("growth", "retention", "rfm", "concentration")}, indent=1))


if __name__ == "__main__":
    main()
