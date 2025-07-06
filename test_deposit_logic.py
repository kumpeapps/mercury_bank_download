#!/usr/bin/env python3
"""
Test script to verify deposit handling in budget categories.
This script demonstrates how deposits in expense categories affect remaining budget.
"""

def simulate_budget_calculation():
    """Simulate the budget calculation logic used in the app."""
    
    # Example: Groceries category with $500 budget
    budgeted_amount = 500.00
    
    # Simulate transactions (negative = expense, positive = deposit/refund)
    transactions = [
        -120.50,  # Grocery expense
        -85.30,   # Grocery expense  
        -45.20,   # Grocery expense
        +25.00,   # Refund/return at grocery store
        -90.75,   # Grocery expense
    ]
    
    print("=== Budget Calculation Simulation ===")
    print(f"Category: Groceries")
    print(f"Budgeted Amount: ${budgeted_amount:.2f}")
    print()
    print("Transactions:")
    
    total_spending = 0
    for i, transaction in enumerate(transactions, 1):
        if transaction < 0:
            # Expense - add to spending (use absolute value)
            amount = abs(transaction)
            total_spending += amount
            print(f"  {i}. Expense: ${transaction:.2f} -> Adds ${amount:.2f} to spending")
        else:
            # Deposit/refund - subtract from spending (negative amount)
            amount = -transaction
            total_spending += amount  # amount is negative, so this reduces total_spending
            print(f"  {i}. Deposit/Refund: +${transaction:.2f} -> Reduces spending by ${transaction:.2f}")
    
    print()
    print(f"Total Spending: ${total_spending:.2f}")
    
    # Calculate remaining budget
    remaining_budget = budgeted_amount - total_spending
    
    print(f"Remaining Budget: ${budgeted_amount:.2f} - ${total_spending:.2f} = ${remaining_budget:.2f}")
    
    if remaining_budget > 0:
        print(f"Status: ${remaining_budget:.2f} left (UNDER BUDGET)")
    elif remaining_budget < 0:
        print(f"Status: ${abs(remaining_budget):.2f} over (OVER BUDGET)")
    else:
        print("Status: On budget")

if __name__ == "__main__":
    simulate_budget_calculation()
