#!/usr/bin/env python3
"""
Verification script for sub-category functionality
"""

# Test category parsing and formatting functions
def parse_category(category_string):
    """Parse a category string into main category and sub-category."""
    if not category_string or '/' not in category_string:
        return category_string, None
    parts = category_string.split('/', 1)
    return parts[0].strip(), parts[1].strip()

def format_category_display(category_string):
    """Format category for display with sub-category arrow notation."""
    main_cat, sub_cat = parse_category(category_string)
    if sub_cat:
        return f'{main_cat} → {sub_cat}'
    return main_cat

def test_subcategory_logic():
    """Test sub-category parsing and formatting logic."""
    print("=== Sub-Category Logic Test ===")
    
    test_cases = [
        "Office/Supplies",
        "Travel/Hotels", 
        "Food/Restaurants",
        "Entertainment/Movies",
        "Office",  # No sub-category
        "Entertainment",  # No sub-category
        "",  # Empty
        None,  # None
        "Complex/Category/With/Multiple/Slashes",  # Multiple slashes
        "  Spaced / Category  ",  # With spaces
    ]
    
    for test_case in test_cases:
        main_cat, sub_cat = parse_category(test_case)
        formatted = format_category_display(test_case)
        print(f"Input: '{test_case}' → Main: '{main_cat}', Sub: '{sub_cat}' → Display: '{formatted}'")
    
    print("✓ Sub-category logic test complete\n")

def test_http_endpoints():
    """Test HTTP endpoints that should return sub-category data."""
    import requests
    
    print("=== HTTP Endpoint Test ===")
    
    try:
        # Test main page accessibility
        response = requests.get('http://localhost:5001', timeout=5)
        print(f"✓ Main page accessible (status: {response.status_code})")
        
        # Test if we can find any sub-category arrows in the response
        if '→' in response.text:
            print("✓ Found sub-category arrows in main page")
        else:
            print("ℹ No sub-category arrows found in main page (expected if not logged in)")
            
    except Exception as e:
        print(f"✗ HTTP test failed: {e}")
    
    print("✓ HTTP endpoint test complete\n")

if __name__ == "__main__":
    test_subcategory_logic()
    test_http_endpoints()
    print("=== Verification Complete ===")
