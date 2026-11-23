{{ config(materialized='view') }}

/*
    Silver: delivered orders only, with every SLA timestamp guaranteed non-null.
    Feature engineering is deliberately kept out of this model; it belongs to
    int_order_sla_calculated.
*/

with source as (

    select *
    from {{ source('bronze', 'raw_orders') }}

),

cleaned as (

    select
        trim(order_id)                                              as order_id,
        trim(customer_id)                                           as customer_id,
        lowerUTF8(trim(order_status))                               as order_status,
        toDateTime(assumeNotNull(order_purchase_timestamp))         as order_purchase_timestamp,
        toDateTime(assumeNotNull(order_approved_at))                as order_approved_at,
        toDateTime(assumeNotNull(order_delivered_carrier_date))     as order_delivered_carrier_date,
        toDateTime(assumeNotNull(order_delivered_customer_date))    as order_delivered_customer_date,
        toDateTime(assumeNotNull(order_estimated_delivery_date))    as order_estimated_delivery_date
    from source
    where
        lowerUTF8(trim(order_status)) = '{{ var("delivered_status", "delivered") }}'
        and notEmpty(trim(order_id))
        and notEmpty(trim(customer_id))
        and order_purchase_timestamp is not null
        and order_approved_at is not null
        and order_delivered_carrier_date is not null
        and order_delivered_customer_date is not null
        and order_estimated_delivery_date is not null

)

select *
from cleaned
order by order_purchase_timestamp desc
limit 1 by order_id
