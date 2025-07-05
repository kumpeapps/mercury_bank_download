"""
Category utilities for Mercury Bank sync service.

This module provides helper functions for parsing and handling categories with sub-categories.
"""

from collections import defaultdict


def parse_category(category_string):
    """
    Parse a category string into main category and sub-category.
    
    Args:
        category_string (str): Category string, potentially with sub-category (e.g., "Office/Supplies")
    
    Returns:
        tuple: (main_category, sub_category) or (category, None) if no sub-category
    """
    if not category_string:
        return (None, None)
    
    if '/' in category_string:
        parts = category_string.split('/', 1)  # Split on first '/' only
        return (parts[0].strip(), parts[1].strip())
    else:
        return (category_string.strip(), None)


def get_unique_categories_and_subcategories(db_session, account_ids):
    """
    Get all unique categories and sub-categories from transactions.
    
    Returns:
        dict: {
            'categories': ['Office', 'Travel', ...],
            'subcategories': {
                'Office': ['Supplies', 'Equipment'],
                'Travel': ['Flights', 'Hotels']
            },
            'all_combinations': ['Office', 'Office/Supplies', 'Travel', ...]
        }
    """
    if not account_ids:
        return {'categories': [], 'subcategories': {}, 'all_combinations': []}
    
    from models.transaction import Transaction
    
    # Get all category strings from transactions
    category_results = (
        db_session.query(Transaction.note)
        .filter(Transaction.account_id.in_(account_ids))
        .filter(Transaction.note.isnot(None))
        .distinct()
        .all()
    )
    
    category_strings = [cat[0] for cat in category_results if cat[0]]
    
    categories = set()
    subcategories = defaultdict(set)
    all_combinations = set()
    
    for category_string in category_strings:
        main_cat, sub_cat = parse_category(category_string)
        if main_cat:
            categories.add(main_cat)
            all_combinations.add(main_cat)
            
            if sub_cat:
                subcategories[main_cat].add(sub_cat)
                all_combinations.add(category_string)
    
    # Convert to sorted lists
    sorted_categories = sorted(categories)
    sorted_subcategories = {
        cat: sorted(list(subs)) for cat, subs in subcategories.items()
    }
    sorted_all_combinations = sorted(all_combinations)
    
    return {
        'categories': sorted_categories,
        'subcategories': sorted_subcategories,
        'all_combinations': sorted_all_combinations
    }


def format_category_display(category_string):
    """
    Format a category string for display, highlighting sub-categories.
    
    Args:
        category_string (str): Category string
    
    Returns:
        str: Formatted display string
    """
    if not category_string:
        return "Uncategorized"
    
    main_cat, sub_cat = parse_category(category_string)
    if sub_cat:
        return f"{main_cat} → {sub_cat}"
    else:
        return main_cat
