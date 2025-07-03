"""Role model for role-based access control."""

from sqlalchemy import Column, String, DateTime, Boolean, text, Integer, Table, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


# Association table for many-to-many relationship between users and roles
user_role_association = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
)


class Role(Base):
    """
    SQLAlchemy model representing a role in the system.
    
    Roles define a set of permissions that can be assigned to users.
    Multiple users can have the same role, and a user can have multiple roles.
    
    Attributes:
        id (int): Primary key - unique role identifier
        name (str): Role name (e.g., "admin", "user", "reports")
        description (str): Description of what this role allows
        is_system_role (bool): Whether this is a system-defined role that cannot be deleted
        created_at (datetime): Timestamp when role was created
        updated_at (datetime): Timestamp when role was last updated
        
        users (list): List of User objects who have this role
    """
    
    __tablename__ = "roles"
    
    # Core role fields
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    is_system_role = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )
    
    # Many-to-many relationship with User
    users = relationship(
        "User",
        secondary=user_role_association,
        back_populates="roles"
    )
    
    def __repr__(self):
        """
        Return a string representation of the Role instance.
        
        Returns:
            str: A formatted string showing the role name
        """
        return f"<Role(name='{self.name}')>"
    
    @classmethod
    def get_or_create(cls, session, name, description=None, is_system_role=False):
        """
        Get an existing role by name or create a new one if it doesn't exist.
        
        Args:
            session: SQLAlchemy session
            name (str): Role name
            description (str, optional): Role description
            is_system_role (bool, optional): Whether this is a system role
            
        Returns:
            Role: The existing or newly created role
        """
        role = session.query(cls).filter_by(name=name).first()
        if not role:
            role = cls(
                name=name,
                description=description,
                is_system_role=is_system_role
            )
            session.add(role)
            session.flush()  # Flush to get the ID
        return role
