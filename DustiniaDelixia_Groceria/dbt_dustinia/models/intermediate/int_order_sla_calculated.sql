{{ config(
    materialized='table',
    engine='MergeTree()',
    order_by='order_id'
) }}

/*
    Silver -> Gold bridge: one row per delivered order.

    Business grain: an order can contain several items and several sellers.
    To keep the fact table at order grain, the first item (lowest order_item_id)
    is used for the product and seller attributes, matching the original
    operational reporting definition.

    All SLA measures are derived here in SQL; no Python feature engineering.
*/

with orders as (

    select *
    from {{ ref('stg_orders') }}

),

first_item as (

    select
        order_id,
        argMin(product_id, order_item_id)   as product_id,
        argMin(seller_id, order_item_id)    as seller_id,
        argMin(price, order_item_id)        as price,
        argMin(freight_value, order_item_id) as freight_value
    from {{ ref('stg_order_items') }}
    group by order_id

),

latest_review as (

    select
        order_id,
        argMax(review_score, review_answer_timestamp) as review_score
    from {{ ref('stg_order_reviews') }}
    group by order_id

),

customers as (

    select *
    from {{ ref('stg_customers') }}

),

sellers as (

    select *
    from {{ ref('stg_sellers') }}

),

products as (

    select *
    from {{ ref('stg_products') }}

),

geolocation as (

    select *
    from {{ ref('stg_geolocation') }}

),

enriched as (

    select
        o.order_id                                              as order_id,
        o.customer_id                                           as customer_id,
        o.order_status                                          as order_status,
        o.order_purchase_timestamp                              as order_purchase_timestamp,
        o.order_approved_at                                     as order_approved_at,
        o.order_delivered_carrier_date                          as order_delivered_carrier_date,
        o.order_delivered_customer_date                         as order_delivered_customer_date,
        o.order_estimated_delivery_date                         as order_estimated_delivery_date,

        coalesce(i.product_id, 'unknown')       as product_id,
        coalesce(p.product_category_name, 'unknown') as product_category_name,
        coalesce(p.product_weight_g, 0)         as product_weight_g,
        coalesce(i.price, 0)                    as price,
        coalesce(i.freight_value, 0)            as freight_value,

        coalesce(i.seller_id, 'unknown')        as seller_id,
        coalesce(s.seller_city, 'unknown')      as seller_city,
        coalesce(s.seller_state, 'unknown')     as seller_state,
        coalesce(s.seller_zip_code_prefix, '')  as seller_zip_code_prefix,

        c.customer_city                         as customer_city,
        c.customer_state                        as customer_state,
        c.customer_zip_code_prefix              as customer_zip_code_prefix,
        g.lat                                   as customer_lat,
        g.lng                                   as customer_lng,

        r.review_score                          as review_score,

        dateDiff(
            'second',
            o.order_purchase_timestamp,
            o.order_approved_at
        ) / 86400.0                             as approval_time_days,
        dateDiff(
            'second',
            o.order_approved_at,
            o.order_delivered_carrier_date
        ) / 86400.0                             as seller_processing_days,
        dateDiff(
            'second',
            o.order_delivered_carrier_date,
            o.order_delivered_customer_date
        ) / 86400.0                             as carrier_transit_days,
        dateDiff(
            'second',
            o.order_purchase_timestamp,
            o.order_delivered_customer_date
        ) / 86400.0                             as actual_delivery_days,
        dateDiff(
            'second',
            o.order_estimated_delivery_date,
            o.order_delivered_customer_date
        ) / 86400.0                             as delay_days
    from orders as o
    left join first_item as i      on o.order_id = i.order_id
    left join latest_review as r   on o.order_id = r.order_id
    left join customers as c       on o.customer_id = c.customer_id
    left join sellers as s         on i.seller_id = s.seller_id
    left join products as p        on i.product_id = p.product_id
    left join geolocation as g     on c.customer_zip_code_prefix = g.geolocation_zip_code_prefix

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

    greatest(approval_time_days, 0)         as approval_time_days,
    greatest(seller_processing_days, 0)     as seller_processing_days,
    greatest(carrier_transit_days, 0)       as carrier_transit_days,
    actual_delivery_days,
    delay_days,
    if(delay_days > 0, 1, 0)                as is_delayed,

    price,
    freight_value,

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
from enriched
