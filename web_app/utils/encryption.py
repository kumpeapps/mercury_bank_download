"""
Encryption utilities for Mercury Bank application.
Uses Fernet symmetric encryption to encrypt sensitive data like API keys.
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionManager:
    """Manages encryption and decryption of sensitive data."""
    
    def __init__(self, secret_key=None):
        """
        Initialize encryption manager with secret key.
        
        Args:
            secret_key (str): Secret key from environment variable
        """
        if secret_key is None:
            secret_key = os.environ.get('SECRET_KEY')
        
        if not secret_key:
            raise ValueError("SECRET_KEY environment variable is required for encryption")
        
        self._fernet = self._create_fernet_key(secret_key)
    
    def _create_fernet_key(self, secret_key):
        """Create a Fernet key from the secret key."""
        # Use a fixed salt for consistency (in production, you might want to store this)
        salt = b'mercury_bank_salt_2025'
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
        return Fernet(key)
    
    def encrypt(self, plaintext):
        """
        Encrypt plaintext string.
        
        Args:
            plaintext (str): String to encrypt
            
        Returns:
            str: Base64 encoded encrypted string
        """
        if not plaintext:
            return plaintext
        
        encrypted_data = self._fernet.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt(self, encrypted_text):
        """
        Decrypt encrypted string.
        
        Args:
            encrypted_text (str): Base64 encoded encrypted string
            
        Returns:
            str: Decrypted plaintext string
        """
        if not encrypted_text:
            return encrypted_text
        
        try:
            encrypted_data = base64.urlsafe_b64decode(encrypted_text.encode())
            decrypted_data = self._fernet.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception as e:
            # If decryption fails, it might be an unencrypted legacy value
            # In production, you might want to handle this differently
            raise ValueError(f"Failed to decrypt data: {str(e)}") from e


# Global instance for easy access
_encryption_manager = None

def get_encryption_manager():
    """Get or create the global encryption manager instance."""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager


def encrypt_api_key(api_key):
    """Convenience function to encrypt an API key."""
    return get_encryption_manager().encrypt(api_key)


def decrypt_api_key(encrypted_api_key):
    """Convenience function to decrypt an API key."""
    return get_encryption_manager().decrypt(encrypted_api_key)
