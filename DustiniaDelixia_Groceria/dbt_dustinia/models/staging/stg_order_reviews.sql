{{ config(materialized='view') }}

/*
    Silver: valid reviews only (score 1-5). Duplicate review rows are removed
    per review_id; the intermediate model then selects one review per order.
*/

with source as (

    select *
    from {{ source('bronze', 'raw_order_reviews') }}

),

cleaned as (

    select
        trim(review_id)                     as review_id,
        trim(order_id)                      as order_id,
        review_score                        as review_score,
        toDateTime(review_creation_date)    as review_creation_date,
        toDateTime(review_answer_timestamp) as review_answer_timestamp
    from source
    where
        notEmpty(trim(review_id))
        and notEmpty(trim(order_id))
        and (review_score is null or review_score between 1 and 5)

)

select *
from cleaned
order by review_answer_timestamp desc
limit 1 by review_id
