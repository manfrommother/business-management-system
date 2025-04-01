from pydantic import BaseModel
from typing import Optional


class BaseSchema(BaseModel):
    class Config:
        from_attributes = True # Pydantic V2, замена orm_mode


class BaseSchemaWithId(BaseSchema):
    id: int 