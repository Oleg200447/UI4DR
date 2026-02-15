"""Main Streamlit application with authentication."""
import streamlit as st
import logging
import os
from dotenv import load_dotenv
from streamlit_cookies_manager import EncryptedCookieManager
from utils.auth import OAuthManager, SessionManager
from utils.api_client import APIClient
from utils.validators import Validator
from components.styles import get_global_styles, get_login_styles

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
    page_title="DeepResearch",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inject global styles
st.markdown(get_global_styles(), unsafe_allow_html=True)
st.markdown(get_login_styles(), unsafe_allow_html=True)

# Initialize cookie manager
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
    user_info = st.session_state.get("user_info", {})

    st.markdown(
        """
        <div class="onboarding-container">
            <div class="onboarding-card" style="text-align:center;">
                <div style="font-size:3rem;">🎉</div>
                <h1 style="font-size:1.5rem;font-weight:700;color:#f1f5f9;margin-bottom:0.25rem;">Welcome to DeepResearch!</h1>
                <p style="color:#94a3b8;font-size:0.9rem;">Let's set up your account</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Centered form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("")
        st.markdown(
            f"""
            <div style="background:#0f172a;border:1px solid #334155;border-radius:12px;padding:1rem 1.25rem;margin-bottom:1rem;">
                <div style="font-size:0.85rem;color:#94a3b8;">Email</div>
                <div style="font-weight:600;color:#e2e8f0;">{user_info.get('email', 'N/A')}</div>
                <div style="font-size:0.85rem;color:#94a3b8;margin-top:0.5rem;">Name</div>
                <div style="font-weight:600;color:#e2e8f0;">{user_info.get('full_name', 'N/A')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("username_form"):
            username = st.text_input(
                "Choose your username",
                max_chars=30,
                help="3-30 characters, letters, numbers, underscores, and hyphens only",
                placeholder="e.g. john_doe"
            )

            submit = st.form_submit_button("Complete Registration", type="primary", use_container_width=True)

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
    # Beautiful centered login card
    st.markdown(
        """
        <div class="login-container">
            <div class="login-card">
                <div class="logo">🔬</div>
                <h1>DeepResearch</h1>
                <p class="subtitle">Intelligent document search &amp; AI assistant</p>
                <hr class="divider">
                <div class="features">
                    🔍&nbsp; Search across all your documents instantly<br>
                    💬&nbsp; Chat with an AI that knows your files<br>
                    📁&nbsp; Organize documents into topics<br>
                    👥&nbsp; Share topics with your team
                </div>
                <hr class="divider">
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Streamlit button must be outside the HTML
    col1, col2, col3 = st.columns([1.2, 1.6, 1.2])
    with col2:
        if st.button("🔑  Sign in with Google", type="primary", use_container_width=True):
            # Generate PKCE pair
            code_verifier, code_challenge = st.session_state.oauth_manager.generate_pkce_pair()

            # Generate state for CSRF protection
            state = st.session_state.oauth_manager.generate_state()

            # Store in cookies
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
