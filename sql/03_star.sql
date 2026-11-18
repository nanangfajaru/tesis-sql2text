-- =====================================================================
-- 03_star.sql
-- Varian 2: STAR SCHEMA, schema "star". Dibangun dari schema "oltp"
-- sehingga isi datanya identik.
-- Grain fact_sales: satu baris = satu item dalam satu pesanan.
-- Dimensi didenormalisasi (kategori masuk dim_product, lokasi masuk
-- dim_customer / dim_seller). Surrogate key integer.
-- Catatan: waktu (jam) tidak disimpan; granularitas waktu terkecil = tanggal.
-- =====================================================================
\set ON_ERROR_STOP on

DROP SCHEMA IF EXISTS star CASCADE;
CREATE SCHEMA star;

-- ---------- dim_date ----------
CREATE TABLE star.dim_date (
    date_key      INTEGER PRIMARY KEY,      -- format YYYYMMDD
    full_date     DATE NOT NULL UNIQUE,
    day_of_month  SMALLINT NOT NULL,
    day_of_week   SMALLINT NOT NULL,        -- 1 = Senin ... 7 = Minggu (ISO)
    day_name      TEXT NOT NULL,
    is_weekend    BOOLEAN NOT NULL,
    week_of_year  SMALLINT NOT NULL,
    month         SMALLINT NOT NULL,
    month_name    TEXT NOT NULL,
    quarter       SMALLINT NOT NULL,
    year          SMALLINT NOT NULL
);
INSERT INTO star.dim_date
SELECT TO_CHAR(d, 'YYYYMMDD')::INT, d::DATE,
       EXTRACT(DAY FROM d), EXTRACT(ISODOW FROM d), TRIM(TO_CHAR(d, 'Day')),
       EXTRACT(ISODOW FROM d) IN (6, 7), EXTRACT(WEEK FROM d),
       EXTRACT(MONTH FROM d), TRIM(TO_CHAR(d, 'Month')),
       EXTRACT(QUARTER FROM d), EXTRACT(YEAR FROM d)
FROM GENERATE_SERIES(
        (SELECT LEAST(MIN(order_purchase_timestamp), MIN(order_approved_at),
                      MIN(order_delivered_carrier_date), MIN(order_delivered_customer_date),
                      MIN(order_estimated_delivery_date))::DATE FROM oltp.orders),
        (SELECT GREATEST((SELECT MAX(shipping_limit_date) FROM oltp.order_items),
                         MAX(order_approved_at), MAX(order_delivered_carrier_date),
                         MAX(order_delivered_customer_date), MAX(order_estimated_delivery_date))::DATE
         FROM oltp.orders),
        INTERVAL '1 day') AS g(d);
INSERT INTO star.dim_date
SELECT TO_CHAR(d, 'YYYYMMDD')::INT, d::DATE,
       EXTRACT(DAY FROM d), EXTRACT(ISODOW FROM d), TRIM(TO_CHAR(d, 'Day')),
       EXTRACT(ISODOW FROM d) IN (6, 7), EXTRACT(WEEK FROM d),
       EXTRACT(MONTH FROM d), TRIM(TO_CHAR(d, 'Month')),
       EXTRACT(QUARTER FROM d), EXTRACT(YEAR FROM d)
FROM (SELECT DISTINCT shipping_limit_date::DATE AS d FROM oltp.order_items) x
WHERE NOT EXISTS (SELECT 1 FROM star.dim_date dd WHERE dd.full_date = x.d);

-- ---------- dim_customer ----------
CREATE TABLE star.dim_customer (
    customer_key        INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id         TEXT NOT NULL UNIQUE,
    customer_unique_id  TEXT NOT NULL,
    zip_code_prefix     TEXT,
    city                TEXT,
    state               CHAR(2)
);
INSERT INTO star.dim_customer (customer_id, customer_unique_id, zip_code_prefix, city, state)
SELECT customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state
FROM oltp.customers ORDER BY customer_id;

-- ---------- dim_seller ----------
CREATE TABLE star.dim_seller (
    seller_key       INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    seller_id        TEXT NOT NULL UNIQUE,
    zip_code_prefix  TEXT,
    city             TEXT,
    state            CHAR(2)
);
INSERT INTO star.dim_seller (seller_id, zip_code_prefix, city, state)
SELECT seller_id, seller_zip_code_prefix, seller_city, seller_state
FROM oltp.sellers ORDER BY seller_id;

-- ---------- dim_product (kategori didenormalisasi) ----------
CREATE TABLE star.dim_product (
    product_key                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id                 TEXT NOT NULL UNIQUE,
    category_name              TEXT NOT NULL,   -- nama kategori (Inggris)
    category_name_portuguese   TEXT NOT NULL,
    name_length                INTEGER,
    description_length         INTEGER,
    photos_qty                 INTEGER,
    weight_g                   INTEGER,
    length_cm                  INTEGER,
    height_cm                  INTEGER,
    width_cm                   INTEGER
);
INSERT INTO star.dim_product (product_id, category_name, category_name_portuguese, name_length,
                              description_length, photos_qty, weight_g, length_cm, height_cm, width_cm)
SELECT p.product_id, t.product_category_name_english, p.product_category_name,
       p.product_name_lenght, p.product_description_lenght, p.product_photos_qty,
       p.product_weight_g, p.product_length_cm, p.product_height_cm, p.product_width_cm
FROM oltp.products p
JOIN oltp.product_category_name_translation t USING (product_category_name)
ORDER BY p.product_id;

-- ---------- dim_order_status ----------
CREATE TABLE star.dim_order_status (
    order_status_key  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_status      TEXT NOT NULL UNIQUE
);
INSERT INTO star.dim_order_status (order_status)
SELECT DISTINCT order_status FROM oltp.orders ORDER BY 1;

-- ---------- fact_sales ----------
CREATE TABLE star.fact_sales (
    order_id                     TEXT NOT NULL,      -- degenerate dimension
    order_item_id                INTEGER NOT NULL,
    purchase_date_key            INTEGER NOT NULL REFERENCES star.dim_date(date_key),
    approved_date_key            INTEGER REFERENCES star.dim_date(date_key),
    delivered_carrier_date_key   INTEGER REFERENCES star.dim_date(date_key),
    delivered_customer_date_key  INTEGER REFERENCES star.dim_date(date_key),
    estimated_delivery_date_key  INTEGER REFERENCES star.dim_date(date_key),
    shipping_limit_date_key      INTEGER REFERENCES star.dim_date(date_key),
    customer_key                 INTEGER NOT NULL REFERENCES star.dim_customer(customer_key),
    product_key                  INTEGER NOT NULL REFERENCES star.dim_product(product_key),
    seller_key                   INTEGER NOT NULL REFERENCES star.dim_seller(seller_key),
    order_status_key             INTEGER NOT NULL REFERENCES star.dim_order_status(order_status_key),
    price                        NUMERIC(10,2) NOT NULL,
    freight_value                NUMERIC(10,2) NOT NULL,
    total_value                  NUMERIC(10,2) NOT NULL,   -- price + freight_value
    PRIMARY KEY (order_id, order_item_id)
);
INSERT INTO star.fact_sales
SELECT i.order_id, i.order_item_id,
       TO_CHAR(o.order_purchase_timestamp, 'YYYYMMDD')::INT,
       TO_CHAR(o.order_approved_at, 'YYYYMMDD')::INT,
       TO_CHAR(o.order_delivered_carrier_date, 'YYYYMMDD')::INT,
       TO_CHAR(o.order_delivered_customer_date, 'YYYYMMDD')::INT,
       TO_CHAR(o.order_estimated_delivery_date, 'YYYYMMDD')::INT,
       TO_CHAR(i.shipping_limit_date, 'YYYYMMDD')::INT,
       dc.customer_key, dp.product_key, ds.seller_key, dos.order_status_key,
       i.price, i.freight_value, i.price + i.freight_value
FROM oltp.order_items i
JOIN oltp.orders o              USING (order_id)
JOIN star.dim_customer dc       ON dc.customer_id = o.customer_id
JOIN star.dim_product dp        ON dp.product_id = i.product_id
JOIN star.dim_seller ds         ON ds.seller_id = i.seller_id
JOIN star.dim_order_status dos  ON dos.order_status = o.order_status;

CREATE INDEX ON star.fact_sales (purchase_date_key);
CREATE INDEX ON star.fact_sales (customer_key);
CREATE INDEX ON star.fact_sales (product_key);
CREATE INDEX ON star.fact_sales (seller_key);
ANALYZE;
