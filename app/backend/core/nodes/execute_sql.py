from __future__ import annotations
from typing import Dict, Any, Optional

from pydantic import BaseModel
from sqlalchemy import create_engine, text
from app.backend.db_connection import create_connection
from app.backend.core.graph import GraphState

engine = create_engine("mssql+pymssql://", creator=create_connection, pool_pre_ping=True)

def execute_sql(state: GraphState) -> Dict[str, Any]:
    """Executes SQL."""
    if not state.sql:
        return {"error": "Invalid SQL."}
    
    safe_sql = state.sql

    try:
        with engine.begin() as conn:
            rows = conn.execute(text(safe_sql)).mappings().all()
        return {"execution_result": [dict(row) for row in rows]}
    except Exception as e:
        return {"error": f"Query failed: {e}."}
