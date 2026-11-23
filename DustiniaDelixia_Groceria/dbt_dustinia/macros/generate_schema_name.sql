{#
    Keep ClickHouse database names clean.

    dbt's default behaviour concatenates the target schema with a custom schema
    (for example `default_silver`). This project maps the Medallion layers to
    explicit ClickHouse databases instead:

        staging + intermediate -> silver
        marts                  -> gold
        unconfigured models    -> target.schema
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
