{{ config(materialized='view') }}

/*
    Silver: one clean row per customer_id with normalised text and ZIP code.
*/

with source as (

    select *
    from {{ source('bronze', 'raw_customers') }}

),

cleaned as (

    select
        trim(customer_id)                                                   as customer_id,
        trim(customer_unique_id)                                            as customer_unique_id,
        trim(toString(customer_zip_code_prefix))                            as customer_zip_code_prefix,
        coalesce(nullIf(lowerUTF8(trim(customer_city)), ''), 'unknown')     as customer_city,
        coalesce(nullIf(upperUTF8(trim(customer_state)), ''), 'unknown')    as customer_state
    from source
    where notEmpty(trim(customer_id))

)

select *
from cleaned
order by customer_id
limit 1 by customer_id
