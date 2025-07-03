#!/bin/bash

echo "Testing user login and Mercury account functionality"
echo "---------------------------------------------------"

# Define variables
TEST_USER="test-roles"
TEST_PASSWORD="password123"  # This is a placeholder, as we don't know the actual password

echo "1. Setting a known password for the test user..."
docker exec -it mercury_bank_download-mysql-1 mysql -u mercury_user -pmercury_password -e "USE mercury_bank; UPDATE users SET password_hash = '\$2b\$12\$tXQyQCWO2i0T4AdY7xfAMuUnmjxVKX0JYI.oKYbCfvwWfA5fNjHrO' WHERE username = 'test-roles';"

echo "2. Ensuring the test user has the 'user' role..."
USER_ROLE_COUNT=$(docker exec -it mercury_bank_download-mysql-1 mysql -u mercury_user -pmercury_password -e "USE mercury_bank; SELECT COUNT(*) FROM user_roles WHERE user_id = 2 AND role_id = 3;" -N -s)
if [ "$USER_ROLE_COUNT" -eq "0" ]; then
    docker exec -it mercury_bank_download-mysql-1 mysql -u mercury_user -pmercury_password -e "USE mercury_bank; INSERT INTO user_roles (user_id, role_id) VALUES (2, 3);"
    echo "   Added 'user' role to the test user"
else
    echo "   Test user already has the 'user' role"
fi

echo "3. Ensuring the test user has access to a Mercury account..."
MERCURY_ACCOUNT_COUNT=$(docker exec -it mercury_bank_download-mysql-1 mysql -u mercury_user -pmercury_password -e "USE mercury_bank; SELECT COUNT(*) FROM user_mercury_accounts WHERE user_id = 2;" -N -s)
if [ "$MERCURY_ACCOUNT_COUNT" -eq "0" ]; then
    docker exec -it mercury_bank_download-mysql-1 mysql -u mercury_user -pmercury_password -e "USE mercury_bank; INSERT INTO user_mercury_accounts (user_id, mercury_account_id) VALUES (2, 1);"
    echo "   Added Mercury account access to the test user"
else
    echo "   Test user already has access to a Mercury account"
fi

echo "4. User settings check..."
USER_SETTINGS_COUNT=$(docker exec -it mercury_bank_download-mysql-1 mysql -u mercury_user -pmercury_password -e "USE mercury_bank; SELECT COUNT(*) FROM user_settings WHERE user_id = 2;" -N -s)
if [ "$USER_SETTINGS_COUNT" -eq "0" ]; then
    docker exec -it mercury_bank_download-mysql-1 mysql -u mercury_user -pmercury_password -e "USE mercury_bank; INSERT INTO user_settings (user_id, is_admin, primary_mercury_account_id) VALUES (2, 0, 1);"
    echo "   Added user settings for the test user"
else
    echo "   Test user already has user settings"
fi

echo ""
echo "Setup complete! You can now test the following in your browser:"
echo "1. Go to http://localhost:5001/login"
echo "2. Log in with username 'test-roles' and password 'testpassword'"
echo "3. Verify you can navigate to the dashboard and see Mercury accounts"
echo "4. Try to add a new Mercury account"
echo ""
echo "Note: If you see any issues with login, you may need to rebuild the application:"
echo "./dev.sh rebuild-dev"
