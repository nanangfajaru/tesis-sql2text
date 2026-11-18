-- =====================================================================
-- 04_snowflake.sql
-- Varian 3: SNOWFLAKE SCHEMA, schema "snowflake". Dibangun dari schema
-- "oltp" sehingga isi datanya identik dengan varian lain.
-- fact_sales sama dengan star; dimensi dinormalisasi bertingkat:
--   dim_product  -> dim_category
--   dim_customer -> dim_city -> dim_state
--   dim_seller   -> dim_city -> dim_state
--   dim_date     -> dim_month -> dim_year
-- =====================================================================
\set ON_ERROR_STOP on

DROP SCHEMA IF EXISTS snowflake CASCADE;
CREATE SCHEMA snowflake;

-- ---------- hierarki waktu ----------
CREATE TABLE snowflake.dim_year (
    year_key  SMALLINT PRIMARY KEY            -- contoh 2017
);
CREATE TABLE snowflake.dim_month (
    month_key   INTEGER PRIMARY KEY,           -- format YYYYMM
    year_key    SMALLINT NOT NULL REFERENCES snowflake.dim_year(year_key),
    month       SMALLINT NOT NULL,
    month_name  TEXT NOT NULL,
    quarter     SMALLINT NOT NULL
);
CREATE TABLE snowflake.dim_date (
    date_key      INTEGER PRIMARY KEY,         -- format YYYYMMDD
    full_date     DATE NOT NULL UNIQUE,
    month_key     INTEGER NOT NULL REFERENCES snowflake.dim_month(month_key),
    day_of_month  SMALLINT NOT NULL,
    day_of_week   SMALLINT NOT NULL,           -- 1 = Senin ... 7 = Minggu (ISO)
    day_name      TEXT NOT NULL,
    is_weekend    BOOLEAN NOT NULL,
    week_of_year  SMALLINT NOT NULL
);
INSERT INTO snowflake.dim_year SELECT DISTINCT year FROM star.dim_date ORDER BY 1;
INSERT INTO snowflake.dim_month
SELECT DISTINCT year * 100 + month, year, month, month_name, quarter FROM star.dim_date;
INSERT INTO snowflake.dim_date
SELECT date_key, full_date, year * 100 + month, day_of_month, day_of_week, day_name, is_weekend, week_of_year
FROM star.dim_date;

-- ---------- hierarki lokasi ----------
CREATE TABLE snowflake.dim_state (
    state_key   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    state_code  CHAR(2) NOT NULL UNIQUE
);
INSERT INTO snowflake.dim_state (state_code)
SELECT customer_state FROM oltp.customers UNION SELECT seller_state FROM oltp.sellers ORDER BY 1;

CREATE TABLE snowflake.dim_city (
    city_key   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    city_name  TEXT NOT NULL,
    state_key  INTEGER NOT NULL REFERENCES snowflake.dim_state(state_key),
    UNIQUE (city_name, state_key)
);
INSERT INTO snowflake.dim_city (city_name, state_key)
SELECT x.city, s.state_key
FROM (SELECT customer_city AS city, customer_state AS state FROM oltp.customers
      UNION
      SELECT seller_city, seller_state FROM oltp.sellers) x
JOIN snowflake.dim_state s ON s.state_code = x.state
ORDER BY 2, 1;

CREATE TABLE snowflake.dim_customer (
    customer_key        INTEGER PRIMARY KEY,
    customer_id         TEXT NOT NULL UNIQUE,
    customer_unique_id  TEXT NOT NULL,
    zip_code_prefix     TEXT,
    city_key            INTEGER NOT NULL REFERENCES snowflake.dim_city(city_key)
);
INSERT INTO snowflake.dim_customer
SELECT dc.customer_key, dc.customer_id, dc.customer_unique_id, dc.zip_code_prefix, ci.city_key
FROM star.dim_customer dc
JOIN snowflake.dim_state st ON st.state_code = dc.state
JOIN snowflake.dim_city ci  ON ci.city_name = dc.city AND ci.state_key = st.state_key;

CREATE TABLE snowflake.dim_seller (
    seller_key       INTEGER PRIMARY KEY,
    seller_id        TEXT NOT NULL UNIQUE,
    zip_code_prefix  TEXT,
    city_key         INTEGER NOT NULL REFERENCES snowflake.dim_city(city_key)
);
INSERT INTO snowflake.dim_seller
SELECT ds.seller_key, ds.seller_id, ds.zip_code_prefix, ci.city_key
FROM star.dim_seller ds
JOIN snowflake.dim_state st ON st.state_code = ds.state
JOIN snowflake.dim_city ci  ON ci.city_name = ds.city AND ci.state_key = st.state_key;

-- ---------- hierarki produk ----------
CREATE TABLE snowflake.dim_category (
    category_key              INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_name             TEXT NOT NULL UNIQUE,   -- nama kategori (Inggris)
    category_name_portuguese  TEXT NOT NULL UNIQUE
);
INSERT INTO snowflake.dim_category (category_name, category_name_portuguese)
SELECT DISTINCT category_name, category_name_portuguese FROM star.dim_product ORDER BY 1;

CREATE TABLE snowflake.dim_product (
    product_key         INTEGER PRIMARY KEY,
    product_id          TEXT NOT NULL UNIQUE,
    category_key        INTEGER NOT NULL REFERENCES snowflake.dim_category(category_key),
    name_length         INTEGER,
    description_length  INTEGER,
    photos_qty          INTEGER,
    weight_g            INTEGER,
    length_cm           INTEGER,
    height_cm           INTEGER,
    width_cm            INTEGER
);
INSERT INTO snowflake.dim_product
SELECT dp.product_key, dp.product_id, c.category_key, dp.name_length, dp.description_length,
       dp.photos_qty, dp.weight_g, dp.length_cm, dp.height_cm, dp.width_cm
FROM star.dim_product dp
JOIN snowflake.dim_category c ON c.category_name = dp.category_name;

-- ---------- status ----------
CREATE TABLE snowflake.dim_order_status (
    order_status_key  INTEGER PRIMARY KEY,
    order_status      TEXT NOT NULL UNIQUE
);
INSERT INTO snowflake.dim_order_status SELECT * FROM star.dim_order_status;

-- ---------- fact_sales ----------
CREATE TABLE snowflake.fact_sales (
    order_id                     TEXT NOT NULL,
    order_item_id                INTEGER NOT NULL,
    purchase_date_key            INTEGER NOT NULL REFERENCES snowflake.dim_date(date_key),
    approved_date_key            INTEGER REFERENCES snowflake.dim_date(date_key),
    delivered_carrier_date_key   INTEGER REFERENCES snowflake.dim_date(date_key),
    delivered_customer_date_key  INTEGER REFERENCES snowflake.dim_date(date_key),
    estimated_delivery_date_key  INTEGER REFERENCES snowflake.dim_date(date_key),
    shipping_limit_date_key      INTEGER REFERENCES snowflake.dim_date(date_key),
    customer_key                 INTEGER NOT NULL REFERENCES snowflake.dim_customer(customer_key),
    product_key                  INTEGER NOT NULL REFERENCES snowflake.dim_product(product_key),
    seller_key                   INTEGER NOT NULL REFERENCES snowflake.dim_seller(seller_key),
    order_status_key             INTEGER NOT NULL REFERENCES snowflake.dim_order_status(order_status_key),
    price                        NUMERIC(10,2) NOT NULL,
    freight_value                NUMERIC(10,2) NOT NULL,
    total_value                  NUMERIC(10,2) NOT NULL,
    PRIMARY KEY (order_id, order_item_id)
);
INSERT INTO snowflake.fact_sales SELECT * FROM star.fact_sales;

CREATE INDEX ON snowflake.fact_sales (purchase_date_key);
CREATE INDEX ON snowflake.fact_sales (customer_key);
CREATE INDEX ON snowflake.fact_sales (product_key);
CREATE INDEX ON snowflake.fact_sales (seller_key);
ANALYZE;
