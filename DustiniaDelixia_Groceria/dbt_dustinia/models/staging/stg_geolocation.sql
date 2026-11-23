{{ config(materialized='view') }}

/*
    Silver: collapse many raw geolocation points to one coordinate per ZIP code
    prefix. Points outside the Brazilian bounding box are discarded to protect
    the regional map from bad GPS data.
*/

with source as (

    select *
    from {{ source('bronze', 'raw_geolocation') }}

),

valid_points as (

    select
        trim(toString(geolocation_zip_code_prefix))                     as geolocation_zip_code_prefix,
        geolocation_lat                                                 as lat,
        geolocation_lng                                                 as lng,
        coalesce(nullIf(lowerUTF8(trim(geolocation_city)), ''), 'unknown')  as city,
        coalesce(nullIf(upperUTF8(trim(geolocation_state)), ''), 'unknown') as state_code
    from source
    where
        notEmpty(trim(toString(geolocation_zip_code_prefix)))
        and geolocation_lat between -33.75 and 5.27
        and geolocation_lng between -73.99 and -34.79

)

select
    geolocation_zip_code_prefix,
    round(avg(lat), 6)          as lat,
    round(avg(lng), 6)          as lng,
    any(city)                   as city,
    any(state_code)             as state_code
from valid_points
group by geolocation_zip_code_prefix
