from locale import D_FMT
import pandas as pd


def get_order_details():
    order_details_df = pd.read_csv("app/data/order_details.csv")
    psp_df = pd.read_csv("app/data/psp_data.csv")

    df = pd.merge(
        order_details_df,
        psp_df,
        left_on='Order Number',
        right_on='order_number',
        how='right',
        suffixes=("", "_psp")
    )

    prefer_cols = [
        "gross_amount",
        "Tax",
        "settlement_amount",
        "currency_code",
        "conversion_rate",
    ]
    for col in prefer_cols:
        psp_col = f"{col}_psp"
        if psp_col in df.columns:
            if col not in df.columns:
                df[col] = df[psp_col]
            else:
                df[col] = df[col].where(df[col].notna(), df[psp_col])

    df.loc[df['transaction_id'].str.endswith('-refund'), 'currency_code'] = 'Refunded'

    drop_cols = [
        "Payment Transaction ID",
        "transaction_id",
        # "payment_method",
        "order_number",
    ] + [f"{c}_psp" for c in prefer_cols if f"{c}_psp" in df.columns]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns], errors='ignore')

    numeric_cols = [
        "gross_amount", "Vendor Amount", "psp_fees", "Subtotal Purchased",
        "Tax", "Shipping", "Discount", "Vendor Subtotal", "Vendor Shipping"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    
    
    currency_cols = [
        "Total Purchased","Subtotal Purchased", "Tax", "Shipping",
        "Discount"
    ]
    
    rate = pd.to_numeric(df["conversion_rate"], errors='coerce').fillna(1) if "conversion_rate" in df.columns else 1
    for col in currency_cols:
        if col in df.columns:       
            df[col] = df[col] * rate

    if {"currency_code", "psp_fees", "gross_amount"}.issubset(df.columns):
        mask = (df["currency_code"] == "Refunded") & (df["psp_fees"] == 0)
        df.loc[mask, "psp_fees"] = -(0.035 * df["Total Purchased"])

    if "gross_amount" in df.columns and "Vendor Amount" in df.columns and "psp_fees" in df.columns:
        df["margin_profit"] = df["settlement_amount"] - df["Vendor Subtotal"] - df["Vendor Shipping"] - df["psp_fees"]

    if 'Purchased on' in df.columns:
        df['Purchased on'] = pd.to_datetime(df['Purchased on'])
    
    return df

if __name__ == "__main__":
    df = get_order_details()
    df["value_check"] = df["Total Purchased"] - df["gross_amount"]
    cols = ["Order Number", "Total Purchased", "gross_amount","currency_code","value_check",'payment_method']
    cols = [c for c in cols if c in df.columns]
    mismatched = df.loc[df["value_check"] > 0.1, cols]
    mismatched.to_csv("app/data/mismatched_orders.csv", index=False, columns=cols)