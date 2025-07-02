"""
Add receipt requirement fields to accounts table

This migration adds receipt_required and receipt_threshold columns 
to the accounts table to enable per-account receipt requirements.
"""

from sqlalchemy import text


def upgrade(engine):
    """Add receipt requirement columns to accounts table"""
    with engine.connect() as conn:
        # Check if receipt_required column exists, add if not
        result = conn.execute(text("""
            SELECT COUNT(*) as count FROM information_schema.columns 
            WHERE table_name = 'accounts' AND column_name = 'receipt_required'
        """))
        if result.fetchone()[0] == 0:
            conn.execute(text("""
                ALTER TABLE accounts 
                ADD COLUMN receipt_required VARCHAR(20) DEFAULT 'none'
            """))
        
        # Check if receipt_threshold column exists, add if not
        result = conn.execute(text("""
            SELECT COUNT(*) as count FROM information_schema.columns 
            WHERE table_name = 'accounts' AND column_name = 'receipt_threshold'
        """))
        if result.fetchone()[0] == 0:
            conn.execute(text("""
                ALTER TABLE accounts 
                ADD COLUMN receipt_threshold FLOAT NULL
            """))
        
        conn.commit()


def downgrade(engine):
    """Remove receipt requirement columns from accounts table"""
    with engine.connect() as conn:
        # Check if receipt_threshold column exists, drop if it does
        result = conn.execute(text("""
            SELECT COUNT(*) as count FROM information_schema.columns 
            WHERE table_name = 'accounts' AND column_name = 'receipt_threshold'
        """))
        if result.fetchone()[0] > 0:
            conn.execute(text("ALTER TABLE accounts DROP COLUMN receipt_threshold"))
            
        # Check if receipt_required column exists, drop if it does
        result = conn.execute(text("""
            SELECT COUNT(*) as count FROM information_schema.columns 
            WHERE table_name = 'accounts' AND column_name = 'receipt_required'
        """))
        if result.fetchone()[0] > 0:
            conn.execute(text("ALTER TABLE accounts DROP COLUMN receipt_required"))
            
        conn.commit()
