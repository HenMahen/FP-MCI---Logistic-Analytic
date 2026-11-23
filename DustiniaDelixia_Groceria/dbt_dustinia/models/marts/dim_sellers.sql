{{ config(
    materialized='table',
    engine='MergeTree()',
    order_by='seller_id'
) }}

/*
    Gold dimension: one row per seller that appears in the delivered-order
    fact table. Risk is volume-aware: sellers with fewer than 10 delivered
    orders are flagged as insufficient_data instead of being labelled critical
    from a single late order.
*/

with seller_metrics as (

    select
        seller_id,
        count()                                             as total_orders,
        countIf(is_delayed = 1)                             as delayed_orders,
        round(countIf(is_delayed = 1) * 100.0 / count(), 2) as delay_rate_pct,
        round(avg(seller_processing_days), 2)               as avg_processing_days,
        round(avg(carrier_transit_days), 2)                 as avg_transit_days,
        round(avg(actual_delivery_days), 2)                 as avg_delivery_days,
        round(avg(review_score), 2)                         as avg_review_score,
        round(sum(total_order_value), 2)                    as total_revenue,
        min(order_purchase_timestamp)                       as first_order_at,
        max(order_purchase_timestamp)                       as last_order_at
    from {{ ref('fct_operational_delivery') }}
    group by seller_id

),

seller_attributes as (

    select
        seller_id,
        any(seller_city)            as seller_city,
        any(seller_state)           as seller_state,
        any(seller_zip_code_prefix) as seller_zip_code_prefix
    from {{ ref('stg_sellers') }}
    group by seller_id

)

select
    m.seller_id                                 as seller_id,
    coalesce(a.seller_city, 'unknown')          as seller_city,
    coalesce(a.seller_state, 'unknown')         as seller_state,
    coalesce(a.seller_zip_code_prefix, '')      as seller_zip_code_prefix,

    m.total_orders                              as total_orders,
    m.delayed_orders                            as delayed_orders,
    m.delay_rate_pct                            as delay_rate_pct,
    m.avg_processing_days                       as avg_processing_days,
    m.avg_transit_days                          as avg_transit_days,
    m.avg_delivery_days                         as avg_delivery_days,
    m.avg_review_score                          as avg_review_score,
    m.total_revenue                             as total_revenue,
    m.first_order_at                            as first_order_at,
    m.last_order_at                             as last_order_at,

    multiIf(
        m.total_orders < 10,              'insufficient_data',
        m.delay_rate_pct >= 30,           'critical',
        m.delay_rate_pct >= 20,           'high',
        m.delay_rate_pct >= 10,           'medium',
        'low'
    )                                           as risk_category
from seller_metrics as m
left join seller_attributes as a on m.seller_id = a.seller_id
