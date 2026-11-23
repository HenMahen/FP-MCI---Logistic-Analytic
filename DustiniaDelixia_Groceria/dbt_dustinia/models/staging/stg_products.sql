{{ config(materialized='view') }}

/*
    Silver: product catalogue with corrected legacy typo aliases and a
    non-null category. Physical dimensions of zero mean "not informed".
*/

with source as (

    select *
    from {{ source('bronze', 'raw_products') }}

),

cleaned as (

    select
        trim(product_id)                                                    as product_id,
        coalesce(nullIf(lowerUTF8(trim(product_category_name)), ''), 'unknown') as product_category_name,
        product_name_lenght                                                 as product_name_length,
        product_description_lenght                                          as product_description_length,
        product_photos_qty                                                  as product_photos_qty,
        coalesce(product_weight_g, 0)                                       as product_weight_g,
        coalesce(product_length_cm, 0)                                      as product_length_cm,
        coalesce(product_height_cm, 0)                                      as product_height_cm,
        coalesce(product_width_cm, 0)                                       as product_width_cm
    from source
    where notEmpty(trim(product_id))

)

select *
from cleaned
order by product_id
limit 1 by product_id
