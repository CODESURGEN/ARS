import os
import csv
import logging
from pathlib import Path
from app.backend.psp_data.paypal import get_paypal_capture
from app.backend.psp_data.stripe import get_stripe_capture
from app.backend.db_connection import create_connection, list_tables
from app.frontend.queries.orders import DEFAULT_QUERY
import pandas as pd
from tqdm import tqdm
import time


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


CACHE_HEADERS = [
    "payment_method",
    "transaction_id",
    "order_number",
    "gross_amount",
    "psp_fees",
    "settlement_amount",
    "currency_code",
    "conversion_rate",
]

intent_id = None

def _cache_path() -> Path:
    base = Path(__file__).resolve().parents[2]
    return base / "data" / "psp_data.csv"


def _ensure_cache():
    path = _cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(CACHE_HEADERS)


def _read_cached(payment_method: str, transaction_id: str, order_number: str) -> dict | None:
    path = _cache_path()
    if not path.exists():
        return None
    with path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "paypal" in payment_method.lower():
                if (
                    row.get("payment_method", "").lower() == "paypal"
                    and row.get("transaction_id") == transaction_id
                ):
                    return {
                        "gross_amount": float(row.get("gross_amount") or 0.0),
                        "psp_fees": float(row.get("psp_fees") or 0.0),
                        "settlement_amount": float(row.get("settlement_amount") or 0.0),
                        "currency_code": row.get("currency_code") or None,
                        "conversion_rate": float(row.get("conversion_rate") or 1.0),
                    }
            elif "stripe" in payment_method.lower():
                if (
                    row.get("payment_method", "").lower() == "stripe"
                    and row.get("transaction_id") == transaction_id
                    and row.get("order_number") == (order_number or "")
                ):
                    return {
                        "gross_amount": float(row.get("gross_amount") or 0.0),
                        "psp_fees": float(row.get("psp_fees") or 0.0),
                        "settlement_amount": float(row.get("settlement_amount") or 0.0),
                        "currency_code": row.get("currency_code") or None,
                        "conversion_rate": float(row.get("conversion_rate") or 1.0),
                    }
    return None


def _append_cache(payment_method: str, transaction_id: str, order_number: str, data: dict) -> None:
    _ensure_cache()
    path = _cache_path()
    with path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CACHE_HEADERS)
        writer.writerow({
            "payment_method": payment_method.lower(),
            "transaction_id": transaction_id,
            "order_number": order_number or "",
            "gross_amount": data.get("gross_amount", 0.0),
            "psp_fees": data.get("psp_fees", 0.0),
            "settlement_amount": data.get("settlement_amount", 0.0),
            "currency_code": data.get("currency_code"),
            "conversion_rate": data.get("conversion_rate", 1.0),
        })


def fetch_psp_data(payment_method: str, transaction_id: str, order_number: str) -> dict:
    """
    PSP data
    """
    psp_data = {
        "gross_amount": 0.0,
        "psp_fees": 0.0,
        "settlement_amount": 0.0,
        "currency_code": "Refunded",
        "conversion_rate": 1,
        }
    try:
        if not payment_method or not transaction_id:
            return psp_data

        cached = _read_cached(payment_method, transaction_id, order_number)
        if cached is not None:
            logging.info(f"Cached data found for {payment_method} transaction {transaction_id}")
            return cached

        if "paypal" in payment_method.lower():
            logging.info(f"Fetching PayPal data for transaction ID: {transaction_id}")
            data = get_paypal_capture(transaction_id)
            psp_data.update(data)
            _append_cache(payment_method, transaction_id,order_number, psp_data)
        elif "stripe" in payment_method.lower():
            if transaction_id.lower().endswith("-refund"):
                intent_id = transaction_id.replace("-refund", "")
            else:
                intent_id = transaction_id
            logging.info(
                f"Fetching Stripe data for order number: {order_number}, payment intent ID: {transaction_id}"
            )
            data = get_stripe_capture(order_number, intent_id)
            psp_data.update(data)
            _append_cache(payment_method, transaction_id, order_number, psp_data)
    except Exception as e:
        _append_cache(payment_method, transaction_id, order_number, psp_data)
        logging.error(
            f"Error fetching PSP data for {payment_method} transaction {transaction_id}: {e}"
        )
    return psp_data

if __name__ == "__main__":
    conn = create_connection()
    rows, columns = list_tables(conn, DEFAULT_QUERY)
    print(len(rows))
    if rows:
        df = pd.DataFrame(rows, columns=columns if columns else None)
    else:
        df = pd.DataFrame(columns=columns if columns else None)

    batch_size = 500
    num_rows = len(df)

    for i in range(0, num_rows, batch_size):
        batch_df = df.iloc[i:i + batch_size]
        
        for index, row in tqdm(batch_df.iterrows(), total=len(batch_df), desc=f"Caching batch {i // batch_size + 1}", unit="row"):
            fetch_psp_data(row["Payment Method"], row["Payment Transaction ID"], row["Order Number"])

        if i + batch_size < num_rows:
            logging.info("Taking a 3-minute break...")
            time.sleep(180)
            
    print("PSP data cached successfully")