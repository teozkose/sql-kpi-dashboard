-- Each month's known customers split into first-time buyers and returning buyers, with their revenue.
SELECT o.order_month,
       COUNT(DISTINCT CASE WHEN c.cohort_month =  o.order_month THEN o.customer_id END) AS new_customers,
       COUNT(DISTINCT CASE WHEN c.cohort_month <> o.order_month THEN o.customer_id END) AS returning_customers,
       ROUND(SUM(CASE WHEN c.cohort_month =  o.order_month THEN o.order_value ELSE 0 END), 2) AS new_revenue,
       ROUND(SUM(CASE WHEN c.cohort_month <> o.order_month THEN o.order_value ELSE 0 END), 2) AS returning_revenue,
       ROUND(1.0 * SUM(CASE WHEN c.cohort_month <> o.order_month THEN o.order_value ELSE 0 END)
             / SUM(o.order_value), 4)                                                    AS returning_revenue_share
FROM fact_orders o
JOIN dim_customer c ON c.customer_id = o.customer_id
WHERE o.order_month <= '2011-11'
GROUP BY o.order_month
ORDER BY o.order_month;
