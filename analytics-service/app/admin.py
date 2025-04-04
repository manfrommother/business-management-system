# flake8: noqa
from sqladmin import ModelView
from app.db.models.analytics_data import AnalyticsData
from app.db.models.metrics import Metric
from app.db.models.report import Report
from app.db.models.dashboard import Dashboard


class AnalyticsDataAdmin(ModelView, model=AnalyticsData):
    column_list = [AnalyticsData.id, AnalyticsData.event_type, AnalyticsData.timestamp, AnalyticsData.user_id, AnalyticsData.team_id]
    column_searchable_list = [AnalyticsData.event_type, AnalyticsData.user_id, AnalyticsData.team_id]
    column_sortable_list = [AnalyticsData.timestamp, AnalyticsData.event_type]
    name = "Данные Аналитики"
    name_plural = "Данные Аналитики"
    icon = "fa-solid fa-database"


class MetricAdmin(ModelView, model=Metric):
    column_list = [Metric.id, Metric.name, Metric.value, Metric.timestamp, Metric.team_id, Metric.department_id]
    column_searchable_list = [Metric.name, Metric.team_id, Metric.department_id]
    column_sortable_list = [Metric.name, Metric.timestamp, Metric.value]
    name = "Метрика"
    name_plural = "Метрики"
    icon = "fa-solid fa-chart-line"


class ReportAdmin(ModelView, model=Report):
    column_list = [Report.id, Report.name, Report.generated_at, Report.team_id, Report.created_by]
    column_searchable_list = [Report.name, Report.team_id, Report.created_by]
    column_sortable_list = [Report.name, Report.generated_at]
    name = "Отчет"
    name_plural = "Отчеты"
    icon = "fa-solid fa-file-alt"


class DashboardAdmin(ModelView, model=Dashboard):
    column_list = [Dashboard.id, Dashboard.name, Dashboard.team_id, Dashboard.created_by]
    column_searchable_list = [Dashboard.name, Dashboard.team_id, Dashboard.created_by]
    column_sortable_list = [Dashboard.name, Dashboard.created_at]
    name = "Дашборд"
    name_plural = "Дашборды"
    icon = "fa-solid fa-tachometer-alt" 