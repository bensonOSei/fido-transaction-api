from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
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
    transaction: TransactionCreate,
    service: TransactionService = Depends(get_transaction_service)
):
    """Create a new transaction."""
    return await service.create_transaction(transaction)


@router.get("/", response_model=List[TransactionResponse])
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
async def get_user_transactions(
    user_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=100),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    service: TransactionService = Depends(get_transaction_service)
):
    """Get all transactions for a user."""

    try:
        return await service.get_user_transactions(
            user_id,
            skip=skip,
            limit=limit,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        return Response.error(e)


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
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
        return updated_transaction
    except Exception as e:
        return Response.error(e)


@router.delete("/{transaction_id}")
async def delete_transaction(
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
        return Response.success(message="Transaction deleted successfully")
    except Exception as e:
        return Response.error(e)


@router.get("/analytics/{user_id}", response_model=TransactionAnalytics)
async def get_transaction_analytics(
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    service: TransactionService = Depends(get_transaction_service)
):
    """Get transaction analytics for a user."""
    try:
        return await service.get_transaction_analytics(user_id, start_date, end_date)
    except Exception as e:
        return Response.error(e)
