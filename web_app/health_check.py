#!/usr/bin/env python3
"""
Health check script for the Mercury Bank web application.
"""

import sys
import socket
from sqlalchemy import text

def check_web_server():
    """Check if the Flask web server is responding on port 5000."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex(('localhost', 5000))
        sock.close()
        return result == 0
    except Exception:
        return False

def check_database():
    """Check if database connection is working."""
    try:
        from models.base import create_engine_and_session
        
        engine, SessionLocal = create_engine_and_session()
        db = SessionLocal()
        
        # Simple query to test connection
        result = db.execute(text("SELECT 1"))
        db.close()
        return True
        
    except Exception:
        return False

def main():
    """Run all health checks."""
    checks = {
        'web_server': check_web_server(),
        'database': check_database()
    }
    
    failed_checks = [name for name, passed in checks.items() if not passed]
    
    if failed_checks:
        print(f"Health check failed: {', '.join(failed_checks)}")
        sys.exit(1)
    else:
        print("Health check passed")
        sys.exit(0)

if __name__ == "__main__":
    main()
