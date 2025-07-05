"""
Debug utility for Flask application to troubleshoot reverse proxy issues.
Add this to app.py temporarily to debug session and proxy issues.
"""
from flask import jsonify, request

@app.route('/debug/proxy')
def debug_proxy():
    """
    Debug endpoint to check proxy headers and session configuration.
    Access this through your reverse proxy to diagnose issues.
    """
    # Get the WSGI environment
    wsgi_env = {key: str(value) for key, value in request.environ.items() 
               if key.startswith('wsgi.') or key.startswith('HTTP_') or key.startswith('SERVER_')}
    
    # Get headers
    headers = dict(request.headers)
    
    # Check if running behind proxy
    proxy_headers = {
        'X-Forwarded-For': request.headers.get('X-Forwarded-For'),
        'X-Forwarded-Proto': request.headers.get('X-Forwarded-Proto'),
        'X-Forwarded-Host': request.headers.get('X-Forwarded-Host'),
        'X-Forwarded-Port': request.headers.get('X-Forwarded-Port'),
        'X-Forwarded-Prefix': request.headers.get('X-Forwarded-Prefix'),
    }
    
    # Check session configuration
    session_config = {
        'SESSION_COOKIE_SECURE': app.config.get('SESSION_COOKIE_SECURE'),
        'SESSION_COOKIE_SAMESITE': app.config.get('SESSION_COOKIE_SAMESITE'),
        'PREFERRED_URL_SCHEME': app.config.get('PREFERRED_URL_SCHEME'),
    }
    
    # URL generation info
    url_info = {
        'url': request.url,
        'base_url': request.base_url,
        'url_root': request.url_root,
        'host': request.host,
        'host_url': request.host_url,
        'is_secure': request.is_secure,
        'scheme': request.scheme,
    }
    
    # ProxyFix info
    proxy_fix_active = hasattr(app.wsgi_app, '__wrapped__') and 'ProxyFix' in str(app.wsgi_app.__class__)
    
    return jsonify({
        'proxy_fix_active': proxy_fix_active,
        'wsgi_environment': wsgi_env,
        'headers': headers,
        'proxy_headers': proxy_headers,
        'session_config': session_config,
        'url_info': url_info,
        'cookies': {key: str(value) for key, value in request.cookies.items()},
    })

@app.route('/debug/redirect-test')
def debug_redirect_test():
    """
    Tests a redirect to confirm proper URL generation.
    """
    return redirect(url_for('debug_proxy'))

@app.route('/debug/session-test')
def debug_session_test():
    """
    Tests session functionality.
    """
    # Increment counter in session
    if 'counter' not in session:
        session['counter'] = 0
    session['counter'] += 1
    
    # Set a timestamp
    session['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return jsonify({
        'session': {key: str(value) for key, value in session.items()},
        'message': 'Session updated. Refresh to test persistence.'
    })
