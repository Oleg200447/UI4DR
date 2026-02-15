"""Shared header component for all authenticated pages."""
import streamlit as st


def show_header(title: str, icon: str, logout_callback, username: str, active_page: str = "", key_suffix: str = ""):
    """
    Render a top navigation bar with brand, page links, user badge and logout.

    Args:
        title: Page title text (shown below nav)
        icon: Emoji icon for the page
        logout_callback: Function to call on logout
        username: Current user's display name
        active_page: One of 'search', 'topics', 'chat' to highlight the active nav link
        key_suffix: Unique suffix for the logout button key
    """
    initial = username[0].upper() if username else "?"

    # ── Brand + User badge (HTML) ──
    st.markdown(
        f"""
        <div class="top-nav">
            <div class="brand">
                <span class="logo-icon">🔬</span>
                DeepResearch
            </div>
            <div class="user-section">
                <span class="user-chip">
                    <span class="avatar">{initial}</span>
                    {username}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Navigation buttons (Streamlit widgets — guaranteed to work) ──
    nav_col1, nav_col2, nav_col3, spacer, logout_col = st.columns([1, 1, 1, 4, 1])

    with nav_col1:
        search_type = "primary" if active_page == "search" else "secondary"
        if st.button("🔍 Search", key=f"nav_search_{key_suffix}", use_container_width=True, type=search_type):
            st.switch_page("pages/1_🔍_Search.py")

    with nav_col2:
        topics_type = "primary" if active_page == "topics" else "secondary"
        if st.button("📁 Topics", key=f"nav_topics_{key_suffix}", use_container_width=True, type=topics_type):
            st.switch_page("pages/2_📁_Topics.py")

    with nav_col3:
        chat_type = "primary" if active_page == "chat" else "secondary"
        if st.button("💬 Chat", key=f"nav_chat_{key_suffix}", use_container_width=True, type=chat_type):
            st.switch_page("pages/3_💬_Chat.py")

    with logout_col:
        if st.button("🚪 Logout", key=f"logout_{key_suffix}", use_container_width=True):
            logout_callback()

    # ── Page title ──
    st.markdown(
        f"""
        <div class="page-header">
            <h1>{icon} {title}</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )
