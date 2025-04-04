# task-service/app/schemas/analytics.py
from typing import Optional, Dict, List

from pydantic import BaseModel, Field

# Схема для статистики по задачам
class TasksAnalytics(BaseModel):
    total_tasks: int = Field(..., description="Общее количество активных задач")
    tasks_by_status: Dict[str, int] = Field(..., description="Количество задач по статусам")
    overdue_tasks: int = Field(..., description="Количество просроченных задач (срок < сегодня, статус не DONE/CANCELLED)")
    # Можно добавить другие метрики: среднее время выполнения, и т.д.

# Схема для данных об эффективности (на основе оценок)
class AverageScores(BaseModel):
    avg_timeliness: Optional[float] = Field(None, description="Средняя оценка своевременности")
    avg_quality: Optional[float] = Field(None, description="Средняя оценка качества")
    avg_completeness: Optional[float] = Field(None, description="Средняя оценка полноты")
    total_evaluated: int = Field(..., description="Количество оцененных задач")

class PerformanceAnalytics(BaseModel):
    # Можно возвращать данные по компании, отделу, пользователю
    # Для примера сделаем общую по компании и опционально по пользователю/отделу
    company_avg_scores: AverageScores
    department_avg_scores: Optional[AverageScores] = None
    user_avg_scores: Optional[AverageScores] = None

# Схема для данных о загруженности (упрощенная версия)
class WorkloadAnalytics(BaseModel):
    tasks_per_assignee: Dict[str, int] = Field(..., description="Количество активных задач на каждого исполнителя (ID -> Count)")
    # Можно добавить более сложные метрики: задачи со скорым дедлайном, и т.д. 