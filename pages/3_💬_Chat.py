"""Chat page - placeholder for future agent integration."""
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


def logout():
    """Logout user."""
    # Clear cookies
    cookies["access_token"] = ""
    cookies["oauth_state"] = ""
    cookies["code_verifier"] = ""
    cookies.save()

    logger.info("User logged out")

    # Set logout flag for two-step logout

    # Clear session state (but keep logging_out flag)
    #st.session_state.clear()
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


def main():
    """Main chat page logic."""
    show_header()
    
    st.markdown("---")
    
    # Placeholder content
    st.info("🚧 **Coming Soon!**")
    
    st.write("""
    This page will feature an intelligent chat interface where you can:
    
    - 🤖 Ask questions to an AI agent
    - 📚 Get answers based on your documents
    - 💡 Receive intelligent suggestions and insights
    - 🔍 Deep dive into specific topics with follow-up questions
    
    The chat functionality is currently under development and will be integrated soon.
    """)
    
    st.markdown("---")
    
    # Mockup of future interface
    st.subheader("Preview")
    
    with st.container():
        st.chat_message("assistant").write("Hello! How can I help you today?")
        
        # Disabled input as placeholder
        st.chat_input("Type your message here...", disabled=True)
    
    st.caption("💡 This is a preview of the upcoming chat interface")


if __name__ == "__main__":
    main()
