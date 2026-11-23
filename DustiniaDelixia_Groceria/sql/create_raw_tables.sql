-- =============================================================================
-- BRONZE LAYER DDL — DustiniaDelixia Groceria
-- Engine: ClickHouse
--
-- These tables receive raw CSV extracts from the Airflow ingestion DAG.
-- No business cleaning happens here: timestamps are nullable, duplicate rows are
-- allowed, and status is not filtered. All cleaning and feature engineering is
-- owned by dbt (silver + gold layers).
-- =============================================================================

DROP TABLE IF EXISTS raw_orders;
DROP TABLE IF EXISTS raw_order_items;
DROP TABLE IF EXISTS raw_customers;
DROP TABLE IF EXISTS raw_sellers;
DROP TABLE IF EXISTS raw_geolocation;
DROP TABLE IF EXISTS raw_products;
DROP TABLE IF EXISTS raw_order_reviews;

-- 1. RAW ORDERS ---------------------------------------------------------------
CREATE TABLE raw_orders
(
    order_id                        String,
    customer_id                     String,
    order_status                    String,
    order_purchase_timestamp        Nullable(DateTime),
    order_approved_at               Nullable(DateTime),
    order_delivered_carrier_date    Nullable(DateTime),
    order_delivered_customer_date   Nullable(DateTime),
    order_estimated_delivery_date   Nullable(DateTime)
)
ENGINE = MergeTree()
ORDER BY order_id
COMMENT 'Bronze: raw orders extract, unfiltered and uncleaned';

-- 2. RAW ORDER ITEMS ----------------------------------------------------------
CREATE TABLE raw_order_items
(
    order_id            String,
    order_item_id       UInt16,
    product_id          String,
    seller_id           String,
    shipping_limit_date Nullable(DateTime),
    price               Nullable(Float64),
    freight_value       Nullable(Float64)
)
ENGINE = MergeTree()
ORDER BY (order_id, order_item_id)
COMMENT 'Bronze: raw order line items';

-- 3. RAW CUSTOMERS ------------------------------------------------------------
CREATE TABLE raw_customers
(
    customer_id                 String,
    customer_unique_id          String,
    customer_zip_code_prefix    String,
    customer_city               Nullable(String),
    customer_state              Nullable(String)
)
ENGINE = MergeTree()
ORDER BY customer_id
COMMENT 'Bronze: raw customer master';

-- 4. RAW SELLERS --------------------------------------------------------------
CREATE TABLE raw_sellers
(
    seller_id               String,
    seller_zip_code_prefix  String,
    seller_city             Nullable(String),
    seller_state            Nullable(String)
)
ENGINE = MergeTree()
ORDER BY seller_id
COMMENT 'Bronze: raw seller master';

-- 5. RAW GEOLOCATION ----------------------------------------------------------
CREATE TABLE raw_geolocation
(
    geolocation_zip_code_prefix String,
    geolocation_lat             Nullable(Float64),
    geolocation_lng             Nullable(Float64),
    geolocation_city            Nullable(String),
    geolocation_state           Nullable(String)
)
ENGINE = MergeTree()
ORDER BY geolocation_zip_code_prefix
COMMENT 'Bronze: raw ZIP-code geolocation points (many rows per ZIP)';

-- 6. RAW PRODUCTS -------------------------------------------------------------
CREATE TABLE raw_products
(
    product_id                  String,
    product_category_name       Nullable(String),
    product_name_lenght         Nullable(UInt32),
    product_description_lenght  Nullable(UInt32),
    product_photos_qty          Nullable(UInt8),
    product_weight_g            Nullable(Float32),
    product_length_cm           Nullable(Float32),
    product_height_cm           Nullable(Float32),
    product_width_cm            Nullable(Float32)
)
ENGINE = MergeTree()
ORDER BY product_id
COMMENT 'Bronze: raw product catalogue (legacy typo columns preserved)';

-- 7. RAW ORDER REVIEWS --------------------------------------------------------
CREATE TABLE raw_order_reviews
(
    review_id               String,
    order_id                String,
    review_score            Nullable(UInt8),
    review_creation_date    Nullable(DateTime),
    review_answer_timestamp Nullable(DateTime)
)
ENGINE = MergeTree()
ORDER BY (order_id, review_id)
COMMENT 'Bronze: raw reviews (text comments intentionally excluded)';
