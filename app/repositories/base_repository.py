# base_repository.py
from typing import Generic, Type, TypeVar, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from pydantic import BaseModel

from app.db.database import Base
from app.db.transaction_model import Transaction

# Declare a generic variable for the model type
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, db: AsyncSession, model: Type[ModelType]):
        self.db = db
        self.model = model

    async def get(self, id: int) -> Optional[ModelType]:
        """Fetch an entity by its ID."""
        query = select(self.model).where(self.model.id == id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100, order_by: Optional[str] = None, other_filters: Optional[dict] = None) -> List[ModelType]:
        """Fetch all entities, with optional pagination."""
        query = select(self.model).offset(skip).limit(limit)
        if order_by:
            query = query.order_by(order_by)
        if other_filters:
            query = query.where(**other_filters)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create a new entity."""
        db_obj = self.model(**obj_in.model_dump())  # Convert schema to dict
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)  # Refresh to get the new ID
        return db_obj

    async def update(self, db_obj: ModelType, obj_in: UpdateSchemaType) -> ModelType:
        """Update an existing entity."""
        obj_data = db_obj.__dict__
        update_data = obj_in.dict(exclude_unset=True)

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, id: int) -> ModelType:
        """Delete an entity by its ID."""
        obj = await self.get(id)
        if obj:
            await self.db.delete(obj)
            await self.db.commit()
        return obj