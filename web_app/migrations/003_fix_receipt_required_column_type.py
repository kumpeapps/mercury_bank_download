"""
Fix receipt_required column type from boolean to varchar

This migration fixes the receipt_required column type from tinyint(1) 
to varchar(20) to properly store the receipt requirement values:
'none', 'always', 'threshold'
"""

from sqlalchemy import text


def upgrade(engine):
    """Fix receipt_required column type from boolean to varchar"""
    with engine.connect() as conn:
        # Check current column type
        result = conn.execute(text("""
            SELECT DATA_TYPE FROM information_schema.columns 
            WHERE table_name = 'accounts' AND column_name = 'receipt_required'
        """))
        
        current_type = result.fetchone()
        if current_type and current_type[0] == 'tinyint':
            # Column exists but is wrong type, need to alter it
            # First, alter the column type to varchar (this will convert 0->0, 1->1)
            conn.execute(text("""
                ALTER TABLE accounts 
                MODIFY COLUMN receipt_required VARCHAR(20) DEFAULT 'none'
            """))
            
            # Now update the values: '0' -> 'none', '1' -> 'always'
            conn.execute(text("""
                UPDATE accounts 
                SET receipt_required = CASE 
                    WHEN receipt_required = '1' THEN 'always'
                    ELSE 'none'
                END
            """))
        elif not current_type:
            # Column doesn't exist, create it with correct type
            conn.execute(text("""
                ALTER TABLE accounts 
                ADD COLUMN receipt_required VARCHAR(20) DEFAULT 'none'
            """))
        
        conn.commit()


def downgrade(engine):
    """Revert receipt_required column type back to boolean"""
    with engine.connect() as conn:
        # Convert string values back to boolean: 'none' -> 0, anything else -> 1
        conn.execute(text("""
            UPDATE accounts 
            SET receipt_required = CASE 
                WHEN receipt_required = 'none' THEN 0
                ELSE 1
            END
        """))
        
        # Alter column type back to tinyint
        conn.execute(text("""
            ALTER TABLE accounts 
            MODIFY COLUMN receipt_required TINYINT(1) DEFAULT 0
        """))
        
        conn.commit()
