from __future__ import annotations
import os
from typing import Literal, Optional, Any
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# ----- State -----
class GraphState(BaseModel):
    user_msg: str
    sql: Optional[str] = None
    execution_result: Optional[Any] = None
    result: Optional[Any] = None
    error: Optional[str] = None

# ----- Nodes -----
from app.backend.core.nodes.generate_sql import generate_sql
from app.backend.core.nodes.execute_sql import execute_sql
from app.backend.core.nodes.generate_response import generate_response


# ----- Graph wiring -----
graph = StateGraph(GraphState)

graph.add_node("generate_sql", generate_sql)
graph.add_node("execute_sql", execute_sql)
graph.add_node("generate_response", generate_response)

# Entry point
graph.set_entry_point("generate_sql")

# Edges
graph.add_edge("generate_sql", "execute_sql")
graph.add_edge("execute_sql", "generate_response")
graph.add_edge("generate_response", END)


lg_app = graph.compile()