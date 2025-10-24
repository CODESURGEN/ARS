import streamlit as st
import pandas as pd
import sys
import os
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from app.frontend.dashboard.kpis import display_kpis
from app.frontend.dashboard.time_series import display_time_series_charts
from app.frontend.dashboard.categorical_breakdowns import display_categorical_charts
from app.frontend.dashboard.interactive_filters import display_filters, display_tables
from app.frontend.dashboard.order_details import get_order_details
from app.frontend.dashboard.refunds import display_refund_dashboard
load_dotenv()

def run():
    st.set_page_config(page_title="Executive Commerce Overview", layout="wide", page_icon="📊")
    st.title("Executive Overview")
    
    try:
        df = get_order_details()
        df.to_csv("app/data/order_details_with_psp.csv", index=False)

        if not df.empty:
            filtered_df = display_filters(df)
            display_kpis(filtered_df)
            display_time_series_charts(filtered_df)
            display_categorical_charts(filtered_df)
            display_tables(filtered_df)
            display_refund_dashboard(filtered_df)
            
        else:
            st.write("No data to display.")
        
    except Exception as e:
        st.error(str(e))

if __name__ == "__main__":
    run()

