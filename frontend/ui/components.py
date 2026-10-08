"""Small reusable rendering helpers shared by frontend modules."""

import streamlit as st


def html(markup: str) -> None:
    """Render compact HTML without Markdown treating indented lines as code."""
    cleaned = " ".join(line.strip() for line in markup.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)


def as_text(value) -> str:
    """Accept plain text or the dataset's {text: ...} representation."""
    if isinstance(value, dict):
        return str(value.get("text", ""))
    return str(value or "")
