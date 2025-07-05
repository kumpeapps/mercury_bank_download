# Mercury Bank Integration Reverse Proxy Troubleshooting Guide

## Current Status
The Mercury Bank Integration web application is currently showing a blank page after login when running behind an Nginx reverse proxy. This document provides comprehensive troubleshooting steps to resolve the issue.

## Updated Nginx Configuration
The Nginx configuration has been updated to include all the necessary headers and settings for proper reverse proxy functionality with Flask. Key improvements include:
- Complete set of X-Forwarded-* headers
- Cookie handling configuration
- Better buffer settings
- Explicit pass_request_headers directive

## Troubleshooting Steps

### 1. Verify IP Address and Port
First, ensure that the proxy_pass URL is correct:
```nginx
proxy_pass http://172.16.18.18:5001;
```
- Confirm this IP address points to your web-app container
- Verify the port matches your Docker Compose configuration (5001 on host maps to 5000 in container)

### 2. Check Browser Console for Errors
Open your browser's developer tools (F12) and check the Console tab for JavaScript errors that might explain the blank page. Common issues include:
- Mixed content warnings (HTTP resources on HTTPS page)
- CORS issues
- JavaScript syntax errors
- Failed to load resources

### 3. Check Flask Application Logs
```bash
./dev.sh logs-web
```
Look for any errors related to:
- Authentication failures
- Session issues
- Middleware exceptions
- Database connection problems

### 4. Add Debug Route to Flask Application
Add a temporary debug route to app.py to troubleshoot header passing:

```python
@app.route('/debug-headers')
def debug_headers():
    return jsonify({
        'headers': dict(request.headers),
        'env': dict(request.environ),
        'url_scheme': request.environ.get('wsgi.url_scheme', 'unknown'),
        'is_secure': request.is_secure,
        'url': request.url,
        'host': request.host,
    })
```

Then access this route through your proxy to check if all headers are correctly passed.

### 5. Check for TLS/SSL Issues
- If your site uses HTTPS but Flask isn't properly configured for it, session cookies may not work
- Ensure these environment variables are set in your docker-compose.yml:
  ```yaml
  environment:
    - SECURE_COOKIES=true
    - PREFERRED_URL_SCHEME=https
  ```

### 6. Check Nginx Error Logs
```bash
sudo cat /www/wwwlogs/mercury.vm.kumpeapps.com.error.log
```
Look for any proxy-related errors or connection issues.

### 7. Verify Network Connectivity
Ensure the Nginx server can connect to the Flask application:
```bash
curl -v http://172.16.18.18:5001/health
```

### 8. Check Session Cookie Behavior
- Examine cookies in browser developer tools
- Look for issues with domain, path, secure flag, or SameSite attribute
- Ensure cookies aren't being blocked by browser privacy settings

### 9. Test Direct Access
If possible, try accessing the Flask application directly (without the proxy) to confirm it works correctly.

### 10. Additional Flask Configuration
If the above steps don't resolve the issue, try adding these additional configurations to your Flask app:

```python
# Force HTTPS for all generated URLs when behind SSL proxy
if os.environ.get("PREFERRED_URL_SCHEME", "http") == "https":
    class ReverseProxied:
        def __init__(self, app):
            self.app = app

        def __call__(self, environ, start_response):
            environ['wsgi.url_scheme'] = 'https'
            return self.app(environ, start_response)

    app.wsgi_app = ReverseProxied(app.wsgi_app)
```

### 11. Check for Redirect Loops
The blank page might be caused by a redirect loop. Check the Network tab in browser developer tools to see if there are continuous redirects happening.

### 12. Try Different Browser / Incognito Mode
Test with a different browser or in incognito/private mode to rule out browser-specific issues or cached data problems.

## Implementation Plan

1. Apply the updated Nginx configuration from `nginx_configuration_updated.conf`
2. Restart Nginx:
   ```bash
   sudo systemctl restart nginx
   ```
3. Add the debug route to Flask app temporarily
4. Check logs for any errors
5. If needed, update Docker Compose environment variables for HTTPS
6. Rebuild and restart the application:
   ```bash
   ./dev.sh rebuild-dev
   ```

## Docker Environment Variables

Add these environment variables to your docker-compose.yml file for proper HTTPS handling:

```yaml
services:
  web-app:
    environment:
      - SECURE_COOKIES=true
      - PREFERRED_URL_SCHEME=https
      - FLASK_DEBUG=false
```

Remember to rebuild the containers after making these changes.
