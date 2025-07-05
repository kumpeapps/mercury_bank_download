"""
This script adds a proper app.run block to the end of app.py if it's missing.
"""

import os

# Get the file path
app_py_path = "/Users/justinkumpe/Documents/mercury_bank_download/web_app/app.py"

# Check if the file ends properly
with open(app_py_path, 'r', encoding='utf-8') as file:
    content = file.read()

# Check if the file already has an app.run block
if "if __name__ == \"__main__\":" not in content and "app.run" not in content:
    # Add the app.run block
    with open(app_py_path, 'a', encoding='utf-8') as file:
        file.write("""

# Run the Flask application if script is executed directly
if __name__ == "__main__":
    # Get debug setting from environment or default to False for production
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=debug)
""")
    print("Added app.run block to app.py")
else:
    print("app.py already has an app.run block")
