-- Monthly return rate: value of cancelled lines as a share of gross sales value.
WITH s AS (SELECT order_month, SUM(revenue) AS gross FROM v_sales_lines GROUP BY order_month),
     r AS (SELECT order_month, -SUM(revenue) AS returned FROM fact_returns GROUP BY order_month)
SELECT s.order_month,
       ROUND(s.gross, 2)                              AS gross_sales,
       ROUND(COALESCE(r.returned, 0), 2)              AS returned_value,
       ROUND(COALESCE(r.returned, 0) / s.gross, 4)    AS return_rate
FROM s LEFT JOIN r USING (order_month)
WHERE s.order_month <= '2011-11'
ORDER BY s.order_month;
