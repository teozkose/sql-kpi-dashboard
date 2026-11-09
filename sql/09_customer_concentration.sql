-- How concentrated is FY2011 revenue? Customers ranked into deciles by spend.
WITH spend AS (
    SELECT customer_id, SUM(order_value) AS revenue
    FROM fact_orders
    WHERE customer_id IS NOT NULL AND order_month BETWEEN '2010-12' AND '2011-11'
    GROUP BY customer_id
),
deciles AS (
    SELECT *, NTILE(10) OVER (ORDER BY revenue DESC) AS decile FROM spend
)
SELECT decile,
       COUNT(*)                                             AS customers,
       ROUND(MIN(revenue), 2)                               AS min_revenue,
       ROUND(SUM(revenue), 2)                               AS revenue,
       ROUND(SUM(revenue) / SUM(SUM(revenue)) OVER (), 4)   AS share,
       ROUND(SUM(SUM(revenue)) OVER (ORDER BY decile) / SUM(SUM(revenue)) OVER (), 4) AS cumulative_share
FROM deciles
GROUP BY decile
ORDER BY decile;
