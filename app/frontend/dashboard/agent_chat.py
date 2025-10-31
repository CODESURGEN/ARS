from __future__ import annotations
import os
import json
import time
import datetime
import textwrap
from typing import Dict, Generator, Optional
import requests
import streamlit as st
from htbuilder.units import rem
from htbuilder import div, styles


def display_agent_chat():
    """Chat UI"""
    base_url = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
    min_gap_s = 3
    title = "Agent Assistant"

    suggestions: Dict[str, str] = {
        ":blue[:material/psychology:] PSP mix by count": "What is the distribution of Payment Method across recent orders?",
        ":green[:material/insights:] Top vendors by revenue": "Which Vendor Name generated the highest Total Purchased in the last 7 days?",
        ":orange[:material/trending_up:] Margin by payment method": "Compare margin_profit by Payment Method and summarize insights.",
        ":violet[:material/swap_horizontal_circle:] Settlements vs gross": "How do settlement_amount and gross_amount differ across currencies?",
        ":red[:material/currency_exchange:] Currency impact": "Does conversion_rate correlate with margin_profit? Explain briefly.",
    }

    disclaimer_md = textwrap.dedent(
        """
        This chatbot may produce inaccurate or biased content. Do not share
        sensitive or regulated data. You are responsible for verifying outputs
        before use in production.
        """
    )

    def _init_state():
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "initial_question" not in st.session_state:
            st.session_state.initial_question = None
        if "selected_suggestion" not in st.session_state:
            st.session_state.selected_suggestion = None
        if "prev_question_ts" not in st.session_state:
            st.session_state.prev_question_ts = datetime.datetime.fromtimestamp(0)

    def _rate_limit():
        now = datetime.datetime.now()
        delta = now - st.session_state.prev_question_ts
        if delta.total_seconds() < min_gap_s:
            time.sleep(min_gap_s - delta.total_seconds())
        st.session_state.prev_question_ts = datetime.datetime.now()

    @st.dialog("Legal disclaimer")
    def show_disclaimer_dialog():
        st.caption(disclaimer_md)


    def sse_stream(prompt: str) -> Generator[str, None, None]:
        """SSE"""
        url = f"{base_url}/chat"
        headers = {"Accept": "text/event-stream"}
        payload = {"message": prompt}
        acc = ""
        try:
            with requests.post(url, json=payload, headers=headers, stream=True, timeout=300) as resp:
                resp.raise_for_status()
                for raw in resp.iter_lines(decode_unicode=True):
                    if not raw:
                        continue
                    if not raw.startswith("data: "):
                        continue
                    payload_str = raw[6:]
                    try:
                        data = json.loads(payload_str)
                    except Exception:
                        if payload_str.strip() == "[DONE]":
                            break
                        continue
                    if data.get("data") == "[DONE]":
                        break
                    if "delta" in data and data["delta"]:
                        acc += data["delta"]
                        yield data["delta"]
                    elif "result" in data and data["result"]:
                        yield data["result"]
                    elif data.get("type") == "error":
                        err = data.get("message") or "unknown error"
                        yield f"\n\n**Error:** {err}"
                        break
        except Exception as e:
            yield f"**Request failed:** {e}"

    _init_state()


    col_left, col_center, col_right = st.columns([1, 2, 1])

    with col_center:
        title_row = st.container(horizontal=True, vertical_alignment="bottom")
        with title_row:
            st.title(title, anchor=False, width="stretch")

            def clear_conversation():
                st.session_state.messages = []
                st.session_state.initial_question = None
                st.session_state.selected_suggestion = None

            st.button("Clear Conversation", icon=":material/refresh:", on_click=clear_conversation)

    user_just_asked_initial_question = bool(st.session_state.get("initial_question"))
    user_just_clicked_suggestion = bool(st.session_state.get("selected_suggestion"))
    user_first_interaction = user_just_asked_initial_question or user_just_clicked_suggestion
    has_history = len(st.session_state.messages) > 0

    if not user_first_interaction and not has_history:
        st.session_state.messages = []

        with col_center:
            with st.container():
                st.chat_input("Ask a question...", key="initial_question")
                selected = st.pills(
                    label="Examples",
                    label_visibility="collapsed",
                    options=suggestions.keys(),
                    key="selected_suggestion",
                )

        with col_center:
            st.button(
                "&nbsp;:small[:gray[:material/balance: Legal disclaimer]]",
                type="tertiary",
                on_click=show_disclaimer_dialog,
            )
        st.stop()

    

    for i, message in enumerate(st.session_state.messages):
        with col_center:
            with st.chat_message(message["role"]):
                if message["role"] == "assistant":
                    st.container()
                st.markdown(message["content"])

    user_message: Optional[str] = st.chat_input("Ask a follow-up...")
    if not user_message:
        if user_just_asked_initial_question:
            user_message = st.session_state.initial_question
        if user_just_clicked_suggestion:
            user_message = suggestions[st.session_state.selected_suggestion]

    if user_message:
        user_message = user_message.replace("$", r"\$")

        with col_center:
            with st.chat_message("user"):
                st.text(user_message)

        with col_center:
            with st.chat_message("assistant"):
                with st.spinner("Waiting..."):
                    _rate_limit()
                    with st.container():
                        response_text = st.write_stream(sse_stream(user_message))

                    st.session_state.messages.append({"role": "user", "content": user_message})
                    st.session_state.messages.append({"role": "assistant", "content": response_text})

    


