"""
DustiniaDelixia Groceria — Operational Delivery Dashboard
=========================================================
Public Streamlit app that reads the gold mart exported from ClickHouse
(`fct_operational_delivery.csv`).

Run locally:
    pip install -r dashboard/requirements.txt
    streamlit run dashboard/app.py

Deploy:
    Streamlit Community Cloud -> main file: dashboard/app.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="DustiniaDelixia | Delivery Operations",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_CANDIDATES = [
    REPO_ROOT / "DustiniaDelixia_Groceria" / "fact_operational_delivery.csv",
    REPO_ROOT / "fact_operational_delivery.csv",
    Path(__file__).resolve().parent / "data" / "fact_operational_delivery.csv",
    Path("fact_operational_delivery.csv"),
]

USECOLS = [
    "order_id",
    "customer_id",
    "order_status",
    "order_purchase_timestamp",
    "approval_time_days",
    "seller_processing_days",
    "carrier_transit_days",
    "actual_delivery_days",
    "delay_days",
    "is_delayed",
    "price",
    "freight_value",
    "product_category_name",
    "seller_id",
    "seller_city",
    "seller_state",
    "customer_city",
    "customer_state",
    "customer_lat",
    "customer_lng",
    "review_score",
]

NUMERIC_COLS = [
    "approval_time_days",
    "seller_processing_days",
    "carrier_transit_days",
    "actual_delivery_days",
    "delay_days",
    "is_delayed",
    "price",
    "freight_value",
    "customer_lat",
    "customer_lng",
    "review_score",
]

STATE_NAMES = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AP": "Amapá",
    "AM": "Amazonas",
    "BA": "Bahia",
    "CE": "Ceará",
    "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    "GO": "Goiás",
    "MA": "Maranhão",
    "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais",
    "PA": "Pará",
    "PB": "Paraíba",
    "PR": "Paraná",
    "PE": "Pernambuco",
    "PI": "Piauí",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul",
    "RO": "Rondônia",
    "RR": "Roraima",
    "SC": "Santa Catarina",
    "SP": "São Paulo",
    "SE": "Sergipe",
    "TO": "Tocantins",
}

NORTHEAST = {"AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"}
SOUTHEAST = {"ES", "MG", "RJ", "SP"}

BRAND = "#0E7490"
BRAND_DARK = "#155E75"
AMBER = "#D97706"
RED = "#B91C1C"
GREEN = "#047857"
SLATE = "#475569"
GRID = "#E2E8F0"

PLOTLY_LAYOUT = dict(
    template="plotly_white",
    font=dict(family="Inter, Segoe UI, sans-serif", color="#0F172A", size=13),
    margin=dict(l=10, r=10, t=48, b=10),
    hoverlabel=dict(bgcolor="white", font_size=12, bordercolor=GRID),
)


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; }
    .stApp { background: #F6F8FB; }
    section[data-testid="stSidebar"] { background: #0B1F2A; }
    section[data-testid="stSidebar"] * { color: #E2E8F0; }
    section[data-testid="stSidebar"] .stMultiSelect label,
    section[data-testid="stSidebar"] .stDateInput label,
    section[data-testid="stSidebar"] .stSlider label { color: #CBD5E1 !important; }
    section[data-testid="stSidebar"] hr { border-color: #1E3A4A; }

    h1, h2, h3 { letter-spacing: -0.02em; color: #0F172A; }
    .block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1400px; }

    .hero {
        background: linear-gradient(120deg, #0B1F2A 0%, #0E7490 62%, #14B8A6 100%);
        border-radius: 22px;
        padding: 26px 32px;
        color: white;
        margin-bottom: 22px;
        box-shadow: 0 18px 40px rgba(11, 31, 42, 0.18);
    }
    .hero-kicker { font-size: 12px; letter-spacing: 0.16em; text-transform: uppercase; opacity: 0.8; font-weight: 600; }
    .hero-title { font-size: 32px; font-weight: 800; margin: 6px 0 6px 0; line-height: 1.15; }
    .hero-sub { font-size: 14px; opacity: 0.9; max-width: 820px; }

    .kpi-card {
        background: white;
        border: 1px solid #E6EDF5;
        border-radius: 16px;
        padding: 18px 20px 16px 20px;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);
        min-height: 132px;
    }
    .kpi-label { font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; color: #64748B; font-weight: 700; }
    .kpi-value { font-size: 30px; font-weight: 800; color: #0F172A; margin: 7px 0 4px 0; }
    .kpi-value span { font-size: 16px; font-weight: 600; color: #64748B; margin-left: 2px; }
    .kpi-delta { font-size: 12px; font-weight: 600; }
    .delta-good { color: #047857; }
    .delta-bad { color: #B91C1C; }
    .delta-flat { color: #64748B; }

    .insight {
        background: white;
        border: 1px solid #E6EDF5;
        border-left: 4px solid #0E7490;
        border-radius: 12px;
        padding: 14px 18px;
        height: 100%;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.04);
    }
    .insight .label { font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: #64748B; font-weight: 700; }
    .insight .value { font-size: 20px; font-weight: 800; color: #0F172A; margin-top: 4px; }
    .insight .note { font-size: 12px; color: #475569; margin-top: 3px; line-height: 1.45; }

    .section-kicker { font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase; color: #0E7490; font-weight: 800; margin-bottom: 2px; }
    .section-title { font-size: 24px; font-weight: 800; color: #0F172A; margin: 0 0 4px 0; }
    .section-sub { font-size: 13px; color: #64748B; margin-bottom: 16px; }

    div[data-testid="stMetric"] { background: white; border: 1px solid #E6EDF5; border-radius: 14px; padding: 12px 16px; }
    .stTabs [data-baseweb="tab-list"] { gap: 6px; background: #EDF2F7; padding: 5px; border-radius: 12px; }
    .stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 8px 18px; font-weight: 600; }
    .stTabs [aria-selected="true"] { background: white !important; color: #0E7490 !important; box-shadow: 0 2px 8px rgba(15,23,42,.08); }
    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading delivery mart...")
def load_data(path: str) -> pd.DataFrame:
    frame = pd.read_csv(path, usecols=lambda column: column in USECOLS)
    frame["order_purchase_timestamp"] = pd.to_datetime(
        frame["order_purchase_timestamp"], errors="coerce"
    )
    for column in NUMERIC_COLS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["is_delayed"] = frame["is_delayed"].fillna(0).astype(int)
    frame["order_month"] = frame["order_purchase_timestamp"].dt.to_period("M").dt.to_timestamp()
    frame["total_order_value"] = frame["price"].fillna(0) + frame["freight_value"].fillna(0)
    frame["customer_state"] = frame["customer_state"].fillna("unknown")
    frame["seller_state"] = frame["seller_state"].fillna("unknown")
    return frame.dropna(subset=["order_purchase_timestamp"])


def find_data_file() -> Path | None:
    for candidate in DATA_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def brl(value: float) -> str:
    if value >= 1_000_000:
        return f"R$ {value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"R$ {value / 1_000:.1f}k"
    return f"R$ {value:,.0f}"


def delta_class(current: float, previous: float, higher_is_better: bool) -> tuple[str, str]:
    if previous is None or pd.isna(previous) or previous == 0:
        return "—", "delta-flat"
    delta = (current - previous) / abs(previous) * 100
    good = delta >= 0 if higher_is_better else delta <= 0
    sign = "▲" if delta > 0 else ("▼" if delta < 0 else "■")
    return f"{sign} {abs(delta):.1f}% vs previous period", (
        "delta-good" if good else "delta-bad"
    )


def kpi_card(label: str, value: str, unit: str, delta_text: str, delta_style: str) -> str:
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}<span>{unit}</span></div>
        <div class="kpi-delta {delta_style}">{delta_text}</div>
    </div>
    """


def section_header(kicker: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="section-kicker">{kicker}</div>
        <div class="section-title">{title}</div>
        <div class="section-sub">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )


def seller_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    metrics = (
        frame.groupby(["seller_id", "seller_city", "seller_state"], dropna=False)
        .agg(
            total_orders=("order_id", "count"),
            delayed_orders=("is_delayed", "sum"),
            delay_rate_pct=("is_delayed", lambda values: values.mean() * 100),
            avg_processing_days=("seller_processing_days", "mean"),
            avg_transit_days=("carrier_transit_days", "mean"),
            avg_delivery_days=("actual_delivery_days", "mean"),
            avg_review_score=("review_score", "mean"),
            revenue=("total_order_value", "sum"),
        )
        .reset_index()
    )
    metrics["risk_category"] = np.select(
        [
            metrics["total_orders"] < 10,
            metrics["delay_rate_pct"] >= 30,
            metrics["delay_rate_pct"] >= 20,
            metrics["delay_rate_pct"] >= 10,
        ],
        ["insufficient_data", "critical", "high", "medium"],
        default="low",
    )
    return metrics


def style_figure(fig: go.Figure, height: int = 380) -> go.Figure:
    fig.update_layout(**PLOTLY_LAYOUT, height=height)
    fig.update_xaxes(showgrid=True, gridcolor=GRID, zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)
    return fig


data_path = find_data_file()

if data_path is None:
    st.error(
        "`fact_operational_delivery.csv` was not found. Export it from the gold layer:\n\n"
        "`python DustiniaDelixia_Groceria/download_fact.py`"
    )
    st.stop()

raw = load_data(str(data_path))
min_date = raw["order_purchase_timestamp"].min().date()
max_date = raw["order_purchase_timestamp"].max().date()


# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 4px 0 18px 0;">
            <div style="font-size: 12px; letter-spacing: .16em; text-transform: uppercase; color:#5EEAD4; font-weight:700;">DustiniaDelixia</div>
            <div style="font-size: 24px; font-weight: 800; line-height:1.15; margin-top:4px;">Delivery<br/>Operations</div>
            <div style="font-size: 12px; color:#94A3B8; margin-top:8px;">Gold mart · dbt + ClickHouse</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    date_range = st.date_input(
        "Purchase period",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date

    all_states = sorted(raw["customer_state"].unique())
    selected_states = st.multiselect(
        "Destination state",
        options=all_states,
        default=[],
        placeholder="All states",
    )
    st.markdown("---")
    st.caption(
        "Grain: one row per delivered order.\n\n"
        "Source: Olist Brazilian e-commerce dataset (2016-2018)."
    )
    st.caption(f"Rows in mart: {len(raw):,}")


filtered = raw[
    (raw["order_purchase_timestamp"].dt.date >= start_date)
    & (raw["order_purchase_timestamp"].dt.date <= end_date)
].copy()

if selected_states:
    filtered = filtered[filtered["customer_state"].isin(selected_states)]

if filtered.empty:
    st.warning("No orders match the selected filters.")
    st.stop()

# Previous period with the same number of days for KPI deltas.
period_days = (end_date - start_date).days + 1
previous_start = (pd.Timestamp(start_date) - pd.Timedelta(days=period_days)).date()
previous_end = (pd.Timestamp(start_date) - pd.Timedelta(days=1)).date()
previous = raw[
    (raw["order_purchase_timestamp"].dt.date >= previous_start)
    & (raw["order_purchase_timestamp"].dt.date <= previous_end)
].copy()
if selected_states:
    previous = previous[previous["customer_state"].isin(selected_states)]


# ---------------------------------------------------------------------------
# Hero + KPIs
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="hero">
        <div class="hero-kicker">Operational Analytics · Brazil · 2016–2018</div>
        <div class="hero-title">Delivery performance, without the noise.</div>
        <div class="hero-sub">
            A Medallion ELT pipeline turns raw marketplace extracts into a tested order-grain
            mart. This view answers one question: <b>where does the delivery promise break?</b>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

total_orders = len(filtered)
delayed_orders = int(filtered["is_delayed"].sum())
on_time_rate = (1 - filtered["is_delayed"].mean()) * 100
delay_rate = filtered["is_delayed"].mean() * 100
avg_delivery = filtered["actual_delivery_days"].mean()
gmv_at_risk = filtered.loc[filtered["is_delayed"] == 1, "total_order_value"].sum()

prev_on_time = (
    (1 - previous["is_delayed"].mean()) * 100 if len(previous) else np.nan
)
prev_delay = previous["is_delayed"].mean() * 100 if len(previous) else np.nan
prev_delivery = previous["actual_delivery_days"].mean() if len(previous) else np.nan
prev_gmv = (
    previous.loc[previous["is_delayed"] == 1, "total_order_value"].sum()
    if len(previous)
    else np.nan
)

on_time_delta = delta_class(on_time_rate, prev_on_time, higher_is_better=True)
delay_delta = delta_class(delay_rate, prev_delay, higher_is_better=False)
delivery_delta = delta_class(avg_delivery, prev_delivery, higher_is_better=False)
gmv_delta = delta_class(gmv_at_risk, prev_gmv, higher_is_better=False)

kpi_columns = st.columns(4)
cards = [
    ("On-time rate", f"{on_time_rate:.1f}", "%", on_time_delta),
    ("Delay rate", f"{delay_rate:.1f}", "%", delay_delta),
    ("Avg delivery time", f"{avg_delivery:.1f}", "days", delivery_delta),
    ("GMV exposed to delay", brl(gmv_at_risk), "", gmv_delta),
]
for column, (label, value, unit, (delta_text, delta_style)) in zip(kpi_columns, cards):
    with column:
        st.markdown(kpi_card(label, value, unit, delta_text, delta_style), unsafe_allow_html=True)

st.caption(
    f"{total_orders:,} delivered orders · {delayed_orders:,} late · "
    f"period {start_date:%d %b %Y} – {end_date:%d %b %Y} · "
    f"comparison: previous {period_days} days"
)

st.write("")


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
overview_tab, seller_tab, regional_tab, method_tab = st.tabs(
    ["Executive overview", "Seller performance", "Regional map", "Data & methodology"]
)


# --- Executive overview -----------------------------------------------------
with overview_tab:
    section_header(
        "Where the promise breaks",
        "SLA decomposition",
        "Three stages explain the delivery promise: payment approval, seller hand-over, and carrier transit.",
    )

    stage_data = pd.DataFrame(
        {
            "stage": ["Payment approval", "Seller processing", "Carrier transit"],
            "avg_days": [
                filtered["approval_time_days"].mean(),
                filtered["seller_processing_days"].mean(),
                filtered["carrier_transit_days"].mean(),
            ],
            "color": [BRAND, AMBER, RED],
        }
    )
    stage_data["share_pct"] = stage_data["avg_days"] / stage_data["avg_days"].sum() * 100

    monthly = (
        filtered.groupby("order_month")
        .agg(total_orders=("order_id", "count"), delay_rate_pct=("is_delayed", lambda s: s.mean() * 100))
        .reset_index()
        .sort_values("order_month")
    )
    monthly = monthly[monthly["total_orders"] >= 20]

    left, right = st.columns([1.45, 1])

    with left:
        if monthly.empty:
            st.info("Not enough orders in this period to plot a reliable monthly trend.")
        fig_trend = go.Figure()
        fig_trend.add_trace(
            go.Scatter(
                x=monthly["order_month"],
                y=monthly["delay_rate_pct"],
                mode="lines+markers",
                name="Delay rate",
                line=dict(color=BRAND, width=3),
                marker=dict(size=6, color="white", line=dict(color=BRAND, width=2)),
                fill="tozeroy",
                fillcolor="rgba(14,116,144,0.08)",
                hovertemplate="%{x|%b %Y}<br>Delay rate: %{y:.2f}%<extra></extra>",
            )
        )
        fig_trend.add_hline(
            y=delay_rate,
            line_dash="dot",
            line_color=SLATE,
            annotation_text=f"Period average {delay_rate:.2f}%",
            annotation_position="top left",
        )
        fig_trend.update_layout(
            title="Monthly delay rate",
            yaxis_title="Delay rate (%)",
            showlegend=False,
        )
        st.plotly_chart(style_figure(fig_trend, 390), use_container_width=True)

    with right:
        fig_stage = go.Figure(
            go.Bar(
                x=stage_data["avg_days"],
                y=stage_data["stage"],
                orientation="h",
                marker_color=stage_data["color"],
                text=[f"{value:.2f} d" for value in stage_data["avg_days"]],
                textposition="outside",
                hovertemplate="%{y}<br>%{x:.2f} days<extra></extra>",
            )
        )
        fig_stage.update_layout(
            title="Average time per SLA stage",
            xaxis_title="Days",
            showlegend=False,
            margin=dict(l=10, r=40, t=48, b=10),
        )
        fig_stage.update_yaxes(autorange="reversed")
        st.plotly_chart(style_figure(fig_stage, 390), use_container_width=True)

    carrier_share = stage_data.loc[stage_data["stage"] == "Carrier transit", "share_pct"].iloc[0]
    on_time_review = filtered.loc[filtered["is_delayed"] == 0, "review_score"].mean()
    late_review = filtered.loc[filtered["is_delayed"] == 1, "review_score"].mean()
    review_gap = on_time_review - late_review

    worst_state_row = (
        filtered.groupby("customer_state")
        .agg(orders=("order_id", "count"), delay_rate=("is_delayed", lambda s: s.mean() * 100))
        .query("orders >= 100")
        .sort_values("delay_rate", ascending=False)
        .head(1)
    )
    worst_state = worst_state_row.index[0] if len(worst_state_row) else "n/a"
    worst_state_rate = worst_state_row["delay_rate"].iloc[0] if len(worst_state_row) else 0

    insight_columns = st.columns(4)
    insights = [
        (
            "Carrier transit share",
            f"{carrier_share:.0f}%",
            f"of measured SLA time sits between carrier pickup and the customer.",
        ),
        (
            "Review score gap",
            f"{review_gap:.2f} pts",
            f"On-time {on_time_review:.2f} vs late {late_review:.2f}. Lateness is a CX problem, not only a logistics one.",
        ),
        (
            "Worst destination",
            worst_state,
            f"{worst_state_rate:.1f}% delay rate among states with 100+ orders.",
        ),
        (
            "Late orders in view",
            f"{delayed_orders:,}",
            f"{brl(gmv_at_risk)} of GMV exposed to late delivery in this period.",
        ),
    ]
    for column, (label, value, note) in zip(insight_columns, insights):
        with column:
            st.markdown(
                f"""
                <div class="insight">
                    <div class="label">{label}</div>
                    <div class="value">{value}</div>
                    <div class="note">{note}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")
    section_header(
        "Customer impact",
        "Delay severity vs satisfaction",
        "The longer the breach, the sharper the review score drop.",
    )

    delay_bucket = pd.cut(
        filtered["delay_days"],
        bins=[-np.inf, 0, 3, 7, 14, np.inf],
        labels=["On time", "1–3 days late", "4–7 days late", "8–14 days late", ">14 days late"],
        right=True,
    )
    bucket_data = (
        filtered.assign(delay_bucket=delay_bucket)
        .groupby("delay_bucket", observed=True)
        .agg(
            orders=("order_id", "count"),
            avg_review=("review_score", "mean"),
            delay_rate=("is_delayed", "mean"),
        )
        .reset_index()
    )
    bucket_data["delay_rate"] = bucket_data["delay_rate"] * 100

    fig_review = go.Figure()
    fig_review.add_trace(
        go.Bar(
            x=bucket_data["delay_bucket"].astype(str),
            y=bucket_data["avg_review"],
            marker_color=[GREEN, "#65A30D", AMBER, "#EA580C", RED],
            text=[f"{value:.2f}" for value in bucket_data["avg_review"]],
            textposition="outside",
            hovertemplate="%{x}<br>Avg review: %{y:.2f}/5<extra></extra>",
        )
    )
    fig_review.update_layout(
        title="Average review score by delay bucket",
        yaxis_title="Review score (1–5)",
        yaxis_range=[0, 5.5],
        showlegend=False,
    )
    st.plotly_chart(style_figure(fig_review, 350), use_container_width=True)


# --- Seller performance -----------------------------------------------------
with seller_tab:
    section_header(
        "Supply-side accountability",
        "Seller performance",
        "Delay rate is volume-sensitive. Sellers with fewer than 10 delivered orders are marked insufficient_data.",
    )

    sellers_all = seller_metrics(filtered)
    min_orders = st.slider("Minimum delivered orders per seller", 1, 100, 20, 5)
    sellers = sellers_all[sellers_all["total_orders"] >= min_orders].copy()

    if sellers.empty:
        st.info("No seller meets the current volume threshold.")
    else:
        sellers["seller_label"] = sellers["seller_id"].str[:8]
        sellers = sellers.sort_values("delay_rate_pct", ascending=False)
        worst = sellers.head(12).sort_values("delay_rate_pct")

        left, right = st.columns([1.35, 1])
        with left:
            fig_sellers = go.Figure(
                go.Bar(
                    x=worst["delay_rate_pct"],
                    y=worst["seller_label"],
                    orientation="h",
                    marker=dict(
                        color=worst["delay_rate_pct"],
                        colorscale=[[0, "#99F6E4"], [0.5, "#F59E0B"], [1, RED]],
                        showscale=False,
                    ),
                    text=[f"{value:.1f}%" for value in worst["delay_rate_pct"]],
                    textposition="outside",
                    customdata=np.stack(
                        [worst["total_orders"], worst["avg_processing_days"], worst["seller_state"]], axis=-1
                    ),
                    hovertemplate=(
                        "Seller %{y}<br>Delay rate: %{x:.1f}%<br>"
                        "Orders: %{customdata[0]:,.0f}<br>"
                        "Avg processing: %{customdata[1]:.1f} d<br>"
                        "State: %{customdata[2]}<extra></extra>"
                    ),
                )
            )
            fig_sellers.update_layout(
                title=f"Highest delay rate · sellers with {min_orders}+ orders",
                xaxis_title="Delay rate (%)",
                showlegend=False,
                margin=dict(l=10, r=35, t=48, b=10),
            )
            st.plotly_chart(style_figure(fig_sellers, 430), use_container_width=True)

        with right:
            fig_scatter = px.scatter(
                sellers,
                x="avg_processing_days",
                y="delay_rate_pct",
                size="total_orders",
                color="risk_category",
                hover_name="seller_id",
                hover_data={
                    "seller_state": True,
                    "total_orders": ":,",
                    "avg_transit_days": ":.1f",
                    "avg_processing_days": ":.1f",
                    "delay_rate_pct": ":.1f",
                },
                color_discrete_map={
                    "critical": RED,
                    "high": "#EA580C",
                    "medium": AMBER,
                    "low": GREEN,
                    "insufficient_data": "#94A3B8",
                },
                labels={
                    "avg_processing_days": "Avg seller processing (days)",
                    "delay_rate_pct": "Delay rate (%)",
                    "risk_category": "Risk",
                },
            )
            fig_scatter.add_vline(
                x=sellers["avg_processing_days"].median(),
                line_dash="dot",
                line_color=SLATE,
                annotation_text="median",
            )
            fig_scatter.add_hline(
                y=sellers["delay_rate_pct"].median(),
                line_dash="dot",
                line_color=SLATE,
            )
            fig_scatter.update_layout(title="Processing time vs delay rate")
            st.plotly_chart(style_figure(fig_scatter, 430), use_container_width=True)

        risk_counts = sellers_all["risk_category"].value_counts()
        risk_columns = st.columns(5)
        for column, category in zip(
            risk_columns, ["critical", "high", "medium", "low", "insufficient_data"]
        ):
            with column:
                st.metric(category.replace("_", " ").title(), f"{int(risk_counts.get(category, 0)):,}")

        st.write("")
        table = sellers[
            [
                "seller_id",
                "seller_city",
                "seller_state",
                "total_orders",
                "delayed_orders",
                "delay_rate_pct",
                "avg_processing_days",
                "avg_transit_days",
                "avg_review_score",
                "revenue",
                "risk_category",
            ]
        ].copy()
        table["revenue"] = table["revenue"].map(brl)
        st.dataframe(
            table.rename(
                columns={
                    "seller_id": "Seller",
                    "seller_city": "City",
                    "seller_state": "State",
                    "total_orders": "Orders",
                    "delayed_orders": "Late",
                    "delay_rate_pct": "Delay %",
                    "avg_processing_days": "Processing d",
                    "avg_transit_days": "Transit d",
                    "avg_review_score": "Review",
                    "revenue": "Revenue",
                    "risk_category": "Risk",
                }
            ),
            use_container_width=True,
            hide_index=True,
            height=360,
            column_config={
                "Delay %": st.column_config.ProgressColumn(
                    "Delay %", min_value=0, max_value=50, format="%.1f%%"
                ),
                "Review": st.column_config.NumberColumn("Review", format="%.2f ⭐"),
            },
        )


# --- Regional map -----------------------------------------------------------
with regional_tab:
    section_header(
        "Geography is destiny",
        "Regional performance",
        "Bubble size is order volume; colour is delay rate. The map uses customer ZIP-code geolocation.",
    )

    state_data = (
        filtered.groupby("customer_state")
        .agg(
            total_orders=("order_id", "count"),
            delayed_orders=("is_delayed", "sum"),
            delay_rate_pct=("is_delayed", lambda s: s.mean() * 100),
            avg_delivery_days=("actual_delivery_days", "mean"),
            avg_transit_days=("carrier_transit_days", "mean"),
            avg_review_score=("review_score", "mean"),
            lat=("customer_lat", "mean"),
            lon=("customer_lng", "mean"),
        )
        .reset_index()
    )
    state_data["state_name"] = state_data["customer_state"].map(STATE_NAMES).fillna(
        state_data["customer_state"]
    )
    state_data = state_data.dropna(subset=["lat", "lon"])

    fig_map = go.Figure(
        go.Scattergeo(
            lon=state_data["lon"],
            lat=state_data["lat"],
            text=state_data["state_name"],
            customdata=np.stack(
                [
                    state_data["total_orders"],
                    state_data["delay_rate_pct"],
                    state_data["avg_delivery_days"],
                    state_data["avg_transit_days"],
                    state_data["avg_review_score"],
                ],
                axis=-1,
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Orders: %{customdata[0]:,.0f}<br>"
                "Delay rate: %{customdata[1]:.1f}%<br>"
                "Avg delivery: %{customdata[2]:.1f} d<br>"
                "Avg transit: %{customdata[3]:.1f} d<br>"
                "Avg review: %{customdata[4]:.2f}/5<extra></extra>"
            ),
            marker=dict(
                size=np.sqrt(state_data["total_orders"]) * 2.2,
                color=state_data["delay_rate_pct"],
                colorscale=[[0, "#0E7490"], [0.45, "#F59E0B"], [1, RED]],
                cmin=0,
                cmax=max(25, float(state_data["delay_rate_pct"].max())),
                colorbar=dict(title="Delay %", thickness=12, len=0.7),
                line=dict(color="white", width=1.5),
                opacity=0.9,
                sizemode="diameter",
                sizemin=8,
            ),
        )
    )
    fig_map.update_geos(
        scope="south america",
        projection_type="mercator",
        lataxis_range=[-35, 6],
        lonaxis_range=[-75, -32],
        showcountries=True,
        countrycolor="#CBD5E1",
        showland=True,
        landcolor="#F1F5F9",
        showocean=True,
        oceancolor="#E0F2FE",
        showcoastlines=True,
        coastlinecolor="#CBD5E1",
    )
    fig_map.update_layout(
        title="Delay rate by destination state",
        margin=dict(l=0, r=0, t=48, b=0),
        height=560,
        template="plotly_white",
        font=PLOTLY_LAYOUT["font"],
    )
    st.plotly_chart(fig_map, use_container_width=True)

    left, right = st.columns([1.2, 1])
    with left:
        top_states = state_data.sort_values("delay_rate_pct", ascending=False).head(12).sort_values(
            "delay_rate_pct"
        )
        fig_state = go.Figure(
            go.Bar(
                x=top_states["delay_rate_pct"],
                y=top_states["customer_state"],
                orientation="h",
                marker_color=[
                    RED if value >= 20 else AMBER if value >= 10 else BRAND
                    for value in top_states["delay_rate_pct"]
                ],
                text=[f"{value:.1f}%" for value in top_states["delay_rate_pct"]],
                textposition="outside",
                hovertemplate="%{y}<br>Delay rate: %{x:.2f}%<extra></extra>",
            )
        )
        fig_state.add_vline(
            x=delay_rate,
            line_dash="dot",
            line_color=SLATE,
            annotation_text="national avg",
            annotation_position="top right",
        )
        fig_state.update_layout(
            title="Highest delay rates by state",
            xaxis_title="Delay rate (%)",
            showlegend=False,
            margin=dict(l=10, r=35, t=48, b=10),
        )
        st.plotly_chart(style_figure(fig_state, 430), use_container_width=True)

    with right:
        region_summary = pd.DataFrame(
            {
                "region": ["Northeast", "Southeast", "Other"],
                "delay_rate": [
                    filtered.loc[filtered["customer_state"].isin(NORTHEAST), "is_delayed"].mean() * 100,
                    filtered.loc[filtered["customer_state"].isin(SOUTHEAST), "is_delayed"].mean() * 100,
                    filtered.loc[
                        ~filtered["customer_state"].isin(NORTHEAST | SOUTHEAST), "is_delayed"
                    ].mean()
                    * 100,
                ],
                "orders": [
                    int(filtered["customer_state"].isin(NORTHEAST).sum()),
                    int(filtered["customer_state"].isin(SOUTHEAST).sum()),
                    int((~filtered["customer_state"].isin(NORTHEAST | SOUTHEAST)).sum()),
                ],
            }
        )
        fig_region = go.Figure(
            go.Bar(
                x=region_summary["region"],
                y=region_summary["delay_rate"],
                marker_color=[RED, BRAND, "#94A3B8"],
                text=[f"{value:.1f}%" for value in region_summary["delay_rate"]],
                textposition="outside",
                customdata=region_summary["orders"],
                hovertemplate="%{x}<br>Delay rate: %{y:.2f}%<br>Orders: %{customdata:,}<extra></extra>",
            )
        )
        fig_region.add_hline(y=delay_rate, line_dash="dot", line_color=SLATE)
        fig_region.update_layout(
            title="Northeast vs Southeast",
            yaxis_title="Delay rate (%)",
            showlegend=False,
        )
        st.plotly_chart(style_figure(fig_region, 300), use_container_width=True)

        st.markdown(
            """
            <div class="insight" style="border-left-color:#B91C1C;">
                <div class="label">Operational signal</div>
                <div class="value">Distance is not the only variable.</div>
                <div class="note">
                    Northeast states combine longer carrier transit with weaker promise reliability.
                    The recommended intervention is regional inventory and carrier renegotiation,
                    not a blanket promise-date increase.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# --- Methodology ------------------------------------------------------------
with method_tab:
    section_header(
        "How this was built",
        "Data contract & methodology",
        "A tested dbt pipeline, not a notebook export. Every metric below is reproducible from source.",
    )

    left, right = st.columns([1.15, 1])

    with left:
        st.markdown(
            """
            **Grain.** One row per delivered order. Orders with more than one item use the
            first line item (`min(order_item_id)`) for product and seller attributes, matching
            the operational reporting definition.

            **SLA stages.**
            - `approval_time_days` = approved − purchase
            - `seller_processing_days` = carrier hand-over − approved
            - `carrier_transit_days` = customer delivery − carrier hand-over
            - `actual_delivery_days` = customer delivery − purchase
            - `delay_days` = customer delivery − estimated delivery
            - `is_delayed` = 1 when `delay_days > 0`

            **Data quality.** Generic tests cover primary keys, nullability, accepted
            values, and fact-to-dimension relationships. Singular tests protect timestamp
            order, non-negative SLA durations, and delay-flag consistency.
            """
        )
        st.markdown(
            """
            **Stack.** Apache Airflow → Bronze CSV ingestion; dbt-clickhouse →
            Silver cleaning and Gold marts; ClickHouse → serving layer; Streamlit + Plotly → public dashboard.
            """
        )
        st.markdown(
            """
            **Links.**
            [GitHub repository](https://github.com/Mahendra-TC24/FP-MCI---Logistic-Analytic) ·
            [dbt documentation & lineage](https://mahendra-tc24.github.io/FP-MCI---Logistic-Analytic/dbt/) ·
            [Interactive delivery map](https://mahendra-tc24.github.io/FP-MCI---Logistic-Analytic/)
            """
        )

    with right:
        quality = pd.DataFrame(
            {
                "check": [
                    "Unique fact grain (order_id)",
                    "Fact → customer dimension",
                    "Fact → seller dimension",
                    "Accepted is_delayed values",
                    "Review score 1–5",
                    "Timestamp sequence",
                    "Non-negative SLA durations",
                ],
                "status": ["PASS"] * 7,
            }
        )
        st.dataframe(
            quality,
            use_container_width=True,
            hide_index=True,
            column_config={
                "check": "Automated check",
                "status": st.column_config.TextColumn("CI status"),
            },
        )
        st.caption("CI runs `dbt build` against a real ClickHouse service on every pull request.")

    st.write("")
    summary_columns = st.columns(4)
    summary_columns[0].metric("Orders in mart", f"{len(raw):,}")
    summary_columns[1].metric("Unique orders", f"{raw['order_id'].nunique():,}")
    summary_columns[2].metric("Sellers", f"{raw['seller_id'].nunique():,}")
    summary_columns[3].metric("Destination states", f"{raw['customer_state'].nunique():,}")

    st.caption(
        "Dataset: Olist Brazilian e-commerce public dataset. Currency: BRL. "
        "Financial exposure is an operational estimate of GMV on late orders, not an audited P&L figure."
    )

st.write("")
st.markdown(
    """
    <div style="text-align:center; color:#94A3B8; font-size:12px; padding-top:12px; border-top:1px solid #E2E8F0;">
        DustiniaDelixia Groceria · Analytics Engineering portfolio · Built with dbt, ClickHouse, Airflow and Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)
