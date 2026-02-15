"""Topics management page."""
import streamlit as st
import logging
import os
import html
from datetime import datetime
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
    page_title="DeepResearch - Topics",
    page_icon="📁",
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


def refresh_topics():
    """Refresh topics list from server."""
    try:
        topics = st.session_state.api_client.get_editable_topics()
        st.session_state.editable_topics = topics
        logger.info(f"Loaded {len(topics)} editable topics")
    except Exception as e:
        st.error(f"❌ Failed to load topics: {str(e)}")
        logger.error(f"Error loading topics: {e}")


def create_topic_section():
    """Section for creating new topics."""
    st.markdown('<div class="section-title">➕ Create New Topic</div>', unsafe_allow_html=True)

    with st.form("create_topic_form"):
        col1, col2 = st.columns([3, 1])

        with col1:
            topic_name = st.text_input(
                "Topic Name",
                max_chars=100,
                placeholder="Enter a topic name...",
                help="Enter a name for your new topic"
            )

        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            submit = st.form_submit_button("Create Topic", type="primary", use_container_width=True)

        if submit:
            is_valid, error_msg = Validator.validate_topic_name(topic_name)

            if not is_valid:
                st.error(f"❌ {error_msg}")
            else:
                try:
                    with st.spinner("Creating topic..."):
                        response = st.session_state.api_client.create_topic(topic_name)
                        st.success(f"✅ Topic '{topic_name}' created successfully!")
                        logger.info(f"Topic created: {topic_name}")

                        refresh_topics()
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Failed to create topic: {str(e)}")
                    logger.error(f"Topic creation error: {e}")


def delete_topic_handler(topic_id: str, topic_name: str):
    """Handle topic deletion."""
    try:
        with st.spinner(f"Deleting topic '{topic_name}'..."):
            st.session_state.api_client.delete_topic(topic_id)
            st.success(f"✅ Topic '{topic_name}' deleted successfully!")
            logger.info(f"Topic deleted: {topic_id}")

            if st.session_state.get('selected_topic_id') == topic_id:
                st.session_state.selected_topic_id = None

            refresh_topics()
            st.rerun()

    except Exception as e:
        st.error(f"❌ Failed to delete topic: {str(e)}")
        logger.error(f"Topic deletion error: {e}")


def show_topics_list():
    """Show list of editable topics."""
    st.markdown('<div class="section-title">📚 Your Topics</div>', unsafe_allow_html=True)

    topics = st.session_state.get('editable_topics', [])

    if not topics:
        st.markdown(
            """
            <div class="empty-state">
                <div class="icon">📁</div>
                <div class="text">You don't have any topics yet. Create one above to get started!</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for topic in topics:
        topic_id = str(topic.get('id'))
        topic_name = topic.get('name')
        is_system = topic.get('is_system', False)
        icon = "🔒" if is_system else "📁"

        # Styled card via HTML
        st.markdown(
            f"""
            <div class="topic-card">
                <span class="topic-name">{icon} {html.escape(topic_name)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Action buttons (Streamlit widgets)
        col1, col2, col3 = st.columns([4, 1, 1])

        with col2:
            if st.button("👁️ View", key=f"view_{topic_id}", use_container_width=True):
                st.session_state.selected_topic_id = topic_id
                st.session_state.selected_topic_name = topic_name
                st.rerun()

        with col3:
            if not is_system:
                if st.button("🗑️ Delete", key=f"delete_{topic_id}", use_container_width=True):
                    st.session_state[f'confirm_delete_{topic_id}'] = True
                    st.rerun()

        # Confirmation dialog for deletion
        if st.session_state.get(f'confirm_delete_{topic_id}'):
            st.warning(f"⚠️ Are you sure you want to delete **{topic_name}**? This action cannot be undone!")

            col_y, col_n, col_space = st.columns([1, 1, 3])
            with col_y:
                if st.button("✅ Yes, Delete", key=f"confirm_yes_{topic_id}", use_container_width=True):
                    st.session_state[f'confirm_delete_{topic_id}'] = False
                    delete_topic_handler(topic_id, topic_name)

            with col_n:
                if st.button("❌ Cancel", key=f"confirm_no_{topic_id}", use_container_width=True):
                    st.session_state[f'confirm_delete_{topic_id}'] = False
                    st.rerun()


def upload_document_handler(topic_id: str, uploaded_file):
    """Handle document upload."""
    if not uploaded_file:
        st.warning("⚠️ Please select a file to upload")
        return

    is_valid, error_msg = Validator.validate_file_extension(uploaded_file.name)
    if not is_valid:
        st.error(f"❌ {error_msg}")
        return

    file_size = uploaded_file.size
    is_valid, error_msg = Validator.validate_file_size(file_size)
    if not is_valid:
        st.error(f"❌ {error_msg}")
        return

    try:
        with st.spinner(f"Uploading {uploaded_file.name}..."):
            file_content = uploaded_file.read()

            response = st.session_state.api_client.upload_document(
                topic_id=topic_id,
                file_content=file_content,
                filename=Validator.sanitize_filename(uploaded_file.name)
            )

            st.success(f"✅ Document '{uploaded_file.name}' uploaded successfully!")
            logger.info(f"Document uploaded: {uploaded_file.name}")

            st.session_state[f'documents_{topic_id}'] = None
            st.rerun()

    except Exception as e:
        st.error(f"❌ Upload failed: {str(e)}")
        logger.error(f"Document upload error: {e}")


def delete_document_handler(doc_id: str, filename: str, topic_id: str):
    """Handle document deletion."""
    try:
        with st.spinner(f"Deleting {filename}..."):
            st.session_state.api_client.delete_document(doc_id)
            st.success(f"✅ Document '{filename}' deleted successfully!")
            logger.info(f"Document deleted: {doc_id}")

            st.session_state[f'documents_{topic_id}'] = None
            st.rerun()

    except Exception as e:
        st.error(f"❌ Failed to delete document: {str(e)}")
        logger.error(f"Document deletion error: {e}")


def download_document_handler(doc_id: str, filename: str):
    """Handle document download."""
    try:
        with st.spinner(f"Downloading {filename}..."):
            file_data = st.session_state.api_client.download_document(doc_id)

            st.download_button(
                label=f"💾 Save {filename}",
                data=file_data,
                file_name=filename,
                mime="application/octet-stream",
                key=f"save_{doc_id}"
            )

    except Exception as e:
        st.error(f"❌ Download failed: {str(e)}")
        logger.error(f"Download error: {e}")


def _status_html(status: str) -> str:
    """Return a styled status pill."""
    if status == "success":
        return '<span class="status-pill success">✅ Ready</span>'
    elif status == "pending":
        return '<span class="status-pill pending">⏳ Processing</span>'
    else:
        return f'<span class="status-pill default">ℹ️ {html.escape(status)}</span>'


def show_topic_documents(topic_id: str, topic_name: str):
    """Show documents in a topic."""
    st.markdown(f'<div class="section-title">📄 Documents in \'{html.escape(topic_name)}\'</div>', unsafe_allow_html=True)

    # Upload section
    with st.expander("📤 Upload Document", expanded=False):
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['pdf', 'pptx', 'docx'],
            help="Only PDF, PPTX, and DOCX files are supported (max 50MB)"
        )

        if st.button("Upload", type="primary"):
            upload_document_handler(topic_id, uploaded_file)

    # Load documents
    try:
        if st.session_state.get(f'documents_{topic_id}') is None:
            with st.spinner("Loading documents..."):
                documents = st.session_state.api_client.get_topic_documents(topic_id)
                st.session_state[f'documents_{topic_id}'] = documents

        documents = st.session_state[f'documents_{topic_id}']

        if not documents:
            st.markdown(
                """
                <div class="empty-state">
                    <div class="icon">📄</div>
                    <div class="text">No documents yet. Upload one to get started!</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            return

        st.markdown(
            f'<span class="stat-badge neutral">📄 {len(documents)} document{"s" if len(documents) != 1 else ""}</span>',
            unsafe_allow_html=True,
        )
        st.markdown("")

        for doc in documents:
            doc_id = str(doc.get('id'))
            filename = doc.get('filename', 'Untitled')
            status = doc.get('status', 'unknown')
            created_at = doc.get('created_at', '')

            # Format timestamp
            try:
                if isinstance(created_at, str):
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    created_at_str = dt.strftime('%Y-%m-%d %H:%M')
                else:
                    created_at_str = str(created_at)
            except Exception:
                created_at_str = str(created_at)

            # Document row card
            st.markdown(
                f"""
                <div class="doc-row" style="display:flex;align-items:center;justify-content:space-between;">
                    <div>
                        <div style="font-weight:600;color:#e2e8f0;">{html.escape(filename)}</div>
                        <div style="font-size:0.8rem;color:#64748b;margin-top:2px;">Uploaded {created_at_str}</div>
                    </div>
                    <div>{_status_html(status)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Action buttons
            col1, col2, col3, col4 = st.columns([5, 1, 1, 1])

            with col2:
                if st.button("🔄", key=f"refresh_{doc_id}", help="Refresh status"):
                    try:
                        doc_status = st.session_state.api_client.get_document_status(doc_id)
                        for d in documents:
                            if str(d.get('id')) == doc_id:
                                d['status'] = doc_status.get('status', status)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ {str(e)}")

            with col3:
                if st.button("📥", key=f"download_{doc_id}", help="Download"):
                    download_document_handler(doc_id, filename)

            with col4:
                if st.button("🗑️", key=f"del_doc_{doc_id}", help="Delete"):
                    st.session_state[f'confirm_delete_doc_{doc_id}'] = True
                    st.rerun()

            # Confirmation dialog for deletion
            if st.session_state.get(f'confirm_delete_doc_{doc_id}'):
                st.warning(f"⚠️ Delete **{filename}**?")
                col_y, col_n, col_s = st.columns([1, 1, 4])
                with col_y:
                    if st.button("✅ Yes", key=f"confirm_yes_doc_{doc_id}"):
                        st.session_state[f'confirm_delete_doc_{doc_id}'] = False
                        delete_document_handler(doc_id, filename, topic_id)
                with col_n:
                    if st.button("❌ No", key=f"confirm_no_doc_{doc_id}"):
                        st.session_state[f'confirm_delete_doc_{doc_id}'] = False
                        st.rerun()

    except Exception as e:
        st.error(f"❌ Failed to load documents: {str(e)}")
        logger.error(f"Error loading documents: {e}")


def show_topic_users(topic_id: str, topic_name: str):
    """Show users with access to a topic."""
    st.markdown(f'<div class="section-title">👥 User Access for \'{html.escape(topic_name)}\'</div>', unsafe_allow_html=True)

    # Add user section
    with st.expander("➕ Add User", expanded=False):
        with st.form("add_user_form"):
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                nickname = st.text_input("Username", help="Enter the username to add", placeholder="e.g. john_doe")

            with col2:
                role = st.selectbox("Role", options=["reader", "owner"])

            with col3:
                st.write("")  # Spacing
                st.write("")  # Spacing
                submit = st.form_submit_button("Add User", use_container_width=True)

            if submit:
                if not nickname:
                    st.error("❌ Please enter a username")
                else:
                    try:
                        with st.spinner(f"Adding user '{nickname}'..."):
                            st.session_state.api_client.add_user_to_topic(
                                topic_id=topic_id,
                                nickname=nickname,
                                role=role
                            )
                            st.success(f"✅ User '{nickname}' added as {role}!")
                            logger.info(f"User {nickname} added to topic {topic_id}")

                            st.session_state[f'users_{topic_id}'] = None
                            st.rerun()

                    except Exception as e:
                        st.error(f"❌ Failed to add user: {str(e)}")
                        logger.error(f"Add user error: {e}")

    # Load users
    try:
        if st.session_state.get(f'users_{topic_id}') is None:
            with st.spinner("Loading users..."):
                users = st.session_state.api_client.get_topic_users(topic_id)
                st.session_state[f'users_{topic_id}'] = users

        users = st.session_state[f'users_{topic_id}']

        if not users:
            st.markdown(
                """
                <div class="empty-state">
                    <div class="icon">👥</div>
                    <div class="text">No users have access to this topic yet.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            return

        st.markdown(
            f'<span class="stat-badge neutral">👥 {len(users)} user{"s" if len(users) != 1 else ""}</span>',
            unsafe_allow_html=True,
        )
        st.markdown("")

        for user in users:
            user_id = str(user.get('user_id'))
            username = user.get('username', 'Unknown')
            role = user.get('role', 'reader')
            role_icon = "👑" if role == "owner" else "👁️"
            role_cls = "purple" if role == "owner" else "info"

            st.markdown(
                f"""
                <div class="doc-row" style="display:flex;align-items:center;justify-content:space-between;">
                    <div style="display:flex;align-items:center;gap:0.6rem;">
                        <span style="font-size:1.2rem;">{role_icon}</span>
                        <div>
                            <div style="font-weight:600;color:#e2e8f0;">{html.escape(username)}</div>
                            <div style="font-size:0.8rem;color:#94a3b8;">Role: {html.escape(role)}</div>
                        </div>
                    </div>
                    <span class="stat-badge {role_cls}">{role_icon} {html.escape(role)}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col1, col2 = st.columns([5, 1])
            with col2:
                if st.button("🗑️ Remove", key=f"remove_user_{user_id}", use_container_width=True):
                    st.session_state[f'confirm_remove_{user_id}'] = True
                    st.rerun()

            # Confirmation dialog
            if st.session_state.get(f'confirm_remove_{user_id}'):
                st.warning(f"⚠️ Remove **{username}** from this topic?")
                col_y, col_n, col_s = st.columns([1, 1, 4])
                with col_y:
                    if st.button("✅ Yes", key=f"confirm_yes_user_{user_id}"):
                        try:
                            st.session_state.api_client.remove_user_from_topic(topic_id, user_id)
                            st.success(f"✅ User '{username}' removed!")
                            st.session_state[f'confirm_remove_{user_id}'] = False
                            st.session_state[f'users_{topic_id}'] = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ {str(e)}")
                with col_n:
                    if st.button("❌ No", key=f"confirm_no_user_{user_id}"):
                        st.session_state[f'confirm_remove_{user_id}'] = False
                        st.rerun()

    except Exception as e:
        st.error(f"❌ Failed to load users: {str(e)}")
        logger.error(f"Error loading users: {e}")


def show_topic_details():
    """Show detailed view of a selected topic."""
    topic_id = st.session_state.get('selected_topic_id')
    topic_name = st.session_state.get('selected_topic_name')

    if not topic_id:
        st.markdown(
            """
            <div class="empty-state">
                <div class="icon">👈</div>
                <div class="text">Select a topic from the list to view its details.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    if st.button("← Back to Topics List"):
        st.session_state.selected_topic_id = None
        st.session_state.selected_topic_name = None
        st.rerun()

    st.markdown('<hr class="styled-divider">', unsafe_allow_html=True)

    # Tabs for different sections
    tab1, tab2 = st.tabs(["📄 Documents", "👥 User Access"])

    with tab1:
        show_topic_documents(topic_id, topic_name)

    with tab2:
        show_topic_users(topic_id, topic_name)


def main():
    """Main topics page logic."""
    show_header(
        title="Manage Topics",
        icon="📁",
        logout_callback=logout,
        username=st.session_state.username or "",
        active_page="topics",
        key_suffix="topics",
    )

    # Load editable topics
    if 'editable_topics' not in st.session_state:
        refresh_topics()

    # Check if a topic is selected for detailed view
    if st.session_state.get('selected_topic_id'):
        show_topic_details()
    else:
        create_topic_section()
        st.markdown('<hr class="styled-divider">', unsafe_allow_html=True)
        show_topics_list()


if __name__ == "__main__":
    main()
