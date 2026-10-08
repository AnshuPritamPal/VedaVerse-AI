"""Login, registration, logout, and authentication notices."""

import streamlit as st

from frontend import api_client
from frontend.api_client import APIError

from .components import html


def clear_authentication() -> None:
    for key, value in {
        "access_token": None, "current_user": None, "conversations": [],
        "current_conversation_id": None, "messages": [], "pending_question": None,
    }.items():
        st.session_state[key] = value


def render_navbar(logged_in: bool = False) -> bool:
    columns = st.columns([6, 1, 1] if logged_in else [6, 1])
    with columns[0]:
        html('<span class="navbar-marker" aria-hidden="true"></span><div class="navbar-brand">VedaVerse AI</div>')
    with columns[1]:
        st.toggle("Dark mode", key="dark_mode")
    logout = False
    if logged_in:
        with columns[2]:
            logout = st.button("Logout", key="navbar_logout", use_container_width=True)
    st.divider()
    return logout


def registration_error_messages(exc):
    """Convert API validation details into safe field-specific UI messages."""
    if exc.status_code == 409:
        detail = str(exc.detail or "").lower()
        if "email" in detail:
            return {"email": ["This email is already registered. Please use another email or log in."]}, None
        if "username" in detail:
            return {"username": ["This username is already taken. Please choose another."]}, None
        return {}, "This email or username is already registered. Try another email/username or log in."
    if exc.status_code == 422:
        field_errors = {"email": [], "username": [], "password": []}
        details = exc.detail if isinstance(exc.detail, list) else []
        for error in details:
            location = error.get("loc", []) if isinstance(error, dict) else []
            field = next((part for part in location if part in field_errors), None)
            if not field:
                continue
            message = str(error.get("msg", ""))
            error_type = str(error.get("type", ""))
            if field == "email":
                message = "Please enter a valid email address."
            elif field == "username":
                if "pattern" in error_type:
                    message = "Username can contain only letters, numbers and underscores."
                elif "too_short" in error_type or "min_length" in error_type:
                    message = "Username must be at least 3 characters long."
                elif "too_long" in error_type or "max_length" in error_type:
                    message = "Username must be no more than 30 characters long."
                else:
                    message = "Please enter a valid username."
            elif "at least one letter and one number" in message.lower():
                message = "Password must contain at least one letter and one number."
            elif "too_short" in error_type or "min_length" in error_type:
                message = "Password must be at least 8 characters long."
            elif "too_long" in error_type or "max_length" in error_type:
                message = "Password must be no more than 128 characters long."
            else:
                message = "Please enter a valid password."
            field_errors[field].append(message)
        return {key: value for key, value in field_errors.items() if value}, None
    if exc.status_code is None:
        return {}, "Unable to connect to VedaVerse backend. Please make sure the backend is running."
    if exc.status_code == 500:
        return {}, "Something went wrong on the server. Please try again."
    if exc.status_code == 503:
        return {}, "VedaVerse backend is temporarily unavailable. Please try again."
    return {}, "Unable to create the account. Please check your details and try again."


def render_authentication(refresh_conversations) -> None:
    with st.container(border=True):
        html('<span class="auth-card-marker" aria-hidden="true"></span>')
        st.title("VedaVerse AI")
        st.markdown(
            '<p class="auth-subtitle">Wisdom for your journey through the Bhagavad Gita.</p>',
            unsafe_allow_html=True,
        )
        if st.session_state.auth_notice:
            st.warning(st.session_state.auth_notice)
            st.session_state.auth_notice = None
        login_tab, register_tab = st.tabs(["Login", "Register"])
        with login_tab:
            with st.form("login_form"):
                identifier = st.text_input("Username or email", placeholder="Enter your username or email")
                st.caption("Use your registered username or email address.")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                login_error_slot = st.empty()
                submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
            if submitted:
                try:
                    credentials = api_client.login(identifier, password)
                    token = credentials["access_token"]
                    user = api_client.get_me(token)
                    st.session_state.access_token = token
                    st.session_state.current_user = user
                    refresh_conversations()
                    st.rerun()
                except APIError as exc:
                    messages = {
                        401: "Invalid username/email or password.",
                        None: "Unable to connect to VedaVerse backend. Please make sure the backend is running.",
                        500: "Something went wrong on the server. Please try again.",
                        503: "VedaVerse backend is temporarily unavailable. Please try again.",
                        422: "Enter a valid username/email and password.",
                    }
                    login_error_slot.error(messages.get(exc.status_code, "Unable to log in. Please try again."))
        with register_tab:
            with st.form("register_form"):
                email = st.text_input("Email", placeholder="you@example.com")
                email_error_slot = st.empty()
                username = st.text_input("Username", placeholder="Choose a username")
                username_error_slot = st.empty()
                new_password = st.text_input("Password", type="password", placeholder="At least 8 characters")
                password_error_slot = st.empty()
                registration_error_slot = st.empty()
                submitted = st.form_submit_button("Create account", type="primary", use_container_width=True)
            if submitted:
                try:
                    api_client.register(email, username, new_password)
                    st.success("Account created. Log in to continue.")
                except APIError as exc:
                    field_errors, general_error = registration_error_messages(exc)
                    for message in field_errors.get("email", []):
                        email_error_slot.error(message)
                    for message in field_errors.get("username", []):
                        username_error_slot.error(message)
                    for message in field_errors.get("password", []):
                        password_error_slot.error(message)
                    if general_error:
                        registration_error_slot.error(general_error)
