"""Login, registration, logout, and authentication notices."""

import streamlit as st

from frontend import api_client
from frontend.api_client import APIError

from .assets import data_uri, iskcon_logo, themed_iskcon_logo
from .components import html, theme_toggle


def clear_authentication() -> None:
    for key, value in {
        "access_token": None, "current_user": None, "conversations": [],
        "current_conversation_id": None, "messages": [], "pending_question": None,
    }.items():
        st.session_state[key] = value


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


def _render_source_panel() -> None:
    """Left half of the auth page: where every answer comes from."""
    html(f"""
    <div class="auth-hero">
        <figure class="auth-portrait">
            <img src="{data_uri('prabhupada.jpg')}" alt="His Divine Grace A.C. Bhaktivedanta Swami Prabhupada">
        </figure>
        <div class="auth-hero-copy">
            <div class="auth-hero-eyebrow">Every answer is drawn from</div>
            <div class="auth-hero-title">Bhagavad-gītā As It Is</div>
            <div class="auth-hero-author">
                by His Divine Grace <strong>A.C. Bhaktivedanta Swami Prabhupāda</strong>
            </div>
            <div class="auth-hero-iskcon">
                <img src="{iskcon_logo('#FFF4E6')}" alt="ISKCON logo">
                <span>Founder-Ācārya of the International Society<br>for Krishna Consciousness</span>
            </div>
        </div>
    </div>
    """)


def _login_error(exc: APIError) -> str:
    messages = {
        401: "Invalid username/email or password.",
        None: "Unable to connect to VedaVerse backend. Please make sure the backend is running.",
        500: "Something went wrong on the server. Please try again.",
        503: "VedaVerse backend is temporarily unavailable. Please try again.",
        422: "Enter a valid username/email and password.",
    }
    return messages.get(exc.status_code, "Unable to log in. Please try again.")


def _render_login_form(refresh_conversations) -> None:
    with st.form("login_form", border=False):
        identifier = st.text_input(
            "Username or email", key="login_identifier",
            placeholder="Enter your username or email",
        )
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        error_slot = st.empty()
        submitted = st.form_submit_button("Log in", type="primary", width="stretch")
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
            error_slot.error(_login_error(exc))


def _render_register_form() -> None:
    with st.form("register_form", border=False):
        email = st.text_input("Email", placeholder="you@example.com")
        email_error_slot = st.empty()
        username = st.text_input("Username", placeholder="Letters, numbers and underscores")
        username_error_slot = st.empty()
        new_password = st.text_input("Password", type="password",
                                     placeholder="At least 8 characters, with a number")
        password_error_slot = st.empty()
        registration_error_slot = st.empty()
        submitted = st.form_submit_button("Create account", type="primary", width="stretch")
    if submitted:
        try:
            api_client.register(email, username, new_password)
            # Switch to the login form with the new username filled in.
            st.session_state.auth_switch_to_login = username
            st.rerun()
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


def render_authentication(refresh_conversations) -> None:
    """Single-screen, non-scrolling login/registration page."""
    new_username = st.session_state.pop("auth_switch_to_login", None)
    if new_username is not None:
        st.session_state.auth_mode = "Log in"
        st.session_state.login_identifier = new_username
        st.session_state.auth_success = "Account created. Log in to continue."
    st.session_state.setdefault("auth_mode", "Log in")

    html('<span class="vv-marker vv-auth-page" aria-hidden="true"></span>')
    source_column, form_column = st.columns([1.1, 1], gap="small")
    with source_column:
        _render_source_panel()
    with form_column:
        with st.container(key="auth_theme"):
            theme_toggle("auth_theme_toggle")
        with st.container(key="auth_panel"):
            html(f"""
            <div class="auth-brand">
                <img class="auth-brand-mark" src="{data_uri('krishna_arjuna.png')}" alt="">
                <div class="auth-brand-title">VedaVerse AI</div>
                <div class="auth-brand-subtitle">Ask life's questions. Receive answers from the Gītā.</div>
                <div class="auth-mobile-source">
                    <img class="source-portrait" src="{data_uri('prabhupada.jpg')}" alt="">
                    <span>From <em>Bhagavad-gītā As It Is</em> by Śrīla Prabhupāda</span>
                    {themed_iskcon_logo("source-logo")}
                </div>
            </div>
            """)
            if st.session_state.auth_notice:
                st.warning(st.session_state.auth_notice)
                st.session_state.auth_notice = None
            if st.session_state.get("auth_success"):
                st.success(st.session_state.pop("auth_success"))
            mode = st.segmented_control(
                "Account", ["Log in", "Sign up"], key="auth_mode",
                required=True, label_visibility="collapsed", width="stretch",
            )
            if mode == "Sign up":
                _render_register_form()
            else:
                _render_login_form(refresh_conversations)
