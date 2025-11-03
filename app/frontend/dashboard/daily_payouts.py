import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

def display_daily_payouts(df):
    st.subheader("Day-wise Payout")

    # Convert 'Purchased on' to datetime
    df['Purchased on'] = pd.to_datetime(df['Purchased on'])

    # Date range filter
    min_date = df['Purchased on'].min().date()
    max_date = df['Purchased on'].max().date()
    
    start_date, end_date = st.date_input(
        "Select date range",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date,
    )

    if start_date > end_date:
        st.error("Error: End date must fall after start date.")
        return

    # Filter data based on date range
    mask = (df['Purchased on'].dt.date >= start_date) & (df['Purchased on'].dt.date <= end_date)
    filtered_df = df.loc[mask]

    if filtered_df.empty:
        st.warning("No data available for the selected date range.")
        return

    # Group by day and sum settlement_amount
    daily_payout = filtered_df.set_index('Purchased on').resample('D').agg(
        total_payout=('settlement_amount', 'sum')
    ).reset_index()

    daily_payout = daily_payout.rename(columns={'Purchased on': 'Settelment_date'})
    daily_payout['Settelment_date'] = daily_payout['Settelment_date'].dt.strftime('%d-%m-%Y')

    # Create altair chart
    # st.caption("Daily Payout")
    # chart = alt.Chart(daily_payout).mark_line(color='#2E7D32', size=2).encode(
    #     x=alt.X('Purchased on:T', title='Date'),
    #     y=alt.Y('total_payout:Q', title='Total Payout')
    # ).configure_legend(disable=True)
    
    # st.altair_chart(chart, use_container_width=True)
    fig = px.bar(daily_payout, x='Settelment_date', y='total_payout')
    st.plotly_chart(fig, use_container_width=True)

    st.write("Data View", daily_payout)
