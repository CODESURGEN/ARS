import streamlit as st
import pandas as pd
import altair as alt

def display_time_series_charts(df):
    st.subheader("Time Series")

    weekly_data = df.set_index('Purchased on').resample('W').agg(
        total_profit=('margin_profit', 'sum'),
        total_revenue=('gross_amount', 'sum')
    ).reset_index()

    daily_orders = df.set_index('Purchased on').resample('D').agg(
        order_count=('Order Number', 'nunique')
    ).reset_index()

    cols = st.columns(2, gap="medium")

    with cols[0]:
        st.caption("Weekly Profit vs Revenue")
        base = alt.Chart(weekly_data).encode(x=alt.X('Purchased on:T', title=None))
        profit_chart = base.mark_line(color='#2E7D32', size=2).encode(y=alt.Y('total_profit:Q', title='Profit'))
        revenue_chart = base.mark_line(color='#1565C0', size=2).encode(y=alt.Y('total_revenue:Q', title='Revenue'))
        chart = alt.layer(revenue_chart, profit_chart).resolve_scale(y='independent').configure_legend(disable=True)
        st.altair_chart(chart, use_container_width=True)

    with cols[1]:
        st.caption("Daily Orders")
        chart = alt.Chart(daily_orders).mark_bar(color='#546E7A').encode(
            x=alt.X('Purchased on:T', title=None),
            y=alt.Y('order_count:Q', title='Orders')
        ).configure_legend(disable=True)
        st.altair_chart(chart, use_container_width=True)
