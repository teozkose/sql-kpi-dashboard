-- Star schema for the retail warehouse. Amounts are in GBP.
CREATE TABLE dim_customer (
    customer_id      INTEGER PRIMARY KEY,
    first_order_date TEXT NOT NULL,
    country          TEXT NOT NULL,
    cohort_month     TEXT NOT NULL          -- YYYY-MM of the first order
);

CREATE TABLE dim_product (
    stock_code  TEXT PRIMARY KEY,
    description TEXT
);

CREATE TABLE fact_sales (
    invoice      TEXT NOT NULL,
    invoice_date TEXT NOT NULL,
    order_month  TEXT NOT NULL,
    customer_id  INTEGER REFERENCES dim_customer (customer_id),   -- NULL for guest checkouts
    stock_code   TEXT NOT NULL REFERENCES dim_product (stock_code),
    quantity     INTEGER NOT NULL CHECK (quantity > 0),
    unit_price   REAL NOT NULL CHECK (unit_price > 0),
    revenue      REAL NOT NULL
);

CREATE TABLE fact_returns (
    invoice      TEXT NOT NULL,
    invoice_date TEXT NOT NULL,
    order_month  TEXT NOT NULL,
    customer_id  INTEGER,
    stock_code   TEXT NOT NULL,
    quantity     INTEGER NOT NULL CHECK (quantity < 0),
    revenue      REAL NOT NULL
);

CREATE INDEX ix_sales_month    ON fact_sales (order_month);
CREATE INDEX ix_sales_customer ON fact_sales (customer_id);
CREATE INDEX ix_sales_invoice  ON fact_sales (invoice);
CREATE INDEX ix_returns_month  ON fact_returns (order_month);

-- One row per order, used by most KPI queries.
CREATE VIEW v_orders AS
SELECT invoice,
       MIN(invoice_date) AS order_date,
       MIN(order_month)  AS order_month,
       MIN(customer_id)  AS customer_id,
       SUM(revenue)      AS order_value,
       SUM(quantity)     AS units
FROM fact_sales
GROUP BY invoice;
