"""
Add separate receipt requirements for deposits and charges

This migration adds separate receipt requirement fields for deposits (positive amounts)
and charges (negative amounts) to provide more granular control over when receipts
are required.

New fields:
- receipt_required_deposits: Receipt requirement for deposits ('none', 'always', 'threshold')
- receipt_threshold_deposits: Dollar amount threshold for deposit receipt requirement
- receipt_required_charges: Receipt requirement for charges ('none', 'always', 'threshold')
- receipt_threshold_charges: Dollar amount threshold for charge receipt requirement

The existing receipt_required and receipt_threshold fields are preserved for backward compatibility
and will be used as defaults when the new fields are not set.
"""

from sqlalchemy import text


def upgrade(engine):
    """Add separate receipt requirement columns for deposits and charges"""
    with engine.connect() as conn:
        # Check if receipt_required_deposits column exists, add if not
        result = conn.execute(text("""
            SELECT COUNT(*) as count FROM information_schema.columns 
            WHERE table_name = 'accounts' AND column_name = 'receipt_required_deposits'
        """))
        if result.fetchone()[0] == 0:
            conn.execute(text("""
                ALTER TABLE accounts 
                ADD COLUMN receipt_required_deposits VARCHAR(20) DEFAULT 'none'
            """))
        
        # Check if receipt_threshold_deposits column exists, add if not
        result = conn.execute(text("""
            SELECT COUNT(*) as count FROM information_schema.columns 
            WHERE table_name = 'accounts' AND column_name = 'receipt_threshold_deposits'
        """))
        if result.fetchone()[0] == 0:
            conn.execute(text("""
                ALTER TABLE accounts 
                ADD COLUMN receipt_threshold_deposits FLOAT NULL
            """))
        
        # Check if receipt_required_charges column exists, add if not
        result = conn.execute(text("""
            SELECT COUNT(*) as count FROM information_schema.columns 
            WHERE table_name = 'accounts' AND column_name = 'receipt_required_charges'
        """))
        if result.fetchone()[0] == 0:
            conn.execute(text("""
                ALTER TABLE accounts 
                ADD COLUMN receipt_required_charges VARCHAR(20) DEFAULT 'none'
            """))
        
        # Check if receipt_threshold_charges column exists, add if not
        result = conn.execute(text("""
            SELECT COUNT(*) as count FROM information_schema.columns 
            WHERE table_name = 'accounts' AND column_name = 'receipt_threshold_charges'
        """))
        if result.fetchone()[0] == 0:
            conn.execute(text("""
                ALTER TABLE accounts 
                ADD COLUMN receipt_threshold_charges FLOAT NULL
            """))
        
        conn.commit()


def downgrade(engine):
    """Remove separate receipt requirement columns"""
    with engine.connect() as conn:
        # Check if receipt_threshold_charges column exists, drop if it does
        result = conn.execute(text("""
            SELECT COUNT(*) as count FROM information_schema.columns 
            WHERE table_name = 'accounts' AND column_name = 'receipt_threshold_charges'
        """))
        if result.fetchone()[0] > 0:
            conn.execute(text("ALTER TABLE accounts DROP COLUMN receipt_threshold_charges"))
            
        # Check if receipt_required_charges column exists, drop if it does
        result = conn.execute(text("""
            SELECT COUNT(*) as count FROM information_schema.columns 
            WHERE table_name = 'accounts' AND column_name = 'receipt_required_charges'
        """))
        if result.fetchone()[0] > 0:
            conn.execute(text("ALTER TABLE accounts DROP COLUMN receipt_required_charges"))
            
        # Check if receipt_threshold_deposits column exists, drop if it does
        result = conn.execute(text("""
            SELECT COUNT(*) as count FROM information_schema.columns 
            WHERE table_name = 'accounts' AND column_name = 'receipt_threshold_deposits'
        """))
        if result.fetchone()[0] > 0:
            conn.execute(text("ALTER TABLE accounts DROP COLUMN receipt_threshold_deposits"))
            
        # Check if receipt_required_deposits column exists, drop if it does
        result = conn.execute(text("""
            SELECT COUNT(*) as count FROM information_schema.columns 
            WHERE table_name = 'accounts' AND column_name = 'receipt_required_deposits'
        """))
        if result.fetchone()[0] > 0:
            conn.execute(text("ALTER TABLE accounts DROP COLUMN receipt_required_deposits"))
            
        conn.commit()
