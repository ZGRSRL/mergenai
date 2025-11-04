#!/usr/bin/env python3
"""
Security Mask - Mask sensitive data in logs and outputs
"""

import re
import os
from typing import Any, Dict, List, Optional
from functools import wraps

class SecurityMask:
    """Security mask for sensitive data"""
    
    def __init__(self):
        self.sensitive_patterns = [
            # API Keys
            (r'api[_-]?key["\s]*[:=]["\s]*([a-zA-Z0-9_-]{20,})', r'api_key="***MASKED***"'),
            (r'sam[_-]?api[_-]?key["\s]*[:=]["\s]*([a-zA-Z0-9_-]{20,})', r'sam_api_key="***MASKED***"'),
            (r'openai[_-]?api[_-]?key["\s]*[:=]["\s]*([a-zA-Z0-9_-]{20,})', r'openai_api_key="***MASKED***"'),
            
            # Passwords
            (r'password["\s]*[:=]["\s]*([^"\s]+)', r'password="***MASKED***"'),
            (r'pwd["\s]*[:=]["\s]*([^"\s]+)', r'pwd="***MASKED***"'),
            
            # Email addresses
            (r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', r'***@***.***'),
            
            # Credit card numbers
            (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', r'****-****-****-****'),
            
            # SSN
            (r'\b\d{3}-\d{2}-\d{4}\b', r'***-**-****'),
            
            # Phone numbers
            (r'\b\d{3}-\d{3}-\d{4}\b', r'***-***-****'),
            
            # Database URLs
            (r'postgresql://[^:]+:[^@]+@', r'postgresql://***:***@'),
            (r'mysql://[^:]+:[^@]+@', r'mysql://***:***@'),
            (r'mongodb://[^:]+:[^@]+@', r'mongodb://***:***@'),
        ]
    
    def mask_string(self, text: str) -> str:
        """Mask sensitive data in string"""
        if not isinstance(text, str):
            return text
        
        masked_text = text
        for pattern, replacement in self.sensitive_patterns:
            masked_text = re.sub(pattern, replacement, masked_text, flags=re.IGNORECASE)
        
        return masked_text
    
    def mask_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive data in dictionary"""
        if not isinstance(data, dict):
            return data
        
        masked_data = {}
        for key, value in data.items():
            # Mask key if it contains sensitive terms
            masked_key = self.mask_string(key)
            
            # Mask value based on type
            if isinstance(value, str):
                masked_data[masked_key] = self.mask_string(value)
            elif isinstance(value, dict):
                masked_data[masked_key] = self.mask_dict(value)
            elif isinstance(value, list):
                masked_data[masked_key] = [self.mask_string(str(item)) if isinstance(item, str) else item for item in value]
            else:
                masked_data[masked_key] = value
        
        return masked_data
    
    def mask_log_data(self, data: Any) -> Any:
        """Mask sensitive data for logging"""
        if isinstance(data, str):
            return self.mask_string(data)
        elif isinstance(data, dict):
            return self.mask_dict(data)
        elif isinstance(data, list):
            return [self.mask_log_data(item) for item in data]
        else:
            return data

# Global security mask instance
security_mask = SecurityMask()

def mask_sensitive_data(data: Any) -> Any:
    """Convenience function for masking sensitive data"""
    return security_mask.mask_log_data(data)

def mask_log_function(func):
    """Decorator to mask sensitive data in function logs"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Mask arguments
        masked_args = [security_mask.mask_log_data(arg) for arg in args]
        masked_kwargs = security_mask.mask_dict(kwargs)
        
        # Call original function
        result = func(*args, **kwargs)
        
        # Mask result
        masked_result = security_mask.mask_log_data(result)
        
        return masked_result
    return wrapper

def get_masked_env_vars() -> Dict[str, str]:
    """Get masked environment variables for logging"""
    sensitive_vars = [
        'SAM_API_KEY', 'OPENAI_API_KEY', 'POSTGRES_PASSWORD', 
        'SMTP_PASSWORD', 'SECRET_KEY', 'REDIS_URL'
    ]
    
    masked_vars = {}
    for var in sensitive_vars:
        value = os.getenv(var)
        if value:
            masked_vars[var] = security_mask.mask_string(value)
        else:
            masked_vars[var] = "NOT_SET"
    
    return masked_vars

if __name__ == "__main__":
    # Test the security mask
    print("Testing Security Mask...")
    
    # Test string masking
    test_string = 'API key: sk-1234567890abcdef, password: secret123, email: user@example.com'
    masked_string = security_mask.mask_string(test_string)
    print(f"Original: {test_string}")
    print(f"Masked: {masked_string}")
    
    # Test dictionary masking
    test_dict = {
        'api_key': 'sk-1234567890abcdef',
        'password': 'secret123',
        'email': 'user@example.com',
        'normal_data': 'this is not sensitive'
    }
    masked_dict = security_mask.mask_dict(test_dict)
    print(f"Original dict: {test_dict}")
    print(f"Masked dict: {masked_dict}")
    
    # Test environment variables
    env_vars = get_masked_env_vars()
    print(f"Masked env vars: {env_vars}")
    
    print("Security Mask test completed!")

