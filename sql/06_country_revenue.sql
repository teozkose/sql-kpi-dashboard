-- FY2011 revenue by customer country (known customers only), largest first.
SELECT c.country,
       COUNT(DISTINCT o.customer_id)                           AS customers,
       COUNT(*)                                                AS orders,
       ROUND(SUM(o.order_value), 2)                            AS revenue,
       ROUND(SUM(o.order_value) / COUNT(*), 2)                 AS avg_order_value,
       ROUND(SUM(o.order_value) / SUM(SUM(o.order_value)) OVER (), 4) AS share
FROM v_orders o
JOIN dim_customer c ON c.customer_id = o.customer_id
WHERE o.order_month BETWEEN '2010-12' AND '2011-11'
GROUP BY c.country
ORDER BY revenue DESC;
