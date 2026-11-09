-- RFM segmentation as of 2011-12-01: recency, frequency and monetary quintiles over FY2011 orders,
-- then rule-based segments and what each segment is worth.
WITH base AS (
    SELECT customer_id,
           CAST(JULIANDAY('2011-12-01') - JULIANDAY(MAX(order_date)) AS INTEGER) AS recency_days,
           COUNT(*)                                                           AS frequency,
           SUM(order_value)                                                   AS monetary
    FROM v_orders
    WHERE customer_id IS NOT NULL AND order_month BETWEEN '2010-12' AND '2011-11'
    GROUP BY customer_id
),
scored AS (
    SELECT *,
           NTILE(5) OVER (ORDER BY recency_days DESC) AS r,
           NTILE(5) OVER (ORDER BY frequency)         AS f,
           NTILE(5) OVER (ORDER BY monetary)          AS m
    FROM base
),
segmented AS (
    SELECT *,
           CASE
               WHEN r >= 4 AND f >= 4                 THEN '1 Champions'
               WHEN r >= 3 AND f >= 3                 THEN '2 Loyal'
               WHEN r >= 4 AND f <= 2                 THEN '3 New or promising'
               WHEN r <= 2 AND f >= 3                 THEN '4 At risk'
               WHEN r = 3                             THEN '5 Needs attention'
               ELSE                                        '6 Lapsed'
           END AS segment
    FROM scored
)
SELECT segment,
       COUNT(*)                                             AS customers,
       ROUND(AVG(recency_days), 1)                          AS avg_recency_days,
       ROUND(AVG(frequency), 2)                             AS avg_orders,
       ROUND(AVG(monetary), 2)                              AS avg_revenue,
       ROUND(SUM(monetary), 2)                              AS revenue,
       ROUND(SUM(monetary) / SUM(SUM(monetary)) OVER (), 4) AS revenue_share,
       ROUND(1.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 4)     AS customer_share
FROM segmented
GROUP BY segment
ORDER BY segment;
