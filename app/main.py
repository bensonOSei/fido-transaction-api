import asyncio
from contextlib import asynccontextmanager
from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import transactions, users
from fastapi_events.middleware import EventHandlerASGIMiddleware
from fastapi_events.handlers.local import local_handler
import app.events.handlers.user_balance_update
import redis as sync_redis
from redis.asyncio import Redis

from app.services.email_notification import EmailConfig
from app.services.queue import RedisQueueService

email_config = EmailConfig(
    SMTP_HOST=settings.EMAIL_SMTP_HOST,
    SMTP_PORT=settings.EMAIL_SMTP_PORT,
    SMTP_USER=settings.EMAIL_SMTP_USER,
    SMTP_PASSWORD=settings.EMAIL_SMTP_PASSWORD,
    FROM_EMAIL=settings.EMAIL_FROM_EMAIL,
    ENABLE_NOTIFICATIONS=settings.EMAIL_ENABLE_NOTIFICATIONS
)


async def setup_redis_client():
    redis_client = Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True,
    )
    try:
        await redis_client.ping()
    except Exception as e:
        raise ValueError(f"Redis connection failed: {str(e)}")
    return redis_client


def setup_sync_redis_client():
    redis_client = sync_redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True,
    )
    return redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("starting lifespan")
    app.state.redis_client = await setup_redis_client()
    app.state.sync_redis_client = setup_sync_redis_client()
    queue_service = RedisQueueService(
        redis_url=settings.REDIS_URL, email_config=email_config)
    background_task = asyncio.create_task(queue_service.start_processing())

    app.state.queue_service = queue_service
    yield
    background_task.cancel()
    await app.state.redis_client.close()
    try:
        await background_task
    except asyncio.CancelledError:
        pass
    await queue_service.redis_client.close()
    app.state.sync_redis_client.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)


app.add_middleware(EventHandlerASGIMiddleware, handlers=[local_handler])

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    transactions.router,
    prefix=f"{settings.API_V1_STR}/transactions",
    tags=["transactions"]
)

app.include_router(
    users.router,
    prefix=f"{settings.API_V1_STR}/users",
    tags=["users"]
)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
