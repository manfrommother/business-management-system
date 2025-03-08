from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy import MetaData


convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)

class CustomBase:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()
    
Base = declarative_base(cls=CustomBase, metadata=metadata)