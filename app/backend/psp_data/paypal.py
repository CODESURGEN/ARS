import base64
import http.client
import json
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()


base_url = os.getenv("PAYPAL_API_BASE")
PAYPAL_HOST = urlparse(base_url).netloc or base_url


def _basic_auth_header(client_id: str, client_secret: str) -> str:
    creds = f"{client_id}:{client_secret}".encode()
    return "Basic " + base64.b64encode(creds).decode()


def _paypal_request(method: str, path: str, payload: str, headers: dict, error_context: str) -> dict:
    """paypal request"""
    conn = http.client.HTTPSConnection(PAYPAL_HOST)
    conn.request(method, path, payload, headers)
    res = conn.getresponse()
    data = res.read()
    if res.status < 200 or res.status >= 300:
        raise RuntimeError(f"PayPal {error_context} error {res.status}: {data.decode('utf-8', 'ignore')}")
    if not data:
        return {}
    return json.loads(data.decode("utf-8"))


def get_access_token(client_id: str | None = None, client_secret: str | None = None) -> str:
    """token"""
    cid = client_id or os.getenv("PAYPAL_CLIENT_ID", "")
    csec = client_secret or os.getenv("PAYPAL_SECRET", "") or os.getenv("PAYPAL_CLIENT_SECRET", "")
    if not cid or not csec:
        raise RuntimeError("Missing PayPal creds")
    payload = "grant_type=client_credentials"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US",
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": _basic_auth_header(cid, csec),
    }
    obj = _paypal_request("POST", "/v1/oauth2/token", payload, headers, "token")
    token = obj.get("access_token")
    if not token:
        raise RuntimeError("No access_token")
    return token


def get_paypal_capture(transaction_id: str) -> dict:
    """capture"""
    if not transaction_id:
        raise ValueError("transaction_id required")
    access_token = get_access_token()
    conn = http.client.HTTPSConnection(PAYPAL_HOST)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    path = f"/v2/payments/captures/{transaction_id}"
    capture_data = _paypal_request("GET", path, "", headers, "capture")
    
    breakdown = capture_data.get("seller_receivable_breakdown", {})
    gross_amount = breakdown.get("gross_amount", {})
    paypal_fee = breakdown.get("paypal_fee", {})
    net_amount = breakdown.get("net_amount", {})

    response = {
        "gross_amount": float(gross_amount.get("value", "0.0")),
        "psp_fees": float(paypal_fee.get("value", "0.0")),
        "settlement_amount": float(net_amount.get("value", "0.0")),
        "currency_code": gross_amount.get("currency_code"),
        "conversion_rate": 1
    }
    return response


if __name__ == "__main__":
    capture = get_paypal_capture("9T6730887M6016509")
    print(json.dumps(capture, indent=2))