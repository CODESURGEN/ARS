import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

def display_daily_payouts(df):
    st.subheader("Day-wise Payout")

    if df.empty or df['Purchased on'].isnull().all():
        st.warning("No data available to display daily payouts.")
        return

    df['Purchased on'] = pd.to_datetime(df['Purchased on'])

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

    mask = (df['Purchased on'].dt.date >= start_date) & (df['Purchased on'].dt.date <= end_date)
    filtered_df = df.loc[mask]

    if filtered_df.empty:
        st.warning("No data available for the selected date range.")
        return

    daily_payout = filtered_df.set_index('Purchased on').resample('D').agg(
        total_payout=('settlement_amount', 'sum'),
        total_purchased=('Total Purchased', 'sum'),
        vendor_total=('Vendor Amount', 'sum'),
        psp_fee=('psp_fees', 'sum')
    ).reset_index()

    daily_payout = daily_payout.rename(columns={'Purchased on': 'Settelment_date'})
    daily_payout['Settelment_date'] = daily_payout['Settelment_date'].dt.strftime('%d-%m-%Y')

    fig = px.bar(daily_payout, x='Settelment_date', y='total_payout')
    st.plotly_chart(fig, use_container_width=True)

    st.write("Data View", daily_payout)
