import streamlit as st


_CSS = r"""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&display=swap');

.stApp {
    --page-bg: #F5F5F0;
    --surface: #FFFEFA;
    --surface-soft: #F0EFE8;
    --text: #26332C;
    --text-muted: #68766D;
    --border: #DFE2D8;
    --primary: #28563F;
    --primary-hover: #1D4732;
    --accent: #B88D46;
    --sidebar-bg: #203F32;
    --sidebar-text: #F7F6EE;
    --sidebar-active-bg: #426C55;
    --sidebar-active-text: #FFFFFF;
    --user-bg: #E9F0E7;
    --assistant-bg: #FFFEFA;
    --purport-bg: #F5EEDC;
    --purport-text: #39372F;
    --purport-border: #D8C7A2;
    --error-bg: #FBE9E7;
    --error-text: #762D2A;
    --success-bg: #E8F3EA;
    --success-text: #245337;
    color-scheme: light;
    background: var(--page-bg) !important;
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
}
.stApp:has(.vv-dark) {
    --page-bg: #121A16;
    --surface: #1B2620;
    --surface-soft: #24332B;
    --text: #E9EFEA;
    --text-muted: #B2BFB6;
    --border: #39483F;
    --primary: #8FC4A3;
    --primary-hover: #A5D3B5;
    --accent: #D7B773;
    --sidebar-bg: #0F1914;
    --sidebar-text: #E9EFEA;
    --sidebar-active-bg: #D5B36C;
    --sidebar-active-text: #1B251F;
    --user-bg: #26382E;
    --assistant-bg: #1B2620;
    --purport-bg: #2D2A21;
    --purport-text: #EEE8D9;
    --purport-border: #65583D;
    --error-bg: #3A2423;
    --error-text: #FFD8D3;
    --success-bg: #20372A;
    --success-text: #D4F1DC;
    color-scheme: dark;
}
.theme-marker, .auth-card-marker, .reference-card-marker { display: none !important; }
.navbar-brand { color: var(--text); font-family: 'Playfair Display', Georgia, serif; font-size: 1.25rem; font-weight: 700; }
[data-testid="stVerticalBlockBorderWrapper"]:has(.navbar-marker):not(:has([data-testid="stVerticalBlockBorderWrapper"] .navbar-marker)) {
    margin: .2rem auto .8rem; padding: .45rem .8rem; background: var(--surface);
    border: 1px solid var(--border); border-radius: 13px;
}

[data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] {
    background: var(--page-bg) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stAppDeployButton"], [data-testid="stMainMenu"],
[data-testid="stDecoration"], #MainMenu, footer { display: none !important; }
[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"] {
    display: flex !important; visibility: visible !important;
}
[data-testid="stExpandSidebarButton"] *, [data-testid="stSidebarCollapsedControl"] * {
    color: var(--primary) !important;
}
.block-container {
    max-width: 1120px;
    padding: 1.35rem clamp(1rem, 3vw, 2.25rem) 5rem;
}

h1, h2, h3, h4 {
    color: var(--text) !important;
    font-family: 'Playfair Display', Georgia, serif !important;
    letter-spacing: -0.015em;
}
p, li, label, [data-testid="stMarkdownContainer"] { color: var(--text); }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {
    color: var(--text-muted) !important;
}
hr { border-color: var(--border) !important; }

/* Shared controls */
button[data-testid^="stBaseButton-"], [data-testid="stDownloadButton"] button {
    min-height: 2.65rem;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    background: var(--surface) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    transition: border-color .15s ease, background-color .15s ease, transform .15s ease;
}
button[data-testid^="stBaseButton-"]:hover {
    border-color: var(--accent) !important;
    background: var(--surface-soft) !important;
    color: var(--text) !important;
}
button[data-testid^="stBaseButton-"]:focus-visible,
input:focus-visible, textarea:focus-visible {
    outline: 2px solid var(--accent) !important;
    outline-offset: 2px !important;
}
button[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-primaryFormSubmit"] {
    background: var(--primary) !important;
    border-color: var(--primary) !important;
    color: #FFFFFF !important;
}
.stApp:has(.vv-dark) button[data-testid="stBaseButton-primary"],
.stApp:has(.vv-dark) button[data-testid="stBaseButton-primaryFormSubmit"] {
    color: #14231A !important;
}
.stApp:has(.vv-dark) button[data-testid="stBaseButton-primary"] *,
.stApp:has(.vv-dark) button[data-testid="stBaseButton-primaryFormSubmit"] * {
    color: #14231A !important;
}
button[data-testid="stBaseButton-primary"]:hover,
button[data-testid="stBaseButton-primaryFormSubmit"]:hover {
    background: var(--primary-hover) !important;
}
button[data-testid^="stBaseButton-"] p { color: inherit !important; white-space: normal; }

[data-testid="stTextInputField"], .stTextArea textarea, .stNumberInput input,
[data-testid="stSelectbox"] [data-baseweb="select"] > div, [data-testid="stDateInput"] input {
    min-height: 2.75rem;
    background: var(--surface) !important;
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
    border-color: var(--border) !important;
    border-radius: 9px !important;
}
[data-testid="stTextInputField"]::placeholder, .stTextArea textarea::placeholder {
    color: var(--text-muted) !important;
    -webkit-text-fill-color: var(--text-muted) !important;
    opacity: 1;
}
[data-testid="stTextInputRootElement"] button[aria-label="Show password"],
[data-testid="stTextInputRootElement"] button[aria-label="Hide password"] {
    background: var(--surface) !important;
    color: var(--text-muted) !important;
    border: 0 !important;
    border-left: 1px solid var(--border) !important;
    min-height: 2.75rem;
}
[data-testid="stTextInputRootElement"] button[aria-label="Show password"]:hover,
[data-testid="stTextInputRootElement"] button[aria-label="Hide password"]:hover {
    background: var(--surface-soft) !important;
    color: var(--text) !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label, .stCheckbox label,
.stToggle label, .stRadio label, .stNumberInput label {
    color: var(--text) !important;
    font-weight: 600;
}
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: .35rem;
    border-bottom: 1px solid var(--border);
}
[data-testid="stTabs"] button[role="tab"] {
    color: var(--text-muted) !important;
    font-weight: 600;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: var(--primary) !important;
    border-bottom-color: var(--accent) !important;
}
[data-testid="stExpander"] {
    overflow: hidden;
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * {
    color: var(--text) !important;
    font-weight: 600;
}
[data-testid="stAlert"] {
    border-radius: 10px !important;
    border: 1px solid var(--border) !important;
    background: var(--surface-soft) !important;
}
[data-testid="stAlert"][kind="error"] {
    background: var(--error-bg) !important;
    border-color: var(--error-text) !important;
}
[data-testid="stAlert"][kind="success"] {
    background: var(--success-bg) !important;
    border-color: var(--success-text) !important;
}
[data-testid="stAlert"][kind="error"] [data-testid="stMarkdownContainer"] *,
[data-testid="stAlert"][kind="error"] svg { color: var(--error-text) !important; }
[data-testid="stAlert"][kind="success"] [data-testid="stMarkdownContainer"] *,
[data-testid="stAlert"][kind="success"] svg { color: var(--success-text) !important; }
[data-testid="stAlert"] [data-testid="stMarkdownContainer"],
[data-testid="stAlert"] [data-testid="stMarkdownContainer"] * { color: var(--text) !important; }
[data-testid="stAlert"] svg { color: var(--accent) !important; }

/* Login and registration */
[data-testid="stVerticalBlockBorderWrapper"]:has(.auth-card-marker):not(:has([data-testid="stVerticalBlockBorderWrapper"] .auth-card-marker)) {
    box-sizing: border-box;
    width: min(100%, 510px);
    margin: clamp(1.5rem, 7vh, 4.5rem) auto 2rem;
    padding: clamp(1.25rem, 4vw, 2.25rem);
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    box-shadow: 0 18px 55px rgba(28, 43, 34, .09);
}
[data-testid="stVerticalBlockBorderWrapper"]:has(.auth-card-marker):not(:has([data-testid="stVerticalBlockBorderWrapper"] .auth-card-marker)) h1 { margin: 0 0 .25rem; text-align: center; font-size: clamp(1.8rem, 5vw, 2.35rem); }
.auth-subtitle { margin: 0 0 1.15rem; color: var(--text-muted); text-align: center; line-height: 1.6; }
[data-testid="stVerticalBlockBorderWrapper"]:has(.auth-card-marker):not(:has([data-testid="stVerticalBlockBorderWrapper"] .auth-card-marker)) [data-testid="stForm"] { border: 0; padding: .75rem 0 0; }
[data-testid="stVerticalBlockBorderWrapper"]:has(.auth-card-marker):not(:has([data-testid="stVerticalBlockBorderWrapper"] .auth-card-marker)) [data-testid="stFormSubmitButton"] { margin-top: .45rem; }
[data-testid="stVerticalBlockBorderWrapper"]:has(.auth-card-marker):not(:has([data-testid="stVerticalBlockBorderWrapper"] .auth-card-marker)) [data-testid="stFormSubmitButton"] button { width: 100%; }

/* Sidebar and conversations */
[data-testid="stSidebar"] {
    min-width: 270px !important;
    max-width: 310px !important;
    background: var(--sidebar-bg) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding: 1rem .8rem 1.5rem; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] p,
[data-testid="stSidebar"] span, [data-testid="stSidebar"] div,
[data-testid="stSidebar"] label, [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] * {
    color: var(--sidebar-text) !important;
}
[data-testid="stSidebar"] hr { border-color: rgba(235, 241, 233, .18) !important; }
[data-testid="stSidebar"] button[data-testid^="stBaseButton-"] {
    width: 100%;
    min-height: 2.55rem;
    justify-content: flex-start;
    text-align: left;
    white-space: normal !important;
    overflow-wrap: anywhere;
    padding: .55rem .75rem !important;
    background: rgba(255,255,255,.07) !important;
    color: var(--sidebar-text) !important;
    border: 1px solid rgba(255,255,255,.12) !important;
}
[data-testid="stSidebar"] button[data-testid^="stBaseButton-"]:hover {
    background: rgba(255,255,255,.14) !important;
    border-color: var(--accent) !important;
}
[data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] {
    background-color: rgba(255,255,255,.09) !important;
    background-image: none !important;
    color: var(--sidebar-text) !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] {
    background: var(--sidebar-active-bg) !important;
    border-color: var(--sidebar-active-bg) !important;
    color: var(--sidebar-active-text) !important;
}
[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] [data-testid="stMarkdownContainer"] *,
[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] span {
    color: var(--sidebar-active-text) !important;
}
[data-testid="stSidebar"] [data-testid="stToggle"] label { color: var(--sidebar-text) !important; }
[data-testid="stSidebarCollapseButton"] button,
[data-testid="stSidebarCollapseButton"] * { color: var(--sidebar-text) !important; }

/* Main chat */
.app-header {
    display: flex; align-items: center; gap: .8rem;
    max-width: 900px; margin: 0 auto; padding: .25rem 0 .65rem;
}
.app-header-mark { font-size: 2rem; line-height: 1; }
.app-header-title { color: var(--text); font-family: 'Playfair Display', Georgia, serif; font-size: 1.45rem; font-weight: 700; }
.app-header-subtitle { color: var(--text-muted); font-size: .88rem; }
.hero { max-width: 760px; margin: 2.2rem auto 1.1rem; padding: 1.25rem 1rem; text-align: center; }
.hero-label { color: var(--accent); font-weight: 700; letter-spacing: .14em; font-size: .72rem; }
.hero-title {
    margin: .65rem 0 .55rem; color: var(--text);
    font-family: 'Playfair Display', Georgia, serif;
    font-size: clamp(2rem, 5vw, 3rem); line-height: 1.15;
}
.hero-subtitle { max-width: 540px; margin: 0 auto; color: var(--text-muted); font-size: 1rem; line-height: 1.7; }
[data-testid="stMainBlockContainer"] > div > div > div > div[data-testid="stVerticalBlock"] { min-width: 0; }
[data-testid="stMainBlockContainer"] button[data-testid^="stBaseButton-"] { overflow-wrap: anywhere; }
[data-testid="stMainBlockContainer"] div[data-testid="stChatMessage"] {
    box-sizing: border-box; width: min(100%, 880px); margin: .65rem auto;
    padding: clamp(.8rem, 2vw, 1.15rem);
    background: var(--assistant-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 15px !important;
    color: var(--text) !important;
}
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] * {
    max-width: 100%; color: var(--text) !important; line-height: 1.75;
    overflow-wrap: anywhere; word-break: normal;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    width: min(100%, 760px) !important;
    margin-left: auto !important;
    background: var(--user-bg) !important;
}
[data-testid="stChatMessageAvatarUser"] { background: var(--primary) !important; }
[data-testid="stChatMessageAvatarUser"] svg { color: #FFFFFF !important; }
.stApp:has(.vv-dark) [data-testid="stChatMessageAvatarUser"] svg { color: #14231A !important; }
[data-testid="stChatMessageAvatarAssistant"] { background: var(--surface-soft) !important; }
[data-testid="stChatMessageAvatarAssistant"] svg { color: var(--primary) !important; }
[data-testid="stChatMessage"] [data-testid="stCaptionContainer"],
[data-testid="stChatMessage"] [data-testid="stCaptionContainer"] * { color: var(--text-muted) !important; }
[data-testid="stBottom"], [data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"] {
    background: var(--page-bg) !important;
}
[data-testid="stChatInput"] {
    box-sizing: border-box; width: min(100%, 880px); margin: 0 auto;
    background: var(--surface) !important; border: 1px solid var(--border) !important;
    border-radius: 15px !important; box-shadow: 0 5px 22px rgba(20, 35, 27, .08);
}
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] div[data-baseweb="textarea"],
[data-testid="stChatInput"] div[data-baseweb="base-input"] {
    background: transparent !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: var(--text) !important; -webkit-text-fill-color: var(--text) !important;
    caret-color: var(--primary) !important; font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: var(--text-muted) !important; -webkit-text-fill-color: var(--text-muted) !important;
    opacity: 1 !important;
}
[data-testid="stChatInput"] button { background: var(--primary) !important; border-radius: 10px !important; }
[data-testid="stChatInput"] button svg { fill: #FFFFFF !important; color: #FFFFFF !important; }
[data-testid="stStatusWidget"] { color: var(--text) !important; }

/* Reference cards and long scripture text */
[data-testid="stVerticalBlockBorderWrapper"]:has(.reference-card-marker):not(:has([data-testid="stVerticalBlockBorderWrapper"] .reference-card-marker)) {
    margin: .55rem 0; padding: .75rem; background: var(--surface-soft);
    border: 1px solid var(--border); border-radius: 12px;
}
.purport-paper {
    box-sizing: border-box; width: 100%; margin: .55rem 0 .25rem;
    padding: clamp(1rem, 2.5vw, 1.5rem); color: var(--purport-text);
    background: var(--purport-bg); border: 1px solid var(--purport-border);
    border-radius: 10px; font-family: 'Playfair Display', Georgia, serif;
    font-size: 1rem; line-height: 1.9; overflow-wrap: anywhere; white-space: pre-wrap;
}
[data-testid="stExpander"] .purport-paper { color: var(--purport-text) !important; }
[data-testid="stExpander"] .purport-paper * { color: var(--purport-text) !important; }
.footer { max-width: 900px; margin: 2.5rem auto 0; padding: 1rem 0; color: var(--text-muted); font-size: .82rem; text-align: center; }

@media (max-width: 900px) {
    .block-container { padding-top: 1rem; padding-bottom: 4.5rem; }
    [data-testid="stSidebar"] { min-width: min(84vw, 300px) !important; }
    .hero { margin-top: 1rem; }
}
@media (max-width: 600px) {
    .block-container { padding-left: .8rem; padding-right: .8rem; }
    [data-testid="stVerticalBlockBorderWrapper"]:has(.auth-card-marker):not(:has([data-testid="stVerticalBlockBorderWrapper"] .auth-card-marker)) { margin: 1rem auto; border-radius: 15px; }
    .app-header { padding-inline: .15rem; }
    .app-header-mark { font-size: 1.7rem; }
    .app-header-title { font-size: 1.25rem; }
    [data-testid="stMainBlockContainer"] div[data-testid="stChatMessage"] { border-radius: 12px !important; }
    [data-testid="stChatInput"] { width: 100%; }
    .hero { padding: .7rem .2rem; }
}
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { scroll-behavior: auto !important; transition-duration: .01ms !important; }
}
</style>"""


def apply_styles(theme: bool) -> None:
    """Apply the existing light/dark theme and frontend stylesheet."""
    marker = '<span class="theme-marker vv-dark" aria-hidden="true"></span>' if theme else '<span class="theme-marker vv-light" aria-hidden="true"></span>'
    markup = f'{_CSS}{marker}'
    cleaned = " ".join(line.strip() for line in markup.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)
