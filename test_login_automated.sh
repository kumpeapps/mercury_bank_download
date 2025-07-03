#!/bin/bash

# This script tests if the test-roles user can log in and access Mercury account pages

echo "Testing test-roles user login and Mercury account access..."

# Step 1: Test login
echo "Attempting to log in as test-roles..."
# First get the login page to grab any session cookies
curl -s -c cookies.txt http://localhost:5001/login > /dev/null

# Now post the login form with those cookies
RESPONSE=$(curl -s -b cookies.txt -c cookies.txt -L -X POST http://localhost:5001/login \
  -d "username=test-roles&password=testpassword" \
  -H "Content-Type: application/x-www-form-urlencoded")

# Check if we reached the dashboard page or redirected back to login
if [[ $RESPONSE == *"Dashboard"* ]]; then
  echo "✅ Login successful! Redirected to dashboard."
elif [[ $RESPONSE == *"Invalid username or password"* ]]; then
  echo "❌ Login failed due to invalid credentials!"
  rm cookies.txt
  exit 1
else
  # Let's try to load the dashboard directly to see if we're logged in
  DASHBOARD=$(curl -s -b cookies.txt -L http://localhost:5001/)
  if [[ $DASHBOARD == *"Dashboard"* ]]; then
    echo "✅ Login successful! Can access dashboard."
  else
    echo "❌ Login might have failed, redirected to: ${RESPONSE:0:100}..."
    echo "Response snippet: ${RESPONSE:0:200}..."
    rm cookies.txt
    exit 1
  fi
fi

# Step 2: Check if we can access the Mercury accounts page
echo "Checking access to Mercury accounts page..."
ACCOUNTS_PAGE=$(curl -s -b cookies.txt -L http://localhost:5001/accounts)

if [[ $ACCOUNTS_PAGE == *"Mercury Bank Accounts"* || $ACCOUNTS_PAGE == *"Accounts"* ]]; then
  echo "✅ Can access Mercury accounts page!"
else
  echo "❌ Cannot access Mercury accounts page!"
  echo "Response snippet: ${ACCOUNTS_PAGE:0:200}..."
  rm cookies.txt
  exit 1
fi

# Step 3: Check if we can access the Add Mercury Account page
# Step 3: Check that we CANNOT access the Add Mercury Account page (should be admin only)
echo "Checking that Add Mercury Account page is restricted..."
ADD_ACCOUNT_PAGE=$(curl -s -b cookies.txt -L http://localhost:5001/add_mercury_account)

if [[ $ADD_ACCOUNT_PAGE == *"Access denied"* || $ADD_ACCOUNT_PAGE == *"Admin privileges required"* ]]; then
  echo "✅ Correctly denied access to Add Mercury Account page (admin only)!"
else
  echo "❌ ERROR: User with only 'user' role was able to access the Add Mercury Account page!"
  echo "Response snippet: ${ADD_ACCOUNT_PAGE:0:200}..."
  rm cookies.txt
  exit 1
fi

# Step 4: Check that we CANNOT edit accounts (should be admin only)
echo "Checking that Edit Account page is restricted..."
EDIT_ACCOUNT_PAGE=$(curl -s -b cookies.txt -L http://localhost:5001/edit_account/1)

if [[ $EDIT_ACCOUNT_PAGE == *"Access denied"* || $EDIT_ACCOUNT_PAGE == *"Admin privileges required"* ]]; then
  echo "✅ Correctly denied access to Edit Account page (admin only)!"
else
  echo "❌ ERROR: User with only 'user' role was able to access the Edit Account page!"
  echo "Response snippet: ${EDIT_ACCOUNT_PAGE:0:200}..."
  rm cookies.txt
  exit 1
fi

# Step 5: Check that we CANNOT edit Mercury accounts (should be admin only)
echo "Checking that Edit Mercury Account page is restricted..."
EDIT_MERCURY_ACCOUNT_PAGE=$(curl -s -b cookies.txt -L http://localhost:5001/edit_mercury_account/1)

if [[ $EDIT_MERCURY_ACCOUNT_PAGE == *"Access denied"* || $EDIT_MERCURY_ACCOUNT_PAGE == *"Admin privileges required"* ]]; then
  echo "✅ Correctly denied access to Edit Mercury Account page (admin only)!"
else
  echo "❌ ERROR: User with only 'user' role was able to access the Edit Mercury Account page!"
  echo "Response snippet: ${EDIT_MERCURY_ACCOUNT_PAGE:0:200}..."
  rm cookies.txt
  exit 1
fi
# Cleanup
rm cookies.txt

echo "All tests passed! The test-roles user can log in and view Mercury accounts, but cannot add or edit accounts (admin only)."
