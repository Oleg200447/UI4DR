"""Topics management page."""
import streamlit as st
import logging
import os
from datetime import datetime
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
    page_title="DeepResearch - Topics",
    page_icon="📁",
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
        st.title("📁 Manage Topics")
    
    with col2:
        st.write(f"👤 **{st.session_state.username}**")
        if st.button("Logout", type="secondary"):
            logout()


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
    st.subheader("➕ Create New Topic")
    
    with st.form("create_topic_form"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            topic_name = st.text_input(
                "Topic Name",
                max_chars=100,
                help="Enter a name for your new topic"
            )
        
        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            submit = st.form_submit_button("Create Topic", type="primary", use_container_width=True)
        
        if submit:
            # Validate topic name
            is_valid, error_msg = Validator.validate_topic_name(topic_name)
            
            if not is_valid:
                st.error(f"❌ {error_msg}")
            else:
                try:
                    with st.spinner("Creating topic..."):
                        response = st.session_state.api_client.create_topic(topic_name)
                        st.success(f"✅ Topic '{topic_name}' created successfully!")
                        logger.info(f"Topic created: {topic_name}")
                        
                        # Refresh topics list
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
            
            # Clear selected topic if it was deleted
            if st.session_state.get('selected_topic_id') == topic_id:
                st.session_state.selected_topic_id = None
            
            # Refresh topics list
            refresh_topics()
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ Failed to delete topic: {str(e)}")
        logger.error(f"Topic deletion error: {e}")


def show_topics_list():
    """Show list of editable topics."""
    st.subheader("📚 Your Topics")
    
    topics = st.session_state.get('editable_topics', [])
    
    if not topics:
        st.info("You don't have any topics yet. Create one to get started!")
        return
    
    for topic in topics:
        topic_id = str(topic.get('id'))
        topic_name = topic.get('name')
        is_system = topic.get('is_system', False)
        
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                icon = "🔒" if is_system else "📁"
                st.write(f"### {icon} {topic_name}")
            
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
                st.warning(f"⚠️ Are you sure you want to delete '{topic_name}'? This action cannot be undone!")
                
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    if st.button("✅ Yes, Delete", key=f"confirm_yes_{topic_id}"):
                        st.session_state[f'confirm_delete_{topic_id}'] = False
                        delete_topic_handler(topic_id, topic_name)
                
                with col2:
                    if st.button("❌ Cancel", key=f"confirm_no_{topic_id}"):
                        st.session_state[f'confirm_delete_{topic_id}'] = False
                        st.rerun()
            
            st.markdown("---")


def upload_document_handler(topic_id: str, uploaded_file):
    """Handle document upload."""
    if not uploaded_file:
        st.warning("⚠️ Please select a file to upload")
        return
    
    # Validate file extension
    is_valid, error_msg = Validator.validate_file_extension(uploaded_file.name)
    if not is_valid:
        st.error(f"❌ {error_msg}")
        return
    
    # Validate file size
    file_size = uploaded_file.size
    is_valid, error_msg = Validator.validate_file_size(file_size)
    if not is_valid:
        st.error(f"❌ {error_msg}")
        return
    
    try:
        with st.spinner(f"Uploading {uploaded_file.name}..."):
            # Read file content
            file_content = uploaded_file.read()
            
            # Upload document
            response = st.session_state.api_client.upload_document(
                topic_id=topic_id,
                file_content=file_content,
                filename=Validator.sanitize_filename(uploaded_file.name)
            )
            
            st.success(f"✅ Document '{uploaded_file.name}' uploaded successfully!")
            logger.info(f"Document uploaded: {uploaded_file.name}")
            
            # Refresh documents list
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
            
            # Refresh documents list
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
            
            # Offer download to user
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


def show_topic_documents(topic_id: str, topic_name: str):
    """Show documents in a topic."""
    st.subheader(f"📄 Documents in '{topic_name}'")
    
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
        # Check cache
        if st.session_state.get(f'documents_{topic_id}') is None:
            with st.spinner("Loading documents..."):
                documents = st.session_state.api_client.get_topic_documents(topic_id)
                st.session_state[f'documents_{topic_id}'] = documents
        
        documents = st.session_state[f'documents_{topic_id}']
        
        if not documents:
            st.info("No documents in this topic yet. Upload one to get started!")
            return
        
        # Display documents
        st.write(f"**Total Documents:** {len(documents)}")
        st.markdown("---")
        
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
            except:
                created_at_str = str(created_at)
            
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                
                with col1:
                    st.write(f"**{filename}**")
                    st.caption(f"Uploaded: {created_at_str}")
                
                with col2:
                    # Status indicator
                    if status == "success":
                        st.success("✅ Ready")
                    elif status == "pending":
                        st.warning("⏳ Processing")
                    else:
                        st.info(f"ℹ️ {status}")
                
                with col3:
                    if st.button("🔄", key=f"refresh_{doc_id}", help="Refresh status"):
                        try:
                            doc_status = st.session_state.api_client.get_document_status(doc_id)
                            # Update cached documents
                            for d in documents:
                                if str(d.get('id')) == doc_id:
                                    d['status'] = doc_status.get('status', status)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ {str(e)}")
                
                with col4:
                    if st.button("📥", key=f"download_{doc_id}", help="Download"):
                        download_document_handler(doc_id, filename)
                
                with col5:
                    if st.button("🗑️", key=f"del_doc_{doc_id}", help="Delete"):
                        st.session_state[f'confirm_delete_doc_{doc_id}'] = True
                        st.rerun()
                
                # Confirmation dialog for deletion
                if st.session_state.get(f'confirm_delete_doc_{doc_id}'):
                    st.warning(f"⚠️ Delete '{filename}'?")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Yes", key=f"confirm_yes_doc_{doc_id}"):
                            st.session_state[f'confirm_delete_doc_{doc_id}'] = False
                            delete_document_handler(doc_id, filename, topic_id)
                    with col2:
                        if st.button("❌ No", key=f"confirm_no_doc_{doc_id}"):
                            st.session_state[f'confirm_delete_doc_{doc_id}'] = False
                            st.rerun()
                
                st.markdown("---")
                
    except Exception as e:
        st.error(f"❌ Failed to load documents: {str(e)}")
        logger.error(f"Error loading documents: {e}")


def show_topic_users(topic_id: str, topic_name: str):
    """Show users with access to a topic."""
    st.subheader(f"👥 User Access for '{topic_name}'")
    
    # Add user section
    with st.expander("➕ Add User", expanded=False):
        with st.form("add_user_form"):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                nickname = st.text_input("Username", help="Enter the username to add")
            
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
                            
                            # Refresh users list
                            st.session_state[f'users_{topic_id}'] = None
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"❌ Failed to add user: {str(e)}")
                        logger.error(f"Add user error: {e}")
    
    # Load users
    try:
        # Check cache
        if st.session_state.get(f'users_{topic_id}') is None:
            with st.spinner("Loading users..."):
                users = st.session_state.api_client.get_topic_users(topic_id)
                st.session_state[f'users_{topic_id}'] = users
        
        users = st.session_state[f'users_{topic_id}']
        
        if not users:
            st.info("No users have access to this topic yet.")
            return
        
        # Display users
        st.write(f"**Total Users:** {len(users)}")
        st.markdown("---")
        
        for user in users:
            user_id = str(user.get('user_id'))
            username = user.get('username', 'Unknown')
            role = user.get('role', 'reader')
            
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{username}**")
                    st.caption(f"Role: {role}")
                
                with col2:
                    role_icon = "👑" if role == "owner" else "👁️"
                    st.write(role_icon)
                
                with col3:
                    if st.button("🗑️ Remove", key=f"remove_user_{user_id}"):
                        st.session_state[f'confirm_remove_{user_id}'] = True
                        st.rerun()
                
                # Confirmation dialog
                if st.session_state.get(f'confirm_remove_{user_id}'):
                    st.warning(f"⚠️ Remove '{username}' from this topic?")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Yes", key=f"confirm_yes_user_{user_id}"):
                            try:
                                st.session_state.api_client.remove_user_from_topic(topic_id, user_id)
                                st.success(f"✅ User '{username}' removed!")
                                st.session_state[f'confirm_remove_{user_id}'] = False
                                st.session_state[f'users_{topic_id}'] = None
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ {str(e)}")
                    with col2:
                        if st.button("❌ No", key=f"confirm_no_user_{user_id}"):
                            st.session_state[f'confirm_remove_{user_id}'] = False
                            st.rerun()
                
                st.markdown("---")
                
    except Exception as e:
        st.error(f"❌ Failed to load users: {str(e)}")
        logger.error(f"Error loading users: {e}")


def show_topic_details():
    """Show detailed view of a selected topic."""
    topic_id = st.session_state.get('selected_topic_id')
    topic_name = st.session_state.get('selected_topic_name')
    
    if not topic_id:
        st.info("👈 Select a topic from the list to view its details")
        return
    
    # Back button
    if st.button("← Back to Topics List"):
        st.session_state.selected_topic_id = None
        st.session_state.selected_topic_name = None
        st.rerun()
    
    st.markdown("---")
    
    # Tabs for different sections
    tab1, tab2 = st.tabs(["📄 Documents", "👥 User Access"])
    
    with tab1:
        show_topic_documents(topic_id, topic_name)
    
    with tab2:
        show_topic_users(topic_id, topic_name)


def main():
    """Main topics page logic."""
    show_header()
    
    st.markdown("---")
    
    # Load editable topics
    if 'editable_topics' not in st.session_state:
        refresh_topics()
    
    # Check if a topic is selected for detailed view
    if st.session_state.get('selected_topic_id'):
        show_topic_details()
    else:
        # Show topics list and creation form
        create_topic_section()
        st.markdown("---")
        show_topics_list()


if __name__ == "__main__":
    main()
