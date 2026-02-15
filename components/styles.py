"""Custom CSS styles for the DeepResearch UI — Dark Theme."""

def get_global_styles() -> str:
    """Return global CSS styles for the application (dark theme)."""
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* === ГЛАВНОЕ ИСПРАВЛЕНИЕ === */
    /* Мы убрали селектор [class*="st-"], чтобы не ломать встроенные иконки Streamlit */
    html, body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ===== HIDE DEFAULT STREAMLIT CHROME ===== */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    /* Hide default sidebar navigation */
    section[data-testid="stSidebar"] {
        display: none !important;
    }

    /* Hide Streamlit deploy button */
    .stDeployButton { display: none; }

    /* ===== GLOBAL DARK BACKGROUND ===== */
    .stApp, .main, .block-container {
        background-color: #0f172a !important;
        color: #e2e8f0 !important;
    }

    /* ===== EXPANDER — dark bg ===== */
    /* Стилизуем сам контейнер, но НЕ трогаем стрелку */
    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 0.92rem;
        color: #cbd5e1 !important;
        background-color: #1e293b !important;
        border-color: #334155 !important;
        border-radius: 12px;
    }
    
    /* Исправляем возможные проблемы с цветом стандартной иконки */
    .streamlit-expanderHeader svg {
        fill: #94a3b8 !important; /* Делаем стрелку серой */
    }
    .streamlit-expanderHeader:hover svg {
        fill: #cbd5e1 !important; /* Светлее при наведении */
    }

    details {
        background-color: #1e293b !important;
        border-color: #334155 !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
    }
    details summary {
        color: #cbd5e1 !important;
    }
    .streamlit-expanderContent,
    details > div {
        background-color: #1e293b !important;
        border-color: #334155 !important;
    }

    /* ===== TOP NAVIGATION BAR ===== */
    .top-nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #1e293b;
        border-bottom: 1px solid #334155;
        padding: 0.6rem 1.5rem;
        margin: -1rem -1rem 1rem -1rem;
        position: sticky;
        top: 0;
        z-index: 999;
    }
    .top-nav .brand {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 1.15rem;
        font-weight: 700;
        color: #f1f5f9;
        text-decoration: none;
    }
    .top-nav .brand .logo-icon {
        font-size: 1.4rem;
    }
    .top-nav .user-section {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    .top-nav .user-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: #334155;
        padding: 0.35rem 0.85rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        color: #cbd5e1;
    }
    .top-nav .user-chip .avatar {
        width: 26px;
        height: 26px;
        border-radius: 50%;
        background: #3b82f6;
        color: #fff;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.75rem;
    }

    /* ===== PAGE HEADER ===== */
    .page-header {
        margin-bottom: 1.25rem;
    }
    .page-header h1 {
        font-size: 1.5rem;
        font-weight: 700;
        color: #f1f5f9;
        margin: 0 0 0.25rem 0;
    }

    /* ===== CARDS ===== */
    .card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 0.75rem;
        transition: box-shadow 0.2s ease, transform 0.15s ease;
    }
    .card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.3);
        transform: translateY(-1px);
    }

    /* ===== SEARCH RESULT CARD ===== */
    .result-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 0.75rem;
        transition: box-shadow 0.2s ease, border-color 0.2s ease;
    }
    .result-card:hover {
        box-shadow: 0 4px 20px rgba(59,130,246,0.12);
        border-color: #3b82f6;
    }
    .result-card .doc-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #f1f5f9;
        margin-bottom: 0.4rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .result-card .doc-title .idx {
        background: #3b82f6;
        color: #fff;
        font-size: 0.72rem;
        font-weight: 700;
        width: 24px;
        height: 24px;
        border-radius: 6px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .result-card .snippet {
        color: #94a3b8;
        font-size: 0.9rem;
        line-height: 1.6;
    }

    /* ===== TOPIC CARD ===== */
    .topic-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.5rem;
        transition: box-shadow 0.2s ease, border-color 0.2s ease;
    }
    .topic-card:hover {
        box-shadow: 0 2px 12px rgba(59,130,246,0.1);
        border-color: #475569;
    }
    .topic-card .topic-name {
        font-size: 1rem;
        font-weight: 600;
        color: #f1f5f9;
    }

    /* ===== DOC ROW ===== */
    .doc-row {
        background: #1a2332;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 0.85rem 1.2rem;
        margin-bottom: 0.5rem;
        transition: background 0.15s ease;
    }
    .doc-row:hover {
        background: #253349;
    }

    /* ===== SEARCH BAR AREA ===== */
    .search-area {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.25rem;
    }

    /* ===== SECTION TITLE ===== */
    .section-title {
        font-size: 1rem;
        font-weight: 600;
        color: #cbd5e1;
        margin-bottom: 0.65rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }

    /* ===== METRIC / STAT BADGES ===== */
    .stat-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        background: #14532d;
        color: #4ade80;
        font-size: 0.8rem;
        font-weight: 500;
        padding: 0.25rem 0.7rem;
        border-radius: 20px;
        border: 1px solid #166534;
    }
    .stat-badge.info {
        background: #1e3a5f;
        color: #60a5fa;
        border-color: #1e40af;
    }
    .stat-badge.purple {
        background: #2e1065;
        color: #a78bfa;
        border-color: #5b21b6;
    }
    .stat-badge.neutral {
        background: #1e293b;
        color: #94a3b8;
        border-color: #334155;
    }

    /* ===== STATUS PILLS ===== */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        font-size: 0.76rem;
        font-weight: 600;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
    }
    .status-pill.success {
        background: #14532d;
        color: #4ade80;
        border: 1px solid #166534;
    }
    .status-pill.pending {
        background: #451a03;
        color: #fbbf24;
        border: 1px solid #92400e;
    }
    .status-pill.default {
        background: #1e293b;
        color: #94a3b8;
        border: 1px solid #334155;
    }

    /* ===== EMPTY STATE ===== */
    .empty-state {
        text-align: center;
        padding: 3rem 1rem;
        color: #64748b;
    }
    .empty-state .icon {
        font-size: 2.5rem;
        margin-bottom: 0.75rem;
    }
    .empty-state .text {
        font-size: 0.95rem;
        color: #94a3b8;
    }

    /* ===== CHAT WELCOME ===== */
    .chat-welcome {
        text-align: center;
        padding: 3rem 1rem;
    }
    .chat-welcome .icon {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    .chat-welcome h3 {
        font-weight: 600;
        color: #f1f5f9;
        margin-bottom: 0.25rem;
    }
    .chat-welcome p {
        color: #94a3b8;
        font-size: 0.92rem;
    }

    /* ===== LOGIN PAGE ===== */
    .login-container {
        max-width: 420px;
        margin: 5rem auto;
        text-align: center;
    }
    .login-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 20px;
        padding: 2.5rem 2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .login-card .logo {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    .login-card h1 {
        font-size: 1.7rem;
        font-weight: 700;
        color: #f1f5f9;
        margin-bottom: 0.25rem;
    }
    .login-card .subtitle {
        color: #94a3b8;
        font-size: 0.92rem;
        margin-bottom: 1.5rem;
    }
    .login-card .divider {
        border: none;
        border-top: 1px solid #334155;
        margin: 1.25rem 0;
    }
    .login-card .features {
        text-align: left;
        color: #cbd5e1;
        font-size: 0.88rem;
        line-height: 2;
    }

    /* ===== ONBOARDING PAGE ===== */
    .onboarding-container {
        max-width: 480px;
        margin: 3rem auto;
    }
    .onboarding-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }

    /* ===== DIVIDER ===== */
    .styled-divider {
        border: none;
        border-top: 1px solid #334155;
        margin: 1rem 0;
    }

    /* ===== TOPIC SELECTOR ===== */
    .topic-selector-bar {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 0.85rem 1.25rem;
        margin-bottom: 1rem;
    }
    .topic-selector-bar .label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #94a3b8;
        margin-bottom: 0.35rem;
    }

    /* ===== BUTTON OVERRIDES ===== */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"] {
        border-radius: 10px;
        font-weight: 600;
        background: #3b82f6 !important;
        border-color: #3b82f6 !important;
        color: #fff !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="stBaseButton-primary"]:hover {
        background: #2563eb !important;
        border-color: #2563eb !important;
    }
    .stButton > button[kind="secondary"],
    .stButton > button[data-testid="stBaseButton-secondary"] {
        border-radius: 10px;
        background: #1e293b !important;
        border-color: #475569 !important;
        color: #cbd5e1 !important;
    }
    .stButton > button[kind="secondary"]:hover,
    .stButton > button[data-testid="stBaseButton-secondary"]:hover {
        background: #334155 !important;
        border-color: #64748b !important;
        color: #f1f5f9 !important;
    }

    /* ===== FORM CONTAINERS ===== */
    .stForm {
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        background: #1e293b !important;
    }

    /* ===== TEXT INPUTS ===== */
    input, textarea {
        background-color: #0f172a !important;
        color: #f1f5f9 !important;
        border-color: #475569 !important;
        caret-color: #f1f5f9 !important;
    }
    input::placeholder, textarea::placeholder {
        color: #64748b !important;
        opacity: 1 !important;
    }
    input:focus, textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 1px #3b82f6 !important;
    }
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #0f172a !important;
        color: #f1f5f9 !important;
        border-color: #475569 !important;
        border-radius: 8px !important;
    }

    /* Labels */
    .stTextInput label, .stNumberInput label, .stTextArea label,
    .stSelectbox label, .stMultiSelect label, .stFileUploader label,
    .stCheckbox label, .stSlider label {
        color: #cbd5e1 !important;
    }

    /* Selectbox / Multiselect */
    [data-baseweb="select"] {
        background-color: #0f172a !important;
    }
    [data-baseweb="select"] > div {
        background-color: #0f172a !important;
        border-color: #475569 !important;
        color: #f1f5f9 !important;
    }
    [data-baseweb="select"] input {
        color: #f1f5f9 !important;
    }
    [data-baseweb="tag"] {
        background-color: #334155 !important;
        color: #f1f5f9 !important;
    }
    [data-baseweb="popover"] {
        background-color: #1e293b !important;
        border-color: #334155 !important;
    }
    [data-baseweb="menu"] {
        background-color: #1e293b !important;
    }
    [role="option"] {
        color: #e2e8f0 !important;
    }
    [role="option"]:hover {
        background-color: #334155 !important;
    }
    [aria-selected="true"] {
        background-color: #1e3a5f !important;
    }

    /* File uploader */
    .stFileUploader > div {
        background-color: #1e293b !important;
        border-color: #475569 !important;
    }
    .stFileUploader [data-testid="stFileUploaderDropzone"] {
        background-color: #0f172a !important;
        border-color: #475569 !important;
        color: #94a3b8 !important;
    }

    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.25rem;
        background-color: transparent !important;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        font-weight: 500;
        color: #94a3b8 !important;
        background-color: #1e293b !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #3b82f6 !important;
        background-color: #0f172a !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background-color: transparent !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #3b82f6 !important;
    }
    .stTabs [data-baseweb="tab-border"] {
        background-color: #334155 !important;
    }

    /* ===== CHAT MESSAGES — dark ===== */
    .stChatMessage {
        background-color: #1e293b !important;
        border-radius: 12px;
        border: 1px solid #334155 !important;
    }
    .stChatMessage * {
        color: #e2e8f0 !important;
    }
    .stChatMessage [data-testid="stMarkdownContainer"] p {
        color: #e2e8f0 !important;
    }

    /* ===== CHAT INPUT — FULL dark override ===== */
    .stChatInput,
    .stChatInput > div,
    .stChatInput > div > div,
    .stChatInput form,
    .stChatInput [data-testid="stChatInput"],
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] > div > div,
    [data-testid="stBottom"],
    [data-testid="stBottom"] > div,
    [data-testid="stBottom"] > div > div,
    [data-testid="stBottomBlockContainer"],
    [data-testid="stBottomBlockContainer"] > div,
    [data-testid="stBottomBlockContainer"] > div > div {
        background-color: #0f172a !important;
        background: #0f172a !important;
        border-color: #475569 !important;
    }
    .stChatInput textarea,
    [data-testid="stChatInput"] textarea {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
        border-color: #475569 !important;
        caret-color: #f1f5f9 !important;
    }
    .stChatInput textarea::placeholder,
    [data-testid="stChatInput"] textarea::placeholder {
        color: #64748b !important;
        opacity: 1 !important;
    }
    /* Chat send button */
    .stChatInput button,
    [data-testid="stChatInput"] button {
        background-color: #3b82f6 !important;
        color: #fff !important;
    }

    /* ===== ALERT BOXES ===== */
    .stAlert {
        background-color: #1e293b !important;
        border-color: #334155 !important;
        color: #e2e8f0 !important;
    }

    /* ===== MARKDOWN TEXT ===== */
    .stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span {
        color: #e2e8f0 !important;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #f1f5f9 !important;
    }
    .stMarkdown a {
        color: #60a5fa !important;
    }

    /* Spinner */
    .stSpinner > div {
        color: #94a3b8 !important;
    }

    /* Download button */
    .stDownloadButton > button {
        background-color: #1e293b !important;
        border-color: #475569 !important;
        color: #cbd5e1 !important;
        border-radius: 10px;
    }
    .stDownloadButton > button:hover {
        background-color: #334155 !important;
        color: #f1f5f9 !important;
    }

    /* Scrollbar dark */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0f172a;
    }
    ::-webkit-scrollbar-thumb {
        background: #475569;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #64748b;
    }

    /* Checkbox */
    .stCheckbox label span {
        color: #cbd5e1 !important;
    }

    /* Tooltip / help */
    [data-testid="stTooltipIcon"] {
        color: #64748b !important;
    }
    </style>
    """


def get_login_styles() -> str:
    """Return additional styles for the login page."""
    return """
    <style>
    section[data-testid="stSidebar"] {
        display: none !important;
    }
    </style>
    """
