# task-service/app/api/v1/api.py
from fastapi import APIRouter

# Импортируем роутеры эндпоинтов
from app.api.v1.endpoints import tasks, comments, attachments, evaluations, history, analytics # Добавляем analytics

api_router = APIRouter()

# Подключаем роутеры задач
api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])

# Подключаем роутеры комментариев
# Эндпоинты для /tasks/{task_id}/comments
api_router.include_router(
    comments.task_comments_router, 
    prefix="/tasks/{task_id}/comments", 
    tags=["Task Comments"]
)
# Эндпоинты для /comments/{comment_id}
api_router.include_router(
    comments.comments_router,
    prefix="/comments",
    tags=["Comments (Direct Access)"]
)

# Подключаем роутеры вложений
api_router.include_router(
    attachments.task_attachments_router,
    prefix="/tasks/{task_id}/attachments",
    tags=["Task Attachments"]
)
api_router.include_router(
    attachments.comment_attachments_router,
    prefix="/comments/{comment_id}/attachments",
    tags=["Comment Attachments"]
)
api_router.include_router(
    attachments.attachments_router,
    prefix="/attachments",
    tags=["Attachments (Direct Access)"]
)

# Подключаем роутеры оценок
# Эндпоинт для оценки конкретной задачи
api_router.include_router(
    evaluations.evaluate_task_router,
    prefix="/tasks/{task_id}/evaluate", # Вложенный путь
    tags=["Task Evaluation"]
)
# Эндпоинты для получения списков оценок
api_router.include_router(
    evaluations.evaluations_list_router, 
    prefix="", # Префикс не нужен, т.к. пути полные (/users/..., /departments/...)
    tags=["Evaluations Lists"]
)

# Подключаем роутер истории
api_router.include_router(history.router, tags=["Task History"]) # Префикс уже в history.py

# Подключаем роутер аналитики
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

# Можно добавить другие роутеры (аналитика) сюда же 