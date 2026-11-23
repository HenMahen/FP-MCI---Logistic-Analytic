{{ config(
    materialized='table',
    engine='MergeTree()',
    order_by='order_id',
    partition_by='toYYYYMM(order_purchase_timestamp)'
) }}

/*
    Gold fact table: one row per delivered order, ready for BI and the public
    Streamlit dashboard. Monthly partitions keep time-series scans cheap.
*/

with sla as (

    select *
    from {{ ref('int_order_sla_calculated') }}

)

select
    order_id,
    customer_id,
    order_status,

    order_purchase_timestamp,
    order_approved_at,
    order_delivered_carrier_date,
    order_delivered_customer_date,
    order_estimated_delivery_date,
    toStartOfMonth(order_purchase_timestamp)     as order_month,
    toDayOfWeek(order_purchase_timestamp)       as order_day_of_week,

    approval_time_days,
    seller_processing_days,
    carrier_transit_days,
    actual_delivery_days,
    delay_days,
    is_delayed,

    price,
    freight_value,
    price + freight_value                       as total_order_value,

    product_id,
    product_category_name,
    product_weight_g,

    seller_id,
    seller_city,
    seller_state,
    seller_zip_code_prefix,

    customer_city,
    customer_state,
    customer_zip_code_prefix,
    customer_lat,
    customer_lng,

    review_score
from sla
