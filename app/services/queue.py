import json
import asyncio
from datetime import datetime
from typing import Dict

import redis.asyncio as redis
from app.core.config import settings


from app.schemas.event_schemas import TransactionEvent
from app.services.email_notification import EmailConfig, EmailNotificationService, TransactionEmailContext



class RedisQueueService:
    def __init__(self, redis_url: str, email_config: EmailConfig):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.processing_queues = {
            "stats": "queue:user_stats",
            "credit": "queue:credit_score",
            "notifications": "queue:notifications"
        }
        self.email_service = EmailNotificationService(
            email_config
        )

    async def publish_transaction(self, transaction: TransactionEvent):
        """Publish transaction to different processing queues"""
        transaction_data = transaction.model_dump_json()
        # Add to each processing queue
        async with self.redis_client.pipeline(transaction=True) as pipe:
            for queue_name in self.processing_queues.values():
                await pipe.lpush(queue_name, transaction_data)
            # For real-time subscribers
            await pipe.publish("transactions:new", transaction_data)
            await pipe.execute()

    async def process_user_stats(self, transaction_data: Dict):
        """Update user statistics"""
        user_id = transaction_data["user_id"]
        amount = transaction_data["transaction_amount"]

        # Update user's transaction count
        today = datetime.now().date().isoformat()
        await self.redis_client.hincrby(f"user:{user_id}:stats", f"tx_count:{today}", 1)

        # Update running average
        avg_key = f"user:{user_id}:avg_transaction"
        current_avg = float(await self.redis_client.get(avg_key) or 0)
        tx_count = int(await self.redis_client.get(f"user:{user_id}:tx_count") or 0) + 1
        new_avg = ((current_avg * (tx_count - 1)) + amount) / tx_count

        async with self.redis_client.pipeline(transaction=True) as pipe:
            await pipe.set(avg_key, new_avg)
            await pipe.set(f"user:{user_id}:tx_count", tx_count)
            await pipe.execute()

    async def process_credit_score(self, transaction_data: Dict):
        """Update credit score metrics"""
        user_id = transaction_data["user_id"]
        amount = transaction_data["transaction_amount"]
        tx_type = transaction_data["transaction_type"]

        # Simple credit score adjustment based on transaction type and amount
        score_key = f"user:{user_id}:credit_score"
        # Default score
        current_score = float(await self.redis_client.get(score_key) or 700)

        # Basic credit score adjustment logic
        if tx_type == "credit":
            # Max 5 points for large deposits
            score_adjustment = min(amount / 1000, 5)
        else:  # debit
            # Max -3 points for large withdrawals
            score_adjustment = max(-amount / 2000, -3)

        # Keep between 300-850
        new_score = max(min(current_score + score_adjustment, 850), 300)
        await self.redis_client.set(score_key, new_score)

    async def process_notifications(self, transaction_data: Dict):
        """Handle notification processing"""
        # user_id = transaction_data["user_id"]
        # amount = transaction_data["transaction_amount"]
        
        email_context = TransactionEmailContext(
            user_id=transaction_data["user_id"],
            full_name=transaction_data["full_name"],
            transaction_amount=transaction_data["transaction_amount"],
            transaction_type=transaction_data["transaction_type"],
            transaction_date=datetime.fromisoformat(transaction_data["transaction_date"]),
            transaction_id=transaction_data['transaction_id'],
        )
        
        user_email = transaction_data['email']

        if user_email:
            # Send email notification
            await self.email_service.send_transaction_notification(
                user_email,
                email_context
            )

    async def start_processing(self):
        """Start processing messages from queues"""
        while True:
            try:
                # Process user stats queue
                if stats_data := await self.redis_client.brpop(
                        self.processing_queues["stats"], timeout=1):
                    await self.process_user_stats(json.loads(stats_data[1]))

                # Process credit score queue
                if credit_data := await self.redis_client.brpop(
                        self.processing_queues["credit"], timeout=1):
                    await self.process_credit_score(json.loads(credit_data[1]))
                
                # Process notifications queue
                if notif_data := await self.redis_client.brpop(
                        self.processing_queues["notifications"], timeout=1):
                    await self.process_notifications(json.loads(notif_data[1]))

            except Exception as e:
                print(f"Error processing message: {e}")
                # Prevent tight loop in case of persistent errors
                await asyncio.sleep(1)
