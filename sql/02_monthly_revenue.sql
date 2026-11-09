-- Monthly revenue, orders and average order value, with month-over-month and year-over-year growth.
WITH monthly AS (
    SELECT order_month,
           SUM(order_value)            AS revenue,
           COUNT(*)                    AS orders,
           COUNT(DISTINCT customer_id) AS customers
    FROM fact_orders
    WHERE order_month <= '2011-11'
    GROUP BY order_month
)
SELECT order_month,
       ROUND(revenue, 2)                                            AS revenue,
       orders,
       customers,
       ROUND(revenue / orders, 2)                                   AS avg_order_value,
       ROUND(revenue / LAG(revenue, 1)  OVER (ORDER BY order_month) - 1, 4) AS growth_mom,
       ROUND(revenue / LAG(revenue, 12) OVER (ORDER BY order_month) - 1, 4) AS growth_yoy
FROM monthly
ORDER BY order_month;
