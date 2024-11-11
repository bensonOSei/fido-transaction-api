from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, validator


class UserBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)

class UserCreate(UserBase):
    full_name: str
    balance: Decimal = Field(0, ge=Decimal('0.01'))

    @validator('balance')
    def convert_balance_to_cents(cls, v):
        # Convert balance to cents (multiply by 100)
        return int(v * 100)

class UserResponse(UserBase):
    id: int
    full_name: str
    # balance should be in 2-decimal places
    balance: Decimal
    created_at: Optional[datetime]

    @validator('balance')
    def convert_balance_to_decimal(cls, v):
        return Decimal(v) / 100

    class Config:
        from_attributes = True


class UserUpdate(UserBase):
    balance: Optional[int]

    class Config:
        from_attributes = True
