# Chart API UUID Bug Fix Summary

## Issue Discovered
When filtering by specific accounts on the Reports page, the charts would fail to load because the backend API endpoints were throwing `ValueError` exceptions.

## Root Cause
The chart API endpoints (`/api/budget_data` and `/api/expense_breakdown`) in `web_app/app.py` were trying to convert UUID strings to integers:

```python
# BROKEN CODE (Lines 1915 & 2098)
selected_account_ids = [int(aid) for aid in account_ids_param.split(",") if aid.strip()]
```

The problem: **Bank account IDs are UUIDs (strings), not integers!**

Example UUID that was failing: `'867a1270-54fe-11f0-9652-b7f2a577d83a'`

## Error Details
```
ValueError: invalid literal for int() with base 10: '867a1270-54fe-11f0-9652-b7f2a577d83a'
```

This error occurred in:
- `/api/budget_data` (line 1915)
- `/api/expense_breakdown` (line 2098)

## Solution Applied
Changed the problematic lines to keep account IDs as strings instead of converting to integers:

```python
# FIXED CODE
selected_account_ids = [aid.strip() for aid in account_ids_param.split(",") if aid.strip()]
```

## Files Modified
- `web_app/app.py` (2 locations fixed)

## Testing Results
✅ **Before Fix**: All chart API calls with account filtering returned HTTP 500 errors
✅ **After Fix**: All chart API calls work correctly, returning HTTP 200 with proper data

### API Test Results:
```
Budget API (no filter): ✓ 200 OK - labels=13, datasets=4
Budget API (with filter): ✓ 200 OK - labels=13, datasets=0-3
Expense API (no filter): ✓ 200 OK - labels=4, datasets=1  
Expense API (with filter): ✓ 200 OK - labels=0-3, datasets=1
```

## Impact
- **Reports page charts now load properly when filtering by account**
- **No breaking changes to existing functionality**
- **Both individual account and mercury account + bank account filtering work**

## User Experience
- Users can now filter charts by specific accounts without errors
- Charts display appropriate data based on selected accounts
- Empty accounts return empty datasets (expected behavior)
- Accounts with transactions return proper chart data

## Verification
The fix was verified by:
1. Testing all chart API endpoints with various account filters
2. Confirming the Reports page loads correctly in the browser
3. Ensuring backward compatibility with existing filters
4. Testing edge cases (empty accounts, multiple accounts, mercury account filtering)

This resolves the issue where account filtering would break chart functionality on the Reports page.
