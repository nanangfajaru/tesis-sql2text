-- =====================================================================
-- 05_validasi.sql
-- Memastikan ketiga varian (oltp, star, snowflake) berisi informasi yang
-- identik. Setiap baris harus berstatus 'OK'.
-- =====================================================================
\set ON_ERROR_STOP on
\pset footer off

\echo '== Jumlah baris per tabel =='
SELECT table_schema AS skema, table_name AS tabel,
       (xpath('/row/n/text()', query_to_xml(format('SELECT COUNT(*) AS n FROM %I.%I', table_schema, table_name), false, true, '')))[1]::text::bigint AS jumlah_baris
FROM information_schema.tables
WHERE table_schema IN ('oltp', 'star', 'snowflake') AND table_type = 'BASE TABLE'
ORDER BY 1, 2;

\echo '== Uji kesetaraan antar-varian =='
WITH
o AS (  -- OLTP
  SELECT
    (SELECT COUNT(*) FROM oltp.order_items)                                        AS n_item,
    (SELECT COUNT(*) FROM oltp.orders)                                             AS n_order,
    (SELECT SUM(price + freight_value) FROM oltp.order_items)                      AS total_nilai,
    (SELECT md5(string_agg(k || ':' || v, ',' ORDER BY k)) FROM (
        SELECT t.product_category_name_english k, SUM(i.price)::text v
        FROM oltp.order_items i JOIN oltp.products p USING (product_id)
        JOIN oltp.product_category_name_translation t USING (product_category_name)
        GROUP BY 1) x)                                                             AS sidik_kategori,
    (SELECT md5(string_agg(k || ':' || v, ',' ORDER BY k)) FROM (
        SELECT c.customer_state k, COUNT(DISTINCT o.order_id)::text v
        FROM oltp.orders o JOIN oltp.customers c USING (customer_id) GROUP BY 1) x) AS sidik_negara_bagian,
    (SELECT md5(string_agg(k || ':' || v, ',' ORDER BY k)) FROM (
        SELECT TO_CHAR(o.order_purchase_timestamp, 'YYYY-MM') k, SUM(i.price + i.freight_value)::text v
        FROM oltp.order_items i JOIN oltp.orders o USING (order_id) GROUP BY 1) x)  AS sidik_bulan
),
s AS (  -- STAR
  SELECT
    (SELECT COUNT(*) FROM star.fact_sales),
    (SELECT COUNT(DISTINCT order_id) FROM star.fact_sales),
    (SELECT SUM(total_value) FROM star.fact_sales),
    (SELECT md5(string_agg(k || ':' || v, ',' ORDER BY k)) FROM (
        SELECT p.category_name k, SUM(f.price)::text v
        FROM star.fact_sales f JOIN star.dim_product p USING (product_key) GROUP BY 1) x),
    (SELECT md5(string_agg(k || ':' || v, ',' ORDER BY k)) FROM (
        SELECT c.state k, COUNT(DISTINCT f.order_id)::text v
        FROM star.fact_sales f JOIN star.dim_customer c USING (customer_key) GROUP BY 1) x),
    (SELECT md5(string_agg(k || ':' || v, ',' ORDER BY k)) FROM (
        SELECT d.year || '-' || LPAD(d.month::text, 2, '0') k, SUM(f.total_value)::text v
        FROM star.fact_sales f JOIN star.dim_date d ON d.date_key = f.purchase_date_key GROUP BY 1) x)
),
f AS (  -- SNOWFLAKE
  SELECT
    (SELECT COUNT(*) FROM snowflake.fact_sales),
    (SELECT COUNT(DISTINCT order_id) FROM snowflake.fact_sales),
    (SELECT SUM(total_value) FROM snowflake.fact_sales),
    (SELECT md5(string_agg(k || ':' || v, ',' ORDER BY k)) FROM (
        SELECT c.category_name k, SUM(f.price)::text v
        FROM snowflake.fact_sales f JOIN snowflake.dim_product p USING (product_key)
        JOIN snowflake.dim_category c USING (category_key) GROUP BY 1) x),
    (SELECT md5(string_agg(k || ':' || v, ',' ORDER BY k)) FROM (
        SELECT st.state_code k, COUNT(DISTINCT f.order_id)::text v
        FROM snowflake.fact_sales f JOIN snowflake.dim_customer c USING (customer_key)
        JOIN snowflake.dim_city ci USING (city_key) JOIN snowflake.dim_state st USING (state_key) GROUP BY 1) x),
    (SELECT md5(string_agg(k || ':' || v, ',' ORDER BY k)) FROM (
        SELECT m.year_key || '-' || LPAD(m.month::text, 2, '0') k, SUM(f.total_value)::text v
        FROM snowflake.fact_sales f JOIN snowflake.dim_date d ON d.date_key = f.purchase_date_key
        JOIN snowflake.dim_month m USING (month_key) GROUP BY 1) x)
)
SELECT 'Jumlah item'            AS uji, o.n_item::text AS oltp, s.count::text AS star, f.count::text AS snowflake,
       CASE WHEN o.n_item = s.count AND s.count = f.count THEN 'OK' ELSE 'BEDA' END AS status
FROM o, (SELECT * FROM s) s(count, n_order, total, kat, neg, bln), (SELECT * FROM f) f(count, n_order, total, kat, neg, bln)
UNION ALL
SELECT 'Jumlah pesanan', o.n_order::text, s.n_order::text, f.n_order::text,
       CASE WHEN o.n_order = s.n_order AND s.n_order = f.n_order THEN 'OK' ELSE 'BEDA' END
FROM o, (SELECT * FROM s) s(count, n_order, total, kat, neg, bln), (SELECT * FROM f) f(count, n_order, total, kat, neg, bln)
UNION ALL
SELECT 'Total nilai penjualan', o.total_nilai::text, s.total::text, f.total::text,
       CASE WHEN o.total_nilai = s.total AND s.total = f.total THEN 'OK' ELSE 'BEDA' END
FROM o, (SELECT * FROM s) s(count, n_order, total, kat, neg, bln), (SELECT * FROM f) f(count, n_order, total, kat, neg, bln)
UNION ALL
SELECT 'Penjualan per kategori', LEFT(o.sidik_kategori, 8), LEFT(s.kat, 8), LEFT(f.kat, 8),
       CASE WHEN o.sidik_kategori = s.kat AND s.kat = f.kat THEN 'OK' ELSE 'BEDA' END
FROM o, (SELECT * FROM s) s(count, n_order, total, kat, neg, bln), (SELECT * FROM f) f(count, n_order, total, kat, neg, bln)
UNION ALL
SELECT 'Pesanan per negara bagian', LEFT(o.sidik_negara_bagian, 8), LEFT(s.neg, 8), LEFT(f.neg, 8),
       CASE WHEN o.sidik_negara_bagian = s.neg AND s.neg = f.neg THEN 'OK' ELSE 'BEDA' END
FROM o, (SELECT * FROM s) s(count, n_order, total, kat, neg, bln), (SELECT * FROM f) f(count, n_order, total, kat, neg, bln)
UNION ALL
SELECT 'Penjualan per bulan', LEFT(o.sidik_bulan, 8), LEFT(s.bln, 8), LEFT(f.bln, 8),
       CASE WHEN o.sidik_bulan = s.bln AND s.bln = f.bln THEN 'OK' ELSE 'BEDA' END
FROM o, (SELECT * FROM s) s(count, n_order, total, kat, neg, bln), (SELECT * FROM f) f(count, n_order, total, kat, neg, bln);
