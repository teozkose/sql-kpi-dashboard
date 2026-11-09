"""Load the raw invoice lines into a small SQLite warehouse (data/retail.db).

Schema (order header and order lines, two dimensions, returns kept apart):
    dim_customer(customer_id, country, first_order_date, cohort_month)
    dim_product(stock_code, description)
    fact_orders(invoice, order_date, order_month, customer_id, order_value, units)
    fact_order_lines(invoice, stock_code, quantity, unit_price)
    fact_returns(invoice, invoice_date, order_month, customer_id, stock_code, quantity, revenue)

Cleaning rules, applied in this order:
    - exact duplicate lines are dropped
    - non-product codes (postage, fees, manual adjustments, bank charges) are dropped: real products have
      a stock code that starts with five digits
    - invoices starting with "C" are cancellations and go to fact_returns
    - sales need quantity > 0 and price > 0
    - lines without a customer id stay in the sales tables (they are real revenue) with customer_id NULL;
      customer-level queries filter them out
"""
import os
import sqlite3

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "transactions.parquet")
DB = os.path.join(ROOT, "data", "retail.db")


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    stats = {"raw_lines": len(raw)}
    df = raw.drop_duplicates().copy()
    stats["duplicates_dropped"] = stats["raw_lines"] - len(df)
    is_product = df["StockCode"].str.match(r"^\d{5}")
    stats["non_product_lines_dropped"] = int((~is_product).sum())
    df = df[is_product]
    df = df.rename(columns={"Invoice": "invoice", "StockCode": "stock_code", "Description": "description",
                            "Quantity": "quantity", "InvoiceDate": "invoice_date", "Price": "unit_price",
                            "Customer ID": "customer_id", "Country": "country"})
    df["customer_id"] = df["customer_id"].astype("Int64")
    df["order_month"] = df["invoice_date"].dt.strftime("%Y-%m")
    df["revenue"] = (df["quantity"] * df["unit_price"]).round(2)

    cancelled = df["invoice"].str.startswith("C")
    returns = df[cancelled & (df["quantity"] < 0)].copy()
    sales = df[~cancelled & (df["quantity"] > 0) & (df["unit_price"] > 0)].copy()
    stats["other_lines_dropped"] = len(df) - len(returns) - len(sales)
    stats["sales_lines"], stats["return_lines"] = len(sales), len(returns)
    return sales, returns, stats


def build_dimensions(sales: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    known = sales.dropna(subset=["customer_id"]).sort_values("invoice_date")
    first = known.groupby("customer_id").agg(first_order_date=("invoice_date", "min"))
    # A handful of customers order from two countries; keep the country of their first order.
    country = known.groupby("customer_id")["country"].first()
    customers = first.join(country).reset_index()
    customers["cohort_month"] = customers["first_order_date"].dt.strftime("%Y-%m")
    # Descriptions drift slightly over time for the same code; keep the most common one.
    products = (sales.groupby("stock_code")["description"]
                .agg(lambda s: s.value_counts().index[0]).reset_index())
    return customers, products


def main() -> None:
    raw = pd.read_parquet(SRC)
    sales, returns, stats = clean(raw)
    customers, products = build_dimensions(sales)

    for frame in (sales, returns, customers):
        for col in frame.columns:
            if pd.api.types.is_datetime64_any_dtype(frame[col]):
                frame[col] = frame[col].dt.strftime("%Y-%m-%d %H:%M:%S")

    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    con.executescript(open(os.path.join(ROOT, "sql", "schema.sql")).read())
    sales["invoice"] = sales["invoice"].astype(int)
    orders = (sales.groupby("invoice")
              .agg(order_date=("invoice_date", "min"), order_month=("order_month", "min"),
                   customer_id=("customer_id", "first"), order_value=("revenue", "sum"),
                   units=("quantity", "sum"))
              .reset_index())
    orders["order_value"] = orders["order_value"].round(2)
    customers.to_sql("dim_customer", con, if_exists="append", index=False)
    products.to_sql("dim_product", con, if_exists="append", index=False)
    orders.to_sql("fact_orders", con, if_exists="append", index=False, chunksize=50_000)
    sales[["invoice", "stock_code", "quantity", "unit_price"]].to_sql(
        "fact_order_lines", con, if_exists="append", index=False, chunksize=50_000)
    returns[["invoice", "invoice_date", "order_month", "customer_id", "stock_code", "quantity", "revenue"]].to_sql(
        "fact_returns", con, if_exists="append", index=False, chunksize=50_000)
    con.commit()
    con.execute("VACUUM")
    for t in ("dim_customer", "dim_product", "fact_orders", "fact_order_lines", "fact_returns"):
        stats[f"rows_{t}"] = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    con.close()

    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    pd.Series(stats).to_json(os.path.join(ROOT, "results", "etl_stats.json"), indent=1)
    for k, v in stats.items():
        print(f"{k:>28}: {v:,}")


if __name__ == "__main__":
    main()
