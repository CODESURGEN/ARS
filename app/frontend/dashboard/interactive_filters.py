import streamlit as st
import pandas as pd

def display_filters(df):
    
    st.subheader("Compare different Vendors")
    st.write("Vendors to compare")
    vendors = sorted(df['Vendor Name'].dropna().astype(str).unique().tolist())
    if 'selected_vendors' not in st.session_state:
        st.session_state.selected_vendors = vendors[:]

    def toggle_vendor(vendor):
        if vendor in st.session_state.selected_vendors:
            st.session_state.selected_vendors.remove(vendor)
        else:
            st.session_state.selected_vendors.append(vendor)

    num_vendors = len(vendors)
    cols = st.columns(num_vendors)

    for i, vendor in enumerate(vendors):
        is_selected = vendor in st.session_state.selected_vendors
        button_type = "primary" if is_selected else "secondary"
        cols[i].button(vendor, key=f"vendor_{vendor}", on_click=toggle_vendor, args=(vendor,), type=button_type)
    
    selected_vendors = st.session_state.get('selected_vendors', [])
    
    if not selected_vendors:
        st.warning("Select at least one vendor to see the analytics.")

    filtered_df = df[
        (df['Vendor Name'].isin(selected_vendors))
    ]
    
    return filtered_df

def display_tables(df):
    st.subheader("Full Data Table")
    st.dataframe(df)
