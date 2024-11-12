from decimal import Decimal
from typing import List, Optional
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Transaction
from app.db.transaction_model import TransactionStatus, TransactionType
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.event_schemas import UserBalanceUpdatePayload
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionAnalytics
from app.services.user_service import UserService
from fastapi_events.dispatcher import dispatch


class TransactionService:
    def __init__(self, db: AsyncSession):
        self.transaction_repo = TransactionRepository(db)
        self.user_service = UserService(db)

    async def create_transaction(self, data: TransactionCreate) -> Transaction:
        """Create a new transaction."""
        return await self.transaction_repo.create(data)

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

    async def update_transaction_status(
            self, transaction_id: int, status: TransactionStatus) -> Transaction:
        """Update a transaction status."""
        transaction = await self.get_transaction(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction with ID {transaction_id} not found")

        transaction.transaction_status = status
        await self.transaction_repo.update(transaction, TransactionUpdate(transaction_status=status))
        return transaction

    async def get_transaction_analytics(self, user_id: int) -> TransactionAnalytics:
        """Get transaction analytics for a user."""
        # Create a query for analytics
        query = (
            select(
                func.count().label('total_transactions'),
                func.avg(Transaction.transaction_amount).label('avg_amount'),
                func.max(Transaction.transaction_date).label('max_date'),
                func.sum(
                    case(
                        (Transaction.transaction_type == TransactionType.DEBIT,
                         Transaction.transaction_amount),
                        else_=0
                    )
                ).label('total_debits'),
                func.sum(
                    case(
                        (Transaction.transaction_type == TransactionType.CREDIT,
                         Transaction.transaction_amount),
                        else_=0
                    )
                ).label('total_credits')
            )
            .select_from(Transaction)
            .where(Transaction.user_id == user_id)
        )

        stats = await self.transaction_repo.execute(query)

        if not stats:
            return TransactionAnalytics(
                user_id=user_id,
                average_transaction_value=Decimal(0),
                highest_transaction_day=None,
                total_credits=Decimal(0),
                total_debits=Decimal(0)
            )

        return TransactionAnalytics(
            user_id=user_id,
            average_transaction_value=Decimal(str(stats['avg_amount'] or 0)),
            highest_transaction_day=stats['max_date'],
            total_credits=Decimal(str(stats['total_credits'] or 0)),
            total_debits=Decimal(str(stats['total_debits'] or 0))
        )
