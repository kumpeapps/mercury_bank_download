#!/usr/bin/env python3
"""
Simple health check script for the Mercury Bank sync service.
"""

import sys
import os
from sqlalchemy import text

try:
    from models.base import create_engine_and_session

    # Test database connection
    engine, SessionLocal = create_engine_and_session()
    db = SessionLocal()

    # Simple query to test connection
    result = db.execute(text("SELECT 1"))
    db.close()

    print("Health check passed")
    sys.exit(0)

except Exception as e:
    print(f"Health check failed: {e}")
    sys.exit(1)
