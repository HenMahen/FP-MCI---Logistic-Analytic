-- =============================================================================
-- CI fixture — deterministic two-order dataset.
--
-- Used by GitHub Actions to prove that every dbt model and test runs against
-- a real ClickHouse instance. Not part of the production ingestion path.
-- =============================================================================

TRUNCATE TABLE raw_orders;
TRUNCATE TABLE raw_order_items;
TRUNCATE TABLE raw_customers;
TRUNCATE TABLE raw_sellers;
TRUNCATE TABLE raw_geolocation;
TRUNCATE TABLE raw_products;
TRUNCATE TABLE raw_order_reviews;

INSERT INTO raw_orders
    (order_id, customer_id, order_status, order_purchase_timestamp, order_approved_at,
     order_delivered_carrier_date, order_delivered_customer_date, order_estimated_delivery_date)
VALUES
    ('o1', 'c1', 'delivered', '2018-01-01 10:00:00', '2018-01-01 11:00:00',
     '2018-01-03 10:00:00', '2018-01-06 10:00:00', '2018-01-08 10:00:00'),
    ('o2', 'c2', 'delivered', '2018-02-01 09:00:00', '2018-02-01 11:00:00',
     '2018-02-05 09:00:00', '2018-02-16 09:00:00', '2018-02-11 09:00:00'),
    ('o3', 'c3', 'canceled', '2018-03-01 09:00:00', NULL, NULL, NULL, '2018-03-10 09:00:00');

INSERT INTO raw_order_items
    (order_id, order_item_id, product_id, seller_id, shipping_limit_date, price, freight_value)
VALUES
    ('o1', 1, 'p1', 's1', '2018-01-02 10:00:00', 100.00, 10.00),
    ('o1', 2, 'p2', 's1', '2018-01-02 10:00:00', 50.00, 5.00),
    ('o2', 1, 'p2', 's2', '2018-02-03 09:00:00', 200.00, 20.00),
    ('o3', 1, 'p1', 's3', '2018-03-02 09:00:00', 999.00, 0.00);

INSERT INTO raw_customers
    (customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state)
VALUES
    ('c1', 'u1', '01000', 'sao paulo', 'SP'),
    ('c2', 'u2', '20000', 'rio de janeiro', 'RJ'),
    ('c3', 'u3', '30000', 'belo horizonte', 'MG');

INSERT INTO raw_sellers
    (seller_id, seller_zip_code_prefix, seller_city, seller_state)
VALUES
    ('s1', '01000', 'sao paulo', 'SP'),
    ('s2', '20000', 'rio de janeiro', 'RJ'),
    ('s3', '30000', 'belo horizonte', 'MG');

INSERT INTO raw_geolocation
    (geolocation_zip_code_prefix, geolocation_lat, geolocation_lng, geolocation_city, geolocation_state)
VALUES
    ('01000', -23.550520, -46.633308, 'sao paulo', 'SP'),
    ('20000', -22.906847, -43.172896, 'rio de janeiro', 'RJ'),
    ('30000', -19.916681, -43.934493, 'belo horizonte', 'MG');

INSERT INTO raw_products
    (product_id, product_category_name, product_name_lenght, product_description_lenght,
     product_photos_qty, product_weight_g, product_length_cm, product_height_cm, product_width_cm)
VALUES
    ('p1', 'beleza_saude', 40, 300, 2, 500, 20, 10, 15),
    ('p2', NULL, 30, 200, 1, 1000, 30, 20, 25);

INSERT INTO raw_order_reviews
    (review_id, order_id, review_score, review_creation_date, review_answer_timestamp)
VALUES
    ('r1', 'o1', 5, '2018-01-10 10:00:00', '2018-01-11 10:00:00'),
    ('r2', 'o2', 2, '2018-02-20 10:00:00', '2018-02-21 10:00:00'),
    ('r3', 'o1', 6, '2018-01-12 10:00:00', '2018-01-13 10:00:00'),
    ('r4', 'o2', 1, '2018-02-22 10:00:00', '2018-02-23 10:00:00');
