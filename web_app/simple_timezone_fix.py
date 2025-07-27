"""
Comprehensive timezone normalization for Mercury Bank data.

Since Mercury API already provides dates in customer timezone (not UTC),
we normalize all datetimes to timezone-naive for consistent comparisons.
This approach maintains compatibility with existing database schema while
ensuring all datetime operations use consistent timezone-naive comparisons.
"""

from datetime import datetime
from typing import Optional


def get_naive_now() -> datetime:
    """
    Get current datetime as timezone-naive.
    
    Returns:
        datetime: Current datetime without timezone info
    """
    return datetime.now()


def make_naive(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Convert a datetime to timezone-naive.
    
    Args:
        dt: Datetime to convert (can be None)
        
    Returns:
        datetime: Timezone-naive datetime or None
    """
    if dt is None:
        return None
    return dt.replace(tzinfo=None) if dt.tzinfo else dt


def safe_naive_datetime_compare(dt1: Optional[datetime], dt2: Optional[datetime]) -> int:
    """
    Safely compare two datetime objects using timezone-naive comparison.
    
    Args:
        dt1: First datetime to compare
        dt2: Second datetime to compare
        
    Returns:
        int: -1 if dt1 < dt2, 0 if equal, 1 if dt1 > dt2
        Returns 0 if either datetime is None
    """
    if dt1 is None or dt2 is None:
        return 0
    
    # Strip timezone info for naive comparison
    naive_dt1 = make_naive(dt1)
    naive_dt2 = make_naive(dt2)
    
    # Additional safety check after make_naive
    if naive_dt1 is None or naive_dt2 is None:
        return 0
    
    if naive_dt1 < naive_dt2:
        return -1
    elif naive_dt1 > naive_dt2:
        return 1
    else:
        return 0


def naive_datetime_comparison(dt1: Optional[datetime], operator: str, dt2: Optional[datetime]) -> bool:
    """
    Perform timezone-naive datetime comparison using specified operator.
    
    Args:
        dt1: First datetime
        operator: Comparison operator ('>', '<', '>=', '<=', '==', '!=')
        dt2: Second datetime
        
    Returns:
        bool: Result of comparison
    """
    if dt1 is None or dt2 is None:
        return False
    
    naive_dt1 = make_naive(dt1)
    naive_dt2 = make_naive(dt2)
    
    # Additional safety check
    if naive_dt1 is None or naive_dt2 is None:
        return False
    
    if operator == '>':
        return naive_dt1 > naive_dt2
    elif operator == '<':
        return naive_dt1 < naive_dt2
    elif operator == '>=':
        return naive_dt1 >= naive_dt2
    elif operator == '<=':
        return naive_dt1 <= naive_dt2
    elif operator == '==':
        return naive_dt1 == naive_dt2
    elif operator == '!=':
        return naive_dt1 != naive_dt2
    else:
        raise ValueError(f"Unsupported operator: {operator}")


def normalize_for_db_query(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Normalize datetime for database queries to ensure consistent timezone handling.
    
    Args:
        dt: Datetime to normalize
        
    Returns:
        datetime: Normalized datetime for database operations
    """
    return make_naive(dt) if dt is not None else None
