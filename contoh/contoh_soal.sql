\pset footer off
\echo '=== L1 star'
SET search_path=star;
SELECT COUNT(DISTINCT f.order_id) AS jumlah_pesanan FROM fact_sales f JOIN dim_order_status s ON s.order_status_key=f.order_status_key WHERE s.order_status='canceled';
\echo '=== L1 snowflake'
SET search_path=snowflake;
SELECT COUNT(DISTINCT f.order_id) FROM fact_sales f JOIN dim_order_status s ON s.order_status_key=f.order_status_key WHERE s.order_status='canceled';
\echo '=== L1 oltp'
SET search_path=oltp;
SELECT COUNT(*) FROM orders WHERE order_status='canceled';

\echo '=== L2 star'
SET search_path=star;
SELECT c.state, ROUND(SUM(f.total_value),2) AS omzet FROM fact_sales f JOIN dim_customer c ON c.customer_key=f.customer_key JOIN dim_date d ON d.date_key=f.purchase_date_key WHERE d.year=2017 GROUP BY c.state ORDER BY omzet DESC LIMIT 5;
\echo '=== L2 snowflake'
SET search_path=snowflake;
SELECT st.state_code, ROUND(SUM(f.total_value),2) AS omzet FROM fact_sales f JOIN dim_customer c ON c.customer_key=f.customer_key JOIN dim_city ci ON ci.city_key=c.city_key JOIN dim_state st ON st.state_key=ci.state_key JOIN dim_date d ON d.date_key=f.purchase_date_key JOIN dim_month m ON m.month_key=d.month_key WHERE m.year_key=2017 GROUP BY st.state_code ORDER BY omzet DESC LIMIT 5;
\echo '=== L2 oltp'
SET search_path=oltp;
SELECT c.customer_state, ROUND(SUM(oi.price+oi.freight_value),2) AS omzet FROM order_items oi JOIN orders o ON o.order_id=oi.order_id JOIN customers c ON c.customer_id=o.customer_id WHERE EXTRACT(YEAR FROM o.order_purchase_timestamp)=2017 GROUP BY c.customer_state ORDER BY omzet DESC LIMIT 5;

\echo '=== L3 star'
SET search_path=star;
SELECT p.category_name, ROUND(SUM(f.total_value),2) AS omzet FROM fact_sales f JOIN dim_product p ON p.product_key=f.product_key JOIN dim_date d ON d.date_key=f.purchase_date_key WHERE d.year=2018 AND d.quarter=1 GROUP BY p.category_name HAVING SUM(f.total_value)>100000 ORDER BY omzet DESC;
\echo '=== L3 snowflake'
SET search_path=snowflake;
SELECT k.category_name, ROUND(SUM(f.total_value),2) AS omzet FROM fact_sales f JOIN dim_product p ON p.product_key=f.product_key JOIN dim_category k ON k.category_key=p.category_key JOIN dim_date d ON d.date_key=f.purchase_date_key JOIN dim_month m ON m.month_key=d.month_key WHERE m.year_key=2018 AND m.quarter=1 GROUP BY k.category_name HAVING SUM(f.total_value)>100000 ORDER BY omzet DESC;
\echo '=== L3 oltp'
SET search_path=oltp;
SELECT t.product_category_name_english, ROUND(SUM(oi.price+oi.freight_value),2) AS omzet FROM order_items oi JOIN orders o ON o.order_id=oi.order_id JOIN products p ON p.product_id=oi.product_id JOIN product_category_name_translation t ON t.product_category_name=p.product_category_name WHERE o.order_purchase_timestamp>='2018-01-01' AND o.order_purchase_timestamp<'2018-04-01' GROUP BY 1 HAVING SUM(oi.price+oi.freight_value)>100000 ORDER BY omzet DESC;

\echo '=== L4 star'
SET search_path=star;
WITH b AS (SELECT d.year, d.month, SUM(f.total_value) omzet FROM fact_sales f JOIN dim_date d ON d.date_key=f.purchase_date_key GROUP BY 1,2)
SELECT b18.month, ROUND(100*(b18.omzet-b17.omzet)/b17.omzet,2) AS pertumbuhan_persen FROM b b18 JOIN b b17 ON b17.month=b18.month AND b17.year=2017 WHERE b18.year=2018 ORDER BY b18.month;
\echo '=== L4 snowflake'
SET search_path=snowflake;
WITH b AS (SELECT m.year_key yr, m.month, SUM(f.total_value) omzet FROM fact_sales f JOIN dim_date d ON d.date_key=f.purchase_date_key JOIN dim_month m ON m.month_key=d.month_key GROUP BY 1,2)
SELECT b18.month, ROUND(100*(b18.omzet-b17.omzet)/b17.omzet,2) FROM b b18 JOIN b b17 ON b17.month=b18.month AND b17.yr=2017 WHERE b18.yr=2018 ORDER BY b18.month;
\echo '=== L4 oltp'
SET search_path=oltp;
WITH b AS (SELECT EXTRACT(YEAR FROM o.order_purchase_timestamp) yr, EXTRACT(MONTH FROM o.order_purchase_timestamp) mo, SUM(oi.price+oi.freight_value) omzet FROM order_items oi JOIN orders o ON o.order_id=oi.order_id GROUP BY 1,2)
SELECT b18.mo, ROUND(100*(b18.omzet-b17.omzet)/b17.omzet,2) FROM b b18 JOIN b b17 ON b17.mo=b18.mo AND b17.yr=2017 WHERE b18.yr=2018 ORDER BY b18.mo;
