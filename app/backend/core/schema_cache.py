from __future__ import annotations
import os, time
from typing import Dict, List
from sqlalchemy import create_engine, inspect

from app.backend.db_connection import create_connection

_engine = create_engine("mssql+pymssql://", creator=create_connection, pool_pre_ping=True)
_cache: Dict[str, dict] = {}
TTL_SECS = 3600

def refresh_schema() -> dict:
    insp = inspect(_engine)
    schema = "dbo"
    table = "CustOrderDetails"
    
    # Check if table exists
    if not insp.has_table(table, schema=schema):
        _cache["schema"] = {"data": {}, "ts": time.time()}
        return {}

    cols = insp.get_columns(table, schema=schema)
    payload = {
        "schemas": {
            schema: {
                table: {
                    "columns": [
                        {"name": c["name"], "type": str(c["type"]), "nullable": c.get("nullable", True)}
                        for c in cols
                    ]
                }
            }
        }
    }
    _cache["schema"] = {"data": payload, "ts": time.time()}
    return payload

def get_schema() -> dict:
    item = _cache.get("schema")
    if not item or (time.time() - item["ts"]) > TTL_SECS:
        return refresh_schema()
    return item["data"]


if __name__ == "__main__":
    print(get_schema())
