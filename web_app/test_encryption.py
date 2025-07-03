#!/usr/bin/env python3
"""
Test script to verify Mercury API key encryption functionality.
"""

import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set a test SECRET_KEY for testing
os.environ['SECRET_KEY'] = 'test-secret-key-for-encryption-testing-12345'

from utils.encryption import encrypt_api_key, decrypt_api_key, EncryptionManager


def test_encryption_utilities():
    """Test the encryption utility functions."""
    print("Testing encryption utilities...")
    
    # Test data
    test_api_key = "test-mercury-api-key-12345"
    
    try:
        # Test encryption
        encrypted = encrypt_api_key(test_api_key)
        print(f"✓ Original API key: {test_api_key}")
        print(f"✓ Encrypted API key: {encrypted}")
        
        # Test decryption
        decrypted = decrypt_api_key(encrypted)
        print(f"✓ Decrypted API key: {decrypted}")
        
        # Verify they match
        if test_api_key == decrypted:
            print("✓ Encryption/decryption test PASSED")
            return True
        else:
            print("✗ Encryption/decryption test FAILED - keys don't match")
            return False
            
    except Exception as e:
        print(f"✗ Encryption test FAILED with error: {str(e)}")
        return False


def test_encryption_manager():
    """Test the EncryptionManager class directly."""
    print("\nTesting EncryptionManager class...")
    
    try:
        manager = EncryptionManager()
        test_key = "another-test-api-key-67890"
        
        encrypted = manager.encrypt(test_key)  
        decrypted = manager.decrypt(encrypted)
        
        print(f"✓ Original: {test_key}")
        print(f"✓ Encrypted: {encrypted}")
        print(f"✓ Decrypted: {decrypted}")
        
        if test_key == decrypted:
            print("✓ EncryptionManager test PASSED")
            return True
        else:
            print("✗ EncryptionManager test FAILED")
            return False
            
    except Exception as e:
        print(f"✗ EncryptionManager test FAILED with error: {str(e)}")
        return False


def test_model_encryption():
    """Test the MercuryAccount model encryption."""
    print("\nTesting MercuryAccount model encryption...")
    
    try:
        from models.mercury_account import MercuryAccount
        
        # Create a test account
        account = MercuryAccount()
        account.name = "Test Account"
        account.sandbox_mode = True
        
        test_api_key = "model-test-api-key-abcdef"
        
        # Set the API key (this should trigger encryption)
        account.api_key = test_api_key
        
        print(f"✓ Set API key: {test_api_key}")
        print(f"✓ Encrypted storage: {account._api_key_encrypted}")
        print(f"✓ Retrieved API key: {account.api_key}")
        print(f"✓ Masked API key: {account.masked_api_key}")
        
        # Verify the retrieved key matches the original
        if account.api_key == test_api_key:
            print("✓ MercuryAccount encryption test PASSED")
            return True
        else:
            print("✗ MercuryAccount encryption test FAILED")
            return False
            
    except Exception as e:
        print(f"✗ MercuryAccount test FAILED with error: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("Mercury API Key Encryption Tests")
    print("=" * 40)
    
    results = []
    
    # Run tests
    results.append(test_encryption_utilities())
    results.append(test_encryption_manager())
    results.append(test_model_encryption())
    
    # Summary
    print("\n" + "=" * 40)
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests PASSED!")
        return True
    else:
        print("✗ Some tests FAILED!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
