from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, update

from app.db.base_class import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        result = await db.execute(select(self.model).filter(self.model.id == id))
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        result = await db.execute(
            select(self.model)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True) # Pydantic v2
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: int) -> Optional[ModelType]:
        # First, get the object to return it later (optional)
        obj = await self.get(db=db, id=id)
        if obj:
            await db.delete(obj) # Use instance deletion for cascades, etc.
            # Альтернатива: await db.execute(delete(self.model).where(self.model.id == id))
            await db.commit()
        return obj

    async def mark_as_deleted(self, db: AsyncSession, *, id: int) -> Optional[ModelType]:
        """Marks an object as deleted if the model has an 'is_deleted' flag."""
        if not hasattr(self.model, 'is_deleted'):
            raise AttributeError(f"Model {self.model.__name__} does not have 'is_deleted' attribute.")

        # Update the is_deleted flag
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(is_deleted=True)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(stmt)
        await db.commit()

        # Return the updated object
        return await self.get(db=db, id=id)

    async def restore(self, db: AsyncSession, *, id: int) -> Optional[ModelType]:
        """Restores a soft-deleted object if the model has an 'is_deleted' flag."""
        if not hasattr(self.model, 'is_deleted'):
            raise AttributeError(f"Model {self.model.__name__} does not have 'is_deleted' attribute.")

        # Update the is_deleted flag
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .where(self.model.is_deleted == True)
            .values(is_deleted=False)
            .execution_options(synchronize_session="fetch")
        )
        result = await db.execute(stmt)
        await db.commit()

        if result.rowcount > 0:
            return await self.get(db=db, id=id)
        return None # Object not found or not deleted 