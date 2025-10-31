from __future__ import annotations
import os, json
from decimal import Decimal
from typing import Dict, Any, Optional, AsyncGenerator
import datetime

from pydantic import BaseModel
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.backend.core.prompts import RESPONSE_SYSTEM_PROMPT
from app.backend.core.graph import GraphState


def json_converter(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


llm = AzureChatOpenAI(
    api_key=os.getenv("AZURE_GPT5_CHAT_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_GPT5_CHAT_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_GPT5_CHAT_API_VERSION"),
)
RESPONSE_PROMPT = ChatPromptTemplate.from_template(
    """
    {system}

    The user asked the following question:
    {user_msg}

    The database returned the following result:
    {result}

    Please provide a natural language response to the user's question based on the database result.
    """
)


def generate_response(state: GraphState) -> Dict[str, Any]:
    """Generate text."""
    msg = RESPONSE_PROMPT.format(
        system=RESPONSE_SYSTEM_PROMPT,
        user_msg=state.user_msg,
        result=state.execution_result,
    )
    resp = llm.invoke(msg)
    return {"result": resp.content.strip()}
