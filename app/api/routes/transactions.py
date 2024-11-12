from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from app.cache import CacheManager, CacheNamespace, cache_route
from app.api.dependencies import get_transaction_service
from app.schemas.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
    TransactionAnalytics,
    TransactionWithoutUserResponse
)
from app.services.transaction_service import TransactionService
from app.utils.response import Response

router = APIRouter()


@router.post("/", response_model=TransactionWithoutUserResponse)
async def create_transaction(
    request: Request,
    transaction: TransactionCreate,
    service: TransactionService = Depends(get_transaction_service)
):
    """Create a new transaction."""
    try:
        new_transaction = await service.create_transaction(transaction)
        # Invalidate all relevant caches
        cache_manager = CacheManager(request.app.state.redis_client)
        await cache_manager.invalidate_by_namespace(CacheNamespace.TRANSACTION)
        await cache_manager.invalidate_by_namespace(
            CacheNamespace.USER,
            identifier=transaction.user_id
        )
        await cache_manager.invalidate_by_namespace(
            CacheNamespace.ANALYTICS,
            identifier=transaction.user_id
        )

        return new_transaction
    except Exception as e:
        return Response.error(e)


@router.get("/", response_model=List[TransactionResponse])
@cache_route(
    namespace=CacheNamespace.TRANSACTION,
    prefix="list",
    include_params=["skip", "limit"],
    expire=300
)
async def get_transactions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, le=20),
    order_by: Optional[str] = None,
    service: TransactionService = Depends(get_transaction_service)
):
    """Get all transactions."""
    try:
        transactions = await service.get_transactions(
            skip=skip,
            limit=limit,
            order_by=order_by
        )
        return transactions
    except Exception as e:
        return Response.error(e)


@router.get("/{transaction_id}", response_model=TransactionResponse)
@cache_route(
    namespace=CacheNamespace.TRANSACTION,
    prefix="single",
    identifier_param="transaction_id",
    expire=300
)
async def get_transaction(
    transaction_id: int,
    service: TransactionService = Depends(get_transaction_service)
):
    """Get a specific transaction."""
    transaction = await service.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=404, detail="Transaction not found")
    return transaction


@router.get("/user/{user_id}", response_model=List[TransactionResponse])
@cache_route(
    namespace=CacheNamespace.TRANSACTION,
    prefix="user",
    identifier_param="user_id",
    include_params=["skip", "limit"],
    expire=300
)
async def get_user_transactions(
    user_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=100),
    service: TransactionService = Depends(get_transaction_service)
):
    """Get all transactions for a user."""
    try:
        return await service.get_user_transactions(
            user_id,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        return Response.error(e)


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    request: Request,  # Added request parameter
    transaction_id: int,
    user_id: int,
    transaction: TransactionUpdate,
    service: TransactionService = Depends(get_transaction_service)
):
    """Update a transaction."""
    try:
        updated_transaction = await service.update_transaction(
            transaction_id,
            user_id,
            transaction
        )
        if not updated_transaction:
            raise HTTPException(
                status_code=404, detail="Transaction not found")

        # Invalidate caches after update
        cache_manager = CacheManager(request.app.state.redis_client)
        await cache_manager.invalidate_by_namespace(CacheNamespace.TRANSACTION)
        await cache_manager.invalidate_by_namespace(
            CacheNamespace.USER,
            identifier=user_id
        )

        return updated_transaction
    except Exception as e:
        return Response.error(e)


@router.delete("/{transaction_id}")
async def delete_transaction(
    request: Request,  # Added request parameter
    transaction_id: int,
    user_id: int,
    service: TransactionService = Depends(get_transaction_service)
):
    """Delete a transaction."""
    try:
        deleted = await service.delete_transaction(transaction_id, user_id)
        if not deleted:
            raise HTTPException(
                status_code=404, detail="Transaction not found")

        # Invalidate caches after deletion
        cache_manager = CacheManager(request.app.state.redis_client)
        await cache_manager.invalidate_by_namespace(CacheNamespace.TRANSACTION)
        await cache_manager.invalidate_by_namespace(
            CacheNamespace.USER,
            identifier=user_id
        )

        return Response.success(message="Transaction deleted successfully")
    except Exception as e:
        return Response.error(e)


@router.get("/analytics/{user_id}", response_model=TransactionAnalytics)
@cache_route(
    namespace=CacheNamespace.ANALYTICS,
    prefix="transaction",
    identifier_param="user_id",
    expire=600  # 10 minutes for analytics
)
async def get_transaction_analytics(
    user_id: int,
    service: TransactionService = Depends(get_transaction_service)
):
    """Get transaction analytics for a user."""
    try:
        return await service.get_transaction_analytics(user_id)
    except Exception as e:
        return Response.error(e)
