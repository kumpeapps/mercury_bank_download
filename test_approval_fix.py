#!/usr/bin/env python3
"""
Final test script to verify that the approval system correctly uses 
note field categories and that gas transactions are properly approved
"""

import sys
sys.path.insert(0, '/app')

from models.base import create_engine_and_session
from models.transaction_approval import TransactionApproval
from models.transaction import Transaction
from category_utils import parse_category

def main():
    print("Testing Approval System Category Fix")
    print("=" * 50)
    
    engine, Session = create_engine_and_session()
    session = Session()
    
    try:
        # 1. Check approval configuration
        approval = session.query(TransactionApproval).first()
        if approval:
            print(f"✓ Found approval: ID {approval.id}")
            print(f"  Category Filter: {approval.category_filter}")
            print(f"  Subcategory Filter: {approval.subcategory_filter}")
            print(f"  Active: {approval.is_active}")
            print(f"  Used: ${approval.used_amount} / ${approval.max_amount if approval.max_amount else 'unlimited'}")
        else:
            print("✗ No approvals found")
            return
            
        # 2. Test category parsing on sample notes
        print(f"\n✓ Testing category parsing:")
        test_notes = ["Gas/Station", "Food/Restaurant", "Regular note"]
        for note in test_notes:
            category, subcategory = parse_category(note)
            print(f"  '{note}' -> Category: '{category}', Subcategory: '{subcategory}'")
            
        # 3. Check gas transactions and their approval status
        print(f"\n✓ Checking gas transactions:")
        gas_transactions = session.query(Transaction).filter(
            Transaction.note.like('%Gas%')
        ).order_by(Transaction.posted_at.desc()).limit(5).all()
        
        approved_count = 0
        violation_count = 0
        
        for t in gas_transactions:
            category, subcategory = parse_category(t.note)
            print(f"  Note: '{t.note}'")
            print(f"    Parsed -> Category: '{category}', Subcategory: '{subcategory}'")
            print(f"    Mercury Category: '{t.mercury_category}'")
            print(f"    Approval Status: {t.approval_status}")
            print(f"    Amount: ${t.amount}")
            
            if t.approval_status == 'approved':
                approved_count += 1
            elif t.approval_status == 'violation':
                violation_count += 1
            print()
            
        # 4. Summary
        print("=" * 50)
        print("SUMMARY:")
        print(f"  Gas transactions found: {len(gas_transactions)}")
        print(f"  Approved: {approved_count}")
        print(f"  Violations: {violation_count}")
        
        if approved_count > 0:
            print("✓ SUCCESS: Gas transactions are being approved!")
        elif violation_count > 0:
            print("✗ ISSUE: Gas transactions still showing as violations")
            print("  This suggests the approval system may not be matching correctly")
        else:
            print("ℹ INFO: No gas transactions found with approval/violation status")
            
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    main()
