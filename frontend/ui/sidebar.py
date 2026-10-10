"""Conversation loading and sidebar navigation."""

from datetime import datetime, timedelta
from html import escape as html_escape

import streamlit as st

from frontend import api_client
from frontend.api_client import APIError

from .assets import data_uri, themed_iskcon_logo
from .auth import clear_authentication
from .components import html, theme_toggle


DEFAULT_TITLE = "New Conversation"


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
        start_new_chat()


def start_new_chat() -> None:
    """Show an empty chat; the conversation is created when the first question is sent."""
    st.session_state.current_conversation_id = None
    st.session_state.messages = []
    st.session_state.pending_question = None


def handle_api_error(exc, refresh=refresh_conversations) -> None:
    if exc.status_code == 401:
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


def _date_group(updated_at: str) -> str:
    try:
        moment = datetime.fromisoformat(str(updated_at).replace("Z", "+00:00")).astimezone()
    except ValueError:
        return "Older"
    today = datetime.now().astimezone().date()
    day = moment.date()
    if day >= today:
        return "Today"
    if day == today - timedelta(days=1):
        return "Yesterday"
    if day > today - timedelta(days=7):
        return "Previous 7 days"
    if day > today - timedelta(days=30):
        return "Previous 30 days"
    return "Older"


def _delete_conversation(conversation_id: str) -> None:
    try:
        api_client.delete_conversation(st.session_state.access_token, conversation_id)
    except APIError as exc:
        if exc.status_code != 404:
            handle_api_error(exc)
            return
    st.session_state.conversations = [
        item for item in st.session_state.conversations if item["id"] != conversation_id
    ]
    if st.session_state.current_conversation_id == conversation_id:
        start_new_chat()
    st.rerun()


def _render_conversation_list() -> None:
    if not st.session_state.conversations:
        st.caption("Your conversations will appear here.")
        return
    current_group = None
    for conversation in st.session_state.conversations:
        group = _date_group(conversation.get("updated_at", ""))
        if group != current_group:
            html(f'<div class="conv-group">{group}</div>')
            current_group = group
        conversation_id = conversation["id"]
        is_selected = conversation_id == st.session_state.current_conversation_id
        title = conversation.get("title") or DEFAULT_TITLE
        if title == DEFAULT_TITLE:
            title = "New chat"
        with st.container(key=f"conv_row_{conversation_id}", horizontal=True, gap=None,
                          vertical_alignment="center"):
            if st.button(
                title, key=f"conversation_{conversation_id}",
                type="primary" if is_selected else "tertiary",
                width="stretch", help=title,
            ) and not is_selected:
                try:
                    load_conversation(conversation_id)
                    st.rerun()
                except APIError as exc:
                    handle_api_error(exc)
            with st.popover("", icon=":material/more_horiz:", type="tertiary",
                            help="Conversation options"):
                if st.button("Delete conversation", key=f"delete_{conversation_id}",
                             icon=":material/delete:", type="tertiary"):
                    _delete_conversation(conversation_id)


def render_sidebar() -> None:
    with st.sidebar:
        html(f"""
        <div class="sidebar-brand">
            <img class="sidebar-brand-mark" src="{data_uri('krishna_arjuna.png')}" alt="">
            <div>
                <div class="sidebar-brand-title">VedaVerse AI</div>
                <div class="sidebar-brand-subtitle">Wisdom of the Bhagavad-gītā</div>
            </div>
        </div>
        """)
        if st.button("New chat", key="new_chat", icon=":material/edit_square:", width="stretch"):
            start_new_chat()
            st.rerun()

        with st.container(key="conversation_list"):
            _render_conversation_list()

        with st.container(key="sidebar_footer"):
            html(f"""
            <div class="source-card">
                <img class="source-portrait" src="{data_uri('prabhupada.jpg')}"
                     alt="A.C. Bhaktivedanta Swami Prabhupada">
                <div class="source-copy">
                    <div class="source-title">Bhagavad-gītā<br>As It Is</div>
                    <div class="source-sub">Śrīla Prabhupāda · Founder-Ācārya of ISKCON</div>
                </div>
                {themed_iskcon_logo("source-logo")}
            </div>
            """)
            user = st.session_state.current_user or {}
            username = html_escape(user.get("username", ""))
            initial = username[:1].upper() or "?"
            html(f"""
            <div class="account-chip">
                <span class="account-avatar">{initial}</span>
                <span class="account-name">{username}</span>
            </div>
            """)
            with st.container(horizontal=True, gap="small"):
                theme_toggle("sidebar_theme_toggle", width="stretch")
                st.button("Log out", key="logout", icon=":material/logout:",
                          on_click=clear_authentication, width="stretch")
