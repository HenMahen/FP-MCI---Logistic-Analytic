{{ config(
    materialized='table',
    engine='MergeTree()',
    order_by='customer_id'
) }}

/*
    Gold dimension: one row per customer_id with delivery location, purchase
    history, and a simple frequency segment. One customer_id represents one
    order in the Olist schema; customer_unique_id links repeat buyers.
*/

with customer_metrics as (

    select
        customer_id,
        count()                                             as total_orders,
        countIf(is_delayed = 1)                             as delayed_orders,
        round(countIf(is_delayed = 1) * 100.0 / count(), 2) as delay_rate_pct,
        round(avg(actual_delivery_days), 2)                 as avg_delivery_days,
        round(avg(review_score), 2)                         as avg_review_score,
        round(sum(total_order_value), 2)                    as total_spend,
        min(order_purchase_timestamp)                       as first_order_at,
        max(order_purchase_timestamp)                       as last_order_at
    from {{ ref('fct_operational_delivery') }}
    group by customer_id

),

customer_attributes as (

    select *
    from {{ ref('stg_customers') }}

),

geolocation as (

    select *
    from {{ ref('stg_geolocation') }}

)

select
    m.customer_id                               as customer_id,
    coalesce(c.customer_unique_id, '')          as customer_unique_id,
    coalesce(c.customer_city, 'unknown')        as customer_city,
    coalesce(c.customer_state, 'unknown')       as customer_state,
    coalesce(c.customer_zip_code_prefix, '')    as customer_zip_code_prefix,
    g.lat                                       as customer_lat,
    g.lng                                       as customer_lng,

    m.total_orders                              as total_orders,
    m.delayed_orders                            as delayed_orders,
    m.delay_rate_pct                            as delay_rate_pct,
    m.avg_delivery_days                         as avg_delivery_days,
    m.avg_review_score                          as avg_review_score,
    m.total_spend                               as total_spend,
    m.first_order_at                            as first_order_at,
    m.last_order_at                             as last_order_at,
    dateDiff('day', m.first_order_at, m.last_order_at) as customer_lifetime_days,

    multiIf(
        m.total_orders >= 5, 'high_frequency',
        m.total_orders >= 2, 'repeat',
        'one_time'
    )                                           as customer_segment
from customer_metrics as m
left join customer_attributes as c on m.customer_id = c.customer_id
left join geolocation as g on c.customer_zip_code_prefix = g.geolocation_zip_code_prefix
