#!/bin/bash

# Test the before_request handler to ensure users are logged out when they lose permissions

echo "🔐 Testing automatic logout when user permissions change"
echo "============================================="

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Test 1: Create a test user with "user" role
echo "📝 Creating test user with 'user' role..."
cd /Users/justinkumpe/Documents/mercury_bank_download

# Create user directly in the database via docker exec
docker exec mercury_bank_download-web-app-1 python -c "
import sys
sys.path.insert(0, '/app')
from models.user import User
from models.role import Role
from models.base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'mysql+pymysql://user:password@db:3306/mercury_bank')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db_session = Session()

try:
    # Create test user
    user = User(
        username='test-permissions',
        email='test-permissions@test.com'
    )
    user.set_password('testpass123')
    db_session.add(user)
    db_session.commit()
    
    # Assign user role
    user_role = db_session.query(Role).filter_by(name='user').first()
    if user_role:
        user.roles.append(user_role)
        db_session.commit()
        print('✓ User created successfully with user role')
    else:
        print('✗ User role not found')
        
except Exception as e:
    print(f'✗ Error creating user: {e}')
    db_session.rollback()
finally:
    db_session.close()
"

# Test 2: Verify user can log in
echo "🔓 Testing initial login..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:5001/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test-permissions&password=testpass123" \
  -c cookies.txt)

if echo "$LOGIN_RESPONSE" | grep -q "Dashboard"; then
    echo "✅ User successfully logged in"
else
    echo "❌ User failed to log in"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

# Test 3: Access dashboard to verify user is logged in
echo "🏠 Accessing dashboard..."
DASHBOARD_RESPONSE=$(curl -s -b cookies.txt http://localhost:5001/dashboard)

if echo "$DASHBOARD_RESPONSE" | grep -q "Dashboard"; then
    echo "✅ User can access dashboard"
else
    echo "❌ User cannot access dashboard"
    echo "Response: $DASHBOARD_RESPONSE"
    exit 1
fi

# Test 4: Remove the "user" role while user is logged in
echo "🔒 Removing 'user' role from logged-in user..."
docker exec mercury_bank_download-web-app-1 python -c "
import sys
sys.path.insert(0, '/app')
from models.user import User
from models.role import Role
from models.base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.environ.get('DATABASE_URL', 'mysql+pymysql://user:password@db:3306/mercury_bank')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db_session = Session()

try:
    user = db_session.query(User).filter_by(username='test-permissions').first()
    user_role = db_session.query(Role).filter_by(name='user').first()
    
    if user and user_role:
        user.roles.remove(user_role)
        db_session.commit()
        print('✓ User role removed')
    else:
        print('✗ User or role not found')
        
except Exception as e:
    print(f'✗ Error removing role: {e}')
    db_session.rollback()
finally:
    db_session.close()
"

# Test 5: Try to access dashboard again - should be redirected to login
echo "🚪 Attempting to access dashboard after role removal..."
DASHBOARD_RESPONSE_AFTER=$(curl -s -b cookies.txt http://localhost:5001/dashboard)

if echo "$DASHBOARD_RESPONSE_AFTER" | grep -q "Log in"; then
    echo "✅ User was automatically logged out after losing 'user' role"
else
    echo "❌ User was not logged out after losing 'user' role"
    echo "Response: $DASHBOARD_RESPONSE_AFTER"
    exit 1
fi

# Test 6: Test locking a user
echo "🔐 Testing user locking..."
# First, re-assign user role and log in again
./dev.sh assign-role test-permissions user

# Login again
LOGIN_RESPONSE2=$(curl -s -X POST http://localhost:5001/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test-permissions&password=testpass123" \
  -c cookies2.txt)

if echo "$LOGIN_RESPONSE2" | grep -q "Dashboard"; then
    echo "✅ User successfully logged in again"
else
    echo "❌ User failed to log in again"
    echo "Response: $LOGIN_RESPONSE2"
    exit 1
fi

# Now lock the user
echo "🔒 Locking user..."
./dev.sh assign-role test-permissions locked

# Try to access dashboard - should be redirected to login
DASHBOARD_RESPONSE_LOCKED=$(curl -s -b cookies2.txt http://localhost:5001/dashboard)

if echo "$DASHBOARD_RESPONSE_LOCKED" | grep -q "Log in"; then
    echo "✅ User was automatically logged out after being locked"
else
    echo "❌ User was not logged out after being locked"
    echo "Response: $DASHBOARD_RESPONSE_LOCKED"
    exit 1
fi

# Test 7: Try to log in as locked user - should be denied
echo "🚫 Testing login as locked user..."
LOGIN_RESPONSE_LOCKED=$(curl -s -X POST http://localhost:5001/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test-permissions&password=testpass123")

if echo "$LOGIN_RESPONSE_LOCKED" | grep -q "locked"; then
    echo "✅ Locked user was denied login"
else
    echo "❌ Locked user was not denied login"
    echo "Response: $LOGIN_RESPONSE_LOCKED"
    exit 1
fi

# Clean up
echo "🧹 Cleaning up..."
./dev.sh remove-role test-permissions locked
./dev.sh remove-role test-permissions user
./dev.sh delete-user test-permissions 2>/dev/null || true
rm -f cookies.txt cookies2.txt

echo ""
echo "✅ All tests passed! The before_request handler is working correctly:"
echo "   - Users are automatically logged out when they lose the 'user' role"
echo "   - Users are automatically logged out when they gain the 'locked' role"
echo "   - Locked users cannot log in"
echo "   - Permission changes take effect immediately"
