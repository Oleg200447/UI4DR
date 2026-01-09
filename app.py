"""Main Streamlit application with authentication."""
import streamlit as st
import logging
import os
from dotenv import load_dotenv
from streamlit_cookies_manager import EncryptedCookieManager
from utils.auth import OAuthManager, SessionManager
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
    page_title="DeepResearch - Login",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize cookie manager
# Use a secret key - in production this should be from environment variable
cookies = EncryptedCookieManager(
    prefix="deepresearch_",
    password=os.getenv("COOKIE_PASSWORD", "change_this_to_a_secure_random_key_in_production")
)

if not cookies.ready():
    st.stop()

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.oauth_manager = None
    st.session_state.api_client = None
    st.session_state.user_id = None
    st.session_state.username = None
    logger.info(f"Session state initialized {cookies.get('access_token')}")

# Load configuration
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://kong:8015")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8501")

# Validate configuration
if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    st.error("⚠️ Google OAuth credentials not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env file.")
    st.stop()

# Initialize OAuth manager
if st.session_state.oauth_manager is None:
    st.session_state.oauth_manager = OAuthManager(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_uri=REDIRECT_URI
    )
    logger.info("OAuth manager initialized")

# Initialize API client
if st.session_state.api_client is None:
    access_token = cookies.get("access_token")
    st.session_state.api_client = APIClient(GATEWAY_URL, access_token)
    logger.info("API client initialized")


def handle_oauth_callback():
    """Handle OAuth callback from Google."""
    query_params = st.query_params
    
    # Check for authorization code
    code = query_params.get("code")
    state = query_params.get("state")
    
    if not code:
        return False
    
    # Verify state (CSRF protection)
    expected_state = cookies.get("oauth_state")
    if state != expected_state:
        st.error(f"⚠️ Invalid state parameter. Possible CSRF attack.{state,expected_state}")
        logger.warning("OAuth state mismatch")
        return False
    
    # Get code verifier from cookies
    code_verifier = cookies.get("code_verifier")
    if not code_verifier:
        st.error("⚠️ Code verifier not found. Please try again.")
        return False
    
    try:
        with st.spinner("Authenticating with Google..."):
            # Exchange code for token
            response = st.session_state.api_client.google_oauth_callback(code, code_verifier)
            
            if response.get("status") == "AUTHENTICATED":
                # User is authenticated
                access_token = response.get("access_token")
                cookies["access_token"] = access_token
                
                # Clear temporary OAuth cookies
                if "oauth_state" in cookies:
                    del cookies["oauth_state"]
                if "code_verifier" in cookies:
                    del cookies["code_verifier"]
                
                cookies.save()
                
                # Update API client with token
                st.session_state.api_client.set_token(access_token)
                
                # Extract user info
                st.session_state.user_id = SessionManager.extract_user_id_from_token(access_token)
                st.session_state.username = SessionManager.extract_username_from_token(access_token)
                
                logger.info(f"User authenticated: {st.session_state.username}")
                
                # Clear query params and redirect
                st.query_params.clear()
                st.success("✅ Login successful! Redirecting...")
                st.rerun()
                
            elif response.get("status") == "ONBOARDING_REQUIRED":
                # User needs to set username
                st.session_state.onboarding_required = True
                st.session_state.pre_auth_token = response.get("pre_auth_token")
                st.session_state.user_info = response.get("user_info")
                
                logger.info("Onboarding required for new user")
                
                # Clear query params
                st.query_params.clear()
                st.rerun()
                
    except Exception as e:
        st.error(f"❌ Authentication failed: {str(e)}")
        logger.error(f"OAuth callback error: {e}")
        return False
    
    return True


def show_onboarding():
    """Show onboarding form for new users."""
    st.title("🎉 Welcome to DeepResearch!")
    
    user_info = st.session_state.get("user_info", {})
    
    st.write(f"**Email:** {user_info.get('email', 'N/A')}")
    st.write(f"**Name:** {user_info.get('full_name', 'N/A')}")
    
    st.markdown("---")
    st.subheader("Choose Your Username")
    st.write("Please choose a unique username to complete your registration.")
    
    with st.form("username_form"):
        username = st.text_input(
            "Username",
            max_chars=30,
            help="3-30 characters, letters, numbers, underscores, and hyphens only"
        )
        
        submit = st.form_submit_button("Complete Registration", type="primary")
        
        if submit:
            # Validate username
            is_valid, error_msg = Validator.validate_username(username)
            
            if not is_valid:
                st.error(f"❌ {error_msg}")
            else:
                try:
                    with st.spinner("Setting up your account..."):
                        # Set username
                        response = st.session_state.api_client.set_username(
                            st.session_state.pre_auth_token,
                            username
                        )
                        
                        # Save access token
                        access_token = response.get("access_token")
                        cookies["access_token"] = access_token
                        cookies.save()
                        
                        # Update API client
                        st.session_state.api_client.set_token(access_token)
                        
                        # Extract user info
                        st.session_state.user_id = SessionManager.extract_user_id_from_token(access_token)
                        st.session_state.username = SessionManager.extract_username_from_token(access_token)
                        
                        # Clear onboarding state
                        st.session_state.onboarding_required = False
                        st.session_state.pre_auth_token = None
                        
                        logger.info(f"User onboarding completed: {username}")
                        
                        st.success("✅ Registration complete! Redirecting...")
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ Registration failed: {str(e)}")
                    logger.error(f"Onboarding error: {e}")


def show_login():
    """Show login page."""
    st.title("🔐 DeepResearch")
    st.subheader("Sign in to continue")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.write("Welcome to DeepResearch - Your intelligent document search platform.")
        st.write("")
        
        if st.button("🔑 Sign in with Google", type="primary", use_container_width=True):
            # Generate PKCE pair
            code_verifier, code_challenge = st.session_state.oauth_manager.generate_pkce_pair()
            
            # Generate state for CSRF protection
            state = st.session_state.oauth_manager.generate_state()
            
            # Store in cookies (not session state, as it won't survive redirect)
            cookies["code_verifier"] = code_verifier
            cookies["oauth_state"] = state
            cookies.save()
            
            # Get authorization URL
            auth_url = st.session_state.oauth_manager.get_authorization_url(state, code_challenge)
            
            logger.info("Redirecting to Google OAuth")
            
            # Redirect to Google
            st.markdown(f'<meta http-equiv="refresh" content="0; url={auth_url}">', unsafe_allow_html=True)
            st.write("Redirecting to Google...")


def main():
    """Main application logic."""
    # Check for OAuth callback
    if "code" in st.query_params:
        handle_oauth_callback()
        return
    
    # Check if user needs onboarding
    if st.session_state.get("onboarding_required"):
        show_onboarding()
        return
    
    # Check if user is authenticated
    access_token = cookies.get("access_token")
    
    # Check that token exists, is not None, and is not empty string
    if access_token and access_token != "" and SessionManager.is_authenticated(access_token):
        # User is authenticated, extract info if not already done
        if not st.session_state.user_id:
            st.session_state.user_id = SessionManager.extract_user_id_from_token(access_token)
            st.session_state.username = SessionManager.extract_username_from_token(access_token)
            st.session_state.api_client.set_token(access_token)
        
        # Redirect to search page
        st.switch_page("pages/1_🔍_Search.py")
    else:
        # Show login page
        show_login()


if __name__ == "__main__":
    main()
