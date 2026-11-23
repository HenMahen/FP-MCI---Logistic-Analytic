{{ config(materialized='view') }}

/*
    Silver: order line items with a deterministic composite key and
    non-negative financial measures.
*/

with source as (

    select *
    from {{ source('bronze', 'raw_order_items') }}

),

cleaned as (

    select
        trim(order_id)                                  as order_id,
        toUInt16(order_item_id)                         as order_item_id,
        concat(trim(order_id), '-', toString(order_item_id)) as order_item_sk,
        trim(product_id)                                as product_id,
        trim(seller_id)                                 as seller_id,
        toDateTime(shipping_limit_date)                 as shipping_limit_date,
        coalesce(price, 0)                              as price,
        coalesce(freight_value, 0)                      as freight_value
    from source
    where
        notEmpty(trim(order_id))
        and notEmpty(trim(product_id))
        and notEmpty(trim(seller_id))
        and coalesce(price, 0) >= 0
        and coalesce(freight_value, 0) >= 0

)

select *
from cleaned
order by order_item_id
limit 1 by order_item_sk
