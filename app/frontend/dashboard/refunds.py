import streamlit as st
import pandas as pd
import altair as alt


def display_refund_dashboard(df: pd.DataFrame) -> None:
    st.subheader("Refunds")

    work_df = df.copy()

    # Ensure datetime & boolean
    if not pd.api.types.is_datetime64_any_dtype(work_df["Purchased on"]):
        work_df.loc[:, "Purchased on"] = pd.to_datetime(work_df["Purchased on"], errors="coerce")

    work_df.loc[:, "is_refunded"] = work_df["currency_code"].astype(str).str.lower().eq("refunded")

    # --- KPIs ---
    total_orders = len(work_df)
    refunded_orders = int(work_df["is_refunded"].sum())
    refund_rate = (refunded_orders / total_orders * 100) if total_orders > 0 else 0.0
    refund_amount = work_df.loc[work_df["is_refunded"], "Total Purchased"].sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Orders", f"{total_orders}")
    c2.metric("Refunded Orders", f"{refunded_orders}")
    c3.metric("Refund Rate (%)", f"{refund_rate:.2f}")
    c4.metric("Refund Amount", f"${refund_amount:,.2f}")
    st.progress(min(max(refund_rate / 100.0, 0.0), 1.0))

    # --- Tabs (Payment Methods removed) ---
    tabs = st.tabs([
        "Refund Trends",
        "Vendor Refunds",
        "Margin Impact",
        "Detailed Data",
    ])

    # --- Refund Trends ---
    with tabs[0]:
        st.caption("Refunds Over Time")
        trend_df = work_df.assign(date=work_df["Purchased on"].dt.normalize())

        refunds_daily = (
            trend_df.groupby("date", dropna=True)["is_refunded"].mean()
            .mul(100)
            .reset_index(name="refund_rate")
        )
        sales_daily = (
            trend_df.groupby("date", dropna=True)["Total Purchased"].sum()
            .reset_index(name="total_sales")
        )

        chart_refund = (
            alt.Chart(refunds_daily)
            .mark_line(point=True)
            .encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y("refund_rate:Q", title="Refund Rate (%)"),
                tooltip=["date:T", alt.Tooltip("refund_rate:Q", format=".2f", title="Refund Rate (%)")]
            )
            .properties(title="Daily Refund Rate")
        )

        chart_sales = (
            alt.Chart(sales_daily)
            .mark_bar()
            .encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y("total_sales:Q", title="Total Sales ($)"),
                tooltip=["date:T", alt.Tooltip("total_sales:Q", format=",.2f", title="Sales ($)")]
            )
            .properties(title="Daily Total Sales")
        )

        st.altair_chart(chart_refund, use_container_width=True)
        st.altair_chart(chart_sales, use_container_width=True)

    # --- Vendor Refunds ---
    with tabs[1]:
        st.caption("Refunds by Vendor")
        if "Vendor Name" in work_df.columns:
            vendor_refunds = (
                work_df.groupby("Vendor Name", dropna=False)["is_refunded"]
                .mean()
                .mul(100)
                .reset_index(name="refund_rate")
                .sort_values("refund_rate", ascending=False)
            )
            chart = (
                alt.Chart(vendor_refunds)
                .mark_bar()
                .encode(
                    x=alt.X("refund_rate:Q", title="Refund Rate (%)"),
                    y=alt.Y("Vendor Name:N", sort='-x', title=None),
                    tooltip=["Vendor Name:N", alt.Tooltip("refund_rate:Q", format=".2f", title="Refund Rate (%)")]
                )
                .properties(title="Vendor Refund Comparison")
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Missing `Vendor Name` column")

    # --- Margin Impact (revamped) ---
    with tabs[2]:
        st.caption("Margin Profit Impact (Refunded vs Non-refunded)")

        if "margin_profit" in work_df.columns:
            mp_df = work_df[["margin_profit", "is_refunded", "Total Purchased"]].copy()
            mp_df = mp_df.dropna(subset=["margin_profit"])

            # Summary KPIs
            non_ref_avg = mp_df.loc[~mp_df["is_refunded"], "margin_profit"].mean()
            ref_avg = mp_df.loc[mp_df["is_refunded"], "margin_profit"].mean()
            delta = (ref_avg - non_ref_avg) if pd.notnull(ref_avg) and pd.notnull(non_ref_avg) else None

            k1, k2, k3 = st.columns(3)
            k1.metric("Avg Margin (Non-refunded)", f"${(non_ref_avg or 0):,.2f}")
            k2.metric("Avg Margin (Refunded)", f"${(ref_avg or 0):,.2f}")
            if delta is not None:
                k3.metric("Δ Refunded vs Non-ref", f"${delta:,.2f}", delta=f"{delta:,.2f}")

            # A. Smooth distribution (density) for both groups
            #    Shows shape & overlap of margins
            density = (
                alt.Chart(mp_df.rename(columns={"is_refunded": "Refunded"}))
                .transform_density(
                    "margin_profit",
                    groupby=["Refunded"],
                    as_=["margin_profit", "density"]
                )
                .mark_area(opacity=0.5)
                .encode(
                    x=alt.X("margin_profit:Q", title="Margin Profit"),
                    y=alt.Y("density:Q", title="Density"),
                    color=alt.Color("Refunded:N", title="Refunded"),
                    tooltip=[alt.Tooltip("Refunded:N"), alt.Tooltip("margin_profit:Q", format=",.2f")]
                )
                .properties(title="Margin Profit Distribution")
            )

            # B. Boxplot for quick median/IQR comparison
            box = (
                alt.Chart(mp_df.rename(columns={"is_refunded": "Refunded"}))
                .mark_boxplot(size=50)
                .encode(
                    x=alt.X("Refunded:N", title=None),
                    y=alt.Y("margin_profit:Q", title="Margin Profit"),
                    color=alt.Color("Refunded:N", legend=None),
                )
                .properties(title="Margin Profit (Boxplot)")
            )

            # C. Scatter: Margin vs Order Amount (helps spot outliers)
            scatter = (
                alt.Chart(mp_df.rename(columns={"is_refunded": "Refunded"}))
                .mark_circle(size=70, opacity=0.45)
                .encode(
                    x=alt.X("Total Purchased:Q", title="Order Amount"),
                    y=alt.Y("margin_profit:Q", title="Margin Profit"),
                    color=alt.Color("Refunded:N", title="Refunded"),
                    tooltip=[
                        alt.Tooltip("Total Purchased:Q", format=",.2f", title="Order Amount"),
                        alt.Tooltip("margin_profit:Q", format=",.2f", title="Margin"),
                        alt.Tooltip("Refunded:N")
                    ]
                )
                .properties(title="Margin vs Order Amount (Outliers & Patterns)")
            )

            st.altair_chart(density, use_container_width=True)
            st.altair_chart(box, use_container_width=True)
            st.altair_chart(scatter, use_container_width=True)
        else:
            st.info("Missing `margin_profit` column")

    # --- Detailed Data ---
    with tabs[3]:
        st.caption("Refunded Orders")
        st.dataframe(work_df[work_df["is_refunded"]])
