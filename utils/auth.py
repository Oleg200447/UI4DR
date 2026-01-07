"""Authentication and OAuth utilities."""
import logging
import hashlib
import base64
import secrets
import os
from typing import Optional, Dict, Any
from urllib.parse import urlencode
from authlib.integrations.base_client import OAuthError

logger = logging.getLogger(__name__)


class OAuthManager:
    """Manager for Google OAuth flow with PKCE."""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """
        Initialize OAuth manager.
        
        Args:
            client_id: Google OAuth client ID
            client_secret: Google OAuth client secret
            redirect_uri: Redirect URI for OAuth callback
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.authorization_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_endpoint = "https://oauth2.googleapis.com/token"
        
        logger.info(f"OAuth manager initialized with redirect_uri: {redirect_uri}")
    
    def generate_pkce_pair(self) -> tuple[str, str]:
        """
        Generate PKCE code verifier and challenge.
        
        Returns:
            Tuple of (code_verifier, code_challenge)
        """
        # Generate random code verifier (43-128 characters)
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # Create code challenge (SHA256 hash of verifier)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        
        logger.debug("PKCE pair generated")
        return code_verifier, code_challenge
    
    def get_authorization_url(self, state: str, code_challenge: str) -> str:
        """
        Build Google OAuth authorization URL.
        
        Args:
            state: Random state for CSRF protection
            code_challenge: PKCE code challenge
            
        Returns:
            Authorization URL
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "access_type": "offline",
            "prompt": "select_account"
        }
        
        auth_url = f"{self.authorization_endpoint}?{urlencode(params)}"
        logger.info("Authorization URL generated")
        return auth_url
    
    def generate_state(self) -> str:
        """Generate random state for CSRF protection."""
        return secrets.token_urlsafe(32)


class SessionManager:
    """Manager for user session and JWT token."""
    
    @staticmethod
    def is_authenticated(access_token: Optional[str]) -> bool:
        """
        Check if user is authenticated.
        
        Args:
            access_token: JWT access token from cookies
            
        Returns:
            True if authenticated, False otherwise
        """
        return access_token is not None and len(access_token) > 0
    
    @staticmethod
    def extract_user_id_from_token(access_token: str) -> Optional[str]:
        """
        Extract user ID from JWT token (simplified - just for client-side use).
        
        Note: This is NOT cryptographically verified. Server will verify token.
        This is just for displaying user info in UI.
        
        Args:
            access_token: JWT access token
            
        Returns:
            User ID if extractable, None otherwise
        """
        try:
            # JWT format: header.payload.signature
            parts = access_token.split('.')
            if len(parts) != 3:
                return None
            
            # Decode payload (add padding if needed)
            payload_b64 = parts[1]
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += '=' * padding
            
            import json
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
            
            # Extract 'sub' (subject) claim which contains user ID
            user_id = payload.get('sub')
            logger.debug(f"Extracted user_id from token: {user_id}")
            return user_id
            
        except Exception as e:
            logger.error(f"Failed to extract user_id from token: {e}")
            return None
    
    @staticmethod
    def extract_username_from_token(access_token: str) -> Optional[str]:
        """
        Extract username from JWT token.
        
        Args:
            access_token: JWT access token
            
        Returns:
            Username if extractable, None otherwise
        """
        try:
            # JWT format: header.payload.signature
            parts = access_token.split('.')
            if len(parts) != 3:
                return None
            
            # Decode payload (add padding if needed)
            payload_b64 = parts[1]
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += '=' * padding
            
            import json
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
            
            # Extract 'nickname' claim
            username = payload.get('nickname')
            logger.debug(f"Extracted username from token: {username}")
            return username
            
        except Exception as e:
            logger.error(f"Failed to extract username from token: {e}")
            return None
