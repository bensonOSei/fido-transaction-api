from decimal import Decimal
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Enum, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.database import Base

class TransactionType(str, enum.Enum):
    """Enumeration for transaction types"""
    CREDIT = "credit"
    DEBIT = "debit"
    
class TransactionStatus(str, enum.Enum):
    """Enumeration for transaction statuses"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    


class Transaction(Base):
    """Transaction model for storing financial transactions"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    transaction_amount = Column(Integer, nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    transaction_status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="transactions")

    # Indexes for optimization
    __table_args__ = (
        Index('idx_transaction_user_date', 'user_id', 'transaction_date'),
        Index('idx_transaction_type', 'transaction_type'),
        Index('idx_transaction_created_at', 'created_at'),
    )

    @property
    def transaction_amount_cents(self) -> int:
        """Get transaction amount in cents."""
        return Decimal()
    
    @transaction_amount_cents.setter
    def transaction_amount_cents(self, value: int) -> None:
        """Set transaction amount in cents."""
        self.transaction_amount = int(value * 100)
        
    def __repr__(self):
        return f"Transaction(amount=${self.transaction_amount})"
