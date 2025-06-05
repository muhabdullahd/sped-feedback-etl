from typing import Dict, Any, List, Tuple, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class DataValidator:
    """Utility for validating data structures."""
    
    @staticmethod
    def validate_feedback(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate feedback data structure.
        
        Args:
            data: Feedback data to validate
            
        Returns:
            Tuple containing:
                - bool: Whether the data is valid
                - Optional[str]: Error message if invalid, None otherwise
        """
        required_fields = ['content', 'source', 'timestamp']
        
        # Check for required fields
        for field in required_fields:
            if field not in data:
                return False, f"Missing required field: {field}"
                
        # Validate content
        if not isinstance(data['content'], str) or len(data['content'].strip()) == 0:
            return False, "Content must be a non-empty string"
            
        # Validate source
        if not isinstance(data['source'], str) or len(data['source'].strip()) == 0:
            return False, "Source must be a non-empty string"
            
        # Additional validations could be added here
        
        return True, None
    
    @staticmethod
    def validate_embedding_request(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate embedding request data.
        
        Args:
            data: Embedding request data to validate
            
        Returns:
            Tuple containing:
                - bool: Whether the data is valid
                - Optional[str]: Error message if invalid, None otherwise
        """
        required_fields = ['text', 'id']
        
        # Check for required fields
        for field in required_fields:
            if field not in data:
                return False, f"Missing required field: {field}"
                
        # Validate text
        if not isinstance(data['text'], str) or len(data['text'].strip()) == 0:
            return False, "Text must be a non-empty string"
            
        # Validate ID
        if not isinstance(data['id'], str) or len(data['id'].strip()) == 0:
            return False, "ID must be a non-empty string"
            
        return True, None
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        Sanitize input text.
        
        Args:
            text: Input text to sanitize
            
        Returns:
            str: Sanitized text
        """
        # Basic sanitization - more sophisticated methods could be implemented
        if not text:
            return ""
            
        # Remove potentially harmful characters
        sanitized = text.strip()
        
        # Additional sanitization could be added here
        
        return sanitized
