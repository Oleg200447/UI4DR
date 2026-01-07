"""Input validation utilities."""
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class Validator:
    """Input validation for user data."""
    
    @staticmethod
    def validate_username(username: str) -> tuple[bool, Optional[str]]:
        """
        Validate username format.
        
        Args:
            username: Username to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not username:
            return False, "Username cannot be empty"
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters long"
        
        if len(username) > 30:
            return False, "Username cannot exceed 30 characters"
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False, "Username can only contain letters, numbers, underscores, and hyphens"
        
        logger.debug(f"Username validation passed: {username}")
        return True, None
    
    @staticmethod
    def validate_topic_name(topic_name: str) -> tuple[bool, Optional[str]]:
        """
        Validate topic name.
        
        Args:
            topic_name: Topic name to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not topic_name:
            return False, "Topic name cannot be empty"
        
        if len(topic_name) < 1:
            return False, "Topic name must be at least 1 character long"
        
        if len(topic_name) > 100:
            return False, "Topic name cannot exceed 100 characters"
        
        # Allow more flexible topic names
        if not re.match(r'^[a-zA-Z0-9_\-\s]+$', topic_name):
            return False, "Topic name can only contain letters, numbers, spaces, underscores, and hyphens"
        
        logger.debug(f"Topic name validation passed: {topic_name}")
        return True, None
    
    @staticmethod
    def validate_search_query(query: str) -> tuple[bool, Optional[str]]:
        """
        Validate search query.
        
        Args:
            query: Search query to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not query or not query.strip():
            return False, "Search query cannot be empty"
        
        if len(query) > 500:
            return False, "Search query cannot exceed 500 characters"
        
        logger.debug(f"Search query validation passed")
        return True, None
    
    @staticmethod
    def validate_file_extension(filename: str) -> tuple[bool, Optional[str]]:
        """
        Validate file extension for document uploads.
        
        Args:
            filename: Filename to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not filename:
            return False, "Filename cannot be empty"
        
        allowed_extensions = ['.pdf', '.pptx', '.docx']
        file_ext = filename.lower()[-5:] if len(filename) >= 5 else filename.lower()
        
        if not any(file_ext.endswith(ext) for ext in allowed_extensions):
            return False, f"Only {', '.join(allowed_extensions)} files are allowed"
        
        logger.debug(f"File extension validation passed: {filename}")
        return True, None
    
    @staticmethod
    def validate_file_size(file_size: int, max_size_mb: int = 50) -> tuple[bool, Optional[str]]:
        """
        Validate file size.
        
        Args:
            file_size: File size in bytes
            max_size_mb: Maximum file size in MB
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size == 0:
            return False, "File cannot be empty"
        
        if file_size > max_size_bytes:
            return False, f"File size cannot exceed {max_size_mb}MB"
        
        logger.debug(f"File size validation passed: {file_size} bytes")
        return True, None
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename for safe display.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove any path components
        filename = filename.split('/')[-1].split('\\')[-1]
        
        # Remove any potentially dangerous characters
        filename = re.sub(r'[^\w\s\-\.]', '', filename)
        
        # Limit length
        if len(filename) > 100:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:95] + '.' + ext if ext else name[:100]
        
        logger.debug(f"Filename sanitized: {filename}")
        return filename
