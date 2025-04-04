from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import all models here for Alembic discoverability
# Need to make sure the paths are correct relative to the project root
# when running alembic commands.
from app.db.models.analytics_data import AnalyticsData
from app.db.models.metrics import Metric
from app.db.models.dashboard import Dashboard
from app.db.models.report import Report 