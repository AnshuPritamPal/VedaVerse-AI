"""Chat history, welcome prompts, input handling, and API submissions."""

from html import escape as html_escape

import streamlit as st

from frontend import api_client
from frontend.api_client import APIError

from .assets import EMBLEM_PATH, data_uri, themed_iskcon_logo
from .components import html
from .references import show_references
from .sidebar import handle_api_error


SUGGESTIONS = [
    (":material/local_fire_department:", "How can I control anger?"),
    (":material/explore:", "What is the purpose of life?"),
    (":material/self_improvement:", "How do I find inner peace?"),
    (":material/autorenew:", "What is karma?"),
]


def _render_welcome() -> None:
    user = st.session_state.current_user or {}
    name = html_escape(user.get("username", ""))
    greeting = f"Hare Kṛṣṇa, {name}" if name else "Hare Kṛṣṇa"
    html(f"""
    <div class="welcome">
        <img class="welcome-emblem" src="{data_uri('krishna_arjuna.png')}" alt="Kṛṣṇa instructing Arjuna">
        <div class="welcome-title">{greeting}</div>
        <div class="welcome-subtitle">What would you like to understand from the Bhagavad-gītā today?</div>
    </div>
    """)
    with st.container(key="suggestions"):
        for row in (SUGGESTIONS[:2], SUGGESTIONS[2:]):
            with st.container(horizontal=True, gap="small"):
                for icon, suggestion in row:
                    if st.button(suggestion, key=f"suggestion_{suggestion}", icon=icon, width="stretch"):
                        st.session_state.pending_question = suggestion
                        st.rerun()
    html(f"""
    <div class="welcome-source">
        <img class="welcome-source-portrait" src="{data_uri('prabhupada.jpg')}"
             alt="A.C. Bhaktivedanta Swami Prabhupada">
        <div>
            Answers are grounded in <em>Bhagavad-gītā As It Is</em> by
            His Divine Grace A.C. Bhaktivedanta Swami Prabhupāda,
            Founder-Ācārya of ISKCON.
        </div>
        {themed_iskcon_logo("welcome-source-logo")}
    </div>
    """)


def _render_message(message: dict, message_index: int) -> None:
    if message["role"] == "user":
        with st.chat_message("user"):
            st.markdown(message["content"])
        return
    with st.chat_message("assistant", avatar=EMBLEM_PATH):
        st.markdown(message["content"])
        show_references(
            message.get("display_items", []), message.get("verses", []),
            message_key=f"{st.session_state.current_conversation_id}_history_{message_index}",
        )


def _scroll_to_latest_question() -> None:
    """Bring the newest question to the top of the view, as chat apps do."""
    with st.container(key=f"scroll_helper_{len(st.session_state.messages)}"):
        st.iframe("""
    <script>
    const doc = window.parent.document;
    const questions = doc.querySelectorAll('[data-testid="stChatMessageContent"][aria-label="Chat message from user"]');
    const latest = questions[questions.length - 1];
    if (latest) latest.closest('[data-testid="stChatMessage"]').scrollIntoView({block: 'start', behavior: 'smooth'});
    </script>
    """, height=1)


def _answer(question: str) -> None:
    """Show a thinking indicator under the already-visible question, then fetch the answer."""
    with st.chat_message("assistant", avatar=EMBLEM_PATH):
        html("""
        <div class="thinking" role="status" aria-live="polite">
            <span class="thinking-dots" aria-hidden="true"><i></i><i></i><i></i></span>
            <span class="thinking-text">Contemplating your question</span>
        </div>
        """)
    _scroll_to_latest_question()
    try:
        response = api_client.send_message(
            st.session_state.access_token,
            st.session_state.current_conversation_id,
            question,
        )
        st.session_state.messages.append({
            "role": response["role"], "content": response["content"],
            "references": response.get("references", []),
            "verses": response.get("verses", []),
            "display_items": response.get("display_items", []),
        })
        # The first question names the conversation; refresh so the sidebar shows it.
        st.session_state.conversations = api_client.get_conversations(st.session_state.access_token)
    except APIError as exc:
        handle_api_error(exc)
        if exc.status_code not in (401, 404):
            st.info("Your question was saved. Reload this conversation to check its history.")
        return
    st.session_state.scroll_to_question = True
    st.rerun()


def take_question() -> str:
    """Read a submitted question and make sure it has a conversation.

    Runs before the sidebar is drawn so a brand-new chat is listed, under its
    question, while the answer is still being prepared.
    """
    question = st.chat_input(
        "Ask anything about life, spirituality, or the Bhagavad-gītā…",
        submit_mode="disable",
    )
    if st.session_state.pending_question:
        question = st.session_state.pending_question
        st.session_state.pending_question = None
    question = (question or "").strip()
    if not question:
        return ""

    if not st.session_state.current_conversation_id:
        try:
            conversation = api_client.create_conversation(st.session_state.access_token)
        except APIError as exc:
            handle_api_error(exc)
            return ""
        # The backend names the conversation from this question; show it right away.
        st.session_state.conversations.insert(0, {**conversation, "title": question})
        st.session_state.current_conversation_id = conversation["id"]
        st.session_state.messages = []

    # Show the question straight away; the answer appears below it once ready.
    st.session_state.messages.append({"role": "user", "content": question})
    return question


def render_chat(question: str = "") -> None:
    if not st.session_state.messages:
        _render_welcome()
        return
    for message_index, message in enumerate(st.session_state.messages):
        _render_message(message, message_index)

    if question:
        _answer(question)
    elif st.session_state.pop("scroll_to_question", False):
        _scroll_to_latest_question()
