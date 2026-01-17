"""API client for communication with Kong gateway."""
import logging
import os
from typing import Optional, Dict, Any, List
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

logger = logging.getLogger(__name__)


class APIClient:
    """Centralized API client for all backend communication through Kong gateway."""
    
    def __init__(self, base_url: str, jwt_token: Optional[str] = None):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL of Kong gateway
            jwt_token: Optional JWT token for authenticated requests
        """
        self.base_url = base_url.rstrip('/')
        self.jwt_token = jwt_token
        self.timeout = 30
        
    def set_token(self, token: str):
        """Set JWT token for authenticated requests."""
        self.jwt_token = token
        logger.info("JWT token updated in API client")
        
    def clear_token(self):
        """Clear JWT token."""
        self.jwt_token = None
        logger.info("JWT token cleared from API client")
        
    def _get_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Build request headers with JWT if available."""
        headers = {"Content-Type": "application/json"}
        
        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
            
        if additional_headers:
            headers.update(additional_headers)
            
        return headers
    
    def _handle_response(self, response: requests.Response, endpoint: str) -> Dict[str, Any]:
        """
        Handle API response and errors.
        
        Args:
            response: Requests response object
            endpoint: API endpoint for logging
            
        Returns:
            Parsed JSON response
            
        Raises:
            Exception: For various error conditions
        """
        try:
            if response.status_code == 200 or response.status_code == 201:
                logger.info(f"Success: {endpoint} - Status {response.status_code}")
                return response.json() if response.content else {}
            elif response.status_code == 204:
                logger.info(f"Success: {endpoint} - Status 204 (No Content)")
                return {}
            elif response.status_code == 401:
                logger.error(f"Unauthorized: {endpoint}")
                raise Exception("Session expired. Please login again.")
            elif response.status_code == 403:
                logger.error(f"Forbidden: {endpoint}")
                raise Exception("You don't have permission to perform this action.")
            elif response.status_code == 404:
                logger.error(f"Not found: {endpoint}")
                raise Exception("Resource not found.")
            elif response.status_code == 409:
                logger.error(f"Conflict: {endpoint}")
                error_detail = response.json().get("detail", "Conflict occurred")
                raise Exception(error_detail)
            elif response.status_code >= 400:
                logger.error(f"Error {response.status_code}: {endpoint} - {response.text}")
                try:
                    error_data = response.json()
                    error_msg = error_data.get("detail", f"Error: {response.status_code}")
                except:
                    error_msg = f"Error: {response.status_code}"
                raise Exception(error_msg)
            else:
                return response.json() if response.content else {}
        except requests.exceptions.JSONDecodeError:
            logger.error(f"Invalid JSON response from {endpoint}")
            raise Exception("Invalid response from server")
    
    # ==================== AUTH SERVICE ====================
    
    def google_oauth_callback(self, code: str, code_verifier: str) -> Dict[str, Any]:
        """
        Exchange Google authorization code for JWT token.
        
        Args:
            code: Authorization code from Google
            code_verifier: PKCE code verifier
            
        Returns:
            Authentication response (AUTHENTICATED or ONBOARDING_REQUIRED)
        """
        endpoint = "/auth/oauth/google"
        url = f"{self.base_url}{endpoint}"
        
        payload = {
            "code": code,
            "code_verifier": code_verifier
        }
        
        try:
            logger.info(f"Making OAuth callback request to {endpoint}")
            response = requests.post(url, json=payload, timeout=self.timeout)
            return self._handle_response(response, endpoint)
        except Timeout:
            logger.error(f"Timeout calling {endpoint}")
            raise Exception("Request timeout. Please try again.")
        except ConnectionError:
            logger.error(f"Connection error calling {endpoint}")
            raise Exception("Cannot connect to server. Please check your connection.")
        except RequestException as e:
            logger.error(f"Request error calling {endpoint}: {e}")
            raise Exception(f"Request failed: {str(e)}")
    
    def set_username(self, pre_auth_token: str, username: str) -> Dict[str, Any]:
        """
        Complete onboarding by setting username.
        
        Args:
            pre_auth_token: Pre-auth token from onboarding response
            username: Desired username
            
        Returns:
            Authentication response with JWT token
        """
        endpoint = "/auth/onboarding/username"
        url = f"{self.base_url}{endpoint}"
        
        payload = {"username": username}
        headers = {"Authorization": f"PreAuth {pre_auth_token}", "Content-Type": "application/json"}
        
        try:
            logger.info(f"Setting username: {username}")
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            return self._handle_response(response, endpoint)
        except Timeout:
            logger.error(f"Timeout calling {endpoint}")
            raise Exception("Request timeout. Please try again.")
        except ConnectionError:
            logger.error(f"Connection error calling {endpoint}")
            raise Exception("Cannot connect to server. Please check your connection.")
        except RequestException as e:
            logger.error(f"Request error calling {endpoint}: {e}")
            raise Exception(f"Request failed: {str(e)}")
    
    # ==================== TOPICS SERVICE ====================
    
    def create_topic(self, name: str) -> Dict[str, Any]:
        """Create a new topic."""
        endpoint = "/topics"
        url = f"{self.base_url}{endpoint}"
        
        payload = {"name": name}
        
        try:
            logger.info(f"Creating topic: {name}")
            response = requests.post(
                url, 
                json=payload, 
                headers=self._get_headers(),
                timeout=self.timeout
            )
            return self._handle_response(response, endpoint)
        except RequestException as e:
            logger.error(f"Error creating topic: {e}")
            raise Exception(f"Failed to create topic: {str(e)}")
    
    def delete_topic(self, topic_id: str):
        """Delete a topic."""
        endpoint = f"/topics/{topic_id}"
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.info(f"Deleting topic: {topic_id}")
            response = requests.delete(
                url,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            return self._handle_response(response, endpoint)
        except RequestException as e:
            logger.error(f"Error deleting topic: {e}")
            raise Exception(f"Failed to delete topic: {str(e)}")
    
    def get_editable_topics(self) -> List[Dict[str, Any]]:
        """Get list of topics user can edit."""
        endpoint = "/topics/editable"
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.info("Fetching editable topics")
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            return self._handle_response(response, endpoint)
        except RequestException as e:
            logger.error(f"Error fetching editable topics: {e}")
            raise Exception(f"Failed to fetch topics: {str(e)}")
    
    def get_readable_topics(self) -> List[Dict[str, Any]]:
        """Get list of topics user can read/search."""
        endpoint = "/topics/readable"
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.info("Fetching readable topics")
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            return self._handle_response(response, endpoint)
        except RequestException as e:
            logger.error(f"Error fetching readable topics: {e}")
            raise Exception(f"Failed to fetch topics: {str(e)}")
    
    def get_topic_documents(self, topic_id: str) -> List[Dict[str, Any]]:
        """Get list of documents in a topic."""
        endpoint = f"/topics/{topic_id}/documents"
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.info(f"Fetching documents for topic: {topic_id}")
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            return self._handle_response(response, endpoint)
        except RequestException as e:
            logger.error(f"Error fetching documents: {e}")
            raise Exception(f"Failed to fetch documents: {str(e)}")
    
    def get_topic_users(self, topic_id: str) -> List[Dict[str, Any]]:
        """Get list of users with access to a topic."""
        endpoint = f"/topics/{topic_id}/users"
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.info(f"Fetching users for topic: {topic_id}")
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            return self._handle_response(response, endpoint)
        except RequestException as e:
            logger.error(f"Error fetching topic users: {e}")
            raise Exception(f"Failed to fetch users: {str(e)}")
    
    def add_user_to_topic(self, topic_id: str, nickname: str, role: str = "reader"):
        """Add a user to a topic."""
        endpoint = f"/topics/{topic_id}/users"
        url = f"{self.base_url}{endpoint}"
        
        payload = {"nickname": nickname, "role": role}
        
        try:
            logger.info(f"Adding user {nickname} to topic {topic_id} with role {role}")
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            return self._handle_response(response, endpoint)
        except RequestException as e:
            logger.error(f"Error adding user to topic: {e}")
            raise Exception(f"Failed to add user: {str(e)}")
    
    def remove_user_from_topic(self, topic_id: str, user_id: str):
        """Remove a user from a topic."""
        endpoint = f"/topics/{topic_id}/users/{user_id}"
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.info(f"Removing user {user_id} from topic {topic_id}")
            response = requests.delete(
                url,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            return self._handle_response(response, endpoint)
        except RequestException as e:
            logger.error(f"Error removing user from topic: {e}")
            raise Exception(f"Failed to remove user: {str(e)}")
    
    # ==================== DOCUMENTS SERVICE ====================
    
    def upload_document(self, topic_id: str, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Upload a document to a topic."""
        endpoint = "/documents/upload"
        url = f"{self.base_url}{endpoint}"
        
        files = {"file": (filename, file_content)}
        data = {"topic_id": topic_id}
        
        headers = {}
        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
        
        try:
            logger.info(f"Uploading document {filename} to topic {topic_id}")
            response = requests.post(
                url,
                files=files,
                data=data,
                headers=headers,
                timeout=60  # Longer timeout for file uploads
            )
            return self._handle_response(response, endpoint)
        except RequestException as e:
            logger.error(f"Error uploading document: {e}")
            raise Exception(f"Failed to upload document: {str(e)}")
    
    def delete_document(self, doc_id: str):
        """Delete a document."""
        endpoint = f"/documents/{doc_id}"
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.info(f"Deleting document: {doc_id}")
            response = requests.delete(
                url,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            return self._handle_response(response, endpoint)
        except RequestException as e:
            logger.error(f"Error deleting document: {e}")
            raise Exception(f"Failed to delete document: {str(e)}")
    
    def get_document_status(self, doc_id: str) -> Dict[str, Any]:
        """Get document processing status."""
        endpoint = f"/documents/{doc_id}/status"
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.info(f"Fetching status for document: {doc_id}")
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            return self._handle_response(response, endpoint)
        except RequestException as e:
            logger.error(f"Error fetching document status: {e}")
            raise Exception(f"Failed to fetch status: {str(e)}")
    
    def download_document(self, doc_id: str) -> bytes:
        """Download a document file."""
        endpoint = f"/documents/{doc_id}/download"
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.info(f"Downloading document: {doc_id}")
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=60,
                stream=True
            )
            
            if response.status_code == 200:
                logger.info(f"Document {doc_id} downloaded successfully")
                return response.content
            else:
                self._handle_response(response, endpoint)
        except RequestException as e:
            logger.error(f"Error downloading document: {e}")
            raise Exception(f"Failed to download document: {str(e)}")
    
    # ==================== SEARCH SERVICE ====================
    
    def search(
        self,
        query: str,
        user_id: str,
        indices: List[str],
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform search across specified topics."""
        endpoint = "/search"
        url = f"{self.base_url}{endpoint}"
        
        payload = {
            "query": query,
            "user_id": user_id,
            "indices": indices,
        }
        
        if filters:
            payload["filters"] = filters
        
        try:
            logger.info(f"Searching query: '{query}' in {len(indices)} indices")
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )
            return self._handle_response(response, endpoint)
        except RequestException as e:
            logger.error(f"Error performing search: {e}")
            raise Exception(f"Search failed: {str(e)}")
    
    # ==================== AGENT/CHAT SERVICE ====================
    
    def chat(
        self,
        question: str,
        topics: List[str]
    ) -> Dict[str, Any]:
        """Send a chat message to the agent.
        
        Args:
            question: User's question or message
            topics: List of topic IDs to search in
            
        Returns:
            Dict with 'response' and 'session_id' fields
        """
        endpoint = "/api/v1/chat"
        url = f"{self.base_url}{endpoint}"
        
        payload = {
            "question": question,
            "topics": topics
        }
        
        try:
            logger.info(f"Sending chat message with {len(topics)} topics")
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=60  # Longer timeout for agent processing
            )
            return self._handle_response(response, endpoint)
        except Timeout:
            logger.error(f"Timeout calling {endpoint}")
            raise Exception("Request timeout. The agent is taking too long to respond.")
        except RequestException as e:
            logger.error(f"Error in chat request: {e}")
            raise Exception(f"Chat request failed: {str(e)}")
