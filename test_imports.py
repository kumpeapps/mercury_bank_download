#!/usr/bin/env python3
"""Test script to verify model imports and relationships."""

print("Testing full model import chain...")

try:
    # Import models package first
    import models
    print("✅ models package imported")

    # Now try importing specific models
    from models.user import User
    from models.user_settings import UserSettings
    print("✅ Individual models imported")

    # Test relationship access
    print(f"User.settings: {User.settings}")
    print(f"UserSettings.user: {UserSettings.user}")
    print("✅ Relationships working correctly")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
