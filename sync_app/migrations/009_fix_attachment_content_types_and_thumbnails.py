"""
Fix missing attachment content types and thumbnails.

This migration looks for attachments with missing content types or thumbnails
and fixes them by inferring the content type from the filename and setting 
thumbnails for image attachments.
"""

from sqlalchemy import text
from models.base import create_engine_and_session
from models.transaction_attachment import TransactionAttachment
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upgrade(db_session=None):
    """Fix attachment content types and thumbnails."""
    try:
        engine, SessionLocal = create_engine_and_session()
        session = SessionLocal() if db_session is None else db_session
        
        # Get all attachments that need fixing
        attachments = (
            session.query(TransactionAttachment)
            .filter(
                (TransactionAttachment.content_type.is_(None)) |
                ((TransactionAttachment.thumbnail_url.is_(None)) & 
                 (TransactionAttachment.mercury_url.isnot(None)))
            )
            .all()
        )
        
        fixed_count = 0
        extension_map = {
            'pdf': 'application/pdf',
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'tiff': 'image/tiff',
            'tif': 'image/tiff',
            'bmp': 'image/bmp',
            'webp': 'image/webp',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'ppt': 'application/vnd.ms-powerpoint',
            'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'txt': 'text/plain',
            'csv': 'text/csv',
            'html': 'text/html',
            'htm': 'text/html',
        }
        
        for attachment in attachments:
            was_updated = False
            
            # Fix content type if missing
            if attachment.content_type is None and attachment.filename:
                # Get file extension
                parts = attachment.filename.split('.')
                if len(parts) > 1:
                    extension = parts[-1].lower()
                    attachment.content_type = extension_map.get(extension, f'application/{extension}')
                    was_updated = True
            
            # Fix thumbnail URL for images
            if attachment.thumbnail_url is None and attachment.mercury_url:
                if attachment.content_type and attachment.content_type.startswith('image/'):
                    # For images, we can use the actual image URL as the thumbnail
                    attachment.thumbnail_url = attachment.mercury_url
                    was_updated = True
            
            # Reset URL expiration date
            if was_updated:
                attachment.url_expires_at = datetime.utcnow() + timedelta(hours=12)
                fixed_count += 1
        
        if fixed_count > 0:
            session.commit()
        
        logger.info(f"Fixed content types and thumbnails for {fixed_count} attachments")
        print(f"✅ Fixed content types and thumbnails for {fixed_count} attachments")
        
        if db_session is None:
            session.close()
        return True
        
    except Exception as e:
        logger.error(f"Error fixing attachment content types and thumbnails: {e}")
        print(f"❌ Error fixing attachment content types and thumbnails: {e}")
        if db_session is None and 'session' in locals():
            session.rollback()
            session.close()
        return False


def downgrade(db_session=None):
    """No downgrade needed - this is a data fix."""
    print("⚠️ No downgrade available for this migration")
    return True


if __name__ == "__main__":
    upgrade()
