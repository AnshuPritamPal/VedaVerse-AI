"""Conversation loading and sidebar navigation."""

import streamlit as st

from frontend import api_client
from frontend.api_client import APIError

from .components import html


def load_conversation(conversation_id) -> None:
    stored = api_client.get_messages(st.session_state.access_token, conversation_id)
    st.session_state.current_conversation_id = conversation_id
    st.session_state.messages = [
        {"role": item["role"], "content": item["content"],
         "references": item.get("references", []), "verses": item.get("verses", []),
         "display_items": item.get("display_items", [])} for item in stored
    ]


def refresh_conversations() -> None:
    st.session_state.conversations = api_client.get_conversations(st.session_state.access_token)
    ids = {item["id"] for item in st.session_state.conversations}
    current_id = st.session_state.current_conversation_id
    if current_id and current_id not in ids:
        st.session_state.current_conversation_id = None
        st.session_state.messages = []
    if not st.session_state.current_conversation_id and st.session_state.conversations:
        load_conversation(st.session_state.conversations[0]["id"])


def handle_api_error(exc, refresh=refresh_conversations) -> None:
    if exc.status_code == 401:
        from .auth import clear_authentication
        clear_authentication()
        st.session_state.auth_notice = "Your session has expired. Please log in again."
        st.rerun()
    if exc.status_code == 404:
        try:
            refresh()
        except APIError:
            st.session_state.current_conversation_id = None
            st.session_state.messages = []
        st.info("That conversation is no longer available. Choose another conversation.")
    elif exc.status_code == 422:
        st.error("Please check the submitted information and try again.")
    elif exc.status_code is None:
        st.error("Unable to connect to VedaVerse backend. Please make sure the backend is running.")
    elif exc.status_code == 500:
        st.error("Something went wrong on the server. Please try again.")
    else:
        st.error("The backend could not complete the request. Please try again.")


def render_sidebar() -> None:
    with st.sidebar:
        html("""
        <div class="sidebar-brand">
            <div class="sidebar-brand-mark">&#x1FAB7;</div>
            <div class="sidebar-brand-title">VedaVerse AI</div>
            <div class="sidebar-brand-subtitle">Wisdom for your journey</div>
        </div>
        """)
        st.divider()
        if st.button("New conversation", type="primary", use_container_width=True):
            try:
                conversation = api_client.create_conversation(st.session_state.access_token)
                st.session_state.conversations.insert(0, conversation)
                load_conversation(conversation["id"])
                st.session_state.pending_question = None
                st.rerun()
            except APIError as exc:
                handle_api_error(exc)
        st.markdown("### Your conversations")
        if not st.session_state.conversations:
            st.caption("Your saved conversations will appear here.")
        for conversation in st.session_state.conversations:
            is_selected = conversation["id"] == st.session_state.current_conversation_id
            title = conversation.get("title", "Conversation")
            if st.button(
                title, key=f"conversation_{conversation['id']}",
                type="primary" if is_selected else "secondary",
                use_container_width=True, help=title,
            ):
                try:
                    load_conversation(conversation["id"])
                    st.rerun()
                except APIError as exc:
                    handle_api_error(exc)
        st.divider()
        user = st.session_state.current_user or {}
        st.caption(f"Signed in as {user.get('username', '')}")
        st.markdown("### About VedaVerse")
        st.caption("Explore spiritual wisdom through scripture-based answers and thoughtful explanations.")
