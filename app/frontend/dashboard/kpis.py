import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def display_kpis(df):

    st.subheader("Executive KPIs")
    
    # Month filter
    months = st.multiselect(
        "Select Month",
        options=[7, 8],
        format_func=lambda month: datetime(2024, month, 1).strftime('%B'),
        default=[7, 8]
    )
    
    if months:
        df = df[df['Purchased on'].dt.month.isin(months)]

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    successful_orders_df = df[df['currency_code'] != 'Refunded']
    total_revenue = successful_orders_df['gross_amount'].sum()
    total_profit = df['margin_profit'].sum()
    total_orders = df['Order Number'].nunique()
    aov = total_revenue / total_orders if total_orders > 0 else 0
    total_refunded_orders = df[df['currency_code'] == 'Refunded']['Order Number'].nunique()
    refund_rate = (total_refunded_orders / total_orders) * 100 if total_orders > 0 else 0
    margin_pct = (total_profit / total_revenue * 100) if total_revenue > 0 else 0

    col1.metric("Total Revenue", f"${total_revenue:,.2f}")
    col2.metric("Total Profit", f"${total_profit:,.2f}")
    col3.metric("Total Orders", f"{total_orders}")
    col4.metric("Avg Order Value", f"${aov:,.2f}")
    col5.metric("Refund Rate", f"{refund_rate:.2f}%")
    col6.metric("Margin %", f"{margin_pct:.2f}%")
