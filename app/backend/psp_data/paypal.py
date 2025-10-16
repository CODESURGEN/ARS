import base64
import http.client
import json
import os
from urllib.parse import urlparse

def _resolve_host() -> str:
    base = os.getenv("PAYPAL_API_BASE", "https://api-m.paypal.com")
    p = urlparse(base)
    return p.netloc or base


PAYPAL_HOST = _resolve_host()


def _basic_auth_header(client_id: str, client_secret: str) -> str:
    creds = f"{client_id}:{client_secret}".encode()
    return "Basic " + base64.b64encode(creds).decode()


def get_access_token(client_id: str | None = None, client_secret: str | None = None) -> str:
    """token"""
    cid = client_id or os.getenv("PAYPAL_CLIENT_ID", "")
    csec = client_secret or os.getenv("PAYPAL_SECRET", "") or os.getenv("PAYPAL_CLIENT_SECRET", "")
    if not cid or not csec:
        raise RuntimeError("Missing PayPal creds")
    conn = http.client.HTTPSConnection(PAYPAL_HOST)
    payload = "grant_type=client_credentials"
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en_US",
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": _basic_auth_header(cid, csec),
    }
    conn.request("POST", "/v1/oauth2/token", payload, headers)
    res = conn.getresponse()
    data = res.read()
    if res.status < 200 or res.status >= 300:
        raise RuntimeError(f"PayPal token error {res.status}: {data.decode('utf-8', 'ignore')}")
    obj = json.loads(data.decode("utf-8"))
    token = obj.get("access_token")
    if not token:
        raise RuntimeError("No access_token")
    return token


def get_capture(transaction_id: str, access_token: str) -> dict:
    """capture"""
    if not transaction_id:
        raise ValueError("transaction_id required")
    if not access_token:
        raise ValueError("access_token required")
    conn = http.client.HTTPSConnection(PAYPAL_HOST)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    path = f"/v2/payments/captures/{transaction_id}"
    conn.request("GET", path, "", headers)
    res = conn.getresponse()
    data = res.read()
    if res.status < 200 or res.status >= 300:
        raise RuntimeError(f"PayPal capture error {res.status}: {data.decode('utf-8', 'ignore')}")
    return json.loads(data.decode("utf-8"))


def _main() -> None:
    """cli"""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("transaction_id")
    parser.add_argument("--client-id", default=os.getenv("PAYPAL_CLIENT_ID", ""))
    parser.add_argument("--client-secret", default=os.getenv("PAYPAL_CLIENT_SECRET", ""))
    args = parser.parse_args()

    token = get_access_token(args.client_id, args.client_secret)
    obj = get_capture(args.transaction_id, token)
    print(json.dumps(obj, indent=2, sort_keys=True))


if __name__ == "__main__":
    _main()


