from sqlalchemy import (
    Column,
    String,
    DateTime,
    Integer,
    Text,
    ForeignKey,
    text,
)
from sqlalchemy.orm import relationship
from .base import Base


class TransactionAttachment(Base):
    """
    SQLAlchemy model representing an attachment associated with a Mercury Bank transaction.
    
    This model stores detailed information about attachments (receipts, invoices, etc.)
    that are associated with transactions from the Mercury Bank API. Each attachment
    contains metadata such as filename, content type, size, and Mercury-specific identifiers.
    
    Attributes:
        id (str): Primary key - Mercury attachment ID
        transaction_id (str): Foreign key referencing the associated transaction
        filename (str, optional): Original filename of the attachment
        content_type (str, optional): MIME type of the attachment (e.g., image/jpeg, application/pdf)
        file_size (int, optional): Size of the attachment in bytes
        description (str, optional): Description or note about the attachment
        mercury_url (str, optional): Mercury Bank URL for accessing the attachment
        thumbnail_url (str, optional): URL for attachment thumbnail if available
        upload_date (datetime, optional): When the attachment was uploaded to Mercury
        created_at (datetime): Timestamp when record was created in our database
        updated_at (datetime): Timestamp when record was last updated
        
        transaction (Transaction): Related Transaction object
    """
    __tablename__ = "transaction_attachments"

    # Core attachment fields
    id = Column(String(255), primary_key=True)  # Mercury attachment ID
    transaction_id = Column(String(255), ForeignKey("transactions.id"), nullable=False)
    
    # File metadata
    filename = Column(String(500), nullable=True)
    content_type = Column(String(100), nullable=True)  # MIME type
    file_size = Column(Integer, nullable=True)  # Size in bytes
    description = Column(Text, nullable=True)
    
    # Mercury-specific fields
    mercury_url = Column(Text, nullable=True)  # Mercury URL for accessing the file
    thumbnail_url = Column(Text, nullable=True)  # Thumbnail URL if available
    url_expires_at = Column(DateTime(timezone=True), nullable=True)  # When Mercury URLs expire

    # Timing information
    upload_date = Column(DateTime(timezone=True), nullable=True)  # When uploaded to Mercury
    created_at = Column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    # Relationship to transaction
    transaction = relationship("Transaction", back_populates="attachments")

    def __repr__(self):
        """
        Return a string representation of the TransactionAttachment instance.
        
        Returns:
            str: A formatted string showing the attachment ID, filename, and transaction ID
        """
        return f"<TransactionAttachment(id='{self.id}', filename='{self.filename}', transaction_id='{self.transaction_id}')>"

    @property
    def file_size_formatted(self):
        """
        Get human-readable file size.
        
        Returns:
            str: Formatted file size (e.g., "1.2 MB", "156 KB")
        """
        if not self.file_size:
            return "Unknown"
        
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size / (1024 * 1024 * 1024):.1f} GB"

    @property
    def is_image(self):
        """
        Check if attachment is an image.
        
        Returns:
            bool: True if the attachment is an image type
        """
        if not self.content_type:
            return False
        return self.content_type.startswith('image/')

    @property
    def is_pdf(self):
        """
        Check if attachment is a PDF.
        
        Returns:
            bool: True if the attachment is a PDF
        """
        return self.content_type == 'application/pdf'

    @property
    def file_extension(self):
        """
        Get file extension from filename.
        
        Returns:
            str: File extension (e.g., "pdf", "jpg") or empty string if not available
        """
        if not self.filename:
            return ""
        
        parts = self.filename.split('.')
        if len(parts) > 1:
            return parts[-1].lower()
        return ""

    @property
    def is_url_expired(self):
        """
        Check if the Mercury URLs have expired.
        
        Returns:
            bool: True if the URLs are expired or expiration date is unknown
        """
        if not self.url_expires_at:
            return True  # Consider expired if we don't know the expiration
        
        from datetime import datetime
        return datetime.utcnow() > self.url_expires_at.replace(tzinfo=None)
