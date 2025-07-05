# Reverse Proxy Configuration Guide for Mercury Bank Integration Platform

This guide outlines the necessary configurations for running the Mercury Bank Integration Platform behind an Nginx reverse proxy.

## Key Changes in the Nginx Configuration

We've made the following changes to your Nginx configuration:

1. **Updated Headers**: Added the required headers for ProxyFix to work correctly:
   - `X-Forwarded-Proto`: Tells Flask what protocol was used (HTTP/HTTPS)
   - `X-Forwarded-Host`: Passes the original host requested by the client
   - `X-Forwarded-Port`: Passes the port that was used for the request
   - `X-Forwarded-Prefix`: Used if your application is mounted at a non-root path

2. **Session Cookie Handling**: Added configuration for proper cookie handling:
   - `proxy_cookie_path`: Ensures cookies are set with the correct path
   - `proxy_cookie_domain`: Maps the domain correctly for cookies

## Flask Application Configuration

The Flask application has been configured to work with a reverse proxy using:

1. **ProxyFix Middleware**: Added to handle the X-Forwarded-* headers
```python
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)
```

2. **Session Configuration**: Set for proper cookie handling behind a proxy
```python
app.config.update(
    SESSION_COOKIE_SECURE=os.environ.get("SECURE_COOKIES", "false").lower() == "true",
    SESSION_COOKIE_SAMESITE="Lax",
    PREFERRED_URL_SCHEME=os.environ.get("PREFERRED_URL_SCHEME", "http")
)
```

## Troubleshooting

If you're still experiencing issues after applying these changes:

1. **Check Log Files**:
   - Flask application logs: Check for any errors in the Flask app
   - Nginx error logs: Look for any proxy-related errors in `/www/wwwlogs/mercury.vm.kumpeapps.com.error.log`

2. **Verify Headers**:
   - You can add a debugging route to your Flask app to print all received headers:
   ```python
   @app.route('/debug-headers')
   def debug_headers():
       return jsonify(dict(request.headers))
   ```

3. **Check Network Traffic**:
   - Use browser developer tools to inspect network requests
   - Look for redirects, cookie issues, or CORS problems

4. **SSL Issues**:
   - If using HTTPS, make sure `SESSION_COOKIE_SECURE=true` in Flask
   - Verify all assets are loaded over HTTPS to prevent mixed content warnings

## Environment Variables

You may need to set these environment variables in your Flask container:

- `SECURE_COOKIES=true` (when using HTTPS)
- `PREFERRED_URL_SCHEME=https` (when using HTTPS)

## Implementation Steps

1. Update your Nginx configuration with the file we've provided (`nginx_configuration_updated.conf`)
2. Restart Nginx: `sudo systemctl restart nginx` or `sudo service nginx restart`
3. Ensure your Flask app is running on port 5001 (or update the proxy_pass accordingly)
4. Test access through your domain

If you're using SSL, make sure Flask is aware of this by setting the appropriate environment variables.
