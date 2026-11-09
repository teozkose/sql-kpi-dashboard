-- Monthly acquisition cohorts: share of each cohort that orders again N months after its first month.
WITH activity AS (
    SELECT DISTINCT o.customer_id,
           c.cohort_month,
           (CAST(SUBSTR(o.order_month, 1, 4) AS INTEGER) * 12 + CAST(SUBSTR(o.order_month, 6, 2) AS INTEGER))
         - (CAST(SUBSTR(c.cohort_month, 1, 4) AS INTEGER) * 12 + CAST(SUBSTR(c.cohort_month, 6, 2) AS INTEGER))
               AS months_since
    FROM v_orders o
    JOIN dim_customer c ON c.customer_id = o.customer_id
    WHERE o.order_month <= '2011-11'
),
sizes AS (
    SELECT cohort_month, COUNT(*) AS cohort_size
    FROM activity WHERE months_since = 0
    GROUP BY cohort_month
)
SELECT a.cohort_month,
       s.cohort_size,
       a.months_since,
       COUNT(*)                                AS active_customers,
       ROUND(1.0 * COUNT(*) / s.cohort_size, 4) AS retention
FROM activity a
JOIN sizes s USING (cohort_month)
GROUP BY a.cohort_month, a.months_since
ORDER BY a.cohort_month, a.months_since;
