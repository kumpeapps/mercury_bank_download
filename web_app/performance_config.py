"""
Auto Performance Configuration Module
Automatically applies performance optimizations to Flask app at startup
"""

import os
from flask import Flask, request


def apply_performance_optimizations(app: Flask):
    """Apply automatic performance optimizations to Flask app"""
    
    print("🚀 Applying automatic performance optimizations...")
    
    # Enable compression if available
    try:
        from flask_compress import Compress
        Compress(app)
        print("  ✅ Compression enabled")
    except ImportError:
        print("  ⚠️ flask-compress not available, compression disabled")
    
    # Configure caching
    try:
        from flask_caching import Cache
        cache_config = {
            'CACHE_TYPE': 'simple',
            'CACHE_DEFAULT_TIMEOUT': 300
        }
        cache = Cache(app, config=cache_config)
        print("  ✅ Flask caching enabled")
    except ImportError:
        print("  ⚠️ flask-caching not available, caching disabled")
    
    # Set performance-related config
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year for static files
    
    # Add performance headers
    @app.after_request
    def add_performance_headers(response):
        # Cache static resources
        if '/static/' in str(request.url):
            response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year
            response.headers['Expires'] = 'Thu, 31 Dec 2025 23:59:59 GMT'
        
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Performance headers
        if response.content_type and response.content_type.startswith('text/html'):
            response.headers['Vary'] = 'Accept-Encoding'
        
        return response
    
    # Add static file route for optimized serving
    @app.route('/static/<path:filename>')
    def static_files(filename):
        """Serve static files with optimal caching"""
        from flask import send_from_directory, current_app
        
        static_dir = os.path.join(current_app.root_path, 'static')
        
        # Check if file exists locally
        if os.path.exists(os.path.join(static_dir, filename)):
            response = send_from_directory(static_dir, filename)
            # Add far-future expires header for static assets
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
            response.headers['Expires'] = 'Thu, 31 Dec 2025 23:59:59 GMT'
            return response
        else:
            # File not found, return 404
            from flask import abort
            abort(404)
    
    print("✅ Performance optimizations applied")
    
    return app


def get_performance_stats():
    """Get performance optimization status"""
    static_dir = "/app/static"
    
    stats = {
        'local_bootstrap_css': os.path.exists(f"{static_dir}/css/bootstrap.min.css"),
        'local_bootstrap_js': os.path.exists(f"{static_dir}/js/bootstrap.bundle.min.js"),
        'local_chartjs': os.path.exists(f"{static_dir}/js/chart.min.js"),
        'local_fontawesome': os.path.exists(f"{static_dir}/css/fontawesome.min.css"),
        'optimized': os.path.exists("/app/.static_downloaded")
    }
    
    return stats
