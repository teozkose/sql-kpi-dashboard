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

-- Order header: one row per invoice, with its totals stored at load time.
CREATE TABLE fact_orders (
    invoice      INTEGER PRIMARY KEY,
    order_date   TEXT NOT NULL,
    order_month  TEXT NOT NULL,
    customer_id  INTEGER REFERENCES dim_customer (customer_id),   -- NULL for guest checkouts
    order_value  REAL NOT NULL,
    units        INTEGER NOT NULL
);

-- Order lines: one row per product on an invoice. Line revenue = quantity * unit_price.
CREATE TABLE fact_order_lines (
    invoice     INTEGER NOT NULL REFERENCES fact_orders (invoice),
    stock_code  TEXT NOT NULL REFERENCES dim_product (stock_code),
    quantity    INTEGER NOT NULL CHECK (quantity > 0),
    unit_price  REAL NOT NULL CHECK (unit_price > 0)
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

CREATE INDEX ix_orders_month    ON fact_orders (order_month);
CREATE INDEX ix_orders_customer ON fact_orders (customer_id);

-- Order lines with their order month and revenue, used by product-level queries.
CREATE VIEW v_sales_lines AS
SELECT l.invoice, o.order_month, o.customer_id, l.stock_code, l.quantity, l.unit_price,
       l.quantity * l.unit_price AS revenue
FROM fact_order_lines l
JOIN fact_orders o USING (invoice);
