from typing import Generic, Type, TypeVar, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import Select, delete
from pydantic import BaseModel
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.db.database import Base
from app.db.transaction_model import Transaction

# Set up logging
logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, db: AsyncSession, model: Type[ModelType]):
        if not isinstance(db, AsyncSession):
            raise ValueError("db must be an instance of AsyncSession")
        self.db = db
        self.model = model
        
        
    def get_db(self) -> AsyncSession:
        """Get the database session."""
        return self.db
    
    def get_model(self) -> Type[ModelType]:
        """Get the model class."""
        return self.model
    

    async def get(self, id: int, related: Optional[str] = None) -> Optional[ModelType]:
        """Fetch an entity by its ID."""
        try:
            if not self.db or not self.db.is_active:
                raise ValueError("Database session is not active")

            query = select(self.model).where(self.model.id == id)
            if related:
                query = query.options(selectinload(
                    getattr(self.model, related)))

            result = await self.db.execute(query)
            item = result.scalars().first()

            if item is None:
                logger.debug(f"No {self.model.__name__} found with id {id}")

            return item

        except SQLAlchemyError as e:
            logger.error(f"Database error in get(): {str(e)}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error in get(): {str(e)}")
            raise

    async def get_all(self, skip: int = 0, limit: int = 100, order_by: Optional[str] = None, other_filters: Optional[dict] = None) -> List[ModelType]:
        """Fetch all entities, with optional pagination."""
        try:
            if not self.db or not self.db.is_active:
                raise ValueError("Database session is not active")

            query = select(self.model).offset(skip).limit(limit)
            if order_by:
                query = query.order_by(getattr(self.model, order_by))
            if other_filters:
                query = query.filter_by(**other_filters)

            result = await self.db.execute(query)
            return result.scalars().all()

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_all(): {str(e)}")
            raise

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create a new entity."""
        try:
            if not self.db or not self.db.is_active:
                raise ValueError("Database session is not active")

            obj_data = obj_in.model_dump()
            db_obj = self.model(**obj_data)
            self.db.add(db_obj)
            await self.db.commit()
            await self.db.refresh(db_obj)
            return db_obj

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error in create(): {str(e)}")
            raise

    async def update(self, db_obj: ModelType, obj_in: UpdateSchemaType) -> ModelType:
        """Update an existing entity."""
        try:
            if not self.db or not self.db.is_active:
                raise ValueError("Database session is not active")

            obj_data = obj_in.model_dump(exclude_unset=True)
            for field, value in obj_data.items():
                setattr(db_obj, field, value)

            self.db.add(db_obj)
            await self.db.commit()
            await self.db.refresh(db_obj)
            return db_obj

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error in update(): {str(e)}")
            raise

    async def delete(self, id: int) -> Optional[ModelType]:
        """Delete an entity by its ID."""
        try:
            if not self.db or not self.db.is_active:
                raise ValueError("Database session is not active")

            obj = await self.get(id)
            if obj:
                await self.db.delete(obj)
                await self.db.commit()
                return obj
            return None

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error in delete(): {str(e)}")
            raise
        
    async def execute(self, query: Select) -> Optional[dict]:
        """Execute a raw SQL query."""
        try:
            if not self.db or not self.db.is_active:
                raise ValueError("Database session is not active")
            
            result = await self.db.execute(query)
            row = result.mappings().first()
            if row is None:
                return None
            return dict(row)

        except SQLAlchemyError as e:
            logger.error(f"Database error in execute(): {str(e)}")
            raise