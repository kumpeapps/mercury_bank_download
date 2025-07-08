#!/usr/bin/env python3

"""
Smart Template Asset Manager
Automatically updates base.html to use local static assets when available,
with CDN fallback for reliability.
"""

import os
import re


def update_base_template():
    """Update base.html to use local assets with CDN fallback"""
    
    template_path = "/app/templates/base.html"
    static_dir = "/app/static"
    
    if not os.path.exists(template_path):
        print(f"❌ Template not found: {template_path}")
        return False
    
    print("🔧 Updating base.html for optimized asset loading...")
    
    try:
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Define asset mappings (local path -> CDN fallback)
        assets = {
            '/static/css/bootstrap.min.css': 'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css',
            '/static/css/fontawesome.min.css': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
            '/static/js/chart.min.js': 'https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js',
            '/static/js/bootstrap.bundle.min.js': 'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js'
        }
        
        # Update CSS links
        bootstrap_css_pattern = r'<link href="https://cdn\.jsdelivr\.net/npm/bootstrap@[^"]*" rel="stylesheet">'
        fontawesome_css_pattern = r'<link href="https://cdnjs\.cloudflare\.com/ajax/libs/font-awesome/[^"]*" rel="stylesheet">'
        
        # Check if local Bootstrap CSS exists
        if os.path.exists(f"{static_dir}/css/bootstrap.min.css"):
            new_bootstrap_css = '''<link href="/static/css/bootstrap.min.css" rel="stylesheet" onerror="this.onerror=null;this.href='https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css';">'''
            content = re.sub(bootstrap_css_pattern, new_bootstrap_css, content)
            print("  ✅ Updated Bootstrap CSS to use local assets with CDN fallback")
        
        # Check if local Font Awesome CSS exists  
        if os.path.exists(f"{static_dir}/css/fontawesome.min.css"):
            new_fontawesome_css = '''<link href="/static/css/fontawesome.min.css" rel="stylesheet" onerror="this.onerror=null;this.href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css';">'''
            content = re.sub(fontawesome_css_pattern, new_fontawesome_css, content)
            print("  ✅ Updated Font Awesome CSS to use local assets with CDN fallback")
        
        # Update JavaScript includes
        chartjs_pattern = r'<script src="https://cdn\.jsdelivr\.net/npm/chart\.js[^"]*"></script>'
        bootstrap_js_pattern = r'<script src="https://cdn\.jsdelivr\.net/npm/bootstrap@[^"]*"></script>'
        
        # Check if local Chart.js exists
        if os.path.exists(f"{static_dir}/js/chart.min.js"):
            new_chartjs = '''<script src="/static/js/chart.min.js" onerror="document.write('<script src=\\"https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js\\"><\\/script>')"></script>'''
            content = re.sub(chartjs_pattern, new_chartjs, content)
            print("  ✅ Updated Chart.js to use local assets with CDN fallback")
        
        # Check if local Bootstrap JS exists
        if os.path.exists(f"{static_dir}/js/bootstrap.bundle.min.js"):
            new_bootstrap_js = '''<script src="/static/js/bootstrap.bundle.min.js" onerror="document.write('<script src=\\"https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js\\"><\\/script>')"></script>'''
            content = re.sub(bootstrap_js_pattern, new_bootstrap_js, content)
            print("  ✅ Updated Bootstrap JS to use local assets with CDN fallback")
        
        # Write the updated content back
        with open(template_path, 'w') as f:
            f.write(content)
        
        print("✅ Template optimization complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error updating template: {e}")
        return False


if __name__ == "__main__":
    update_base_template()
