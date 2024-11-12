from decimal import Decimal
import pytest

from app.db.models import Transaction
from app.schemas.transaction import TransactionCreate
from app.services.transaction_service import TransactionService
from sqlalchemy.ext.asyncio import AsyncSession

class TestTransactionService:

    # Creating a transaction successfully stores it in the database
    @pytest.mark.asyncio
    async def test_create_transaction_success(self, mocker):
        # Arrange
        db_session = mocker.Mock(spec=AsyncSession)
        transaction_service = TransactionService(db_session)
        transaction_data = TransactionCreate(user_id=1, transaction_amount=Decimal('100.00'))
        mock_transaction = mocker.Mock(spec=Transaction)
        mocker.patch.object(transaction_service.transaction_repo, 'create', return_value=mock_transaction)

        # Act
        result = await transaction_service.create_transaction(transaction_data)

        # Assert
        transaction_service.transaction_repo.create.assert_called_once_with(transaction_data)
        assert result == mock_transaction

    # Creating a transaction with invalid data raises an error
    @pytest.mark.asyncio
    async def test_create_transaction_invalid_data(self, mocker):
        # Arrange
        db_session = mocker.Mock(spec=AsyncSession)
        transaction_service = TransactionService(db_session)
        invalid_transaction_data = TransactionCreate(user_id=1, transaction_amount=Decimal('-100.00'))
        mocker.patch.object(transaction_service.transaction_repo, 'create', side_effect=ValueError("Invalid data"))

        # Act & Assert
        with pytest.raises(ValueError):
            await transaction_service.create_transaction(invalid_transaction_data)