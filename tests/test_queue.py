from datetime import datetime
from unittest.mock import AsyncMock
import pytest

from app.schemas.event_schemas import TransactionEvent
from app.services.email_notification import EmailConfig
from app.services.queue import RedisQueueService

class TestRedisQueueService:

    # Successfully publish a transaction to all processing queues
    @pytest.mark.asyncio
    async def test_publish_transaction_success(self, mocker):
        # Arrange
        redis_url = "redis://localhost"
        email_config = EmailConfig()
        service = RedisQueueService(redis_url, email_config)
        transaction = TransactionEvent(
            user_id="123",
            full_name="John Doe",
            email="john.doe@example.com",
            transaction_amount=100.0,
            transaction_type="credit",
            transaction_date=datetime.now(),
            transaction_id="tx123"
        )
        mock_redis_client = mocker.patch.object(service, 'redis_client', autospec=True)
        mock_pipeline = mock_redis_client.pipeline.return_value.__aenter__.return_value

        # Act
        await service.publish_transaction(transaction)

        # Assert
        transaction_data = transaction.model_dump_json()
        for queue_name in service.processing_queues.values():
            mock_pipeline.lpush.assert_any_call(queue_name, transaction_data)
        mock_pipeline.publish.assert_called_once_with("transactions:new", transaction_data)
        mock_pipeline.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_transaction_validation(self, mocker):
        # Arrange
        redis_url = "redis://localhost"
        email_config = EmailConfig()
        service = RedisQueueService(redis_url, email_config)

        # Test 1: Empty user_id
        with pytest.raises(ValueError, match="user_id must not be empty"):
            TransactionEvent(
                user_id="",  # This will trigger the validation error
                full_name="Jane Doe",
                email="jane.doe@example.com",
                transaction_amount=50.0,
                transaction_type="credit",  # Use valid type here
                transaction_date=datetime.now(),
                transaction_id="tx124"
            )

        # Test 2: Invalid transaction type
        with pytest.raises(ValueError, match="transaction_type must be one of"):
            TransactionEvent(
                user_id="123",  # Valid user_id
                full_name="Jane Doe",
                email="jane.doe@example.com",
                transaction_amount=50.0,
                transaction_type="invalid_type",  # This will trigger the validation error
                transaction_date=datetime.now(),
                transaction_id="tx124"
            )
