-- Top 15 products by revenue in FY2011, with their share and the running share of total revenue.
WITH product_revenue AS (
    SELECT stock_code,
           SUM(revenue)              AS revenue,
           SUM(quantity)             AS units,
           COUNT(DISTINCT invoice)   AS orders
    FROM v_sales_lines
    WHERE order_month BETWEEN '2010-12' AND '2011-11'
    GROUP BY stock_code
),
ranked AS (
    SELECT p.*,
           RANK() OVER (ORDER BY revenue DESC)                          AS revenue_rank,
           revenue / SUM(revenue) OVER ()                               AS share,
           SUM(revenue) OVER (ORDER BY revenue DESC
                              ROWS UNBOUNDED PRECEDING) / SUM(revenue) OVER () AS cumulative_share
    FROM product_revenue p
)
SELECT r.revenue_rank,
       r.stock_code,
       d.description,
       ROUND(r.revenue, 2)           AS revenue,
       r.units,
       r.orders,
       ROUND(r.share, 4)             AS share,
       ROUND(r.cumulative_share, 4)  AS cumulative_share
FROM ranked r
JOIN dim_product d USING (stock_code)
WHERE r.revenue_rank <= 15
ORDER BY r.revenue_rank;
