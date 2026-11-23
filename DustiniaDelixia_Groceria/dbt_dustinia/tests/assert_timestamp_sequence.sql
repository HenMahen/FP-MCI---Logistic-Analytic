{{ config(severity = 'warn') }}

/*
    Timeline integrity:
    purchase <= approved <= carrier hand-over <= customer delivery.

    Note: In real-world Olist data, ~1,350 orders have carrier scan dates slightly
    before payment approval sync. Severity is set to 'warn' to alert on anomalies
    without blocking production pipelines.
*/

select
    order_id,
    order_purchase_timestamp,
    order_approved_at,
    order_delivered_carrier_date,
    order_delivered_customer_date
from {{ ref('fct_operational_delivery') }}
where
    order_approved_at < order_purchase_timestamp
    or order_delivered_carrier_date < order_approved_at
    or order_delivered_customer_date < order_delivered_carrier_date
