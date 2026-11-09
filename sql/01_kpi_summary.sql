-- Headline KPIs for the two full trading years (December to November).
-- December 2011 is cut off on the 9th, so it is left out everywhere a full period is compared.
WITH tagged AS (
    SELECT o.*,
           CASE WHEN order_month BETWEEN '2009-12' AND '2010-11' THEN 'FY2010'
                WHEN order_month BETWEEN '2010-12' AND '2011-11' THEN 'FY2011' END AS fiscal_year
    FROM v_orders o
)
SELECT fiscal_year,
       ROUND(SUM(order_value), 2)                                  AS revenue,
       COUNT(*)                                                    AS orders,
       COUNT(DISTINCT customer_id)                                 AS customers,
       ROUND(SUM(order_value) / COUNT(*), 2)                       AS avg_order_value,
       ROUND(SUM(CASE WHEN customer_id IS NOT NULL THEN order_value END)
             / COUNT(DISTINCT customer_id), 2)                     AS revenue_per_customer,
       ROUND(1.0 * COUNT(customer_id) / COUNT(DISTINCT customer_id), 2) AS orders_per_customer
FROM tagged
WHERE fiscal_year IS NOT NULL
GROUP BY fiscal_year
ORDER BY fiscal_year;
