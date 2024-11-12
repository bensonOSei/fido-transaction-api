from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from app.db.transaction_model import TransactionType
from app.schemas.user import UserResponse


class TransactionBase(BaseModel):
    transaction_date: datetime
    transaction_type: TransactionType
    description: Optional[str] = Field(None, max_length=500)


class TransactionCreate(TransactionBase):
    user_id: int
    transaction_amount: Decimal = Field(..., ge=Decimal('0.01'))

    @validator('transaction_amount', pre=True)
    def amount_to_cents(cls, v):
        return int(v * 100)

class TransactionUpdate(BaseModel):
    transaction_date: Optional[datetime] = None
    transaction_amount: Optional[Decimal] = Field(None, ge=Decimal('0.01'))
    transaction_type: Optional[TransactionType] = None
    description: Optional[str] = Field(None, max_length=500)

    @validator('transaction_amount')
    def validate_amount(cls, v):
        if v is not None:
            return Decimal(str(v)).quantize(Decimal('0.01'))
        return v


class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    transaction_amount: Decimal
    created_at: datetime
    updated_at: Optional[datetime]
    # user: Optional[UserResponse]
    
    @validator('transaction_amount', pre=True)
    def amount_to_cents(cls, v):
        return (Decimal(v) / 100).quantize(Decimal('0.01'))

    class Config:
        from_attributes = True


class TransactionWithoutUserResponse(TransactionResponse):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    transaction_amount: Decimal
    
    @validator('transaction_amount')
    def amount_to_cents(cls, v: Decimal):
        return v / 100

    class Config:
        from_attributes = True


class TransactionAnalytics(BaseModel):
    user_id: int
    average_transaction_value: Decimal
    highest_transaction_day: datetime
    total_credits: Optional[Decimal]
    total_debits: Optional[Decimal]
    
    @validator('average_transaction_value', pre=True)
    def convert_average_transaction_to_currency(cls, v):
        # to 2 decimal places
        return (Decimal(v) / 100).quantize(Decimal('0.01'))
    
    @validator('total_credits', pre=True)
    def convert_total_credits_to_currency(cls, v):
        # to 2 decimal places
        return (Decimal(v) / 100).quantize(Decimal('0.01'))
    
    @validator('total_debits', pre=True)
    def convert_total_debits_to_currency(cls, v):
        # to 2 decimal places
        return (Decimal(v) / 100).quantize(Decimal('0.01'))

    class Config:
        from_attributes = True
