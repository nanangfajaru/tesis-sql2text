-- Skema database PostgreSQL. Tulis nama tabel tanpa prefiks skema.

CREATE TABLE dim_order_status (
  order_status_key integer,
  order_status text
);

CREATE TABLE dim_category (
  category_key integer,
  category_name text,
  category_name_portuguese text
);

CREATE TABLE dim_product (
  product_key integer,
  product_id text,
  category_key integer,
  name_length integer,
  description_length integer,
  photos_qty integer,
  weight_g integer,
  length_cm integer,
  height_cm integer,
  width_cm integer
);

CREATE TABLE dim_state (
  state_key integer,
  state_code char(2)
);

CREATE TABLE dim_city (
  city_key integer,
  city_name text,
  state_key integer
);

CREATE TABLE dim_seller (
  seller_key integer,
  seller_id text,
  zip_code_prefix text,
  city_key integer
);

CREATE TABLE dim_customer (
  customer_key integer,
  customer_id text,
  customer_unique_id text,
  zip_code_prefix text,
  city_key integer
);

CREATE TABLE dim_year (
  year_key smallint
);

CREATE TABLE dim_month (
  month_key integer,
  year_key smallint,
  month smallint,
  month_name text,
  quarter smallint
);

CREATE TABLE dim_date (
  date_key integer,
  full_date date,
  month_key integer,
  day_of_month smallint,
  day_of_week smallint,
  day_name text,
  is_weekend boolean,
  week_of_year smallint
);

CREATE TABLE fact_sales (
  order_id text,
  order_item_id integer,
  purchase_date_key integer,
  approved_date_key integer,
  delivered_carrier_date_key integer,
  delivered_customer_date_key integer,
  estimated_delivery_date_key integer,
  shipping_limit_date_key integer,
  customer_key integer,
  product_key integer,
  seller_key integer,
  order_status_key integer,
  price numeric(10,2),
  freight_value numeric(10,2),
  total_value numeric(10,2)
);
