/*
    is_delayed must be the exact binary projection of delay_days.
*/

select
    order_id,
    delay_days,
    is_delayed
from {{ ref('fct_operational_delivery') }}
where
    (delay_days > 0 and is_delayed != 1)
    or (delay_days <= 0 and is_delayed != 0)
