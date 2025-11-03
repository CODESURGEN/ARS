import os,sys
import pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.backend.db_connection import create_connection, list_tables
from app.frontend.queries.orders import DEFAULT_QUERY
def create_order_details_csv():
    """
    Fetches order details and saves them to a CSV file.
    """
    print("Fetching order details...")
    conn = create_connection()
    rows, columns = list_tables(conn, DEFAULT_QUERY)
    df = pd.DataFrame(rows, columns=columns if columns else None)
    

    if df is not None and not df.empty:
        output_path = "app/data/order_details.csv"
        print(f"Saving order details to {output_path}...")
        df.to_csv(output_path, index=False)
        print("Done.")
    else:
        print("No data returned from get_order_details.")

if __name__ == "__main__":
    create_order_details_csv()
