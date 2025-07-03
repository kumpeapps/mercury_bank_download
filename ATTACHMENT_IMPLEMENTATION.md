# Mercury Bank Attachment Data Storage Implementation

## Overview

This document describes the implementation of detailed attachment data storage for Mercury Bank transactions. The system now captures and stores comprehensive metadata about attachments (receipts, invoices, etc.) associated with each transaction.

## What Was Implemented

### 1. Database Schema Changes

#### New Table: `transaction_attachments`
- **id** (VARCHAR(255), PRIMARY KEY) - Mercury attachment ID
- **transaction_id** (VARCHAR(255), FOREIGN KEY) - Reference to transactions table
- **filename** (VARCHAR(500)) - Original filename of the attachment
- **content_type** (VARCHAR(100)) - MIME type (e.g., image/jpeg, application/pdf)
- **file_size** (INT) - Size of the attachment in bytes
- **description** (TEXT) - Description or note about the attachment
- **mercury_url** (TEXT) - Mercury Bank URL for accessing the attachment
- **thumbnail_url** (TEXT) - URL for attachment thumbnail if available
- **upload_date** (DATETIME) - When the attachment was uploaded to Mercury
- **created_at** (DATETIME) - When record was created in our database
- **updated_at** (DATETIME) - When record was last updated

#### Indexes Created
- Primary key on `id`
- Foreign key constraint on `transaction_id` with CASCADE DELETE
- Indexes on `transaction_id`, `filename`, `content_type`, and `upload_date`

### 2. New Models

#### TransactionAttachment Model
Created in both `sync_app/models/` and `web_app/models/` with:
- Complete field definitions matching the database schema
- Helpful property methods:
  - `file_size_formatted` - Human-readable file size (e.g., "1.2 MB")
  - `is_image` - Boolean check if attachment is an image
  - `is_pdf` - Boolean check if attachment is a PDF
  - `file_extension` - Extract file extension from filename
- SQLAlchemy relationship with Transaction model

#### Updated Transaction Model
- Added `attachments` relationship to link with TransactionAttachment
- Configured cascade delete to remove attachments when transaction is deleted

### 3. Sync Service Enhancements

#### New Attachment Sync Method
`sync_transaction_attachments(transaction_id, mercury_api, db_session)`:
- Fetches attachment metadata from Mercury Bank API
- Handles various API response formats flexibly
- Creates or updates attachment records in the database
- Supports multiple API method names (future-proofing)
- Graceful error handling with warnings for failed attachment syncs

#### Integration with Transaction Sync
- Automatically attempts to sync attachments for transactions with `numberOfAttachments > 0`
- Runs attachment sync for both new and updated transactions
- Non-blocking: transaction sync continues even if attachment sync fails
- Detailed logging for debugging and monitoring

### 4. API Enhancements

#### New REST Endpoint
`GET /api/transaction/<transaction_id>/attachments`:
- Returns detailed attachment information for a specific transaction
- Includes access control (user must have access to the transaction's account)
- JSON response with complete attachment metadata
- Formatted file sizes and file type indicators

### 5. Database Migrations

#### Migration Scripts Created
- `004_create_transaction_attachments_table.py` (both sync_app and web_app)
- Idempotent migrations that check for table existence
- Proper foreign key constraints and indexes
- Compatible with existing migration framework

## Mercury Bank API Integration

### Expected API Fields
The sync service looks for these fields in Mercury Bank API responses:

#### Primary Field Names
- `id` - Attachment identifier
- `filename` - Original filename
- `contentType` - MIME type
- `fileSize` - Size in bytes
- `description` - Attachment description
- `url` - Download URL
- `thumbnailUrl` - Thumbnail URL
- `uploadDate` - Upload timestamp

#### Alternative Field Names (Fallbacks)
- `mimeType` (instead of contentType)
- `size` (instead of fileSize)
- `downloadUrl` (instead of url)
- `createdAt` (instead of uploadDate)

### API Method Detection
The system attempts to call Mercury Bank API methods in this order:
1. `get_transaction_attachments(transaction_id)`
2. `get_attachments(transaction_id)`

## Features and Benefits

### 1. Complete Attachment Metadata
- Store comprehensive information about each attachment
- Track file types, sizes, and upload dates
- Maintain Mercury Bank URLs for file access

### 2. Robust Data Handling
- Flexible API response parsing
- Graceful handling of missing or malformed data
- Automatic retry and error recovery

### 3. User Access Control
- Respect existing account access permissions
- Secure API endpoints with authentication
- Filter attachments based on user's account access

### 4. Performance Optimized
- Database indexes for fast queries
- Efficient relationship handling
- Non-blocking attachment sync

### 5. Developer Friendly
- Comprehensive logging and debugging information
- RESTful API design
- Clear error messages and status codes

## Usage Examples

### Query Attachments via API
```bash
# Get attachments for a specific transaction
curl -H "Authorization: Bearer <token>" \
  http://localhost:5001/api/transaction/abc123/attachments
```

### Database Queries
```sql
-- Get all attachments for transactions with receipts
SELECT ta.*, t.description as transaction_description
FROM transaction_attachments ta
JOIN transactions t ON ta.transaction_id = t.id
WHERE ta.content_type LIKE 'image/%';

-- Count attachments by transaction
SELECT t.id, t.description, COUNT(ta.id) as attachment_count
FROM transactions t
LEFT JOIN transaction_attachments ta ON t.id = ta.transaction_id
GROUP BY t.id;
```

### Python/SQLAlchemy Usage
```python
# Get transaction with its attachments
transaction = db_session.query(Transaction).filter(Transaction.id == 'abc123').first()
for attachment in transaction.attachments:
    print(f"File: {attachment.filename} ({attachment.file_size_formatted})")
    print(f"Type: {attachment.content_type}")
    if attachment.is_image:
        print("This is an image file")
```

## Configuration

### Environment Variables
No new environment variables required. The system uses existing Mercury Bank API credentials and database configuration.

### Sync Behavior
- Attachment sync runs automatically during transaction sync
- Controlled by existing `SYNC_DAYS_BACK` and `SYNC_INTERVAL_MINUTES` settings
- Attachment sync failures don't block transaction processing

## Monitoring and Debugging

### Log Messages
- INFO: Successful attachment syncs with counts
- DEBUG: Individual attachment processing
- WARNING: API failures or missing attachment methods
- ERROR: Database errors or critical failures

### Health Checks
The attachment sync integrates with existing health checks and monitoring.

## Future Enhancements

### Potential Improvements
1. **File Download and Storage**: Actually download and store attachment files locally
2. **Attachment Thumbnails**: Generate thumbnails for image attachments
3. **Attachment Search**: Full-text search across attachment descriptions
4. **Attachment Categories**: Classify attachments by type (receipt, invoice, etc.)
5. **Web UI**: Display attachments in the transaction views
6. **File Validation**: Verify file integrity and scan for security issues

### API Extensions
1. **Bulk Attachment Download**: Download multiple attachments as a ZIP
2. **Attachment Upload**: Allow users to add their own attachments
3. **Attachment Sharing**: Share attachments between users with proper permissions

## Migration Notes

### Backward Compatibility
- Existing transaction data remains unchanged
- No breaking changes to existing APIs
- Graceful handling of transactions without attachments

### Rollback Procedure
If needed, the attachment functionality can be rolled back by:
1. Running the migration downgrade function
2. Removing the TransactionAttachment import from models
3. Reverting the sync service changes

## Security Considerations

### Data Protection
- Attachment metadata stored securely in encrypted database
- Mercury Bank URLs are temporary and expire according to Mercury's policies
- User access controls prevent unauthorized attachment access

### API Security
- All attachment endpoints require authentication
- Account-level access control enforced
- Input validation and sanitization applied

## Performance Impact

### Database Impact
- Minimal: Indexes ensure fast queries
- Storage: Small metadata footprint per attachment
- Relationships: Efficient CASCADE DELETE handling

### Sync Performance
- Attachment sync runs in parallel with transaction processing
- Non-blocking: failures don't affect main sync process
- Optimized: Only processes transactions with attachments

## Testing

### Automated Testing
The implementation includes comprehensive error handling and graceful degradation for various scenarios:
- Mercury Bank API method availability
- Network connectivity issues
- Malformed API responses
- Database connectivity problems

### Manual Testing
1. Run a sync cycle and check logs for attachment processing
2. Query the `transaction_attachments` table to verify data
3. Test the attachment API endpoint with a valid transaction ID
4. Verify access control with users having different account permissions

## Summary

This implementation provides a robust, scalable foundation for managing Mercury Bank transaction attachments. It maintains compatibility with existing systems while adding powerful new capabilities for attachment tracking and management. The flexible API integration ensures compatibility with future Mercury Bank API changes, and the comprehensive error handling ensures system reliability.
