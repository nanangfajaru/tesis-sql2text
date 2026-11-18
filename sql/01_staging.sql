-- =====================================================================
-- 01_staging.sql
-- Memuat 8 file CSV Olist apa adanya ke schema "staging".
-- PENTING: jalankan psql dari DALAM folder yang berisi file CSV Olist
-- (lihat 00_jalankan_semua.sql), karena \copy membaca file relatif
-- terhadap folder kerja saat ini.
-- Tabel geolocation sengaja TIDAK dimuat (aturan ETL no. 2).
-- =====================================================================
\set ON_ERROR_STOP on

DROP SCHEMA IF EXISTS staging CASCADE;
CREATE SCHEMA staging;

CREATE TABLE staging.customers (
    customer_id               TEXT,
    customer_unique_id        TEXT,
    customer_zip_code_prefix  TEXT,
    customer_city             TEXT,
    customer_state            TEXT
);
CREATE TABLE staging.orders (
    order_id                       TEXT,
    customer_id                    TEXT,
    order_status                   TEXT,
    order_purchase_timestamp       TIMESTAMP,
    order_approved_at              TIMESTAMP,
    order_delivered_carrier_date   TIMESTAMP,
    order_delivered_customer_date  TIMESTAMP,
    order_estimated_delivery_date  TIMESTAMP
);
CREATE TABLE staging.order_items (
    order_id             TEXT,
    order_item_id        INTEGER,
    product_id           TEXT,
    seller_id            TEXT,
    shipping_limit_date  TIMESTAMP,
    price                NUMERIC(10,2),
    freight_value        NUMERIC(10,2)
);
CREATE TABLE staging.order_payments (
    order_id              TEXT,
    payment_sequential    INTEGER,
    payment_type          TEXT,
    payment_installments  INTEGER,
    payment_value         NUMERIC(10,2)
);
CREATE TABLE staging.order_reviews (
    review_id                TEXT,
    order_id                 TEXT,
    review_score             INTEGER,
    review_comment_title     TEXT,
    review_comment_message   TEXT,
    review_creation_date     TIMESTAMP,
    review_answer_timestamp  TIMESTAMP
);
CREATE TABLE staging.products (
    product_id                  TEXT,
    product_category_name       TEXT,
    product_name_lenght         INTEGER,
    product_description_lenght  INTEGER,
    product_photos_qty          INTEGER,
    product_weight_g            INTEGER,
    product_length_cm           INTEGER,
    product_height_cm           INTEGER,
    product_width_cm            INTEGER
);
CREATE TABLE staging.sellers (
    seller_id               TEXT,
    seller_zip_code_prefix  TEXT,
    seller_city             TEXT,
    seller_state            TEXT
);
CREATE TABLE staging.category_translation (
    product_category_name          TEXT,
    product_category_name_english  TEXT
);

\copy staging.customers FROM 'olist_customers_dataset.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy staging.orders FROM 'olist_orders_dataset.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy staging.order_items FROM 'olist_order_items_dataset.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy staging.order_payments FROM 'olist_order_payments_dataset.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy staging.order_reviews FROM 'olist_order_reviews_dataset.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy staging.products FROM 'olist_products_dataset.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy staging.sellers FROM 'olist_sellers_dataset.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
\copy staging.category_translation FROM 'product_category_name_translation.csv' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')
