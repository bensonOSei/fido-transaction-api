from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
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

    async def update_transaction_status(
            self, transaction_id: int, status: TransactionStatus) -> Transaction:
        """Update a transaction status."""
        transaction = await self.get_transaction(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction with ID {transaction_id} not found")

        transaction.transaction_status = status
        await self.transaction_repo.update(transaction, TransactionUpdate(transaction_status=status))
        return transaction
    
    async def _get_user_debit_and_credit(self, user_id: int) -> Tuple[Decimal, Decimal]:
        """Get user debit and credit amounts."""
        transactions = await self.get_user_transactions(user_id)
        if not transactions:
            return Decimal(0), Decimal(0)
        
        debit_amount = sum(transaction.transaction_amount for transaction in transactions if transaction.transaction_type == TransactionType.DEBIT)
        credit_amount = sum(transaction.transaction_amount for transaction in transactions if transaction.transaction_type == TransactionType.CREDIT)
        
        return debit_amount, credit_amount
    
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
                        (Transaction.transaction_type == TransactionType.DEBIT, Transaction.transaction_amount),
                        else_=0
                    )
                ).label('total_debits'),
                func.sum(
                    case(
                        (Transaction.transaction_type == TransactionType.CREDIT, Transaction.transaction_amount),
                        else_=0
                    )
                ).label('total_credits')
            )
            .select_from(Transaction)
            .where(Transaction.user_id == user_id)
        )
        
        # Add this method to your TransactionRepository
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

    async def _get_highest_transaction_date(self, user_id: int) -> datetime:
        """Get the highest transaction date for a user."""
        transactions = await self.get_user_transactions(user_id)
        if not transactions:
            return None
        return max(transactions, key=lambda x: x.transaction_date).transaction_date

    async def _get_user_transaction_average(self, user_id: int) -> Decimal:
        """Get the average transaction value for a user."""
        transactions = await self.get_user_transactions(user_id)
        if not transactions:
            return Decimal(0)
        return Decimal(
            sum(transaction.transaction_amount for transaction in transactions) /
            len(transactions)
        )
