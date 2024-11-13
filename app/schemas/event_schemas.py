from datetime import datetime
from fastapi_events.registry.payload_schema import registry as payload_schema
from enum import Enum

from pydantic import BaseModel, EmailStr, validator

from app.db.transaction_model import TransactionType

class UserEvents(Enum):
    BALANCE_UPDATE = "user_balance_update"


class UserBalanceUpdatePayload(BaseModel):
    __event_name__ = UserEvents.BALANCE_UPDATE

    user_id: int
    amount: int
    transaction_id: int
    transaction_type: TransactionType
    full_name: str
    email: EmailStr
    
    

class TransactionEvent(BaseModel):
    user_id: str
    full_name: str
    email: EmailStr
    transaction_amount: float
    transaction_type: str
    transaction_date: datetime
    transaction_id: str

    @validator('user_id')
    def user_id_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('user_id must not be empty')
        return v

    @validator('transaction_type')
    def validate_transaction_type(cls, v):
        valid_types = ['credit', 'debit']
        if v.lower() not in valid_types:
            raise ValueError(f'transaction_type must be one of {valid_types}')
        return v.lower()
