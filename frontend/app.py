"""Streamlit application entry point and frontend module orchestrator."""

import sys
from pathlib import Path

# Streamlit may put only the script directory on sys.path when launched from
# inside frontend/. Add the project root so package imports work from either
# the repository root or the frontend directory.
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st

from frontend import api_client
from frontend.api_client import APIError

from frontend.ui import auth, chat, sidebar, styles
from frontend.ui.components import html


st.set_page_config(
    page_title="VedaVerse AI",
    page_icon="🪷",
    layout="wide",
    initial_sidebar_state="expanded",
)

for key, default in {
    "dark_mode": False,
    "access_token": None,
    "current_user": None,
    "conversations": [],
    "current_conversation_id": None,
    "messages": [],
    "pending_question": None,
    "auth_notice": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

styles.apply_styles(st.session_state.dark_mode)

if auth.render_navbar(logged_in=bool(st.session_state.access_token)):
    auth.clear_authentication()
    st.rerun()

if not st.session_state.access_token:
    auth.render_authentication(sidebar.refresh_conversations)
    st.stop()

if st.session_state.current_user is None:
    try:
        st.session_state.current_user = api_client.get_me(st.session_state.access_token)
        sidebar.refresh_conversations()
    except APIError as exc:
        sidebar.handle_api_error(exc)

sidebar.render_sidebar()
chat.render_chat()
html('<div class="footer">🪷 Inspired by the timeless wisdom of the scriptures</div>')
