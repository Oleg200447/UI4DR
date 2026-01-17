"""Chat page - interact with AI agent."""
import streamlit as st
import logging
import os
from dotenv import load_dotenv
from streamlit_cookies_manager import EncryptedCookieManager
from utils.auth import SessionManager
from utils.api_client import APIClient

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
    page_title="DeepResearch - Chat",
    page_icon="💬",
    layout="wide"
)

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

# Initialize chat history in session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Initialize selected topics in session state
if 'chat_selected_topics' not in st.session_state:
    st.session_state.chat_selected_topics = []


def logout():
    """Logout user."""
    # Clear cookies
    cookies["access_token"] = ""
    cookies["oauth_state"] = ""
    cookies["code_verifier"] = ""
    cookies.save()

    logger.info("User logged out")

    # Set logout flag for two-step logout
    st.session_state.logging_out = True

    # Show logout message and rerun
    st.rerun()


def show_header():
    """Show page header with user info."""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title("💬 Chat with Agent")
    
    with col2:
        st.write(f"👤 **{st.session_state.username}**")
        if st.button("Logout", type="secondary", key="logout_chat"):
            logout()


def clear_chat_history():
    """Clear chat history."""
    st.session_state.chat_history = []
    logger.info("Chat history cleared")


def send_message(question: str, selected_topics: list):
    """Send message to agent and get response."""
    if not question or not question.strip():
        st.warning("⚠️ Please enter a message")
        return
    
    if not selected_topics:
        st.warning("⚠️ Please select at least one topic")
        return
    
    # Add user message to history
    st.session_state.chat_history.append({
        "role": "user",
        "content": question
    })
    
    try:
        with st.spinner("🤔 Agent is thinking..."):
            # Send chat request
            response = st.session_state.api_client.chat(
                question=question,
                topics=selected_topics
            )
            
            agent_response = response.get("response", "")
            
            if not agent_response:
                agent_response = "I apologize, but I couldn't generate a response. Please try again."
            
            # Add assistant message to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": agent_response
            })
            
            logger.info(f"Chat message sent and response received")
            
    except Exception as e:
        st.error(f"❌ Failed to get response: {str(e)}")
        logger.error(f"Chat error: {e}")
        # Remove the user message if request failed
        if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
            st.session_state.chat_history.pop()


def display_chat_history():
    """Display chat messages."""
    if not st.session_state.chat_history:
        st.info("👋 Start a conversation! Ask me anything about your documents.")
        return
    
    for message in st.session_state.chat_history:
        role = message["role"]
        content = message["content"]
        
        if role == "user":
            with st.chat_message("user"):
                st.write(content)
        else:
            with st.chat_message("assistant"):
                st.write(content)


def main():
    """Main chat page logic."""
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
            st.info("💡 Go to the Topics page to create a new topic or get access to existing ones.")
            return
        
    except Exception as e:
        st.error(f"❌ Failed to load topics: {str(e)}")
        logger.error(f"Error loading topics: {e}")
        return
    
    # Sidebar for topic selection and controls
    with st.sidebar:
        st.subheader("📁 Select Topics")
        st.caption("Choose which topics the agent should search in")
        
        # Create topic options
        topic_options = {}
        for topic in topics:
            topic_id = str(topic.get("id"))
            topic_name = topic.get("name")
            is_system = topic.get("is_system", False)
            
            display_name = f"🔒 {topic_name}" if is_system else f"📁 {topic_name}"
            topic_options[display_name] = topic_id
        
        # Multi-select for topics
        selected_topic_names = st.multiselect(
            "Topics",
            options=list(topic_options.keys()),
            default=st.session_state.chat_selected_topics if st.session_state.chat_selected_topics else list(topic_options.keys()),
            label_visibility="collapsed",
            key="topic_selector"
        )
        
        # Update selected topics in session state
        st.session_state.chat_selected_topics = selected_topic_names
        
        # Get selected topic IDs
        selected_topics = [topic_options[name] for name in selected_topic_names]
        
        st.markdown("---")
        
        # Show selected topics count
        if selected_topics:
            st.success(f"✅ {len(selected_topics)} topic(s) selected")
        else:
            st.warning("⚠️ No topics selected")
        
        st.markdown("---")
        
        # Clear history button
        st.subheader("🗑️ Chat Controls")
        if st.button("Clear Chat History", type="secondary", use_container_width=True):
            clear_chat_history()
            st.rerun()
        
        # Show message count
        message_count = len(st.session_state.chat_history)
        st.caption(f"💬 {message_count} message(s) in history")
    
    # Main chat area
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        display_chat_history()
    
    # Chat input at the bottom
    user_input = st.chat_input(
        "Type your message here...",
        key="chat_input"
    )
    
    # Process new message
    if user_input:
        send_message(user_input, selected_topics)
        st.rerun()


if __name__ == "__main__":
    main()
