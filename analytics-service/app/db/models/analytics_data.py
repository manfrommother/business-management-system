import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_model import Base


class AnalyticsData(Base):
    __tablename__ = "analytics_data"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    metric_key = sa.Column(sa.String, index=True, nullable=False)
    metric_value = sa.Column(sa.JSON, nullable=False) # Flexible value store
    timestamp = sa.Column(sa.DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Dimensions (Foreign Keys to other services/entities)
    # These might store IDs referencing entities in other services.
    # Consider how to handle potential inconsistencies if IDs change.
    company_id = sa.Column(sa.Integer, index=True, nullable=True)
    department_id = sa.Column(sa.Integer, index=True, nullable=True)
    user_id = sa.Column(sa.Integer, index=True, nullable=True)
    task_id = sa.Column(sa.Integer, index=True, nullable=True) 
    # Add other relevant dimensions as needed, e.g., project_id

    # Relationships (Optional, if needed within this service)
    # Example: If metrics are directly related
    # related_metrics = relationship("Metric", back_populates="data_source")

    # Metadata
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=func.now())
    updated_at = sa.Column(sa.DateTime(timezone=True), server_default=func.now(), onupdate=func.now()) 