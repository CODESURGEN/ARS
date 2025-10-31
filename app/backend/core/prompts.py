from __future__ import annotations

SYSTEM_PROMPT = """
You are a SQL expert.
"""
RESPONSE_SYSTEM_PROMPT = """
You are a helpful assistant.
"""

FEWSHOTS = [
    {
        "user": "What is the total revenue?",
        "sql": "SELECT SUM(price) FROM dbo.CustOrderDetails;"
    },
    {
        "user": "How many orders were placed in the last 7 days?",
        "sql": "SELECT COUNT(*) FROM dbo.CustOrderDetails WHERE order_date >= DATEADD(day, -7, GETDATE());"
    },
    {
        "user": "What is the average order value?",
        "sql": "SELECT AVG(price) FROM dbo.CustOrderDetails;"
    }
]
