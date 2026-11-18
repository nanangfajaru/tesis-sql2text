-- =====================================================================
-- 00_jalankan_semua.sql
-- Menjalankan seluruh tahap secara berurutan.
-- Jalankan dari DALAM folder CSV Olist. Contoh (Windows):
--   cd C:\tesis\olist
--   psql -U postgres -d tesis_dw -f C:/tesis/sql/00_jalankan_semua.sql
-- =====================================================================
\set ON_ERROR_STOP on
\timing on
\echo '[1/5] Memuat CSV ke staging ...'
\ir 01_staging.sql
\echo '[2/5] Membangun varian OLTP ...'
\ir 02_oltp.sql
\echo '[3/5] Membangun varian STAR ...'
\ir 03_star.sql
\echo '[4/5] Membangun varian SNOWFLAKE ...'
\ir 04_snowflake.sql
\echo '[5/5] Validasi kesetaraan ketiga varian ...'
\ir 05_validasi.sql
\echo 'SELESAI.'
