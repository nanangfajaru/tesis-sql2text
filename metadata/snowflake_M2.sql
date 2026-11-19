-- Skema database PostgreSQL. Tulis nama tabel tanpa prefiks skema.

-- Peran: tabel dimensi
CREATE TABLE dim_order_status (
  order_status_key integer,
  order_status text,
  PRIMARY KEY (order_status_key)
);

-- Peran: tabel sub-dimensi (normalisasi)
CREATE TABLE dim_category (
  category_key integer,
  category_name text,
  category_name_portuguese text,
  PRIMARY KEY (category_key)
);

-- Peran: tabel dimensi
CREATE TABLE dim_product (
  product_key integer,
  product_id text,
  category_key integer REFERENCES dim_category(category_key),
  name_length integer,
  description_length integer,
  photos_qty integer,
  weight_g integer,
  length_cm integer,
  height_cm integer,
  width_cm integer,
  PRIMARY KEY (product_key)
);

-- Peran: tabel sub-dimensi (normalisasi)
CREATE TABLE dim_state (
  state_key integer,
  state_code char(2),
  PRIMARY KEY (state_key)
);

-- Peran: tabel sub-dimensi (normalisasi)
CREATE TABLE dim_city (
  city_key integer,
  city_name text,
  state_key integer REFERENCES dim_state(state_key),
  PRIMARY KEY (city_key)
);

-- Peran: tabel dimensi
CREATE TABLE dim_seller (
  seller_key integer,
  seller_id text,
  zip_code_prefix text,
  city_key integer REFERENCES dim_city(city_key),
  PRIMARY KEY (seller_key)
);

-- Peran: tabel dimensi
CREATE TABLE dim_customer (
  customer_key integer,
  customer_id text,
  customer_unique_id text,
  zip_code_prefix text,
  city_key integer REFERENCES dim_city(city_key),
  PRIMARY KEY (customer_key)
);

-- Peran: tabel sub-dimensi (normalisasi)
CREATE TABLE dim_year (
  year_key smallint,
  PRIMARY KEY (year_key)
);

-- Peran: tabel sub-dimensi (normalisasi)
CREATE TABLE dim_month (
  month_key integer,
  year_key smallint REFERENCES dim_year(year_key),
  month smallint,
  month_name text,
  quarter smallint,
  PRIMARY KEY (month_key)
);

-- Peran: tabel dimensi
CREATE TABLE dim_date (
  date_key integer,
  full_date date,
  month_key integer REFERENCES dim_month(month_key),
  day_of_month smallint,
  day_of_week smallint,
  day_name text,
  is_weekend boolean,
  week_of_year smallint,
  PRIMARY KEY (date_key)
);

-- Peran: tabel fakta
CREATE TABLE fact_sales (
  order_id text,
  order_item_id integer,
  purchase_date_key integer REFERENCES dim_date(date_key),
  approved_date_key integer REFERENCES dim_date(date_key),
  delivered_carrier_date_key integer REFERENCES dim_date(date_key),
  delivered_customer_date_key integer REFERENCES dim_date(date_key),
  estimated_delivery_date_key integer REFERENCES dim_date(date_key),
  shipping_limit_date_key integer REFERENCES dim_date(date_key),
  customer_key integer REFERENCES dim_customer(customer_key),
  product_key integer REFERENCES dim_product(product_key),
  seller_key integer REFERENCES dim_seller(seller_key),
  order_status_key integer REFERENCES dim_order_status(order_status_key),
  price numeric(10,2),
  freight_value numeric(10,2),
  total_value numeric(10,2),
  PRIMARY KEY (order_id, order_item_id)
);
