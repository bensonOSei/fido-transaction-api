from app.db.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from sqlalchemy.ext.asyncio import AsyncSession



class UserService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)

    async def create_user(self, data: UserCreate) -> User:
        user = await self.user_repo.create(data)
        return user

    async def get_user_balance(self, user_id: int) -> int:
        user = await self.user_repo.get(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        return user.balance_cents

    async def credit_user(self, user_id: int, amount: int) -> User:
        user = await self.user_repo.get(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        user.balance += amount
        await self.user_repo.update(user, UserUpdate(balance=user.balance/100,full_name=user.full_name))
        # user.balance = user.balance_cents
        return user

    async def debit_user(self, user_id: int, amount: int) -> User:
        user = await self.user_repo.get(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        user.balance -= amount
        await self.user_repo.update(user, UserUpdate(balance=user.balance/100,full_name=user.full_name))
        return user
        