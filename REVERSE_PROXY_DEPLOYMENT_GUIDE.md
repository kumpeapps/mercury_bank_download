# Reverse Proxy Configuration Guide for Mercury Bank Integration

This document explains how to properly configure Nginx as a reverse proxy for the Mercury Bank Integration platform.

## Understanding the Setup

Our application uses a two-tier architecture:
1. **Nginx** - Public-facing web server that handles SSL termination and proxies requests
2. **Flask Application** - Internal web application that processes business logic

## Flask Application Configuration

The Flask application has been configured with the following settings to work properly behind a reverse proxy:

```python
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure ProxyFix middleware for reverse proxy support
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

# Configure session to work properly behind a proxy
app.config.update(
    SESSION_COOKIE_SECURE=os.environ.get("SECURE_COOKIES", "false").lower() == "true",
    SESSION_COOKIE_SAMESITE="Lax",
    PREFERRED_URL_SCHEME=os.environ.get("PREFERRED_URL_SCHEME", "http")
)
```

This configuration ensures the Flask application correctly interprets headers forwarded by Nginx.

## Nginx Configuration

For Nginx to properly proxy requests to the Flask application, it needs to forward the correct headers. Below is the essential Nginx configuration:

```nginx
server {
    listen 80;
    server_name your_domain.com;  # Replace with your domain or IP

    location / {
        proxy_pass http://localhost:5000;  # The port your Flask app runs on
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        proxy_set_header X-Forwarded-Prefix /;
        
        # For WebSockets (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeout settings
        proxy_connect_timeout 75s;
        proxy_read_timeout 300s;
    }
}
```

### Important Headers Explanation

1. **X-Forwarded-For**: Contains the client's real IP address
2. **X-Forwarded-Proto**: Specifies the protocol (HTTP or HTTPS) the client used
3. **X-Forwarded-Host**: Provides the original host requested by the client
4. **X-Forwarded-Port**: Indicates the original port requested by the client
5. **X-Forwarded-Prefix**: Sets any URL path prefix, useful if your app is mounted under a subpath

## SSL Configuration (Recommended for Production)

For production deployments, SSL is strongly recommended:

```nginx
server {
    listen 80;
    server_name your_domain.com;
    # Redirect HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name your_domain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305;
    
    # Same proxy configuration as above
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        proxy_set_header X-Forwarded-Prefix /;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeout settings
        proxy_connect_timeout 75s;
        proxy_read_timeout 300s;
    }
}
```

## Environment Variables

Configure these environment variables in your deployment:

- `SECURE_COOKIES`: Set to "true" when using HTTPS
- `PREFERRED_URL_SCHEME`: Set to "https" when using HTTPS

## Common Issues and Troubleshooting

1. **Blank page after login**: Ensure all headers are correctly passed, especially X-Forwarded-Proto and X-Forwarded-Host.

2. **Redirect loops**: Check that X-Forwarded-Proto is correctly set to "https" when using SSL.

3. **Cookie issues**: Make sure SESSION_COOKIE_SECURE is properly set based on whether you're using HTTPS.

4. **404 errors on static files**: Consider serving static files directly through Nginx by adding a location block.

5. **Connection reset**: Check timeout settings if you have long-running operations.

## Testing the Configuration

After applying the Nginx configuration:

1. Restart Nginx: `sudo systemctl restart nginx` (Linux) or `sudo nginx -s reload` (macOS)
2. Access your application through the domain name
3. Verify headers with browser developer tools
4. Test login functionality and session persistence

## Docker Deployment Considerations

If deploying with Docker, ensure your container network settings allow proper communication between Nginx and the Flask containers. You may need to adjust the `proxy_pass` URL to match your Docker network configuration.
