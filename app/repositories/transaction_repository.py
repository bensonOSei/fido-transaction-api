# transaction_repository.py
from app.db.transaction_model import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.repositories.base_repository import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession

class TransactionRepository(BaseRepository[Transaction, TransactionCreate, TransactionUpdate]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Transaction)