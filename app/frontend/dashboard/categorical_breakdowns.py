import streamlit as st
import pandas as pd
import altair as alt

def display_categorical_charts(df):
    st.subheader("Breakdowns")

    cols = st.columns(2, gap="medium")

    with cols[0]:
        st.caption("Top Vendors by Profit")
        vendor_profit = df.groupby('Vendor Name')['margin_profit'].sum().reset_index()
        vendor_profit = vendor_profit.sort_values('margin_profit', ascending=False).head(12)
        chart = alt.Chart(vendor_profit).mark_bar(color='#3949AB').encode(
            x=alt.X('margin_profit:Q', title='Profit'),
            y=alt.Y('Vendor Name:N', sort='-x', title=None)
        ).configure_legend(disable=True)
        st.altair_chart(chart, use_container_width=True)

    with cols[1]:
        st.caption("Payment Method Mix")
        payment_method_dist = df.groupby('Payment Method')['gross_amount'].sum().reset_index()
        chart = alt.Chart(payment_method_dist).mark_bar(color='#00897B').encode(
            x=alt.X('gross_amount:Q', title='Revenue'),
            y=alt.Y('Payment Method:N', sort='-x', title=None)
        ).configure_legend(disable=True)
        st.altair_chart(chart, use_container_width=True)

    cols = st.columns(2, gap="medium")

    with cols[0]:
        st.caption("Monthly Revenue vs Costs")
        df.loc[:, 'month'] = df['Purchased on'].dt.to_period('M').astype(str)
        monthly = df.groupby('month').agg({
            'Subtotal Purchased': 'sum',
            'Tax': 'sum',
            'Shipping': 'sum',
            'margin_profit': 'sum'
        }).reset_index()
        melted = pd.melt(monthly, id_vars=['month'], value_vars=['Subtotal Purchased', 'Tax', 'Shipping'], var_name='Component', value_name='Amount')
        cost_chart = alt.Chart(melted).mark_bar().encode(
            x=alt.X('month:N', title=None),
            y=alt.Y('Amount:Q', title='Cost'),
            color=alt.Color('Component:N', legend=None)
        )
        revenue_line = alt.Chart(monthly).mark_line(color='#1565C0', size=2).encode(
            x=alt.X('month:N', title=None),
            y=alt.Y('Subtotal Purchased:Q', title='Revenue')
        )
        chart = alt.layer(cost_chart, revenue_line)
        st.altair_chart(chart, use_container_width=True)

    with cols[1]:
        st.caption("Refund Impact by Month")
        refunds = df.copy()
        refunds.loc[:,'month'] = refunds['Purchased on'].dt.to_period('M').astype(str)
        refund_month = refunds[refunds['currency_code'] == 'Refunded'].groupby('month').size().reset_index(name='refund_count')
        chart = alt.Chart(refund_month).mark_bar(color='#C62828').encode(
            x=alt.X('month:N', title=None),
            y=alt.Y('refund_count:Q', title='Refunds')
        )
        st.altair_chart(chart, use_container_width=True)
