import streamlit as st
import pandas as pd
from app.backend.db_connection import create_connection, close_connection, list_tables
from dotenv import load_dotenv
from app.frontend.queries.orders import DEFAULT_QUERY

load_dotenv()

def run():
    st.set_page_config(page_title="Orders Details Dashboard", layout="wide")
    st.title("Orders Details Dashboard")
    conn = None
    try:
        conn = create_connection()
        rows, columns = list_tables(conn, DEFAULT_QUERY)
        if rows:
            df = pd.DataFrame(rows, columns=columns if columns else None)
        else:
            df = pd.DataFrame(columns=columns if columns else None)
        st.write(f"Rows: {len(rows)}")
        st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        st.error(str(e))
    finally:
        close_connection(conn)


if __name__ == "__main__":
    run()

