"""
Fix for missing thumbnail URLs and content types for attachments.

This script identifies attachments with missing content types or thumbnails
and updates them appropriately. It should be run directly using Docker:

    docker-compose exec web-app python fix_attachments.py

"""

from models.base import create_engine_and_session
from models.transaction_attachment import TransactionAttachment
from datetime import datetime, timedelta
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_attachments():
    """Fix attachments with missing content types and thumbnails."""
    engine, SessionLocal = create_engine_and_session()
    session = SessionLocal()
    
    try:
        # Get all attachments to examine
        all_attachments = session.query(TransactionAttachment).all()
        
        fixed_count = 0
        total_count = len(all_attachments)
        
        logger.info(f"Found {total_count} total attachments to examine")
        
        # Mapping of file extensions to MIME types
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
        
        for attachment in all_attachments:
            was_updated = False
            
            # Report current state
            logger.info(f"Processing attachment: {attachment.id}")
            logger.info(f"  Filename: {attachment.filename}")
            logger.info(f"  Content Type: {attachment.content_type}")
            logger.info(f"  Has Mercury URL: {'Yes' if attachment.mercury_url else 'No'}")
            logger.info(f"  Has Thumbnail URL: {'Yes' if attachment.thumbnail_url else 'No'}")
            
            # Fix content type if missing
            if attachment.content_type is None and attachment.filename:
                # Get file extension
                parts = attachment.filename.split('.')
                if len(parts) > 1:
                    extension = parts[-1].lower()
                    attachment.content_type = extension_map.get(extension, f'application/{extension}')
                    was_updated = True
                    logger.info(f"  Updated content_type to: {attachment.content_type}")
            
            # Fix thumbnail URL for images
            if attachment.thumbnail_url is None and attachment.mercury_url:
                # First check based on content type
                is_image = (attachment.content_type and attachment.content_type.startswith('image/'))
                
                # If no content type, try to determine from filename
                if not is_image and attachment.filename and '.' in attachment.filename:
                    extension = attachment.filename.split('.')[-1].lower()
                    is_image = extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'tif']
                    
                    # If it's an image but content_type is missing, fix that too
                    if is_image and not attachment.content_type:
                        attachment.content_type = extension_map.get(extension, f'image/{extension}')
                        logger.info(f"  Inferred content_type: {attachment.content_type}")
                
                # Set thumbnail URL for images
                if is_image:
                    attachment.thumbnail_url = attachment.mercury_url
                    was_updated = True
                    logger.info("  Set thumbnail_url to mercury_url (image file)")
            
            # Reset URL expiration date if we updated anything
            if was_updated:
                attachment.url_expires_at = datetime.utcnow() + timedelta(hours=12)
                fixed_count += 1
        
        # Commit changes if any were made
        if fixed_count > 0:
            session.commit()
            logger.info(f"✅ Fixed {fixed_count} out of {total_count} attachments")
        else:
            logger.info("No attachments needed fixing")
        
        return True
    
    except Exception as e:
        logger.error(f"Error fixing attachments: {e}")
        session.rollback()
        return False
    
    finally:
        session.close()

if __name__ == "__main__":
    success = fix_attachments()
    sys.exit(0 if success else 1)
