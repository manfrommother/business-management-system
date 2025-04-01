import sqlalchemy as sa
from sqlalchemy.sql import func

from app.db.base_model import Base


class Metric(Base):
    __tablename__ = "metrics"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    name = sa.Column(sa.String, unique=True, index=True, nullable=False)
    description = sa.Column(sa.Text, nullable=True)
    calculation_logic = sa.Column(sa.String, nullable=True) # Info on how it's calculated
    aggregation_level = sa.Column(sa.String, index=True) # e.g., 'company', 'department', 'user', 'task'
    granularity = sa.Column(sa.String, index=True) # e.g., 'daily', 'weekly', 'monthly'

    # Historical data could be linked here or stored separately (e.g., in AnalyticsData or ClickHouse)
    # Example relationship (if storing calculated values here):
    # history = relationship("MetricValue", back_populates="metric")

    created_at = sa.Column(sa.DateTime(timezone=True), server_default=func.now())
    updated_at = sa.Column(sa.DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# Potentially a separate table for historical metric values if not using AnalyticsData
# class MetricValue(Base):
#     __tablename__ = "metric_values"
#     id = sa.Column(sa.Integer, primary_key=True)
#     metric_id = sa.Column(sa.Integer, sa.ForeignKey('metrics.id'))
#     value = sa.Column(sa.Float, nullable=False)
#     timestamp = sa.Column(sa.DateTime(timezone=True), index=True)
#     dimensions = sa.Column(sa.JSON) # Store dimensions like company_id, user_id here
#     metric = relationship("Metric", back_populates="history") 