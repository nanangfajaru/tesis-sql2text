-- =====================================================================
-- 02_oltp.sql
-- Varian 1: OLTP (bentuk transaksional asli Olist), schema "oltp".
-- Aturan ETL yang diterapkan (sama untuk ketiga varian):
--   E1. Periode: order_purchase_timestamp 2017-01-01 s.d. 2018-08-31.
--   E2. Pesanan wajib punya minimal 1 item (pesanan tanpa item dibuang).
--   E3. Kategori kosong -> 'unknown'; 2 kategori tanpa terjemahan
--       diberi terjemahan manual.
--   E4. Tabel pembayaran, ulasan, dan geolocation tidak dipakai
--       (desain hanya satu tabel fakta: penjualan).
-- Nama tabel dibersihkan dari awalan "olist_" dan akhiran "_dataset";
-- nama kolom tetap asli (termasuk typo "lenght").
-- =====================================================================
\set ON_ERROR_STOP on

DROP SCHEMA IF EXISTS oltp CASCADE;
CREATE SCHEMA oltp;

-- Pesanan dalam lingkup (E1 + E2)
CREATE TEMP TABLE scope_orders AS
SELECT o.order_id
FROM staging.orders o
WHERE o.order_purchase_timestamp >= '2017-01-01'
  AND o.order_purchase_timestamp <  '2018-09-01'
  AND EXISTS (SELECT 1 FROM staging.order_items i WHERE i.order_id = o.order_id);

-- Terjemahan kategori (E3)
CREATE TABLE oltp.product_category_name_translation (
    product_category_name          TEXT PRIMARY KEY,
    product_category_name_english  TEXT NOT NULL
);
INSERT INTO oltp.product_category_name_translation
SELECT product_category_name, product_category_name_english
FROM staging.category_translation;
INSERT INTO oltp.product_category_name_translation VALUES
    ('pc_gamer', 'pc_gamer'),
    ('portateis_cozinha_e_preparadores_de_alimentos', 'portable_kitchen_and_food_preparers'),
    ('unknown', 'unknown')
ON CONFLICT (product_category_name) DO NOTHING;

CREATE TABLE oltp.customers (
    customer_id               TEXT PRIMARY KEY,
    customer_unique_id        TEXT NOT NULL,
    customer_zip_code_prefix  TEXT,
    customer_city             TEXT,
    customer_state            CHAR(2)
);
INSERT INTO oltp.customers
SELECT c.* FROM staging.customers c
WHERE c.customer_id IN (SELECT o.customer_id FROM staging.orders o JOIN scope_orders s USING (order_id));

CREATE TABLE oltp.sellers (
    seller_id               TEXT PRIMARY KEY,
    seller_zip_code_prefix  TEXT,
    seller_city             TEXT,
    seller_state            CHAR(2)
);
INSERT INTO oltp.sellers
SELECT s.* FROM staging.sellers s
WHERE s.seller_id IN (SELECT i.seller_id FROM staging.order_items i JOIN scope_orders USING (order_id));

CREATE TABLE oltp.products (
    product_id                  TEXT PRIMARY KEY,
    product_category_name       TEXT NOT NULL REFERENCES oltp.product_category_name_translation(product_category_name),
    product_name_lenght         INTEGER,
    product_description_lenght  INTEGER,
    product_photos_qty          INTEGER,
    product_weight_g            INTEGER,
    product_length_cm           INTEGER,
    product_height_cm           INTEGER,
    product_width_cm            INTEGER
);
INSERT INTO oltp.products
SELECT p.product_id, COALESCE(p.product_category_name, 'unknown'),
       p.product_name_lenght, p.product_description_lenght, p.product_photos_qty,
       p.product_weight_g, p.product_length_cm, p.product_height_cm, p.product_width_cm
FROM staging.products p
WHERE p.product_id IN (SELECT i.product_id FROM staging.order_items i JOIN scope_orders USING (order_id));

CREATE TABLE oltp.orders (
    order_id                       TEXT PRIMARY KEY,
    customer_id                    TEXT NOT NULL REFERENCES oltp.customers(customer_id),
    order_status                   TEXT NOT NULL,
    order_purchase_timestamp       TIMESTAMP NOT NULL,
    order_approved_at              TIMESTAMP,
    order_delivered_carrier_date   TIMESTAMP,
    order_delivered_customer_date  TIMESTAMP,
    order_estimated_delivery_date  TIMESTAMP
);
INSERT INTO oltp.orders
SELECT o.* FROM staging.orders o JOIN scope_orders USING (order_id);

CREATE TABLE oltp.order_items (
    order_id             TEXT NOT NULL REFERENCES oltp.orders(order_id),
    order_item_id        INTEGER NOT NULL,
    product_id           TEXT NOT NULL REFERENCES oltp.products(product_id),
    seller_id            TEXT NOT NULL REFERENCES oltp.sellers(seller_id),
    shipping_limit_date  TIMESTAMP,
    price                NUMERIC(10,2) NOT NULL,
    freight_value        NUMERIC(10,2) NOT NULL,
    PRIMARY KEY (order_id, order_item_id)
);
INSERT INTO oltp.order_items
SELECT i.* FROM staging.order_items i JOIN scope_orders USING (order_id);

CREATE INDEX ON oltp.orders (customer_id);
CREATE INDEX ON oltp.order_items (product_id);
CREATE INDEX ON oltp.order_items (seller_id);
ANALYZE;
