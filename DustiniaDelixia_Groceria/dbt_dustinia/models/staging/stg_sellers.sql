{{ config(materialized='view') }}

/*
    Silver: one clean row per seller_id with normalised location attributes.
*/

with source as (

    select *
    from {{ source('bronze', 'raw_sellers') }}

),

cleaned as (

    select
        trim(seller_id)                                                     as seller_id,
        trim(toString(seller_zip_code_prefix))                              as seller_zip_code_prefix,
        coalesce(nullIf(lowerUTF8(trim(seller_city)), ''), 'unknown')       as seller_city,
        coalesce(nullIf(upperUTF8(trim(seller_state)), ''), 'unknown')      as seller_state
    from source
    where notEmpty(trim(seller_id))

)

select *
from cleaned
order by seller_id
limit 1 by seller_id
