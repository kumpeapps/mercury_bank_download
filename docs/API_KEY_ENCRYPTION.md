# Mercury API Key Encryption

This document describes the implementation of encrypted storage for Mercury Bank API keys in the Mercury Bank sync and web applications.

## Overview

The Mercury Bank applications now encrypt all Mercury API keys at rest using the `SECRET_KEY` environment variable. This provides an additional layer of security for sensitive API credentials stored in the database.

## Implementation Details

### Encryption Method
- **Algorithm**: Fernet symmetric encryption (part of the `cryptography` library)
- **Key Derivation**: PBKDF2-HMAC-SHA256 with 100,000 iterations
- **Salt**: Fixed salt for consistency (`mercury_bank_salt_2025`)
- **Secret Source**: `SECRET_KEY` environment variable

### Model Changes

The `MercuryAccount` model has been updated in both applications:

```python
# Before (plaintext storage)
api_key = Column(String(500), nullable=False)

# After (encrypted storage)
_api_key_encrypted = Column("api_key", String(500), nullable=False)

@property
def api_key(self):
    """Get the decrypted API key."""
    # Handles decryption transparently
    
@api_key.setter  
def api_key(self, value):
    """Set the API key (will be encrypted before storage)."""
    # Handles encryption transparently
```

### Key Features

1. **Transparent Encryption/Decryption**: 
   - API keys are automatically encrypted when set
   - API keys are automatically decrypted when accessed
   - Existing code continues to work without changes

2. **Migration Support**:
   - Gracefully handles existing unencrypted keys
   - Provides migration utility to encrypt existing data
   - Backward compatibility during transition period

3. **Error Handling**:
   - Handles decryption failures gracefully
   - Falls back to assume legacy unencrypted keys
   - Provides clear error messages

## Files Modified

### Sync Application (`sync_app/`)
- `models/mercury_account.py` - Updated model with encryption
- `utils/encryption.py` - Encryption utilities
- `encrypt_api_keys.py` - Migration script
- `test_encryption.py` - Test suite

### Web Application (`web_app/`)
- `models/mercury_account.py` - Updated model with encryption  
- `utils/encryption.py` - Encryption utilities
- `encrypt_api_keys.py` - Migration script
- `test_encryption.py` - Test suite

## Environment Requirements

### Required Environment Variable
```bash
SECRET_KEY=your-secret-key-here
```

**Important**: The `SECRET_KEY` must be:
- At least 32 characters long
- Kept secure and backed up
- Consistent across all application instances
- Never changed after encrypting data (will make existing data unreadable)

### Docker Compose Configuration
The `SECRET_KEY` is already configured in `docker-compose.yml`:

```yaml
x-common-variables: &common-variables
   DATABASE_URL: mysql+pymysql://Bot_mercury:LetmeN2it@172.16.21.10:3306/Bot_mercury
   SECRET_KEY: oA>a@Th"R)~KbPm._Hl)AQwf!"@;sK5>slS1D5L
   # ... other variables
```

## Migration Process

### For New Deployments
No special steps required - encryption will be used automatically for all new API keys.

### For Existing Deployments

1. **Deploy the updated code** with encryption support
2. **Run the migration script** to encrypt existing API keys:

```bash
# For sync_app
cd sync_app
python encrypt_api_keys.py

# For web_app  
cd web_app
python encrypt_api_keys.py
```

3. **Verify the migration** by checking that API keys still work correctly

### Migration Script Features
- Connects to the database using `DATABASE_URL` 
- Finds all Mercury accounts with API keys
- Encrypts unencrypted keys automatically
- Handles already-encrypted keys gracefully
- Provides detailed progress output
- Rolls back on errors

## Testing

Test suites are provided to verify encryption functionality:

```bash
# Test sync_app encryption
cd sync_app
python test_encryption.py

# Test web_app encryption  
cd web_app
python test_encryption.py
```

### Test Coverage
- Encryption utility functions
- EncryptionManager class
- MercuryAccount model integration
- Encryption/decryption round-trip
- Masked API key display

## Security Benefits

1. **At-Rest Encryption**: API keys are encrypted in the database
2. **Key Protection**: Uses strong Fernet encryption with PBKDF2 key derivation
3. **Environment Variable Security**: Encryption key stored separately from database
4. **Transparent Operation**: No impact on application functionality
5. **Migration Safety**: Graceful handling of existing data

## Troubleshooting

### Common Issues

1. **Missing SECRET_KEY**:
   ```
   Error: SECRET_KEY environment variable is required for encryption
   ```
   Solution: Ensure `SECRET_KEY` is set in environment variables

2. **Decryption Failures**:
   ```
   Failed to decrypt data: InvalidToken
   ```
   Solution: Check that `SECRET_KEY` matches the key used for encryption

3. **Migration Errors**:
   ```
   Error during migration: ...
   ```
   Solution: Check database connectivity and permissions

### Testing Encryption
```bash
# Set test environment
export SECRET_KEY="test-key-12345"
export DATABASE_URL="your-db-url"

# Run tests
python test_encryption.py
```

## Security Considerations

1. **SECRET_KEY Management**:
   - Store securely (environment variables, secrets management)
   - Never commit to version control
   - Back up securely
   - Rotate periodically (requires data re-encryption)

2. **Database Security**:
   - Encryption is only one layer of security
   - Database access controls still essential
   - Network security remains important
   - Regular security audits recommended

3. **Application Security**:
   - API keys are decrypted in memory during use
   - Monitor application logs for security issues
   - Use HTTPS for all communications
   - Implement proper authentication and authorization

## Future Enhancements

1. **Key Rotation**: Add support for rotating the SECRET_KEY
2. **Multiple Keys**: Support for multiple encryption keys (versioning)  
3. **Hardware Security**: Integration with hardware security modules (HSMs)
4. **Audit Logging**: Log all API key access and modifications
5. **Key Expiration**: Automatic API key expiration and renewal
