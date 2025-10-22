import pandas as pd
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.frontend.dashboard.order_details import get_order_details

def create_order_details_csv():
    """
    Fetches order details and saves them to a CSV file.
    """
    print("Fetching order details...")
    df = get_order_details()
    
    if df is not None and not df.empty:
        output_path = "app/data/order_details.csv"
        print(f"Saving order details to {output_path}...")
        df.to_csv(output_path, index=False)
        print("Done.")
    else:
        print("No data returned from get_order_details.")

if __name__ == "__main__":
    create_order_details_csv()
