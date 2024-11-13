from decimal import ROUND_HALF_UP, Decimal
from sqlalchemy import Column, DateTime, Index, Integer, func
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.utils.encrypted_string import EncryptedString


class User(Base):
    """User model for storing user information"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(EncryptedString, nullable=False)
    balance = Column(Integer, nullable=False, default=0)
    email = Column(EncryptedString, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_user_created_at', 'created_at'),
    )

        
    def __repr__(self):
        return f"User(id={self.id}, balance=${self.balance})"