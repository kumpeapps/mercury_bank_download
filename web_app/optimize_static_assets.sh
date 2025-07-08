#!/bin/bash

# Auto Performance Optimization Script
# Downloads and optimizes static assets automatically at container startup

set -e

STATIC_DIR="/app/static"
DOWNLOAD_LOCK="/app/.static_downloaded"

# Only download if not already downloaded (for container restarts)
if [ -f "$DOWNLOAD_LOCK" ]; then
    echo "📦 Static assets already optimized, skipping download..."
    return 0 2>/dev/null || exit 0
fi

echo "🚀 Auto-optimizing static assets for better performance..."

# Create static directories with proper permissions
mkdir -p "${STATIC_DIR}"
chmod 755 "${STATIC_DIR}"
mkdir -p "${STATIC_DIR}/css"
mkdir -p "${STATIC_DIR}/js" 
mkdir -p "${STATIC_DIR}/fonts"
mkdir -p "${STATIC_DIR}/webfonts"
chmod 755 "${STATIC_DIR}"/{css,js,fonts,webfonts}

# Function to download with retries
download_with_retry() {
    local url="$1"
    local output="$2"
    local max_attempts=3
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        echo "  Downloading: $(basename "$output") (attempt $attempt/$max_attempts)"
        if curl -L -f -s --connect-timeout 10 --max-time 30 "$url" -o "$output"; then
            echo "  ✅ Downloaded: $(basename "$output")"
            return 0
        else
            echo "  ❌ Failed attempt $attempt for $(basename "$output")"
            attempt=$((attempt + 1))
            [ $attempt -le $max_attempts ] && sleep 2
        fi
    done
    
    echo "  ⚠️ Failed to download $(basename "$output") after $max_attempts attempts"
    return 1
}

# Download Bootstrap CSS and JS
echo "📦 Downloading Bootstrap..."
download_with_retry "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" "${STATIC_DIR}/css/bootstrap.min.css" || true
download_with_retry "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js" "${STATIC_DIR}/js/bootstrap.bundle.min.js" || true

# Download Chart.js
echo "📊 Downloading Chart.js..."
download_with_retry "https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js" "${STATIC_DIR}/js/chart.min.js" || true

# Download Font Awesome CSS
echo "🎨 Downloading Font Awesome..."
download_with_retry "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" "${STATIC_DIR}/css/fontawesome.min.css" || true

# Download Font Awesome fonts
echo "🔤 Downloading Font Awesome fonts..."
download_with_retry "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/webfonts/fa-solid-900.woff2" "${STATIC_DIR}/webfonts/fa-solid-900.woff2" || true
download_with_retry "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/webfonts/fa-regular-400.woff2" "${STATIC_DIR}/webfonts/fa-regular-400.woff2" || true
download_with_retry "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/webfonts/fa-brands-400.woff2" "${STATIC_DIR}/webfonts/fa-brands-400.woff2" || true

# Fix Font Awesome CSS paths to point to local fonts
if [ -f "${STATIC_DIR}/css/fontawesome.min.css" ]; then
    echo "🔧 Fixing Font Awesome CSS paths..."
    sed -i 's|https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/webfonts/|/static/webfonts/|g' "${STATIC_DIR}/css/fontawesome.min.css"
fi

# Create a marker file to prevent re-downloading on container restart
touch "$DOWNLOAD_LOCK"

# Update templates to use local assets with CDN fallback
echo "🔧 Updating templates for optimized asset loading..."
python3 update_template_assets.py

echo "✅ Static asset optimization complete!"
echo "📊 Performance improvements:"
echo "  • Local Bootstrap, Chart.js, and Font Awesome assets"
echo "  • Reduced external CDN dependencies" 
echo "  • Faster loading on slow connections"
echo "  • Better caching control"
echo "  • Automatic CDN fallback for reliability"
