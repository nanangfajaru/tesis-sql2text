-- Skema database PostgreSQL. Tulis nama tabel tanpa prefiks skema.

-- Peran: tabel referensi
CREATE TABLE product_category_name_translation (
  product_category_name text,
  product_category_name_english text,
  PRIMARY KEY (product_category_name)
);

-- Peran: tabel master
CREATE TABLE products (
  product_id text,
  product_category_name text REFERENCES product_category_name_translation(product_category_name),
  product_name_lenght integer,
  product_description_lenght integer,
  product_photos_qty integer,
  product_weight_g integer,
  product_length_cm integer,
  product_height_cm integer,
  product_width_cm integer,
  PRIMARY KEY (product_id)
);

-- Peran: tabel master
CREATE TABLE sellers (
  seller_id text,
  seller_zip_code_prefix text,
  seller_city text,
  seller_state char(2),
  PRIMARY KEY (seller_id)
);

-- Peran: tabel master
CREATE TABLE customers (
  customer_id text,
  customer_unique_id text,
  customer_zip_code_prefix text,
  customer_city text,
  customer_state char(2),
  PRIMARY KEY (customer_id)
);

-- Peran: tabel transaksi
CREATE TABLE orders (
  order_id text,
  customer_id text REFERENCES customers(customer_id),
  order_status text,
  order_purchase_timestamp timestamp,
  order_approved_at timestamp,
  order_delivered_carrier_date timestamp,
  order_delivered_customer_date timestamp,
  order_estimated_delivery_date timestamp,
  PRIMARY KEY (order_id)
);

-- Peran: tabel transaksi
CREATE TABLE order_items (
  order_id text REFERENCES orders(order_id),
  order_item_id integer,
  product_id text REFERENCES products(product_id),
  seller_id text REFERENCES sellers(seller_id),
  shipping_limit_date timestamp,
  price numeric(10,2),
  freight_value numeric(10,2),
  PRIMARY KEY (order_id, order_item_id)
);
