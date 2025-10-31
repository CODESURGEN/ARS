from __future__ import annotations
import os,json,sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
from langgraph.graph.state import CompiledStateGraph
from decimal import Decimal
import datetime

APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

class ChatReq(BaseModel):
    message: str

from app.backend.core.graph import GraphState, lg_app
from app.backend.core.nodes.generate_response import json_converter

api = FastAPI(title="ARS Text2SQL Service")
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def stream_chat(req: ChatReq) -> AsyncGenerator[str, None]:
    try:
        async for event in lg_app.astream_events({"user_msg": req.message}, version="v1"):
            ev = event.get("event") or ""
            if ev == "on_chat_model_stream" and event.get('metadata').get("langgraph_node") == "generate_response":
                data = event.get("data") or {}
                chunk = data.get("chunk")
                content = getattr(chunk, "content", None) if chunk is not None else None
                if content:
                    yield f"data: {json.dumps({'delta': content})}\n\n"
        yield f"data: {json.dumps({'data': '[DONE]'})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        
@api.post("/chat")
async def chat(req: ChatReq):
    return StreamingResponse(
        stream_chat(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

