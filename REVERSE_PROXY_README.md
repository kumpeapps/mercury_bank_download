# Mercury Bank Integration - Reverse Proxy Configuration

This guide provides instructions for properly configuring the Mercury Bank Integration Platform to work behind an Nginx reverse proxy.

## Problem Summary

When accessing the Mercury Bank Integration Platform through an Nginx reverse proxy, users were experiencing a blank page after login. This issue occurs because:

1. The Flask application needs to be properly configured to handle proxy headers
2. Nginx needs to pass the correct headers to the Flask application
3. Cookie and session handling need special configuration for HTTPS

## Solution Overview

The solution involves three key components:

1. **Flask Application Configuration**:
   - Added ProxyFix middleware
   - Configured session cookies for secure connections
   - Added proper URL scheme handling

2. **Nginx Configuration**:
   - Added all required proxy headers
   - Configured cookie handling
   - Set appropriate buffer and timeout settings

3. **Docker Environment**:
   - Added environment variables for HTTPS support

## Implementation Steps

### 1. Update Flask Application (Already Completed)

The Flask application has been updated with:

```python
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

app.config.update(
    SESSION_COOKIE_SECURE=os.environ.get("SECURE_COOKIES", "false").lower() == "true",
    SESSION_COOKIE_SAMESITE="Lax",
    PREFERRED_URL_SCHEME=os.environ.get("PREFERRED_URL_SCHEME", "http")
)
```

### 2. Update Nginx Configuration

1. Use the provided `nginx_configuration_updated.conf` file as a reference
2. Key changes:
   - Complete X-Forwarded-* headers set
   - Cookie domain and path configuration
   - Buffer settings
   - Proper passing of request headers

3. Apply the configuration to your Nginx server:
   ```bash
   # Copy to the appropriate location
   sudo cp nginx_configuration_updated.conf /etc/nginx/sites-available/mercury.conf
   
   # Create a symbolic link if using sites-enabled
   sudo ln -s /etc/nginx/sites-available/mercury.conf /etc/nginx/sites-enabled/
   
   # Test the configuration
   sudo nginx -t
   
   # Reload Nginx
   sudo systemctl reload nginx
   ```

### 3. Update Docker Environment

Add these environment variables to your Docker Compose configuration:

```yaml
environment:
  - SECURE_COOKIES=true
  - PREFERRED_URL_SCHEME=https
  - FLASK_DEBUG=false
```

A sample configuration is provided in `docker-compose-proxy-fixed.yml`.

Apply the changes by rebuilding the services:

```bash
./dev.sh rebuild-dev
```

## Verifying the Fix

1. Access your application through the Nginx proxy
2. Check that you can log in successfully without seeing a blank page
3. Verify that redirects work correctly after login
4. Confirm that sessions persist after page refreshes

## Troubleshooting

If you're still experiencing issues, refer to the detailed troubleshooting guide in `REVERSE_PROXY_TROUBLESHOOTING.md`, which includes:

1. Diagnostic steps for header and session issues
2. Debug routes to add to your application
3. Log analysis instructions
4. Advanced configuration options

## Debugging Tools

A debug utility is provided in `flask_proxy_debug.py`. To use it:

1. Add the routes to your Flask application
2. Access the `/debug/proxy` endpoint through your reverse proxy
3. Check the JSON output for any missing or incorrect headers
4. Test session functionality with `/debug/session-test`
5. Test redirects with `/debug/redirect-test`

## Need More Help?

If the blank page issue persists after applying all these changes, you may need to:

1. Check for JavaScript errors in the browser console
2. Verify that all static assets are being loaded correctly
3. Ensure SSL certificates are valid and trusted by the browser
4. Check for mixed content warnings in secure contexts
5. Examine browser cookie settings and permissions

## File Reference

- `nginx_configuration_updated.conf`: Updated Nginx configuration
- `docker-compose-proxy-fixed.yml`: Docker Compose with proxy environment variables
- `flask_proxy_debug.py`: Debug utilities for Flask application
- `REVERSE_PROXY_TROUBLESHOOTING.md`: Detailed troubleshooting guide
- `REVERSE_PROXY_FIX.md`: Documentation of the Flask application changes
- `REVERSE_PROXY_CONFIGURATION.md`: Overview of Nginx configuration changes
