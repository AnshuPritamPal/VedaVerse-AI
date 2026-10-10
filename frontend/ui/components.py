"""Small reusable rendering helpers shared by frontend modules."""

import streamlit as st


def html(markup: str) -> None:
    """Render compact HTML without Markdown treating indented lines as code."""
    cleaned = " ".join(line.strip() for line in markup.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)


def _flip_theme() -> None:
    st.session_state.dark_mode = not st.session_state.dark_mode


def theme_toggle(key: str, width="content") -> None:
    """One button that switches between light and dark mode."""
    dark = st.session_state.dark_mode
    st.button(
        "Light mode" if dark else "Dark mode",
        key=key,
        icon=":material/light_mode:" if dark else ":material/dark_mode:",
        on_click=_flip_theme,
        help="Switch to light mode" if dark else "Switch to dark mode",
        width=width,
    )


def as_text(value) -> str:
    """Accept plain text or the dataset's {text: ...} representation."""
    if isinstance(value, dict):
        return str(value.get("text", ""))
    return str(value or "")
