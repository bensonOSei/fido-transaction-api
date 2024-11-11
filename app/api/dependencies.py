from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import AsyncSessionLocal
from app.services.transaction_service import TransactionService
from app.services.user_service import UserService
# from app.services.user_service import UserService

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

def get_transaction_service(
    db: AsyncSession = Depends(get_db)
) -> TransactionService:
    """Dependency for getting transaction service."""
    return TransactionService(db)

def get_user_service(
    db: AsyncSession = Depends(get_db)
) -> UserService:
    """Dependency for getting user service."""
    return UserService(db)