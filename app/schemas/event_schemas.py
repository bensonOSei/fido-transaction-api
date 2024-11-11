from fastapi_events.registry.payload_schema import registry as payload_schema
from enum import Enum

from pydantic import BaseModel

from app.db.transaction_model import TransactionType

class UserEvents(Enum):
    BALANCE_UPDATE = "user_balance_update"


class UserBalanceUpdatePayload(BaseModel):
    __event_name__ = UserEvents.BALANCE_UPDATE

    user_id: int
    amount: int
    transaction_id: int
    transaction_type: TransactionType