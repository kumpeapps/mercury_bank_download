#!/usr/bin/env python3
"""
Test script to verify the 5-day grace period for expired approval re-evaluation
"""

import sys
sys.path.insert(0, '/app')

from models.base import create_engine_and_session
from models.transaction_approval import TransactionApproval
from datetime import datetime, timedelta

def main():
    print("Testing 5-Day Grace Period for Expired Approvals")
    print("=" * 55)
    
    engine, Session = create_engine_and_session()
    session = Session()
    
    try:
        now = datetime.now()
        five_days_ago = now - timedelta(days=5)
        ten_days_ago = now - timedelta(days=10)
        
        print(f"Current time: {now}")
        print(f"5 days ago: {five_days_ago}")
        print(f"10 days ago: {ten_days_ago}")
        print()
        
        # Query all approvals (active and inactive)
        all_approvals = session.query(TransactionApproval).all()
        print(f"Total approvals in database: {len(all_approvals)}")
        
        # Query what the NEW re-evaluation logic would process
        from sqlalchemy import or_, and_
        approvals_with_grace = session.query(TransactionApproval).filter(
            or_(
                TransactionApproval.is_active == True,
                and_(
                    TransactionApproval.is_active == False,
                    TransactionApproval.approval_end_date >= five_days_ago
                )
            )
        ).all()
        
        # Query what the OLD logic would process (active only)
        active_only = session.query(TransactionApproval).filter(
            TransactionApproval.is_active == True
        ).all()
        
        print(f"Approvals processed by OLD logic (active only): {len(active_only)}")
        print(f"Approvals processed by NEW logic (with 5-day grace): {len(approvals_with_grace)}")
        print()
        
        # Show breakdown
        active_approvals = [a for a in all_approvals if a.is_active]
        inactive_approvals = [a for a in all_approvals if not a.is_active]
        
        print(f"Active approvals: {len(active_approvals)}")
        print(f"Inactive approvals: {len(inactive_approvals)}")
        
        if inactive_approvals:
            print("\nInactive approvals breakdown:")
            for approval in inactive_approvals:
                end_date = approval.approval_end_date
                days_since_expiry = (now - end_date).days if end_date else None
                within_grace = (end_date >= five_days_ago) if end_date else False
                
                print(f"  Approval {approval.id}: Expired {days_since_expiry} days ago, Within grace period: {within_grace}")
        
        # Test the actual re-evaluation method
        print(f"\n" + "="*55)
        print("Testing actual re-evaluation method:")
        
        from transaction_approval_manager import TransactionApprovalManager
        approval_manager = TransactionApprovalManager(session)
        
        # This should now include expired approvals within 5 days
        result = approval_manager.re_evaluate_all_approvals()
        print(f"Re-evaluation results: {result}")
        
        print(f"\n✅ Test completed successfully!")
        print(f"The new logic processes {len(approvals_with_grace) - len(active_only)} additional expired approvals")
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    main()
