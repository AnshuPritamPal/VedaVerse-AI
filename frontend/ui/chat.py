"""Chat history, welcome prompts, input handling, and API submissions."""

import streamlit as st

from frontend import api_client
from frontend.api_client import APIError

from .components import html
from .references import show_references
from .sidebar import handle_api_error


def _render_welcome() -> None:
    html("""
    <div class="hero">
        <div class="hero-label">✦ YOUR SPIRITUAL COMPANION ✦</div>
        <div class="hero-title">Discover the wisdom within.</div>
        <div class="hero-subtitle">
            Explore timeless teachings from the scriptures and find guidance for everyday life.
        </div>
    </div>
    """)
    st.markdown("#### ✨ Explore a question")
    suggestions = [
        "🪷  How can I control anger?",
        "🌿  What is the purpose of life?",
        "🧘  How do I find inner peace?",
        "📖  What is karma?",
    ]
    col1, col2 = st.columns(2)
    for index, suggestion in enumerate(suggestions):
        with (col1 if index % 2 == 0 else col2):
            if st.button(suggestion, key=f"suggestion_{index}", use_container_width=True):
                st.session_state.pending_question = suggestion.split("  ", 1)[-1]
                st.rerun()


def _render_history() -> None:
    for message_index, message in enumerate(st.session_state.messages):
        avatar = "user" if message["role"] == "user" else "assistant"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                show_references(
                    message.get("display_items", []), message.get("verses", []),
                    message_key=f"{st.session_state.current_conversation_id}_history_{message_index}",
                )


def _scroll_to_submitted_question() -> None:
    """Keep the viewport at the new question rather than the answer's bottom."""
    st.components.v1.html("""
    <script>
    const messages = [...window.parent.document.querySelectorAll('[data-testid="stChatMessage"]')];
    const latestQuestion = messages.reverse().find((node) => node.querySelector('[data-testid="stChatMessageAvatarUser"]'));
    if (latestQuestion) latestQuestion.scrollIntoView({block: 'start', behavior: 'instant'});
    </script>
    """, height=0)


def _send_question(question: str) -> None:
    try:
        with st.spinner("Searching the scriptures..."):
            response = api_client.send_message(
                st.session_state.access_token,
                st.session_state.current_conversation_id,
                question,
            )
        st.session_state.messages.extend([
            {"role": "user", "content": question},
            {"role": response["role"], "content": response["content"],
             "references": response.get("references", []),
             "verses": response.get("verses", []),
             "display_items": response.get("display_items", [])},
        ])
        selected_id = st.session_state.current_conversation_id
        st.session_state.conversations = api_client.get_conversations(st.session_state.access_token)
        st.session_state.current_conversation_id = selected_id
        with st.chat_message("user", avatar="user"):
            st.markdown(question)
        with st.chat_message("assistant", avatar="assistant"):
            st.markdown(response["content"])
            show_references(
                response.get("display_items", []), response.get("verses", []),
                message_key=f"{selected_id}_history_{len(st.session_state.messages) - 1}",
            )
        _scroll_to_submitted_question()
    except APIError as exc:
        handle_api_error(exc)
        if exc.status_code not in (401, 404):
            st.info("Your question may have been saved. Reload this conversation to check its history.")


def render_chat() -> None:
    question = st.chat_input("Ask anything about life, spirituality, or scriptures...")
    if st.session_state.pending_question:
        question = st.session_state.pending_question
        st.session_state.pending_question = None

    if question and not st.session_state.current_conversation_id:
        try:
            conversation = api_client.create_conversation(st.session_state.access_token)
            st.session_state.conversations.insert(0, conversation)
            st.session_state.current_conversation_id = conversation["id"]
            st.session_state.messages = []
        except APIError as exc:
            handle_api_error(exc)
            question = None

    if not st.session_state.messages:
        _render_welcome()
    _render_history()
    if question and st.session_state.current_conversation_id:
        _send_question(question)
