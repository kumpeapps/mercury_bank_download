#!/usr/bin/env python3
from werkzeug.security import generate_password_hash

# Generate a password hash for 'testpassword'
password_hash = generate_password_hash('testpassword')
print(f"Generated password hash: {password_hash}")
print(f"SQL command to update user password:")
print(f"UPDATE users SET password_hash = '{password_hash}' WHERE username = 'test-roles';")
