from __future__ import annotations
import os, json
from typing import Dict, Any, Optional
from pydantic import BaseModel
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.backend.core.prompts import SYSTEM_PROMPT, FEWSHOTS
from app.backend.core.graph import GraphState
from dotenv import load_dotenv

load_dotenv()

llm = AzureChatOpenAI(
    api_key=os.getenv("AZURE_GPT5_CHAT_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_GPT5_CHAT_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_GPT5_CHAT_API_VERSION"),
)

examples = "nn".join([f"User: {ex['user']}nSQL:n{ex['sql'].strip()}" for ex in FEWSHOTS])

SQL_PROMPT = ChatPromptTemplate.from_template(
    """
    {system}

    You will receive:
    - The user's request
    - JSON schema of available tables/columns

    Based on the user's request and the schema, generate a SQL query to answer the user's question.
    Produce **only** SQL in a fenced block. Use qualified schema.table, avoid SELECT *.

    FEW-SHOTS:
    {examples}

    USER:
    {user}

    SCHEMA (JSON):
    {schema_json}
    """
)


def generate_sql(state: GraphState) -> Dict[str, Any]:
    """Generates SQL."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
    schema_path = os.path.join(project_root, 'app', 'data', 'schema.json')
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    msg = SQL_PROMPT.format(
        system=SYSTEM_PROMPT,
        examples=examples,
        user=state.user_msg,
        schema_json=json.dumps(schema, indent=2),
    )
    resp = llm.invoke(msg)
    content = resp.content.strip()

    sql = ""
    if "```" in content and "select" in content.lower():
        sql_part = content.split("```")
        sql = "n".join([s for s in sql_part if "select" in s.lower()])
        if "sql" in sql[:10]:
             sql = sql.replace("sql","").strip()

    if not sql:
        return {"error": "Failed to generate SQL."}

    return {"sql": sql}
