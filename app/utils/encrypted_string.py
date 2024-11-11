from sqlalchemy import TypeDecorator, String
from cryptography.fernet import Fernet
from typing import Optional
import os
import base64

class EncryptedString(TypeDecorator):
    """Custom SQLAlchemy type for encrypted strings"""
    impl = String
    cache_ok = True

    def __init__(self, key: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.key = key or os.getenv('ENCRYPTION_KEY')
        if not self.key:
            raise ValueError("No encryption key provided. Set ENCRYPTION_KEY environment variable")
        
        # Ensure the key is properly formatted
        try:
            # If the key is a string, encode it to bytes
            key_bytes = self.key.encode() if isinstance(self.key, str) else self.key
            
            # Validate the key format
            if not self._is_valid_key(key_bytes):
                raise ValueError("Invalid key format")
            
            self.fernet = Fernet(key_bytes)
        except Exception as e:
            raise ValueError(f"Invalid encryption key: {str(e)}")

    def _is_valid_key(self, key: bytes) -> bool:
        """Validate that the key is properly formatted."""
        try:
            # Check if the key is valid base64
            decoded = base64.urlsafe_b64decode(key)
            # Fernet keys must be 32 bytes
            return len(decoded) == 32
        except Exception:
            return False

    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """Encrypt the value before saving to DB"""
        if value is None:
            return None
        return self.fernet.encrypt(value.encode()).decode()

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """Decrypt the value when loading from DB"""
        if value is None:
            return None
        return self.fernet.decrypt(value.encode()).decode()