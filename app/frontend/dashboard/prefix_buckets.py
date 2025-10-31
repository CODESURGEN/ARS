import streamlit as st
import pandas as pd
import altair as alt


def display_prefix_bucket_dashboard(df: pd.DataFrame) -> None:
    """Prefix chart"""
    st.subheader("Business Units")

    prefixes = ["CEFE", "FEUK", "FE", "HNC", "HNK", "HT", "WTB"]

    work_df = df.copy()
    if "Order Number" not in work_df.columns:
        return

    work_df.loc[:, "Order Number"] = work_df["Order Number"].astype(str).str.upper()

    def map_bucket(s: str) -> str:
        for p in prefixes:
            if s.startswith(p):
                return p
        return "OTHER"

    work_df.loc[:, "bucket"] = work_df["Order Number"].map(map_bucket)

    numeric_cols = {
        "gross_amount": 0.0,
        "psp_fees": 0.0,
        "Vendor Subtotal": 0.0,
        "Vendor Shipping": 0.0,
        "margin_profit": 0.0,
        "settlement_amount": 0.0,
        "Total Purchased": 0.0,
        "currency_code": "",
    }

    for c, fill in numeric_cols.items():
        if c in work_df.columns:
            if c == "currency_code":
                work_df.loc[:, c] = work_df[c].astype(str)
            else:
                work_df.loc[:, c] = pd.to_numeric(work_df[c], errors="coerce").fillna(fill)

    if "margin_profit" not in work_df.columns and {
        "settlement_amount",
        "Vendor Subtotal",
        "Vendor Shipping",
        "psp_fees",
    }.issubset(work_df.columns):
        work_df.loc[:, "margin_profit"] = (
            work_df["settlement_amount"]
            - work_df["Vendor Subtotal"]
            - work_df["Vendor Shipping"]
            - work_df["psp_fees"]
        )

    agg = work_df.groupby("bucket", dropna=False).agg(
        revenue=("gross_amount", "sum"),
        expenses=(
            pd.NamedAgg(
                column="psp_fees",
                aggfunc=lambda s: s.sum(),
            )
        ),
        vendor_subtotal=("Vendor Subtotal", "sum"),
        vendor_shipping=("Vendor Shipping", "sum"),
        margin=("margin_profit", "sum"),
        refunds=(
            pd.NamedAgg(
                column="Total Purchased",
                aggfunc=lambda s: s.where(
                    work_df.loc[s.index, "currency_code"].astype(str).str.lower().eq("refunded")
                ).sum(),
            )
        ),
    ).reset_index()

    agg.loc[:, "expenses"] = (
        agg["expenses"].fillna(0)
        + agg["vendor_subtotal"].fillna(0)
        + agg["vendor_shipping"].fillna(0)
    )

    agg = agg[["bucket", "revenue", "expenses", "margin", "refunds"]]

    agg.loc[:, "refund_rate"] = agg.apply(
        lambda r: (r["refunds"] / r["revenue"] * 100) if r["revenue"] > 0 else 0.0,
        axis=1,
    )
    agg.loc[:, "margin_rate"] = agg.apply(
        lambda r: (r["margin"] / r["revenue"] * 100) if r["revenue"] > 0 else 0.0,
        axis=1,
    )

    all_buckets = pd.DataFrame({"bucket": prefixes})
    agg = all_buckets.merge(agg, on="bucket", how="left").fillna(0)

    metrics = ["revenue", "expenses", "margin", "refunds"]

    chart_mode = st.radio("Chart mode", ["Grouped", "Stacked", "100%"], horizontal=True)
    picked = st.multiselect("Series", metrics, default=metrics)
    sort_by = st.selectbox("Sort by", metrics + ["refund_rate", "margin_rate"], index=0)
    asc = st.checkbox("Ascending", value=False)
    overlay_rate = st.selectbox("Overlay", ["None", "Refund rate", "Margin %"], index=0)

    bucket_order = agg.sort_values(sort_by, ascending=asc)["bucket"].tolist()

    melted = agg.melt(
        id_vars=["bucket"],
        value_vars=metrics,
        var_name="metric",
        value_name="value",
    )
    melted = melted[melted["metric"].isin(picked)]

    domain = ["revenue", "expenses", "margin", "refunds"]
    colors = ["#1565C0", "#EF6C00", "#2E7D32", "#C62828"]

    stack_mode = None
    x_offset = "metric:N"
    if chart_mode == "Stacked":
        stack_mode = "zero"
        x_offset = alt.value(0)
    elif chart_mode == "100%":
        stack_mode = "normalize"
        x_offset = alt.value(0)

    bar = (
        alt.Chart(melted)
        .mark_bar()
        .encode(
            x=alt.X("bucket:N", title="Unit", sort=bucket_order),
            xOffset=x_offset,
            y=alt.Y("value:Q", stack=stack_mode, title="Amount ($)" if chart_mode != "100%" else "Share"),
            color=alt.Color("metric:N", scale=alt.Scale(domain=domain, range=colors), title=None),
            tooltip=["bucket:N", "metric:N", alt.Tooltip("value:Q", format=",.2f")],
        )
    )

    if overlay_rate == "Refund rate":
        line_df = agg[["bucket", "refund_rate"]]
        line = (
            alt.Chart(line_df)
            .mark_line(point=True, color="#9C27B0")
            .encode(
                x=alt.X("bucket:N", sort=bucket_order, title="Unit"),
                y=alt.Y("refund_rate:Q", title="Rate (%)"),
                tooltip=["bucket:N", alt.Tooltip("refund_rate:Q", format=".2f")],
            )
        )
        chart = alt.layer(bar, line).resolve_scale(y="independent").properties(
            title="Revenue, Expenses, Margin, Refunds by Unit"
        )
    elif overlay_rate == "Margin %":
        line_df = agg[["bucket", "margin_rate"]]
        line = (
            alt.Chart(line_df)
            .mark_line(point=True, color="#7B1FA2")
            .encode(
                x=alt.X("bucket:N", sort=bucket_order, title="Unit"),
                y=alt.Y("margin_rate:Q", title="Rate (%)"),
                tooltip=["bucket:N", alt.Tooltip("margin_rate:Q", format=".2f")],
            )
        )
        chart = alt.layer(bar, line).resolve_scale(y="independent").properties(
            title="Revenue, Expenses, Margin, Refunds by Unit"
        )
    else:
        chart = bar.properties(title="Revenue, Expenses, Margin, Refunds by Unit")

    st.altair_chart(chart, use_container_width=True)

    st.dataframe(
        agg.set_index("bucket")[
            ["revenue", "expenses", "margin", "refunds", "refund_rate", "margin_rate"]
        ].loc[bucket_order].reset_index()
    )


