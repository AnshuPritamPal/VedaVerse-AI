import streamlit as st


# Saffron "monk robe" palette. Variables live on :root so that popovers and
# menus, which Streamlit renders outside .stApp, are themed as well.
_CSS = r"""<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap');

:root {
    --page-bg: #FFFBF5;
    --surface: #FFFFFF;
    --surface-soft: #FBF1E4;
    --text: #2B1D14;
    --text-muted: #7A6352;
    --border: #EEDFCB;
    --border-strong: #E2C9A9;
    --primary: #C2410C;
    --primary-hover: #9A3412;
    --on-primary: #FFFFFF;
    --primary-soft: rgba(194, 65, 12, .09);
    --accent: #E8892B;
    --sidebar-bg: #F8EDDF;
    --sidebar-text: #3A2618;
    --sidebar-muted: #8A6F5A;
    --sidebar-hover: rgba(154, 52, 18, .07);
    --sidebar-active: #EFD9BF;
    --user-bg: #FCE6CF;
    --hero-gradient: radial-gradient(circle at 25% 15%, rgba(253, 186, 116, .55), transparent 55%),
                     linear-gradient(160deg, #EA7A2C 0%, #C2410C 48%, #7C2D12 100%);
    --purport-bg: #FBF1E4;
    --purport-text: #3A2618;
    --purport-border: #E2C9A9;
    --shadow: 0 6px 24px rgba(124, 45, 18, .08);
    --display-font: 'Cormorant Garamond', 'Iowan Old Style', Georgia, serif;
    --body-font: 'DM Sans', 'Segoe UI', system-ui, sans-serif;
    color-scheme: light;
}
:root:has(.vv-dark) {
    --page-bg: #17110D;
    --surface: #211812;
    --surface-soft: #2B2018;
    --text: #F3E9DD;
    --text-muted: #BCA894;
    --border: #3A2C21;
    --border-strong: #523D2D;
    --primary: #F28C38;
    --primary-hover: #F6A25E;
    --on-primary: #1E120A;
    --primary-soft: rgba(242, 140, 56, .12);
    --accent: #F2B45A;
    --sidebar-bg: #120D0A;
    --sidebar-text: #EADBC9;
    --sidebar-muted: #A48C77;
    --sidebar-hover: rgba(242, 140, 56, .08);
    --sidebar-active: #2E2117;
    --user-bg: #3A2618;
    --hero-gradient: radial-gradient(circle at 25% 15%, rgba(234, 122, 44, .35), transparent 55%),
                     linear-gradient(160deg, #9A3412 0%, #5B1F0A 50%, #2A1209 100%);
    --purport-bg: #2B2018;
    --purport-text: #EEE2D3;
    --purport-border: #523D2D;
    --shadow: 0 6px 24px rgba(0, 0, 0, .35);
    color-scheme: dark;
}

/* ---------- Base ---------- */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: var(--page-bg) !important;
    color: var(--text);
    font-family: var(--body-font);
}
.stApp p, .stApp li, .stApp label, .stApp span, .stApp div,
[data-testid="stMarkdownContainer"] { color: var(--text); }
.stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: var(--text) !important; font-family: var(--display-font) !important; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * { color: var(--text-muted) !important; }
hr { border-color: var(--border) !important; }
::selection { background: var(--primary-soft); }
[data-testid="stElementContainer"]:has(.vv-marker) { display: none !important; }
[class*="st-key-scroll_helper_"] { position: absolute !important; width: 0 !important; height: 0 !important; overflow: hidden; }
.only-dark { display: none !important; }
:root:has(.vv-dark) .only-dark { display: inline-block !important; }
:root:has(.vv-dark) .only-light { display: none !important; }

[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stToolbar"], [data-testid="stAppDeployButton"], [data-testid="stMainMenu"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"], #MainMenu, footer { display: none !important; }
[data-testid="stExpandSidebarButton"] { color: var(--text) !important; }
[data-testid="stExpandSidebarButton"] * { color: var(--text) !important; }

/* ---------- Buttons ---------- */
.stApp button[data-testid^="stBaseButton-"], [data-testid="stPopoverBody"] button {
    font-family: var(--body-font) !important;
    font-weight: 500 !important;
    border-radius: 10px !important;
    transition: background-color .15s ease, border-color .15s ease, color .15s ease;
}
button[data-testid="stBaseButton-secondary"], button[data-testid="stPopoverButton"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
}
button[data-testid="stBaseButton-secondary"]:hover {
    background: var(--surface-soft) !important;
    border-color: var(--border-strong) !important;
}
button[data-testid="stBaseButton-primary"], button[data-testid="stBaseButton-primaryFormSubmit"] {
    background: var(--primary) !important;
    border: 1px solid var(--primary) !important;
    color: var(--on-primary) !important;
}
button[data-testid="stBaseButton-primary"]:hover, button[data-testid="stBaseButton-primaryFormSubmit"]:hover {
    background: var(--primary-hover) !important;
    border-color: var(--primary-hover) !important;
}
button[data-testid="stBaseButton-tertiary"] {
    background: transparent !important;
    border: 0 !important;
    color: var(--text) !important;
}
button[data-testid^="stBaseButton-"] *, button[data-testid="stPopoverButton"] * { color: inherit !important; }
.stApp button:focus-visible, .stApp input:focus-visible, .stApp textarea:focus-visible {
    outline: 2px solid var(--accent) !important;
    outline-offset: 2px !important;
}

/* ---------- Form fields ---------- */
.stTextInput label, .stTextInput label * { color: var(--text) !important; font-weight: 600 !important; font-size: .86rem !important; }
[data-testid="stTextInputRootElement"] {
    background: var(--surface) !important;
    border: 1px solid var(--border-strong) !important;
    border-radius: 10px !important;
}
[data-testid="stTextInputRootElement"]:focus-within {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px var(--primary-soft) !important;
}
[data-testid="stTextInputRootElement"] > div, [data-testid="stTextInputRootElement"] input {
    background: transparent !important;
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
    caret-color: var(--primary);
}
[data-testid="stTextInputRootElement"] input::placeholder { color: var(--text-muted) !important; -webkit-text-fill-color: var(--text-muted) !important; }
[data-testid="stTextInputRootElement"] button { background: transparent !important; border: 0 !important; color: var(--text-muted) !important; }
[data-testid="stTextInputRootElement"] button * { color: var(--text-muted) !important; }
[data-testid="stForm"] { border: 0 !important; padding: 0 !important; }
[data-testid="stAlertContainer"] { border-radius: 10px !important; }
:root:has(.vv-dark) [data-testid="stAlertContainer"] {
    background: var(--surface-soft) !important; border: 1px solid var(--border-strong) !important;
}

/* ---------- Popovers & expanders ---------- */
[data-testid="stPopoverBody"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    box-shadow: var(--shadow) !important;
}
[data-testid="stPopoverBody"] * { color: var(--text) !important; }
[data-testid="stPopoverBody"] button[data-testid="stBaseButton-tertiary"]:hover { background: var(--surface-soft) !important; }
[data-testid="stExpander"] details {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * { color: var(--text) !important; font-weight: 600; }
[data-testid="stExpander"] summary:hover { background: var(--surface-soft) !important; }

/* ---------- Login / registration: one fixed screen ---------- */
:root:has(.vv-auth-page), :root:has(.vv-auth-page) body,
.stApp:has(.vv-auth-page) [data-testid="stAppViewContainer"],
.stApp:has(.vv-auth-page) [data-testid="stMain"] { overflow: hidden !important; height: 100vh; }
.stApp:has(.vv-auth-page) [data-testid="stHeader"] { display: none !important; }
.stApp:has(.vv-auth-page) .block-container {
    max-width: none !important; height: 100vh; padding: 0 !important;
}
.stApp:has(.vv-auth-page) .block-container > [data-testid="stVerticalBlock"] { gap: 0 !important; height: 100vh; }
[data-testid="stHorizontalBlock"]:has(.auth-hero) { height: 100vh; gap: 0 !important; flex-wrap: nowrap !important; }
[data-testid="stColumn"]:has(.auth-hero) { padding: 0 !important; overflow: hidden; }
[data-testid="stColumn"]:has(.auth-hero) [data-testid="stVerticalBlock"] { gap: 0 !important; }
[data-testid="stColumn"]:has(.st-key-auth_panel) {
    position: relative; height: 100vh; overflow-y: auto;
    display: flex; flex-direction: column; justify-content: center;
}
[data-testid="stColumn"]:has(.st-key-auth_panel) > [data-testid="stVerticalBlock"] {
    justify-content: center; min-height: 100%; padding: 1.5rem clamp(1.25rem, 4vw, 3rem);
    box-sizing: border-box;
}
.st-key-auth_theme { position: absolute !important; top: 1rem; right: 1.25rem; width: auto !important; z-index: 5; }
.st-key-auth_panel { width: min(100%, 400px) !important; margin: 0 auto; gap: .7rem !important; }

.auth-hero {
    box-sizing: border-box; height: 100vh;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    gap: clamp(1rem, 3vh, 1.75rem); padding: clamp(1.25rem, 4vh, 2.5rem) clamp(1.5rem, 4vw, 3.5rem);
    background: var(--hero-gradient); text-align: center;
}
.auth-hero * { color: #FFF4E6 !important; }
.auth-portrait {
    margin: 0; height: min(46vh, 430px); aspect-ratio: 560 / 737;
    border-radius: 22px; overflow: hidden;
    border: 4px solid rgba(255, 244, 230, .7);
    box-shadow: 0 25px 60px rgba(50, 15, 3, .45);
}
.auth-portrait img { display: block; width: 100%; height: 100%; object-fit: cover; }
.auth-hero-copy { max-width: 440px; }
.auth-hero-eyebrow { font-size: .72rem; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; opacity: .85; }
.auth-hero-title { margin: .35rem 0 .2rem; font-family: var(--display-font); font-size: clamp(1.8rem, 3.4vw, 2.5rem); font-weight: 700; line-height: 1.1; }
.auth-hero-author { font-size: .95rem; line-height: 1.5; opacity: .95; }
.auth-hero-iskcon {
    display: inline-flex; align-items: center; gap: .75rem; margin-top: 1rem;
    padding: .55rem .9rem; border-radius: 12px;
    background: rgba(255, 244, 230, .12); border: 1px solid rgba(255, 244, 230, .25);
    font-size: .78rem; line-height: 1.35; text-align: left;
}
.auth-hero-iskcon img { width: 44px; height: auto; }

.auth-brand { text-align: center; margin-bottom: .35rem; }
.auth-brand-mark { width: 64px; height: 64px; border-radius: 50%; box-shadow: var(--shadow); }
.auth-brand-title { margin-top: .5rem; font-family: var(--display-font); font-size: 2.1rem; font-weight: 700; color: var(--text); line-height: 1.1; }
.auth-brand-subtitle { margin-top: .25rem; color: var(--text-muted) !important; font-size: .92rem; }
.st-key-auth_mode [data-testid="stButtonGroup"], .st-key-auth_mode > div > div {
    width: 100%;
}
.st-key-auth_mode button {
    flex: 1 1 0; min-height: 2.4rem;
    background: var(--surface-soft) !important; border: 1px solid var(--border) !important;
    color: var(--text-muted) !important; font-weight: 600 !important;
}
.st-key-auth_mode button[aria-checked="true"] {
    background: var(--primary) !important; border-color: var(--primary) !important;
    color: var(--on-primary) !important;
}
.st-key-auth_mode button * { color: inherit !important; }
.st-key-auth_panel [data-testid="stForm"] [data-testid="stVerticalBlock"] { gap: .6rem; }
.st-key-auth_panel [data-testid="stFormSubmitButton"] { margin-top: .35rem; }
.st-key-auth_panel [data-testid="stFormSubmitButton"] button { min-height: 2.75rem; font-weight: 600 !important; }
.st-key-auth_panel [data-testid="stAlert"] { margin: 0; }

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] { background: var(--sidebar-bg) !important; border-right: 1px solid var(--border) !important; }
.stApp [data-testid="stSidebar"] * { color: var(--sidebar-text); }
[data-testid="stSidebarHeader"] { padding-bottom: 0 !important; height: 2.75rem; }
[data-testid="stSidebarCollapseButton"] button, [data-testid="stSidebarCollapseButton"] * { color: var(--sidebar-muted) !important; }
[data-testid="stSidebarUserContent"] { padding-top: 0 !important; padding-bottom: 0 !important; }
[data-testid="stSidebarUserContent"] [data-testid="stVerticalBlock"] { gap: .35rem; }
.sidebar-brand { display: flex; align-items: center; gap: .7rem; padding: 0 .25rem .9rem; }
.sidebar-brand-mark { width: 42px; height: 42px; border-radius: 50%; flex: none; }
.sidebar-brand-title { font-family: var(--display-font); font-size: 1.45rem; font-weight: 700; line-height: 1.05; }
.sidebar-brand-subtitle { font-size: .78rem; color: var(--sidebar-muted) !important; }
.st-key-new_chat button {
    justify-content: flex-start !important; min-height: 2.6rem;
    background: var(--surface) !important; border: 1px solid var(--border) !important;
    color: var(--sidebar-text) !important; font-weight: 600 !important;
}
.st-key-new_chat button:hover { border-color: var(--primary) !important; color: var(--primary) !important; }
.st-key-conversation_list { min-height: calc(100vh - 21rem); padding-top: .4rem; }
.conv-group {
    margin: .85rem .55rem .2rem; font-size: .72rem; font-weight: 700;
    letter-spacing: .06em; text-transform: uppercase; color: var(--sidebar-muted) !important;
}
[class*="st-key-conv_row_"] { position: relative; border-radius: 9px; flex-wrap: nowrap !important; }
[class*="st-key-conv_row_"]:hover { background: var(--sidebar-hover); }
[class*="st-key-conv_row_"]:has(button[data-testid="stBaseButton-primary"]) { background: var(--sidebar-active); }
[class*="st-key-conv_row_"] [data-testid="stElementContainer"]:has(button[data-testid^="stBaseButton-"]) { flex: 1 1 auto; min-width: 0; }
[class*="st-key-conv_row_"] button[data-testid^="stBaseButton-"] {
    justify-content: flex-start !important; min-height: 2.25rem !important; width: 100%;
    padding: .3rem .55rem !important;
    background: transparent !important; border: 0 !important;
    color: var(--sidebar-text) !important; font-weight: 400 !important;
}
[class*="st-key-conv_row_"] button[data-testid="stBaseButton-primary"] { font-weight: 600 !important; }
[class*="st-key-conv_row_"] button[data-testid^="stBaseButton-"] > div { width: 100%; justify-content: flex-start !important; }
[class*="st-key-conv_row_"] button[data-testid^="stBaseButton-"] > div,
[class*="st-key-conv_row_"] button[data-testid^="stBaseButton-"] [data-testid="stMarkdownContainer"] { min-width: 0; max-width: 100%; }
[class*="st-key-conv_row_"] button[data-testid^="stBaseButton-"] p {
    overflow: hidden; white-space: nowrap; text-overflow: ellipsis; text-align: left; font-size: .9rem;
}
[class*="st-key-conv_row_"] [data-testid="stPopover"] { flex: none; width: auto !important; opacity: 0; transition: opacity .15s ease; }
[class*="st-key-conv_row_"]:hover [data-testid="stPopover"],
[class*="st-key-conv_row_"]:focus-within [data-testid="stPopover"],
[class*="st-key-conv_row_"]:has(button[data-testid="stBaseButton-primary"]) [data-testid="stPopover"] { opacity: 1; }
@media (hover: none) { [class*="st-key-conv_row_"] [data-testid="stPopover"] { opacity: 1; } }
[class*="st-key-conv_row_"] button[data-testid="stPopoverButton"] > div > div:last-child:not(:first-child) { display: none !important; }
[class*="st-key-conv_row_"] button[data-testid="stPopoverButton"] {
    min-height: 2rem !important; padding: 0 .35rem !important;
    background: transparent !important; border: 0 !important; color: var(--sidebar-muted) !important;
}
.st-key-sidebar_footer {
    position: sticky; bottom: 0; z-index: 2;
    margin-top: .5rem; padding: .75rem 0 1rem;
    background: var(--sidebar-bg); border-top: 1px solid var(--border);
    gap: .55rem !important;
}
.source-card {
    display: flex; align-items: center; gap: .6rem; padding: .55rem .6rem;
    background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
}
.source-portrait { width: 38px; height: 38px; border-radius: 50%; object-fit: cover; object-position: 60% 25%; flex: none; }
.source-copy { min-width: 0; flex: 1; }
.source-title { font-family: var(--display-font); font-size: 1.02rem; font-weight: 700; line-height: 1.15; }
.source-sub { font-size: .7rem; line-height: 1.3; color: var(--sidebar-muted) !important; }
.source-logo { width: 30px; height: auto; flex: none; }
.account-chip { display: flex; align-items: center; gap: .55rem; padding: .2rem .25rem; }
.account-avatar {
    display: inline-grid; place-items: center; width: 30px; height: 30px; border-radius: 50%;
    background: var(--primary); color: var(--on-primary) !important; font-weight: 700; font-size: .85rem;
}
.account-name { font-weight: 600; font-size: .9rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.st-key-sidebar_footer [data-testid="stElementContainer"]:has(button) { flex: 1 1 0 !important; min-width: 0; }
.st-key-sidebar_footer button[data-testid="stBaseButton-secondary"] { min-height: 2.3rem; font-size: .85rem !important; padding: 0 .5rem !important; }

/* ---------- Chat page ---------- */
.block-container { max-width: 820px !important; padding: 2.5rem 1.25rem 1.5rem !important; }
.welcome { margin: clamp(1rem, 8vh, 5rem) auto 1.75rem; text-align: center; }
.welcome-emblem { width: 84px; height: 84px; border-radius: 50%; box-shadow: var(--shadow); }
.welcome-title { margin-top: .9rem; font-family: var(--display-font); font-size: clamp(2.1rem, 5vw, 2.9rem); font-weight: 700; line-height: 1.1; color: var(--text); }
.welcome-subtitle { margin-top: .4rem; color: var(--text-muted) !important; font-size: 1.05rem; }
.st-key-suggestions { max-width: 660px; margin: 0 auto; gap: .6rem !important; }
.st-key-suggestions button {
    justify-content: flex-start !important; min-height: 3.3rem; padding: .7rem 1rem !important;
    background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: 14px !important;
    text-align: left;
}
.st-key-suggestions [data-testid="stElementContainer"] { flex: 1 1 0 !important; min-width: 0; }
.st-key-suggestions button > div { width: 100%; justify-content: flex-start !important; }
.st-key-suggestions button p { text-align: left; }
.st-key-suggestions button:hover { border-color: var(--primary) !important; background: var(--surface-soft) !important; }
.st-key-suggestions button span[data-testid="stIconMaterial"] { color: var(--primary) !important; }
.welcome-source {
    display: flex; align-items: center; gap: .8rem; max-width: 660px; margin: 2.25rem auto 0;
    padding: .8rem 1rem; border: 1px dashed var(--border-strong); border-radius: 14px;
    color: var(--text-muted) !important; font-size: .85rem; line-height: 1.5;
}
.welcome-source * { color: var(--text-muted) !important; }
.welcome-source em { color: var(--text) !important; font-style: italic; }
.welcome-source-portrait { width: 44px; height: 44px; border-radius: 50%; object-fit: cover; object-position: 60% 25%; flex: none; }
.welcome-source-logo { width: 40px; height: auto; flex: none; margin-left: auto; }

[data-testid="stChatMessage"] {
    background: transparent !important; padding: .35rem 0 !important; margin: .6rem 0 !important; gap: .85rem;
}
[data-testid="stChatMessage"] img { border-radius: 50%; }
[data-testid="stChatMessage"]:has(> [aria-label="Chat message from user"]) { justify-content: flex-end; }
[data-testid="stChatMessage"]:has(> [aria-label="Chat message from user"]) > :first-child { display: none !important; }
[aria-label="Chat message from user"] {
    flex: 0 1 auto !important; width: auto !important; max-width: min(85%, 600px); margin: 0 0 0 auto !important;
    padding: .65rem 1.05rem !important; background: var(--user-bg); border-radius: 20px 20px 6px 20px;
}
[aria-label="Chat message from user"] p, [aria-label="Chat message from user"] [data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }
[data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"],
[data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] * {
    color: var(--text) !important; line-height: 1.75; overflow-wrap: anywhere;
}
[aria-label="Chat message from assistant"] [data-testid="stMarkdownContainer"] { font-size: 1rem; }
[data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] strong { color: var(--text) !important; }
[data-testid="stChatMessageContent"] [data-testid="stMarkdownContainer"] code {
    background: var(--surface-soft) !important; color: var(--primary-hover) !important;
}

.thinking { display: inline-flex; align-items: center; gap: .7rem; padding: .45rem 0; color: var(--text-muted) !important; }
.thinking-dots { display: inline-flex; gap: 5px; }
.thinking-dots i {
    width: 8px; height: 8px; border-radius: 50%; background: var(--primary);
    animation: vv-bounce 1.2s infinite ease-in-out;
}
.thinking-dots i:nth-child(2) { animation-delay: .15s; }
.thinking-dots i:nth-child(3) { animation-delay: .3s; }
.thinking-text { font-style: italic; color: var(--text-muted) !important; }
.thinking-text::after { content: '…'; animation: vv-stage 9s infinite steps(1); }
@keyframes vv-bounce { 0%, 80%, 100% { opacity: .3; transform: translateY(0); } 40% { opacity: 1; transform: translateY(-5px); } }
@keyframes vv-stage {
    0% { content: ' — searching the verses…'; }
    33% { content: ' — reading Śrīla Prabhupāda’s purports…'; }
    66% { content: ' — composing an answer…'; }
}

[data-testid="stBottom"], [data-testid="stBottom"] > div, [data-testid="stBottomBlockContainer"] { background: var(--page-bg) !important; }
[data-testid="stBottomBlockContainer"] { max-width: 820px !important; padding: .75rem 1.25rem 1.5rem !important; }
[data-testid="stChatInput"] {
    background: var(--surface) !important; border: 1px solid var(--border-strong) !important;
    border-radius: 24px !important; box-shadow: var(--shadow);
}
[data-testid="stChatInput"]:focus-within { border-color: var(--primary) !important; }
[data-testid="stChatInput"] > div, [data-testid="stChatInput"] [data-baseweb="textarea"],
[data-testid="stChatInput"] [data-baseweb="base-input"] { background: transparent !important; border: 0 !important; }
[data-testid="stChatInput"] textarea {
    background: transparent !important; color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important; caret-color: var(--primary) !important;
    font-family: var(--body-font) !important; font-size: 1rem !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: var(--text-muted) !important; -webkit-text-fill-color: var(--text-muted) !important; opacity: 1 !important; }
[data-testid="stChatInputSubmitButton"] { background: var(--primary) !important; border-radius: 50% !important; color: var(--on-primary) !important; }
[data-testid="stChatInputSubmitButton"] * { color: var(--on-primary) !important; }
[data-testid="stChatInputSubmitButton"]:disabled { opacity: .45; }

/* ---------- Scripture references ---------- */
[class*="st-key-ref_"] { background: var(--surface-soft) !important; border-color: var(--border) !important; border-radius: 12px !important; }
.purport-paper {
    box-sizing: border-box; width: 100%; margin: .55rem 0 .25rem;
    padding: clamp(1rem, 2.5vw, 1.5rem); color: var(--purport-text);
    background: var(--purport-bg); border: 1px solid var(--purport-border); border-radius: 10px;
    font-family: var(--display-font); font-size: 1.12rem; line-height: 1.8;
    overflow-wrap: anywhere; white-space: pre-wrap;
}
.purport-paper, .purport-paper * { color: var(--purport-text) !important; }

/* ---------- Small screens ---------- */
@media (max-width: 820px) {
    [data-testid="stColumn"]:has(.auth-hero) { display: none !important; }
    [data-testid="stColumn"]:has(.st-key-auth_panel) { flex: 1 1 100% !important; width: 100% !important; }
    .auth-mobile-source { display: flex !important; }
}
@media (max-width: 600px) {
    .block-container { padding: 2.75rem .9rem 1rem !important; }
    .welcome-source { flex-wrap: wrap; }
    [aria-label="Chat message from user"] { max-width: 92%; }
}
.auth-mobile-source {
    display: none; align-items: center; justify-content: center; gap: .55rem; margin-top: .7rem;
    font-size: .78rem; color: var(--text-muted) !important;
}
.auth-mobile-source * { color: var(--text-muted) !important; }
.auth-mobile-source .source-portrait { width: 30px; height: 30px; }
.auth-mobile-source .source-logo { width: 28px; }
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation: none !important; scroll-behavior: auto !important; transition-duration: .01ms !important; }
}
</style>"""


def apply_styles(dark: bool) -> None:
    """Apply the stylesheet plus a marker that selects the light or dark palette."""
    marker_class = "vv-dark" if dark else "vv-light"
    markup = f'{_CSS}<span class="vv-marker {marker_class}" aria-hidden="true"></span>'
    cleaned = " ".join(line.strip() for line in markup.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)
