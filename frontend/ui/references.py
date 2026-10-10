"""Scripture reference cards and complete verse details."""

from html import escape as html_escape

import streamlit as st

from .components import as_text


def show_references(display_items, verses=None, message_key="latest") -> None:
    """Render references with independently expandable complete shlokas."""
    if not display_items and verses:
        # Adapt older saved verse data to the current reference-card shape.
        display_items = []
        for verse in verses:
            reference = verse.get("reference", "Scripture")
            full = {
                "sanskrit": verse.get("sanskrit", ""),
                "transliteration": verse.get("transliteration", ""),
                "word_meanings": verse.get("word_meanings", []),
                "translation": verse.get("text", ""),
                "purport": verse.get("purport", ""),
            }
            display_items.append({
                "reference": reference, "source_type": "translation",
                "display_text": verse.get("text", ""), "full_verse": full,
            })
            if verse.get("purport"):
                display_items.append({
                    "reference": reference, "source_type": "purport",
                    "display_text": verse["purport"], "full_verse": full,
                })

    if not display_items:
        return

    grouped_items = []
    items_by_reference = {}
    for item in display_items:
        reference = item.get("reference") or item.get("heading") or "Bhagavad Gita"
        if reference not in items_by_reference:
            items_by_reference[reference] = {"reference": reference, "items": []}
            grouped_items.append(items_by_reference[reference])
        items_by_reference[reference]["items"].append(item)

    with st.expander("References", expanded=False):
        for index, group in enumerate(grouped_items):
            reference = group["reference"]
            with st.container(border=True, key=f"ref_{message_key}_{index}"):
                st.markdown(f"**{reference}**")
                displayed_passages = set()
                for item in group["items"]:
                    passage = item.get("display_text", "")
                    content_type = str(
                        item.get("source_type") or item.get("content_type") or "retrieved passage"
                    ).lower()
                    label = (
                        "Translation" if "translation" in content_type
                        else "Purport" if "purport" in content_type
                        else "Retrieved passage"
                    )
                    passage_key = (label, passage)
                    if passage and passage_key not in displayed_passages:
                        st.markdown(f"**{reference} {label}**")
                        st.markdown(passage)
                        displayed_passages.add(passage_key)

                full = group["items"][0].get("full_verse", {})
                toggle_key = f"complete_shloka_open_{message_key}_{index}"
                if toggle_key not in st.session_state:
                    st.session_state[toggle_key] = False
                is_open = st.session_state[toggle_key]
                if st.button(
                    f"Complete Shloka {'▲' if is_open else '▼'}",
                    key=f"complete_shloka_button_{message_key}_{index}",
                    width="stretch",
                ):
                    is_open = not is_open
                    st.session_state[toggle_key] = is_open
                if is_open:
                    st.markdown("**Complete Shloka / Verse Details**")
                    st.markdown("**Sanskrit**")
                    st.markdown(as_text(full.get("sanskrit")))
                    st.markdown("**Transliteration**")
                    st.write(as_text(full.get("transliteration")))
                    st.markdown("**Word-to-word**")
                    meanings = full.get("word_meanings", [])
                    if isinstance(meanings, list):
                        for meaning in meanings:
                            if isinstance(meaning, dict):
                                st.write(
                                    f"- **{meaning.get('word', '')}** — "
                                    f"{meaning.get('meaning', '')}"
                                )
                            else:
                                st.write(f"- {meaning}")
                    else:
                        st.write(as_text(meanings))
                    st.markdown(f"**{reference} Translation**")
                    st.write(as_text(full.get("translation")))
                    st.markdown(f"**{reference} Purport**")
                    purport = html_escape(as_text(full.get("purport")))
                    st.markdown(
                        '<div class="purport-paper"><div class="purport-text">'
                        f'{purport}</div></div>',
                        unsafe_allow_html=True,
                    )
