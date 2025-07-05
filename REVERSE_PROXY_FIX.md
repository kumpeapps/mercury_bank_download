# Reverse Proxy Configuration Fix

## Problem
The Flask application was showing a blank white page after login when running behind a reverse proxy. This is a common issue when a Flask application runs as HTTP behind a reverse proxy that serves HTTPS.

## Solution Applied
1. Added Werkzeug's ProxyFix middleware to properly handle reverse proxy headers
2. Added proper session cookie configuration
3. Added proper URL scheme handling
4. Added a proper app.run block (was previously missing)

## Changes Made
1. Added the ProxyFix middleware to app.py:
   ```python
   from werkzeug.middleware.proxy_fix import ProxyFix
   app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)
   ```

2. Added proper session cookie configuration:
   ```python
   app.config.update(
       SESSION_COOKIE_SECURE=os.environ.get("SECURE_COOKIES", "false").lower() == "true",
       SESSION_COOKIE_SAMESITE="Lax",
       PREFERRED_URL_SCHEME=os.environ.get("PREFERRED_URL_SCHEME", "http")
   )
   ```

3. Added a proper app.run block at the end of app.py:
   ```python
   if __name__ == "__main__":
       # Get debug setting from environment or default to False for production
       debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
       app.run(host="0.0.0.0", port=5000, debug=debug)
   ```

## Deployment Instructions
1. Deploy the updated app.py file
2. Add the following environment variables to your production deployment:
   - `SECURE_COOKIES=true` - If your reverse proxy serves HTTPS
   - `PREFERRED_URL_SCHEME=https` - If your reverse proxy serves HTTPS
   - `FLASK_DEBUG=false` - Always use this in production

3. Rebuild the container:
   ```bash
   ./dev.sh rebuild-dev
   ```

## How This Fixes the Issue
The ProxyFix middleware ensures that Flask properly handles the X-Forwarded headers from the reverse proxy. This is critical for:
- Session cookie generation
- URL generation (for redirects)
- Security checks

Without proper proxy handling, Flask might:
- Generate URLs with the wrong protocol (http vs https)
- Set insecure cookies that browsers might reject
- Redirect to incorrect URLs after login

## Additional Recommendations
1. Make sure your reverse proxy is correctly setting these headers:
   - X-Forwarded-For
   - X-Forwarded-Proto
   - X-Forwarded-Host
   - X-Forwarded-Port
   - X-Forwarded-Prefix (if applicable)

2. For Nginx, a common reverse proxy configuration would be:
   ```nginx
   location / {
       proxy_pass http://web-app:5000;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
   }
   ```

3. For Apache:
   ```apache
   ProxyPass / http://web-app:5000/
   ProxyPassReverse / http://web-app:5000/
   RequestHeader set X-Forwarded-Proto "https"
   RequestHeader set X-Forwarded-For "%{REMOTE_ADDR}s"
   ```
