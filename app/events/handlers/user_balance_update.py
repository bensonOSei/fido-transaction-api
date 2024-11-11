from fastapi import Depends
from fastapi_events.handlers.local import local_handler
from fastapi_events.typing import Event
from app.db.database import engine
from app.db.transaction_model import TransactionStatus, TransactionType
from app.schemas.event_schemas import UserEvents
from app.services.transaction_service import TransactionService
from app.services.user_service import UserService
from sqlalchemy.ext.asyncio import AsyncSession, AsyncConnection
import logging

logger = logging.getLogger(__name__)

async def get_db_conn() -> AsyncConnection:
    """Get database connection."""
    return await engine.connect()

async def get_db_session(
    conn: AsyncConnection = Depends(get_db_conn)
) -> AsyncSession:
    """Get database session using an existing connection."""
    return AsyncSession(conn, expire_on_commit=False)

async def close_db_session(session: AsyncSession):
    """Safely close database session and connection."""
    if not session:
        return
    try:
        await session.close()
        session.sync_session.bind.close()  # Close the underlying connection
    except Exception as e:
        logger.error(f"Error closing database session: {str(e)}")

@local_handler.register(event_name=UserEvents.BALANCE_UPDATE)
async def handle_user_balance_update(event: Event, db_session: AsyncSession = Depends(get_db_session)):
    _, payload = event
    transaction_id = payload['transaction_id']
    
    try:
        user_service = UserService(db_session)
        transaction_service = TransactionService(db_session)
        transaction_type = payload['transaction_type']

        logger.info(f"Processing {transaction_type} transaction {transaction_id} for user {payload['user_id']}")

        if transaction_type == TransactionType.CREDIT:
            await user_service.credit_user(payload['user_id'], payload['amount'])
            await transaction_service.update_transaction_status(
                transaction_id=transaction_id,
                status=TransactionStatus.SUCCESS,
            )
            await db_session.commit()

        elif transaction_type == TransactionType.DEBIT:
            await user_service.debit_user(payload['user_id'], payload['amount'])
            await transaction_service.update_transaction_status(
                transaction_id=transaction_id,
                status=TransactionStatus.SUCCESS,
            )
            await db_session.commit()

        else:
            await transaction_service.update_transaction_status(
                transaction_id=transaction_id,
                status=TransactionStatus.FAILED,
            )
            await db_session.commit()
            raise ValueError(f"Invalid transaction type: {transaction_type}")

        logger.info(f"Successfully processed transaction {transaction_id}")

    except Exception as e:
        logger.error(f"Error processing transaction {transaction_id}: {str(e)}")
        await db_session.rollback()
        # Try to update transaction status to FAILED
        try:
            transaction_service = TransactionService(db_session)
            await transaction_service.update_transaction_status(
                transaction_id=transaction_id,
                status=TransactionStatus.FAILED,
            )
            await db_session.commit()
        except Exception as inner_e:
            logger.error(f"Failed to update transaction {transaction_id} status: {str(inner_e)}")
        raise e

    finally:
        await close_db_session(db_session)