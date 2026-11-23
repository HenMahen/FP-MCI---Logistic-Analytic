/*
    SLA stage durations cannot be negative. The intermediate model clips
    approval, processing, and transit to zero; this test protects the fact
    table from regressions.
*/

select
    order_id,
    approval_time_days,
    seller_processing_days,
    carrier_transit_days,
    actual_delivery_days
from {{ ref('fct_operational_delivery') }}
where
    approval_time_days < 0
    or seller_processing_days < 0
    or carrier_transit_days < 0
    or actual_delivery_days < 0
