from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models import Transaction, User
from app.db.transaction_model import TransactionStatus, TransactionType
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.event_schemas import UserBalanceUpdatePayload, UserEvents
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionAnalytics
from app.services.user_service import UserService
from fastapi_events.dispatcher import dispatch


class TransactionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.transaction_repo = TransactionRepository(db)
        self.user_service = UserService(db)

    async def create_transaction(self, data: TransactionCreate) -> Transaction:
        """Create a new transaction."""
        transaction = await self.transaction_repo.create(data)
        dispatch(UserBalanceUpdatePayload(
            user_id=transaction.user_id,
            amount=transaction.transaction_amount * 100,
            transaction_id=transaction.id,
            transaction_type=transaction.transaction_type
        ))
        return transaction

    async def get_transactions(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
    ) -> List[Transaction]:
        """Get all transactions."""
        return await self.transaction_repo.get_all(skip, limit, order_by=order_by)

    async def get_transaction(self, transaction_id: int) -> Optional[Transaction]:
        """Get a specific transaction."""
        return await self.transaction_repo.get(transaction_id)

    async def get_user_transactions(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Transaction]:
        """Get user transactions with optional date filtering."""
        return await self.transaction_repo.get_all(
            skip, limit,
            order_by="transaction_date",
            other_filters={"user_id": user_id})

    async def update_transaction_status(self, transaction_id: int, status: TransactionStatus) -> Transaction:
        """Update a transaction status."""
        transaction = await self.get_transaction(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction with ID {transaction_id} not found")

        transaction.transaction_status = status
        await self.transaction_repo.update(transaction, TransactionUpdate(transaction_status=status))
        return transaction

