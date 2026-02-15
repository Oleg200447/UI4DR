"""Search page for querying documents."""
import streamlit as st
import logging
import os
import html
from dotenv import load_dotenv
from streamlit_cookies_manager import EncryptedCookieManager
from utils.auth import SessionManager
from utils.api_client import APIClient
from utils.validators import Validator
from components.styles import get_global_styles
from components.header import show_header

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="DeepResearch - Search",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inject global styles
st.markdown(get_global_styles(), unsafe_allow_html=True)

# Initialize cookie manager
cookies = EncryptedCookieManager(
    prefix="deepresearch_",
    password=os.getenv("COOKIE_PASSWORD", "change_this_to_a_secure_random_key_in_production")
)

if not cookies.ready():
    st.stop()

# Handle logout redirect
if st.session_state.get('logging_out'):
    if cookies['access_token'] == "":
        st.session_state.logging_out = False
        st.session_state.clear()
        st.switch_page("app.py")
    else:
        cookies["access_token"] = ""
        cookies["oauth_state"] = ""
        cookies["code_verifier"] = ""
        cookies.save()
        st.rerun()


# Check authentication
access_token = cookies.get("access_token")
if not SessionManager.is_authenticated(access_token):
    st.error("⚠️ Please login to access this page")
    st.stop()

# Initialize API client
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://kong:8015")
if 'api_client' not in st.session_state or st.session_state.api_client is None:
    st.session_state.api_client = APIClient(GATEWAY_URL, access_token)
else:
    st.session_state.api_client.set_token(access_token)

# Extract user info
if 'user_id' not in st.session_state or not st.session_state.user_id:
    st.session_state.user_id = SessionManager.extract_user_id_from_token(access_token)
    st.session_state.username = SessionManager.extract_username_from_token(access_token)


def logout():
    """Logout user."""
    cookies["access_token"] = ""
    cookies["oauth_state"] = ""
    cookies["code_verifier"] = ""
    cookies.save()
    logger.info("User logged out")
    st.session_state.logging_out = True
    st.rerun()


def download_document(doc_id: str, filename: str):
    """Download a document."""
    try:
        with st.spinner(f"Downloading {filename}..."):
            file_data = st.session_state.api_client.download_document(doc_id)
            if 'download_data' not in st.session_state:
                st.session_state.download_data = {}
            st.session_state.download_data[doc_id] = {
                'file_data': file_data,
                'filename': filename,
                'doc_id': doc_id
            }
            logger.info(f"Document downloaded: {doc_id}")
    except Exception as e:
        st.error(f"❌ Download failed: {str(e)}")
        logger.error(f"Download error: {e}")


def clear_download_data():
    """Clear download data from session state."""
    if 'download_data' in st.session_state:
        del st.session_state.download_data


def perform_search(query: str, selected_topics: list):
    """Perform search and store results in session state."""
    clear_download_data()
    clear_search_results()

    is_valid, error_msg = Validator.validate_search_query(query)
    if not is_valid:
        st.error(f"❌ {error_msg}")
        return

    if not selected_topics:
        st.warning("⚠️ Please select at least one topic to search")
        return

    try:
        with st.spinner("🔎 Searching..."):
            response = st.session_state.api_client.search(
                query=query,
                user_id=st.session_state.user_id,
                indices=selected_topics,
            )

            results = response.get("results", [])
            query_expanded = response.get("query_expanded", query)
            processing_time = response.get("processing_time_ms", 0)

            logger.info(f"Search completed: {len(results)} results in {processing_time}ms")

            st.session_state.search_results = {
                'results': results,
                'query': query,
                'query_expanded': query_expanded,
                'processing_time': processing_time,
                'selected_topics': selected_topics,
            }
    except Exception as e:
        st.error(f"❌ Search failed: {str(e)}")
        logger.error(f"Search error: {e}")


def _make_snippet(text: str, max_len: int = 300) -> str:
    """Truncate text and always append '...' at the end."""
    if not text:
        return "..."
    text = text.strip()
    if len(text) > max_len:
        text = text[:max_len].rstrip()
    if not text.endswith("..."):
        text = text.rstrip(".") + "..."
    return text


def display_search_results():
    """Display search results from session state."""
    if 'search_results' not in st.session_state:
        return

    search_data = st.session_state.search_results
    results = search_data['results']
    query = search_data['query']
    query_expanded = search_data['query_expanded']
    processing_time = search_data['processing_time']

    st.markdown(
        f"""
        <div style="display:flex;gap:0.6rem;flex-wrap:wrap;margin-bottom:0.75rem;">
            <span class="stat-badge">✅ {len(results)} result{"s" if len(results) != 1 else ""}</span>
            <span class="stat-badge info">⚡ {processing_time:.0f} ms</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if query_expanded != query:
        st.info(f"🔄 Query expanded to: **{query_expanded}**")

    if not results:
        st.markdown(
            """
            <div class="empty-state">
                <div class="icon">🔍</div>
                <div class="text">No results found. Try different keywords or topics.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        for idx, result in enumerate(results, 1):
            doc_name = html.escape(result.get('doc_name', 'Untitled'))
            snippet_raw = result.get('snippet', result.get('text', ''))
            snippet = html.escape(_make_snippet(snippet_raw))

            st.markdown(
                f"""
                <div class="result-card">
                    <div class="doc-title">
                        <span class="idx">{idx}</span>
                        {doc_name}
                    </div>
                    <div class="snippet">{snippet}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            doc_id = result.get('doc_id')
            filename = result.get('doc_name', 'document')
            if doc_id:
                download_ready = (
                    'download_data' in st.session_state
                    and doc_id in st.session_state.download_data
                )

                col_spacer, col_btn = st.columns([5, 1])
                with col_btn:
                    if download_ready:
                        download_info = st.session_state.download_data[doc_id]
                        st.download_button(
                            label="💾 Save",
                            data=download_info['file_data'],
                            file_name=download_info['filename'],
                            mime="application/octet-stream",
                            key=f"download_btn_{doc_id}",
                            use_container_width=True,
                        )
                    else:
                        st.button(
                            "📥 Download",
                            key=f"btn_download_{doc_id}",
                            on_click=download_document,
                            args=(doc_id, filename),
                            use_container_width=True,
                        )


def clear_search_results():
    """Clear search results from session state."""
    if 'search_results' in st.session_state:
        del st.session_state.search_results


def main():
    """Main search page logic."""
    show_header(
        title="Search Documents",
        icon="🔍",
        logout_callback=logout,
        username=st.session_state.username or "",
        active_page="search",
        key_suffix="search",
    )

    # Load readable topics
    try:
        if 'readable_topics' not in st.session_state:
            with st.spinner("Loading topics..."):
                topics = st.session_state.api_client.get_readable_topics()
                st.session_state.readable_topics = topics

        topics = st.session_state.readable_topics

        if not topics:
            st.markdown(
                """
                <div class="empty-state">
                    <div class="icon">📁</div>
                    <div class="text">No topics available. Create or get access to topics first.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            return
    except Exception as e:
        st.error(f"❌ Failed to load topics: {str(e)}")
        logger.error(f"Error loading topics: {e}")
        return

    # ── Search bar ──
    st.markdown('<div class="search-area">', unsafe_allow_html=True)

    col_input, col_btn = st.columns([4, 1])

    with col_input:
        query = st.text_input(
            "Search Query",
            placeholder="What are you looking for?",
            label_visibility="collapsed",
        )

    with col_btn:
        search_button = st.button("🔍  Search", type="primary", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Topic selection ──
    st.markdown('<div class="section-title">📁 Topics to search</div>', unsafe_allow_html=True)

    topic_options = {}
    for topic in topics:
        topic_id = str(topic.get("id"))
        topic_name = topic.get("name")
        is_system = topic.get("is_system", False)
        display_name = f"🔒 {topic_name}" if is_system else f"📁 {topic_name}"
        topic_options[display_name] = topic_id

    selected_topic_names = st.multiselect(
        "Topics",
        options=list(topic_options.keys()),
        default=list(topic_options.keys()),
        label_visibility="collapsed"
    )

    selected_topics = [topic_options[name] for name in selected_topic_names]

    # Perform search
    if search_button and query:
        perform_search(query, selected_topics)
    elif search_button and not query:
        st.warning("⚠️ Please enter a search query")

    # Display results
    display_search_results()


if __name__ == "__main__":
    main()
