-- ============================================================
-- 06_user_readonly.sql
-- Membuat user khusus LLM yang HANYA BOLEH MEMBACA (SELECT).
-- SQL buatan model dijalankan dengan user ini, sehingga tidak
-- mungkin mengubah/menghapus data walaupun model menulis
-- DELETE / DROP / UPDATE.
--
-- Jalankan sebagai postgres (password reader diberikan via -v):
--   psql.exe -U postgres -d tesis_dw -v pw='PASSWORD_READER' -f /c/tesis/sql/06_user_readonly.sql
-- ============================================================
\set ON_ERROR_STOP on

-- Buat role bila belum ada, lalu (selalu) set passwordnya
SELECT 'CREATE ROLE llm_reader LOGIN'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'llm_reader')
\gexec
ALTER ROLE llm_reader WITH LOGIN PASSWORD :'pw';

-- Batasan keamanan & eksperimen
ALTER ROLE llm_reader SET default_transaction_read_only = on;  -- semua transaksi read-only
ALTER ROLE llm_reader SET statement_timeout = '30s';           -- query > 30 dtk dihentikan
ALTER ROLE llm_reader SET search_path = '';                    -- default kosong; diset per kondisi oleh skrip

-- Hak akses: hanya 3 skema eksperimen, staging TIDAK diberikan
REVOKE ALL ON SCHEMA public FROM llm_reader;
GRANT CONNECT ON DATABASE tesis_dw TO llm_reader;
GRANT USAGE  ON SCHEMA oltp, star, snowflake TO llm_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA oltp, star, snowflake TO llm_reader;

-- Catatan search_path:
-- Skrip eksperimen akan men-set search_path per kondisi
-- (mis. SET search_path = star) sebelum menjalankan SQL model,
-- sehingga model cukup menulis nama tabel tanpa prefiks skema
-- dan tidak bisa "mengintip" skema varian lain.

\echo 'User llm_reader siap (read-only, timeout 30 dtk).'