import http.client
import json
import os,re
from urllib.parse import urlencode, urlparse

from dotenv import load_dotenv

load_dotenv()

PREFIX_TO_KEY_MAP = {
    "FE": "STRIPE_SECRET_KEY_PARTSFE",
    "CEFE": "STRIPE_SECRET_KEY_PARTSFE",
    "FEUK":"STRIPE_SECRET_KEY_PARTSFE",
    "HnC": "STRIPE_SECRET_KEY_PARTSHNC",
    "HnK": "STRIPE_SECRET_KEY_HNKPARTS",
    "HT": "STRIPE_SECRET_KEY_HT",
    "WTB": "STRIPE_SECRET_KEY_WTB"
}

def get_secret_key(purchase_order_number: str) -> str:
    match = re.match(r'^[a-zA-Z]+', purchase_order_number)
    if not match:
        raise ValueError("Invalid purchase_order_number format")
    prefix = match.group(0)
    key_name = PREFIX_TO_KEY_MAP.get(prefix)
    if not key_name:
        raise ValueError(f"No secret key mapping for prefix: {prefix}")
    secret_key = os.getenv(key_name)
    if not secret_key:
        raise ValueError(f"Secret key not found in environment: {key_name}")
    return secret_key

base_url = os.getenv("STRIPE_API_BASE", "https://api.stripe.com")
STRIPE_HOST = urlparse(base_url).netloc or base_url


def _stripe_request(
    method: str, path: str, payload: str, headers: dict, error_context: str
) -> dict:
    """stripe request"""
    conn = http.client.HTTPSConnection(STRIPE_HOST)
    conn.request(method, path, payload, headers)
    res = conn.getresponse()
    data = res.read()
    if res.status < 200 or res.status >= 300:
        raise RuntimeError(
            f"Stripe {error_context} error {res.status}: {data.decode('utf-8', 'ignore')}"
        )
    if not data:
        return {}
    return json.loads(data.decode("utf-8"))


def _get_auth_headers(stripe_api_key: str) -> dict:
    if not stripe_api_key:
        raise RuntimeError("Missing Stripe secret key")
    return {
        "Authorization": f"Bearer {stripe_api_key}",
        "Content-Type": "application/x-www-form-urlencoded",
    }


def get_payment_intent(payment_intent_id: str, stripe_api_key: str) -> dict:
    """Get Payment Intent"""
    if not payment_intent_id:
        raise ValueError("payment_intent_id required")
    path = f"/v1/payment_intents/{payment_intent_id}"
    headers = _get_auth_headers(stripe_api_key)
    return _stripe_request("GET", path, "", headers, "get payment intent")


def get_balance_transactions(charge_id: str, stripe_api_key: str) -> dict:
    """Get Balance Transactions"""
    if not charge_id:
        raise ValueError("charge_id required")
    params = {"source": charge_id}
    path = f"/v1/balance_transactions?{urlencode(params)}"
    headers = _get_auth_headers(stripe_api_key)
    return _stripe_request("GET", path, "", headers, "get balance transactions")


def get_stripe_capture(purchase_order_number: str, payment_intent_id: str) -> dict:
    """Get settlement data"""
    stripe_api_key = get_secret_key(purchase_order_number)
    payment_intent = get_payment_intent(payment_intent_id, stripe_api_key)
    latest_charge_id = payment_intent.get("latest_charge")
    if not latest_charge_id:
        raise ValueError("No latest_charge found in payment intent")
    capture_data = get_balance_transactions(latest_charge_id, stripe_api_key)
    response = {
        "gross_amount": capture_data.get("data")[0].get("amount") /100,
        "psp_fees": capture_data.get("data")[0].get("fee") / 100,
        "settlement_amount": capture_data.get("data")[0].get("net") / 100,
        "currency_code": capture_data.get("data")[0].get("currency").upper(),
        "conversion_rate": capture_data.get("data")[0].get("exchange_rate") or 1
    }
    return response



if __name__ == "__main__":
    po_id = "FEUK001000081"
    pi_id = "pi_3RhcjrLbZ7P2XrWw3xWxLn85"
    try:
        settlement_data = get_stripe_capture(po_id, pi_id)
        print(json.dumps(settlement_data, indent=2))
    except (RuntimeError, ValueError) as e:
        print(f"Error: {e}")
    