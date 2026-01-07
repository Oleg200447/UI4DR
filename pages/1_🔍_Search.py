"""Search page for querying documents."""
import streamlit as st
import logging
import os
from dotenv import load_dotenv
from streamlit_cookies_manager import EncryptedCookieManager
from utils.auth import SessionManager
from utils.api_client import APIClient
from utils.validators import Validator

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
    layout="wide"
)

# Initialize cookie manager
cookies = EncryptedCookieManager(
    prefix="deepresearch_",
    password=os.getenv("COOKIE_PASSWORD", "change_this_to_a_secure_random_key_in_production")
)

if not cookies.ready():
    st.stop()

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
    cookies.save()
    st.session_state.clear()
    st.switch_page("app.py")


def show_header():
    """Show page header with user info."""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title("🔍 Search Documents")
    
    with col2:
        st.write(f"👤 **{st.session_state.username}**")
        if st.button("Logout", type="secondary"):
            logout()


def download_document(doc_id: str, filename: str):
    """Download a document."""
    try:
        with st.spinner(f"Downloading {filename}..."):
            file_data = st.session_state.api_client.download_document(doc_id)
            
            # Offer download to user
            st.download_button(
                label=f"💾 Save {filename}",
                data=file_data,
                file_name=filename,
                mime="application/octet-stream",
                key=f"download_{doc_id}"
            )
            
            logger.info(f"Document downloaded: {doc_id}")
            
    except Exception as e:
        st.error(f"❌ Download failed: {str(e)}")
        logger.error(f"Download error: {e}")


def perform_search(query: str, selected_topics: list, filters: dict):
    """Perform search and display results."""
    # Validate query
    is_valid, error_msg = Validator.validate_search_query(query)
    if not is_valid:
        st.error(f"❌ {error_msg}")
        return
    
    # Validate topic selection
    if not selected_topics:
        st.warning("⚠️ Please select at least one topic to search")
        return
    
    try:
        with st.spinner("🔎 Searching..."):
            # Perform search
            response = st.session_state.api_client.search(
                query=query,
                user_id=st.session_state.user_id,
                indices=selected_topics,
                filters=filters if filters else None
            )
            
            results = response.get("results", [])
            query_expanded = response.get("query_expanded", query)
            processing_time = response.get("processing_time_ms", 0)
            
            logger.info(f"Search completed: {len(results)} results in {processing_time}ms")
            
            # Display results
            st.success(f"✅ Found {len(results)} results in {processing_time:.2f}ms")
            
            if query_expanded != query:
                st.info(f"🔄 Query expanded to: **{query_expanded}**")
            
            st.markdown("---")
            
            if not results:
                st.warning("No results found. Try different keywords or topics.")
            else:
                for idx, result in enumerate(results, 1):
                    with st.container():
                        col1, col2 = st.columns([4, 1])
                        
                        with col1:
                            st.subheader(f"{idx}. {result.get('document_name', 'Untitled')}")
                            
                            # Show snippet if available
                            snippet = result.get('snippet', result.get('text', ''))
                            if snippet:
                                st.markdown(f"*{snippet[:300]}...*" if len(snippet) > 300 else f"*{snippet}*")
                            
                            # Show metadata
                            score = result.get('score', 0)
                            page_number = result.get('page_number', 'N/A')
                            
                            st.caption(f"**Score:** {score:.4f} | **Page:** {page_number}")
                        
                        with col2:
                            doc_id = result.get('doc_id')
                            filename = result.get('document_name', 'document')
                            
                            if doc_id and st.button("📥 Download", key=f"btn_download_{idx}"):
                                download_document(doc_id, filename)
                        
                        st.markdown("---")
            
    except Exception as e:
        st.error(f"❌ Search failed: {str(e)}")
        logger.error(f"Search error: {e}")


def main():
    """Main search page logic."""
    show_header()
    
    st.markdown("---")
    
    # Load readable topics
    try:
        if 'readable_topics' not in st.session_state:
            with st.spinner("Loading topics..."):
                topics = st.session_state.api_client.get_readable_topics()
                st.session_state.readable_topics = topics
        
        topics = st.session_state.readable_topics
        
        if not topics:
            st.warning("⚠️ No topics available. Please create or get access to topics first.")
            return
        
    except Exception as e:
        st.error(f"❌ Failed to load topics: {str(e)}")
        logger.error(f"Error loading topics: {e}")
        return
    
    # Search form
    col1, col2 = st.columns([2, 1])
    
    with col1:
        query = st.text_input(
            "Search Query",
            placeholder="Enter your search query...",
            help="Enter keywords to search across selected topics"
        )
    
    with col2:
        st.write("")  # Spacing
        st.write("")  # Spacing
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)
    
    # Topic selection
    st.subheader("📁 Select Topics to Search")
    
    # Create topic options
    topic_options = {}
    system_topics = []
    user_topics = []
    
    for topic in topics:
        topic_id = str(topic.get("id"))
        topic_name = topic.get("name")
        is_system = topic.get("is_system", False)
        
        display_name = f"🔒 {topic_name}" if is_system else f"📁 {topic_name}"
        topic_options[display_name] = topic_id
        
        if is_system:
            system_topics.append(display_name)
        else:
            user_topics.append(display_name)
    
    # Show topics in columns
    if system_topics or user_topics:
        col1, col2 = st.columns(2)
        
        with col1:
            if system_topics:
                st.write("**System Topics**")
        with col2:
            if user_topics:
                st.write("**Your Topics**")
    
    # Multi-select for topics
    selected_topic_names = st.multiselect(
        "Topics",
        options=list(topic_options.keys()),
        default=list(topic_options.keys()),
        label_visibility="collapsed"
    )
    
    # Get selected topic IDs
    selected_topics = [topic_options[name] for name in selected_topic_names]
    
    # Filters section (collapsible)
    with st.expander("🔧 Advanced Filters", expanded=False):
        st.write("Configure optional search filters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            min_score = st.slider(
                "Minimum Score",
                min_value=0.0,
                max_value=1.0,
                value=0.0,
                step=0.01,
                help="Filter results by minimum relevance score"
            )
        
        with col2:
            max_results = st.number_input(
                "Max Results",
                min_value=1,
                max_value=100,
                value=20,
                help="Maximum number of results to return"
            )
        
        use_filters = st.checkbox("Apply filters", value=False)
    
    # Build filters dict
    filters = None
    if use_filters:
        filters = {
            "min_score": min_score,
            "max_results": max_results
        }
    
    # Perform search on button click
    if search_button and query:
        perform_search(query, selected_topics, filters)
    elif search_button and not query:
        st.warning("⚠️ Please enter a search query")


if __name__ == "__main__":
    main()
