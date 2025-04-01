import sqlalchemy as sa
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB # Use JSONB for better performance with JSON

from app.db.base_model import Base


class Dashboard(Base):
    __tablename__ = "dashboards"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    name = sa.Column(sa.String, nullable=False)
    description = sa.Column(sa.Text, nullable=True)
    # Store dashboard layout and components configuration as JSON
    configuration = sa.Column(JSONB, nullable=False, default={})
    
    # Who owns/created this dashboard?
    # Link to User ID (assuming user info comes from User Service)
    owner_id = sa.Column(sa.Integer, index=True, nullable=False) 
    # Could also link to company/department if dashboards are shared
    # company_id = sa.Column(sa.Integer, index=True, nullable=True)

    created_at = sa.Column(sa.DateTime(timezone=True), server_default=func.now())
    updated_at = sa.Column(sa.DateTime(timezone=True), server_default=func.now(), onupdate=func.now()) 