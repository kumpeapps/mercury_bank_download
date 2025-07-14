from sqlalchemy import func, and_, extract
from sqlalchemy.orm import Session
from datetime import datetime, date
from models import Budget, BudgetCategory, Transaction, Account
from typing import List, Dict, Optional, Tuple, Any


def get_budget_progress(session: Session, budget: Budget) -> Dict[str, Any]:
    """
    Calculate budget progress by comparing actual spending vs budgeted amounts.
    
    Args:
        session: Database session
        budget: Budget object
        
    Returns:
        Dictionary containing budget progress data
    """
    result = {
        'budget_id': budget.id,
        'budget_name': budget.name,
        'budget_month': budget.budget_month,
        'categories': [],
        'total_budgeted': 0.0,
        'total_spent': 0.0,
        'total_remaining': 0.0
    }
    
    # Get all budget categories for this budget
    budget_categories = session.query(BudgetCategory).filter(
        BudgetCategory.budget_id == budget.id,
        BudgetCategory.is_active == True
    ).all()
    
    # Get account IDs associated with this budget
    account_ids = [account.id for account in budget.accounts]
    
    if not account_ids:
        # No accounts assigned to budget
        for category in budget_categories:
            result['categories'].append({
                'category_name': category.category_name,
                'budgeted_amount': category.budgeted_amount,
                'spent_amount': 0.0,
                'remaining_amount': category.budgeted_amount,
                'percentage_used': 0.0
            })
            result['total_budgeted'] += category.budgeted_amount
        result['total_remaining'] = result['total_budgeted']
        return result
    
    # Calculate progress for each category
    for category in budget_categories:
        # Get actual spending for this category in the budget month
        # Exclude failed transactions from budget calculations
        spent_amount = session.query(func.sum(Transaction.amount)).filter(
            and_(
                Transaction.account_id.in_(account_ids),
                Transaction.mercury_category == category.category_name,
                extract('year', Transaction.posted_at) == budget.budget_month.year,
                extract('month', Transaction.posted_at) == budget.budget_month.month,
                Transaction.amount < 0,  # Expenses are negative
                Transaction.status != 'failed'  # Exclude failed transactions
            )
        ).scalar() or 0.0
        
        # Convert to positive amount for display
        spent_amount = abs(spent_amount)
        remaining_amount = max(0, category.budgeted_amount - spent_amount)
        percentage_used = (spent_amount / category.budgeted_amount * 100) if category.budgeted_amount > 0 else 0
        
        result['categories'].append({
            'category_name': category.category_name,
            'budgeted_amount': category.budgeted_amount,
            'spent_amount': spent_amount,
            'remaining_amount': remaining_amount,
            'percentage_used': percentage_used
        })
        
        result['total_budgeted'] += category.budgeted_amount
        result['total_spent'] += spent_amount
    
    result['total_remaining'] = max(0, result['total_budgeted'] - result['total_spent'])
    
    return result


def get_available_categories(session: Session, account_ids: List[str], 
                           start_date: Optional[date] = None, 
                           end_date: Optional[date] = None) -> List[str]:
    """
    Get all unique categories from transactions for given accounts and date range.
    
    Args:
        session: Database session
        account_ids: List of account IDs to search
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        List of unique category names
    """
    query = session.query(Transaction.mercury_category).filter(
        Transaction.account_id.in_(account_ids),
        Transaction.mercury_category.isnot(None),
        Transaction.mercury_category != ''
    )
    
    if start_date:
        query = query.filter(Transaction.posted_at >= start_date)
    if end_date:
        query = query.filter(Transaction.posted_at <= end_date)
    
    categories = query.distinct().all()
    return sorted([cat[0] for cat in categories if cat[0]])


def copy_budget_from_previous_month(session: Session, source_budget: Budget, 
                                  target_month: date, target_name: str,
                                  created_by_user_id: int) -> Budget:
    """
    Copy a budget from a previous month to create a new budget.
    
    Args:
        session: Database session
        source_budget: Budget to copy from
        target_month: Target month for new budget (first day of month)
        target_name: Name for the new budget
        created_by_user_id: User ID creating the budget
        
    Returns:
        New Budget object
    """
    # Create new budget
    new_budget = Budget(
        name=target_name,
        mercury_account_id=source_budget.mercury_account_id,
        budget_month=target_month,
        is_active=True,
        created_by_user_id=created_by_user_id
    )
    session.add(new_budget)
    session.flush()  # Get the ID
    
    # Copy budget categories
    for source_category in source_budget.budget_categories:
        if source_category.is_active:
            new_category = BudgetCategory(
                budget_id=new_budget.id,
                category_name=source_category.category_name,
                budgeted_amount=source_category.budgeted_amount,
                is_active=True
            )
            session.add(new_category)
    
    # Copy account associations
    new_budget.accounts = source_budget.accounts
    
    session.commit()
    return new_budget


def validate_budget_access(session: Session, budget: Budget, user_id: int,
                         user_roles: List[str]) -> bool:
    """
    Check if a user has access to a specific budget.
    
    Args:
        session: Database session
        budget: Budget to check access for
        user_id: User ID to check
        user_roles: List of user's role names
        
    Returns:
        True if user has access, False otherwise
    """
    # Check if user has budgets role
    if 'budgets' not in user_roles:
        return False
    
    # Check if user has access to the mercury account
    from models import User
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    # Check if user has access to the mercury account
    mercury_account_ids = [ma.id for ma in user.mercury_accounts]
    if budget.mercury_account_id not in mercury_account_ids:
        return False
    
    return True
