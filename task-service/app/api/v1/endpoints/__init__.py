# task-service/app/api/v1/endpoints/__init__.py
# Импортируем роутеры эндпоинтов
from . import tasks
from . import comments # Раскомментируем comments
from . import attachments # Раскомментируем attachments
from . import evaluations # Раскомментируем evaluations
from . import history # Раскомментируем history
from . import analytics # Раскомментируем analytics
# from . import analytics # Раскомментировать при добавлении 